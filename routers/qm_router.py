from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from auth import get_current_quiz_master
from models import User, Session, Deck, Slide, SlideMapping, TeamSession, Score, ScoreEvent
from schemas import SessionResponse, TimerStart, ScoreAdjustment
import redis.asyncio as redis
from config import settings
from services.timer_service import timer_service

router = APIRouter()


async def get_redis():
    return await redis.from_url(settings.redis_url, decode_responses=True)


async def broadcast_slide_change(session_id: int, slide_id: int, mode: str):
    """Broadcast slide change to all WebSocket clients"""
    from routers.ws_router import manager
    from database import get_async_session_maker

    # Get slide details for broadcast
    async_session = get_async_session_maker()
    async with async_session() as session:
        result = await session.execute(select(Slide).where(Slide.id == slide_id))
        slide = result.scalar_one_or_none()

        if slide:
            await manager.broadcast_to_session(
                session_id,
                {
                    "event": "slide.update",
                    "slide": {
                        "id": slide.id,
                        "png_path": slide.png_path,
                        "slide_index": slide.slide_index
                    },
                    "mode": mode
                }
            )


# ============ Session Control ============

@router.get("/sessions/live", response_model=List[SessionResponse])
async def get_live_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Get live sessions"""
    result = await db.execute(
        select(Session).where(Session.status.in_(["draft", "live"]))
    )
    sessions = result.scalars().all()
    return sessions


# ============ Slide Navigation ============

@router.post("/sessions/{session_id}/slide/next")
async def next_slide(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Move to next question slide"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If no current slide, start with first slide from question deck
    if not session.current_slide_id:
        # Find first question deck
        result = await db.execute(
            select(Deck)
            .where(Deck.session_id == session_id, Deck.deck_type == "question")
            .limit(1)
        )
        question_deck = result.scalar_one_or_none()

        if question_deck:
            # Get first slide
            result = await db.execute(
                select(Slide)
                .where(Slide.deck_id == question_deck.id)
                .order_by(Slide.slide_index)
                .limit(1)
            )
            first_slide = result.scalar_one_or_none()

            if first_slide:
                session.current_slide_id = first_slide.id
                session.mode = "question"
                await db.commit()

                # Broadcast slide change
                await broadcast_slide_change(session_id, first_slide.id, "question")

                return {"message": "Started quiz with first slide", "slide_id": first_slide.id}

        raise HTTPException(status_code=400, detail="No question deck found")

    # Get current slide and find next question slide
    result = await db.execute(select(Slide).where(Slide.id == session.current_slide_id))
    current_slide = result.scalar_one_or_none()

    if current_slide:
        # Find next slide in same deck
        result = await db.execute(
            select(Slide)
            .where(
                Slide.deck_id == current_slide.deck_id,
                Slide.slide_index > current_slide.slide_index
            )
            .order_by(Slide.slide_index)
            .limit(1)
        )
        next_slide = result.scalar_one_or_none()

        if next_slide:
            session.current_slide_id = next_slide.id
            session.mode = "question"
            await db.commit()

            # Broadcast slide change
            await broadcast_slide_change(session_id, next_slide.id, "question")

            return {"message": "Moved to next slide", "slide_id": next_slide.id}

    raise HTTPException(status_code=400, detail="No next slide available")


@router.post("/sessions/{session_id}/slide/prev")
async def prev_slide(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Move to previous slide"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.current_slide_id:
        result = await db.execute(select(Slide).where(Slide.id == session.current_slide_id))
        current_slide = result.scalar_one_or_none()

        if current_slide:
            # Find previous slide
            result = await db.execute(
                select(Slide)
                .where(
                    Slide.deck_id == current_slide.deck_id,
                    Slide.slide_index < current_slide.slide_index
                )
                .order_by(Slide.slide_index.desc())
                .limit(1)
            )
            prev_slide_result = result.scalar_one_or_none()

            if prev_slide_result:
                session.current_slide_id = prev_slide_result.id
                session.mode = "question"
                await db.commit()

                # Broadcast slide change
                await broadcast_slide_change(session_id, prev_slide_result.id, "question")

                return {"message": "Moved to previous slide", "slide_id": prev_slide_result.id}

    raise HTTPException(status_code=400, detail="No previous slide available")


@router.post("/sessions/{session_id}/slide/reveal")
async def reveal_answer(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Show answer slide using mapping"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.current_slide_id:
        raise HTTPException(status_code=400, detail="No current slide")

    # Find answer mapping
    result = await db.execute(
        select(SlideMapping)
        .where(SlideMapping.question_slide_id == session.current_slide_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(status_code=400, detail="No answer mapping for this slide")

    session.current_slide_id = mapping.answer_slide_id
    session.mode = "answer"
    await db.commit()

    # Broadcast slide change
    await broadcast_slide_change(session_id, mapping.answer_slide_id, "answer")

    return {"message": "Answer revealed", "slide_id": mapping.answer_slide_id}


@router.post("/sessions/{session_id}/slide/jump")
async def jump_to_slide(
    session_id: int,
    slide_id: int,
    mode: str = "question",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Jump to specific slide"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify slide exists
    result = await db.execute(select(Slide).where(Slide.id == slide_id))
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    session.current_slide_id = slide_id
    session.mode = mode
    await db.commit()

    # Broadcast slide change
    await broadcast_slide_change(session_id, slide_id, mode)

    return {"message": "Jumped to slide", "slide_id": slide_id}


# ============ Timer Control ============

@router.post("/sessions/{session_id}/timer/start")
async def start_timer(
    session_id: int,
    timer_data: TimerStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Start timer"""
    # Get duration (from request, slide default, or round default)
    duration_ms = timer_data.duration_ms or 30000  # Default 30 seconds

    # Use timer service to start timer with background countdown task
    await timer_service.start_timer(
        session_id=session_id,
        duration_ms=duration_ms,
        fastest_finger=timer_data.fastest_finger or False
    )

    return {"message": "Timer started", "duration_ms": duration_ms}


@router.post("/sessions/{session_id}/timer/pause")
async def pause_timer(
    session_id: int,
    current_user: User = Depends(get_current_quiz_master)
):
    """Pause timer"""
    success = await timer_service.pause_timer(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="No active timer to pause")

    return {"message": "Timer paused"}


@router.post("/sessions/{session_id}/timer/reset")
async def reset_timer(
    session_id: int,
    current_user: User = Depends(get_current_quiz_master)
):
    """Reset timer"""
    await timer_service.reset_timer(session_id)

    return {"message": "Timer reset"}


# ============ Buzzer Control ============

@router.post("/sessions/{session_id}/buzzer/lock")
async def toggle_buzzer_lock(
    session_id: int,
    locked: bool,
    current_user: User = Depends(get_current_quiz_master)
):
    """Lock or unlock buzzers"""
    r = await get_redis()
    buzzer_key = f"buzzer:lock:{session_id}"

    if locked:
        # Auto-unlock after 1 second to remove manual unlock requirement
        await r.set(buzzer_key, "1", ex=1)
    else:
        await r.delete(buzzer_key)
        # Also clear buzzer queue
        await r.delete(f"buzzer:{session_id}")
        await r.delete(f"buzzer:first:{session_id}")

        # Broadcast buzzer cleared event to all clients
        from routers.ws_router import broadcast_event
        await broadcast_event(session_id, {
            "event": "buzzer.cleared"
        })

    return {"message": f"Buzzers {'locked' if locked else 'unlocked'}"}


# ============ Score Management ============

@router.post("/sessions/{session_id}/scores/{team_id}")
async def adjust_score(
    session_id: int,
    team_id: int,
    score_adj: ScoreAdjustment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Adjust team score"""
    # Get team session
    result = await db.execute(
        select(TeamSession)
        .where(
            TeamSession.session_id == session_id,
            TeamSession.team_id == team_id
        )
    )
    team_session = result.scalar_one_or_none()
    if not team_session:
        raise HTTPException(status_code=404, detail="Team not in this session")

    # Get current score
    result = await db.execute(
        select(Score).where(Score.team_session_id == team_session.id)
    )
    score = result.scalar_one_or_none()
    if not score:
        # Create score if doesn't exist
        score = Score(team_session_id=team_session.id, total=0)
        db.add(score)
        await db.flush()

    # Update score
    score.total += score_adj.delta

    # Log score event
    score_event = ScoreEvent(
        team_session_id=team_session.id,
        round_id=score_adj.round_id or 1,  # Default to round 1 if not specified
        actor_user_id=current_user.id,
        delta=score_adj.delta,
        reason=score_adj.reason
    )
    db.add(score_event)

    await db.commit()

    # Broadcast score update to all clients
    from routers.ws_router import broadcast_event
    await broadcast_event(session_id, {
        "event": "score.update",
        "team_id": team_id,
        "total": score.total
    })

    return {
        "message": "Score updated",
        "team_id": team_id,
        "new_total": score.total
    }


@router.post("/sessions/{session_id}/scores/{team_id}/undo")
async def undo_score(
    session_id: int,
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Undo last score event for team"""
    # Get team session
    result = await db.execute(
        select(TeamSession)
        .where(
            TeamSession.session_id == session_id,
            TeamSession.team_id == team_id
        )
    )
    team_session = result.scalar_one_or_none()
    if not team_session:
        raise HTTPException(status_code=404, detail="Team not in this session")

    # Get last score event
    result = await db.execute(
        select(ScoreEvent)
        .where(ScoreEvent.team_session_id == team_session.id)
        .order_by(ScoreEvent.created_at.desc())
        .limit(1)
    )
    last_event = result.scalar_one_or_none()
    if not last_event:
        raise HTTPException(status_code=400, detail="No score events to undo")

    # Get current score
    result = await db.execute(
        select(Score).where(Score.team_session_id == team_session.id)
    )
    score = result.scalar_one_or_none()

    # Revert score
    if score:
        score.total -= last_event.delta

    # Delete score event
    await db.delete(last_event)
    await db.commit()

    # Broadcast score update to all clients
    from routers.ws_router import broadcast_event
    await broadcast_event(session_id, {
        "event": "score.update",
        "team_id": team_id,
        "total": score.total if score else 0
    })

    return {
        "message": "Score event undone",
        "team_id": team_id,
        "new_total": score.total if score else 0
    }

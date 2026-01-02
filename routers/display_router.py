from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import get_db
from models import Session, Slide, Round, TeamSession, Score, Team, AdminSettings
from schemas import DisplaySnapshot, SlideResponse, RoundResponse, ScoreResponse
import redis.asyncio as redis
from config import settings

router = APIRouter()


async def get_redis():
    return await redis.from_url(settings.redis_url, decode_responses=True)


@router.get("/sessions/{session_id}/snapshot")
async def get_display_snapshot(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get complete snapshot for main display screen"""
    # Get session
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get current slide
    current_slide = None
    if session.current_slide_id:
        result = await db.execute(select(Slide).where(Slide.id == session.current_slide_id))
        current_slide = result.scalar_one_or_none()

    # Get current round
    current_round = None
    if session.current_round_id:
        result = await db.execute(select(Round).where(Round.id == session.current_round_id))
        current_round = result.scalar_one_or_none()

    # Get scores
    result = await db.execute(
        select(TeamSession, Team, Score)
        .join(Team, TeamSession.team_id == Team.id)
        .outerjoin(Score, Score.team_session_id == TeamSession.id)
        .where(TeamSession.session_id == session_id)
        .order_by(Team.seat_order, Team.name)
    )

    scores = []
    for team_session, team, score in result:
        scores.append({
            "team_id": team.id,
            "team_name": team.name,
            "total": score.total if score else 0,
            "updated_at": score.updated_at if score else None
        })

    # Get timer state from Redis
    r = await get_redis()
    timer_key = f"timer:{session_id}"
    timer_data = await r.hgetall(timer_key)
    timer_state = None
    if timer_data:
        timer_state = {
            "state": timer_data.get("state"),
            "remaining_ms": int(timer_data.get("remaining_ms", 0)),
            "duration_ms": int(timer_data.get("duration_ms", 0))
        }

    # Get buzzer queue from Redis
    buzzer_key = f"buzzer:{session_id}"
    buzzer_members = await r.zrange(buzzer_key, 0, -1, withscores=True)
    buzzer_queue = []

    for member, timestamp in buzzer_members:
        team_id, device_id = member.split(":", 1)
        # Get team name
        result = await db.execute(select(Team).where(Team.id == int(team_id)))
        team = result.scalar_one_or_none()

        if team:
            placement = await r.zrank(buzzer_key, member)
            buzzer_queue.append({
                "team_id": team.id,
                "team_name": team.name,
                "placement": placement + 1 if placement is not None else 0,
                "timestamp": timestamp
            })

    return {
        "session_id": session.id,
        "session_name": session.name,
        "banner_text": session.banner_text,
        "current_slide": SlideResponse.from_orm(current_slide) if current_slide else None,
        "current_round": RoundResponse.from_orm(current_round) if current_round else None,
        "mode": session.mode,
        "scores": scores,
        "timer_state": timer_state,
        "buzzer_queue": buzzer_queue
    }


@router.get("/display-mode")
async def get_display_mode(db: AsyncSession = Depends(get_db)):
    """Get display mode setting (public endpoint for display screens)"""
    result = await db.execute(
        select(AdminSettings).where(AdminSettings.setting_key == "display_mode")
    )
    setting = result.scalar_one_or_none()

    if not setting:
        return {"display_mode": "png_slides"}

    return {"display_mode": setting.setting_value}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database import get_db
from auth import get_current_team
from models import Team, Session, TeamSession, Score, BuzzerEvent
import redis.asyncio as redis
from config import settings

router = APIRouter()


async def get_redis():
    return await redis.from_url(settings.redis_url, decode_responses=True)


@router.get("/sessions/current")
async def get_current_session(
    db: AsyncSession = Depends(get_db),
    current_team: Team = Depends(get_current_team)
):
    """Get current session for team"""
    # Find active session for this team
    result = await db.execute(
        select(TeamSession, Session)
        .join(Session, TeamSession.session_id == Session.id)
        .where(
            TeamSession.team_id == current_team.id,
            Session.status == "live"
        )
    )
    team_session_row = result.first()

    if not team_session_row:
        raise HTTPException(status_code=404, detail="No active session found")

    team_session, session = team_session_row

    # Get team's score
    result = await db.execute(
        select(Score).where(Score.team_session_id == team_session.id)
    )
    score = result.scalar_one_or_none()

    return {
        "session_id": session.id,
        "session_name": session.name,
        "team_id": current_team.id,
        "team_name": current_team.name,
        "score": score.total if score else 0
    }


@router.post("/sessions/{session_id}/buzz")
async def buzz(
    session_id: int,
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_team: Team = Depends(get_current_team)
):
    """Team buzzes in (fallback HTTP endpoint)"""
    r = await get_redis()

    # Check if buzzers are locked
    lock_key = f"buzzer:lock:{session_id}"
    if await r.exists(lock_key):
        raise HTTPException(status_code=400, detail="Buzzers are locked")

    # Add to sorted set with timestamp as score
    buzzer_key = f"buzzer:{session_id}"
    timestamp = datetime.utcnow().timestamp()
    member = f"{current_team.id}:{device_id}"

    # Use ZADD NX to only add if not exists
    added = await r.zadd(buzzer_key, {member: timestamp}, nx=True)

    if not added:
        return {"message": "Already buzzed", "placement": None}

    # Get placement
    rank = await r.zrank(buzzer_key, member)
    placement = rank + 1 if rank is not None else None

    # Save to database
    buzzer_event = BuzzerEvent(
        session_id=session_id,
        team_id=current_team.id,
        device_id=device_id,
        placement=placement
    )
    db.add(buzzer_event)
    await db.commit()

    return {
        "message": "Buzz registered",
        "placement": placement,
        "timestamp": timestamp
    }

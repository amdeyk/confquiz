from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from database import get_db
from auth import (
    authenticate_user, create_access_token, get_team_by_code,
    get_password_hash
)
from schemas import UserLogin, TeamLogin, Token
from config import settings
import redis.asyncio as redis

router = APIRouter()

# Redis connection for device tracking
redis_client = None


async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Admin/Quiz Master login"""
    user = await authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, role=user.role)


@router.post("/teams/login", response_model=Token)
async def team_login(
    team_login: TeamLogin,
    db: AsyncSession = Depends(get_db)
):
    """Team login with unique code"""
    team = await get_team_by_code(db, team_login.code)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid team code"
        )

    # Check device limit (max 2 devices per team)
    r = await get_redis()
    device_key = f"team:{team.id}:devices"
    device_count = await r.scard(device_key)

    if device_count >= 2:
        # Check if any devices are stale (no activity for 1 hour)
        devices = await r.smembers(device_key)
        # For now, just allow login - in production, implement proper device cleanup
        pass

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "team_id": team.id,
            "nickname": team_login.nickname,
            "role": "team"
        },
        expires_delta=access_token_expires
    )

    # Track device (using token as device ID for simplicity)
    await r.sadd(device_key, access_token[:20])  # Store first 20 chars as device ID
    await r.expire(device_key, 3600 * 24)  # Expire in 24 hours

    return Token(access_token=access_token, role="team")

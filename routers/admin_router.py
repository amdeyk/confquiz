from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from auth import get_current_admin, get_password_hash
from models import User, Team, Session, Round, TeamSession, Score
from schemas import (
    TeamCreate, TeamResponse, SessionCreate, SessionResponse,
    RoundCreate, RoundResponse, SessionUpdate, TeamUpdate
)

router = APIRouter()


# ============ Team Management ============

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new team"""
    # Check if code already exists
    result = await db.execute(select(Team).where(Team.code == team.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Team code already exists")

    new_team = Team(
        name=team.name,
        code=team.code,
        seat_order=team.seat_order
    )
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all teams"""
    result = await db.execute(select(Team).order_by(Team.seat_order, Team.name))
    teams = result.scalars().all()
    return teams


@router.patch("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update team details"""
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team_update.name is not None:
        team.name = team_update.name
    if team_update.is_active is not None:
        team.is_active = team_update.is_active
    if team_update.seat_order is not None:
        team.seat_order = team_update.seat_order

    await db.commit()
    await db.refresh(team)
    return team


# ============ Session Management ============

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new quiz session"""
    new_session = Session(
        name=session.name,
        banner_text=session.banner_text,
        ppt_native_allowed=session.ppt_native_allowed,
        status="draft"
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return new_session


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get session details"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all sessions"""
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    return sessions


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update session details"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_update.name is not None:
        session.name = session_update.name
    if session_update.status is not None:
        if session_update.status not in ["draft", "live", "ended"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        session.status = session_update.status
    if session_update.banner_text is not None:
        session.banner_text = session_update.banner_text
    if session_update.ppt_native_allowed is not None:
        session.ppt_native_allowed = session_update.ppt_native_allowed

    await db.commit()
    await db.refresh(session)
    return session


# ============ Round Management ============

@router.post("/sessions/{session_id}/rounds", response_model=RoundResponse)
async def create_round(
    session_id: int,
    round_data: RoundCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new round in session"""
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate round type
    if round_data.type not in ["normal", "bonus", "penalty", "fastest"]:
        raise HTTPException(status_code=400, detail="Invalid round type")

    new_round = Round(
        session_id=session_id,
        name=round_data.name,
        type=round_data.type,
        timer_default_ms=round_data.timer_default_ms,
        scoring_presets=round_data.scoring_presets,
        order_index=round_data.order_index
    )
    db.add(new_round)
    await db.commit()
    await db.refresh(new_round)

    return new_round


@router.get("/sessions/{session_id}/rounds", response_model=List[RoundResponse])
async def list_rounds(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all rounds in session"""
    result = await db.execute(
        select(Round)
        .where(Round.session_id == session_id)
        .order_by(Round.order_index)
    )
    rounds = result.scalars().all()
    return rounds


# ============ Team-Session Assignment ============

@router.post("/sessions/{session_id}/teams")
async def assign_teams_to_session(
    session_id: int,
    team_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Assign teams to a session"""
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify all teams exist
    result = await db.execute(select(Team).where(Team.id.in_(team_ids)))
    teams = result.scalars().all()
    if len(teams) != len(team_ids):
        raise HTTPException(status_code=400, detail="Some teams not found")

    # Create team sessions and scores
    for team in teams:
        # Check if already assigned
        result = await db.execute(
            select(TeamSession).where(
                TeamSession.session_id == session_id,
                TeamSession.team_id == team.id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            team_session = TeamSession(
                session_id=session_id,
                team_id=team.id,
                starting_score=0
            )
            db.add(team_session)
            await db.flush()

            # Create score entry
            score = Score(
                team_session_id=team_session.id,
                total=0
            )
            db.add(score)

    await db.commit()

    return {"message": f"Assigned {len(teams)} teams to session"}


@router.post("/users/quiz-master")
async def create_quiz_master(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a quiz master user"""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=username,
        password_hash=get_password_hash(password),
        role="quiz_master"
    )
    db.add(new_user)
    await db.commit()

    return {"message": "Quiz master created successfully"}

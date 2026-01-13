from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from auth import (
    get_current_admin,
    get_current_quiz_master,
    get_current_presenter,
    get_current_user,
    get_password_hash
)
from models import User, Team, Session, Round, TeamSession, Score, AdminSettings
from schemas import (
    BandwidthStatusResponse,
    DisplayApprovalRequest,
    PresenterLiveKitTokenRequest,
    TeamCreate,
    TeamResponse,
    SessionCreate,
    SessionResponse,
    RoundCreate,
    RoundResponse,
    SessionUpdate,
    TeamUpdate,
    UserLogin
)
from config import settings
from services.bandwidth_monitor import get_bandwidth_status
from services.display_registry import approve_display, count_protected, list_displays
from services.livekit_tokens import create_livekit_token
from routers.ws_router import manager

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
    current_user: User = Depends(get_current_quiz_master)
):
    """Create a new quiz session (admin or quiz master)"""
    print(f"[DEBUG] Creating session: {session.name} by user {current_user.username} (role: {current_user.role})")

    # Use conference_name from settings if banner_text not provided
    banner = session.banner_text or settings.conference_name

    new_session = Session(
        name=session.name,
        banner_text=banner,
        ppt_native_allowed=session.ppt_native_allowed,
        status="draft"
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    print(f"[DEBUG] Session created successfully: ID={new_session.id}")
    return new_session


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Get session details (admin or quiz master)"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """List all sessions (admin or quiz master)"""
    print(f"[DEBUG] Listing sessions for user {current_user.username} (role: {current_user.role})")
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    print(f"[DEBUG] Found {len(sessions)} sessions")
    return sessions


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_quiz_master)
):
    """Update session details (admin or quiz master)"""
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
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a quiz master user"""
    print(f"[DEBUG] Creating quiz master - Username: {user_data.username}, Password length: {len(user_data.password)}")

    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"[DEBUG] Username '{user_data.username}' already exists")
        raise HTTPException(status_code=400, detail="Username already exists")

    print(f"[DEBUG] Creating new quiz master user: {user_data.username}")
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role="quiz_master"
    )
    db.add(new_user)
    await db.commit()

    print(f"[DEBUG] Quiz master '{user_data.username}' created successfully")
    return {"message": "Quiz master created successfully"}


# ============ Presenter Management ============

@router.post("/users/presenter")
async def create_presenter(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a presenter user"""
    print(f"[DEBUG] Creating presenter - Username: {user_data.username}")

    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"[DEBUG] Username '{user_data.username}' already exists")
        raise HTTPException(status_code=400, detail="Username already exists")

    print(f"[DEBUG] Creating new presenter user: {user_data.username}")
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role="presenter"
    )
    db.add(new_user)
    await db.commit()

    print(f"[DEBUG] Presenter '{user_data.username}' created successfully")
    return {"message": "Presenter created successfully"}


@router.get("/presenter/sessions")
async def get_presenter_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sessions for presenter (requires presenter or admin role)"""
    if current_user.role not in ["presenter", "admin"]:
        raise HTTPException(status_code=403, detail="Presenter or admin access required")

    # Get all sessions (draft and live)
    result = await db.execute(
        select(Session).where(Session.status.in_(["draft", "live"])).order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in sessions
    ]


@router.post("/presenter/livekit-token")
async def create_presenter_livekit_token(
    payload: PresenterLiveKitTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_presenter)
):
    """Create a LiveKit token for the presenter after protected displays are approved"""
    result = await db.execute(select(Session).where(Session.id == payload.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    protected_count = await count_protected(payload.session_id)
    if protected_count < 2:
        raise HTTPException(status_code=400, detail="At least 2 protected displays must be approved before presenting")

    room_name = f"{settings.livekit_room_prefix}-{payload.session_id}"
    try:
        token = create_livekit_token(
            identity=f"presenter_{current_user.id}",
            room=room_name,
            name=current_user.username,
            can_publish=True,
            can_subscribe=False,
            metadata={"role": "presenter", "session_id": payload.session_id, "user_id": current_user.id}
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "token": token,
        "livekit_url": settings.livekit_url,
        "room_name": room_name,
        "protected_count": protected_count
    }


# ============ LiveKit Display Approval ============

@router.get("/livekit/displays")
async def get_livekit_displays(
    session_id: int,
    current_user: User = Depends(get_current_admin)
):
    """List pending/approved displays for a session"""
    return {"displays": await list_displays(session_id)}


@router.post("/livekit/displays/{display_id}/approve")
async def approve_livekit_display(
    display_id: str,
    payload: DisplayApprovalRequest,
    current_user: User = Depends(get_current_admin)
):
    """Approve a display and issue LiveKit token"""
    role = payload.role.lower()
    if role not in ["protected", "normal"]:
        raise HTTPException(status_code=400, detail="Role must be 'protected' or 'normal'")

    registry = await approve_display(payload.session_id, display_id, role, current_user.username)
    room_name = f"{settings.livekit_room_prefix}-{payload.session_id}"
    try:
        token = create_livekit_token(
            identity=display_id,
            room=room_name,
            can_publish=False,
            can_subscribe=True,
            metadata={"role": role, "display_id": display_id, "session_id": payload.session_id}
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    await manager.send_to_display(display_id, {
        "event": "display.approved",
        "display_id": display_id,
        "role": role,
        "token": token,
        "livekit_url": settings.livekit_url,
        "room_name": room_name
    })

    await manager.broadcast_to_session(
        payload.session_id,
        {
            "event": "display.approved",
            "display_id": display_id,
            "role": role
        },
        role="admin"
    )

    return {"display": registry}


# ============ Bandwidth Monitoring ============

@router.get("/bandwidth/status", response_model=BandwidthStatusResponse)
async def get_bandwidth_status_admin(
    current_user: User = Depends(get_current_user)
):
    """Get current bandwidth usage (admin or presenter)"""
    if current_user.role not in ["admin", "presenter"]:
        raise HTTPException(status_code=403, detail="Admin or presenter access required")
    return await get_bandwidth_status()


# ============ Admin Settings Management ============

@router.get("/settings")
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all admin settings"""
    result = await db.execute(select(AdminSettings))
    settings = result.scalars().all()

    # Convert to dict for easier frontend consumption
    settings_dict = {s.setting_key: s.setting_value for s in settings}
    return settings_dict


@router.get("/settings/{key}")
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get a specific admin setting"""
    result = await db.execute(
        select(AdminSettings).where(AdminSettings.setting_key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    return {
        "setting_key": setting.setting_key,
        "setting_value": setting.setting_value,
        "updated_at": setting.updated_at
    }


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an admin setting and broadcast change"""
    result = await db.execute(
        select(AdminSettings).where(AdminSettings.setting_key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Update setting
    setting.setting_value = value
    await db.commit()

    # Broadcast setting change to all WebSocket clients
    from routers.ws_router import broadcast_settings_update
    await broadcast_settings_update(key, value)

    return {
        "message": "Setting updated successfully",
        "setting_key": key,
        "setting_value": value
    }

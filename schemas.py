from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Auth Schemas ============

class UserLogin(BaseModel):
    username: str
    password: str


class TeamLogin(BaseModel):
    code: str
    nickname: str = Field(max_length=50)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    team_id: Optional[int] = None
    role: Optional[str] = None


# ============ Team Schemas ============

class TeamCreate(BaseModel):
    name: str
    code: str
    seat_order: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    seat_order: Optional[int] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    seat_order: Optional[int]

    class Config:
        from_attributes = True


# ============ Session Schemas ============

class SessionCreate(BaseModel):
    name: str
    banner_text: Optional[str] = "AISMOC 2026 QUIZ"
    ppt_native_allowed: Optional[bool] = False


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None  # 'draft', 'live', 'ended'
    banner_text: Optional[str] = None
    ppt_native_allowed: Optional[bool] = None


class SessionResponse(BaseModel):
    id: int
    name: str
    status: str
    banner_text: str
    current_round_id: Optional[int]
    current_slide_id: Optional[int]
    mode: str
    ppt_native_allowed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Round Schemas ============

class RoundCreate(BaseModel):
    name: str
    type: str  # 'normal', 'bonus', 'penalty', 'fastest'
    timer_default_ms: Optional[int] = None
    scoring_presets: Dict[str, List[int]]  # {"positive":[10,20],"negative":[-5]}
    order_index: int


class RoundUpdate(BaseModel):
    name: Optional[str] = None
    timer_default_ms: Optional[int] = None
    scoring_presets: Optional[Dict[str, List[int]]] = None


class RoundResponse(BaseModel):
    id: int
    name: str
    type: str
    timer_default_ms: Optional[int]
    scoring_presets: Dict[str, List[int]]
    order_index: int

    class Config:
        from_attributes = True


# ============ Slide Schemas ============

class SlideResponse(BaseModel):
    id: int
    deck_id: int
    slide_index: int
    png_path: str
    thumb_path: str
    default_timer_ms: Optional[int]

    class Config:
        from_attributes = True


class SlideMappingCreate(BaseModel):
    question_slide_id: int
    answer_slide_id: int
    answer_timer_override_ms: Optional[int] = None


# ============ Deck Schemas ============

class DeckResponse(BaseModel):
    id: int
    session_id: int
    deck_type: str
    ppt_path: str
    native_required: bool
    slides: List[SlideResponse] = []

    class Config:
        from_attributes = True


# ============ Score Schemas ============

class ScoreAdjustment(BaseModel):
    delta: int
    reason: Optional[str] = None
    round_id: Optional[int] = None


class ScoreResponse(BaseModel):
    team_id: int
    team_name: str
    total: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Timer Schemas ============

class TimerStart(BaseModel):
    duration_ms: Optional[int] = None
    preset_id: Optional[int] = None
    fastest_finger: Optional[bool] = False


# ============ WebSocket Event Schemas ============

class WSEvent(BaseModel):
    event: str
    session_id: int
    data: Dict[str, Any]


class TimerTickEvent(BaseModel):
    event: str = "timer.tick"
    session_id: int
    state: str  # 'counting', 'paused', 'stopped'
    remaining_ms: int
    mode: Optional[str] = None


class BuzzerQueueItem(BaseModel):
    team_id: int
    team_name: str
    placement: int
    timestamp: datetime


class BuzzerQueueEvent(BaseModel):
    event: str = "buzzer.queue"
    queue: List[BuzzerQueueItem]
    locked: bool


# ============ Display Schemas ============

class DisplaySnapshot(BaseModel):
    session_id: int
    session_name: str
    banner_text: str
    current_slide: Optional[SlideResponse]
    current_round: Optional[RoundResponse]
    mode: str
    scores: List[ScoreResponse]
    timer_state: Optional[Dict[str, Any]]
    buzzer_queue: List[BuzzerQueueItem]

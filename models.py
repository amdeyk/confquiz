from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'admin' or 'quiz_master'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    seat_order = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team_sessions = relationship("TeamSession", back_populates="team")
    buzzer_events = relationship("BuzzerEvent", back_populates="team")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="draft")  # 'draft', 'live', 'ended'
    banner_text = Column(String, default="AISMOC 2026 QUIZ")
    current_round_id = Column(Integer, ForeignKey("rounds.id"), nullable=True)
    current_slide_id = Column(Integer, ForeignKey("slides.id"), nullable=True)
    mode = Column(String, default="question")  # 'question', 'answer', 'native'
    ppt_native_allowed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rounds = relationship("Round", back_populates="session", foreign_keys="Round.session_id")
    decks = relationship("Deck", back_populates="session")
    team_sessions = relationship("TeamSession", back_populates="session")
    buzzer_events = relationship("BuzzerEvent", back_populates="session")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'normal', 'bonus', 'penalty', 'fastest'
    timer_default_ms = Column(Integer, nullable=True)
    scoring_presets = Column(JSON, nullable=False)  # {"positive":[10,20],"negative":[-5]}
    order_index = Column(Integer, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="rounds", foreign_keys=[session_id])
    score_events = relationship("ScoreEvent", back_populates="round")


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    deck_type = Column(String, nullable=False)  # 'question' or 'answer'
    ppt_path = Column(String, nullable=False)
    native_required = Column(Boolean, default=False)

    # Relationships
    session = relationship("Session", back_populates="decks")
    slides = relationship("Slide", back_populates="deck")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False)
    slide_index = Column(Integer, nullable=False)
    png_path = Column(String, nullable=False)
    thumb_path = Column(String, nullable=False)
    default_timer_ms = Column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint('deck_id', 'slide_index', name='uix_deck_slide'),)

    # Relationships
    deck = relationship("Deck", back_populates="slides")
    question_mapping = relationship(
        "SlideMapping",
        back_populates="question_slide",
        foreign_keys="SlideMapping.question_slide_id"
    )
    answer_mapping = relationship(
        "SlideMapping",
        back_populates="answer_slide",
        foreign_keys="SlideMapping.answer_slide_id"
    )


class SlideMapping(Base):
    __tablename__ = "slide_mappings"

    question_slide_id = Column(Integer, ForeignKey("slides.id", ondelete="CASCADE"), primary_key=True)
    answer_slide_id = Column(Integer, ForeignKey("slides.id", ondelete="CASCADE"), nullable=False)
    answer_timer_override_ms = Column(Integer, nullable=True)

    # Relationships
    question_slide = relationship(
        "Slide",
        back_populates="question_mapping",
        foreign_keys=[question_slide_id]
    )
    answer_slide = relationship(
        "Slide",
        back_populates="answer_mapping",
        foreign_keys=[answer_slide_id]
    )


class TeamSession(Base):
    __tablename__ = "team_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    starting_score = Column(Integer, default=0)

    # Relationships
    session = relationship("Session", back_populates="team_sessions")
    team = relationship("Team", back_populates="team_sessions")
    score = relationship("Score", back_populates="team_session", uselist=False)
    score_events = relationship("ScoreEvent", back_populates="team_session")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    team_session_id = Column(Integer, ForeignKey("team_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    total = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    team_session = relationship("TeamSession", back_populates="score")


class ScoreEvent(Base):
    __tablename__ = "score_events"

    id = Column(Integer, primary_key=True, index=True)
    team_session_id = Column(Integer, ForeignKey("team_sessions.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    delta = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team_session = relationship("TeamSession", back_populates="score_events")
    round = relationship("Round", back_populates="score_events")


class BuzzerEvent(Base):
    __tablename__ = "buzzer_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    device_id = Column(String, nullable=False)
    placement = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="buzzer_events")
    team = relationship("Team", back_populates="buzzer_events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String, nullable=True)
    actor_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

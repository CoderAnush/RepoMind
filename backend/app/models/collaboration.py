import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SavedInsight(Base):
    """A saved chat response, execution trace, or analysis result."""
    __tablename__ = "saved_insights"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    insight_type = Column(String(80), nullable=False)  # CHAT, TRACE, REVIEW, ARCHITECTURE, ONBOARDING
    content = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)   # Full evidence blob from chat response
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RepositoryNote(Base):
    """User-authored notes attached to a repository."""
    __tablename__ = "repository_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)     # Markdown
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ActivityEvent(Base):
    """Audit timeline entry for repository activity feed."""
    __tablename__ = "activity_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(80), nullable=False)   # INDEXED, REVIEW_GENERATED, INSIGHT_SAVED, NOTE_ADDED, etc.
    description = Column(String(512), nullable=True)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

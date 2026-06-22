import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), index=True, nullable=False)  # Groups messages into a chat thread
    role = Column(String(20), nullable=False)  # system, user, assistant
    message = Column(Text, nullable=False)
    references = Column(JSON, nullable=True)  # List of dicts: {"file_path": "...", "snippet": "..."}
    evidence = Column(JSON, nullable=True)  # Explainability metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chats")
    repository = relationship("Repository", back_populates="chats")

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1024), index=True, nullable=False)
    symbol_name = Column(String(255), nullable=True)  # Class, function, or route name
    chunk_type = Column(String(50), nullable=False)  # class, function, file, markdown
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0)
    language = Column(String(50), nullable=True)
    dependencies = Column(JSON, nullable=True)  # List of imports or function calls
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="chunks")


class GeneratedDocumentation(Base):
    __tablename__ = "generated_documentations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String(50), nullable=False)  # README, ARCHITECTURE, API, ONBOARDING, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="documentations")

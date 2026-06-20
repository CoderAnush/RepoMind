import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    github_url = Column(String(1024), nullable=False)
    branch = Column(String(100), default="main")
    status = Column(String(50), default="PENDING")  # PENDING, CLONING, INDEXING, COMPLETE, FAILED
    metadata_info = Column(JSON, nullable=True)  # Languages, LOC, files metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="repositories")
    jobs = relationship("ProcessingJob", back_populates="repository", cascade="all, delete-orphan")
    chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    documentations = relationship("GeneratedDocumentation", back_populates="repository", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="repository", cascade="all, delete-orphan")
    chats = relationship("ChatHistory", back_populates="repository", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="repository", cascade="all, delete-orphan")
    code_reviews = relationship("CodeReview", back_populates="repository", cascade="all, delete-orphan")
    review_findings = relationship("ReviewFinding", back_populates="repository", cascade="all, delete-orphan")
    architecture_graph = relationship("ArchitectureGraph", uselist=False, back_populates="repository", cascade="all, delete-orphan")

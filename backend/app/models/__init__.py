# Expose all models for SQLAlchemy and Alembic migrations
from app.core.database import Base
from app.models.user import User
from app.models.repository import Repository
from app.models.job import ProcessingJob
from app.models.document import CodeChunk, GeneratedDocumentation
from app.models.chat import ChatHistory
from app.models.analysis import Diagram, Report, CodeReview, ArchitectureGraph, ReviewFinding
from app.models.collaboration import SavedInsight, RepositoryNote, ActivityEvent

__all__ = [
    "Base",
    "User",
    "Repository",
    "ProcessingJob",
    "CodeChunk",
    "GeneratedDocumentation",
    "ChatHistory",
    "Diagram",
    "Report",
    "CodeReview",
    "ArchitectureGraph",
    "ReviewFinding",
    "SavedInsight",
    "RepositoryNote",
    "ActivityEvent",
]

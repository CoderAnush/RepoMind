from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Engine configuration
if settings.sync_database_uri.startswith("sqlite"):
    engine = create_engine(
        settings.sync_database_uri,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.sync_database_uri,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=10
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for Models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures it gets closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    diagram_type = Column(String(50), nullable=False)  # ARCHITECTURE, SEQUENCE, CLASS, DEPENDENCY
    format = Column(String(20), default="MERMAID")  # MERMAID, GRAPHVIZ
    code = Column(Text, nullable=False)  # Raw diagram markup/code
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="diagrams")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50), nullable=False)  # SECURITY, QUALITY
    score = Column(Float, default=100.0)  # Maintainability or Security score out of 100
    findings = Column(JSON, nullable=True)  # List of findings: [{"severity": "HIGH", "message": "Secret leak in app.py", "line": 23}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="reports")

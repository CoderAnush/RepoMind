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


class CodeReview(Base):
    __tablename__ = "code_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, default=100.0)
    security_score = Column(Float, default=100.0)
    quality_score = Column(Float, default=100.0)
    architecture_score = Column(Float, default=100.0)
    performance_score = Column(Float, default=100.0)
    findings = Column(JSON, nullable=True)  # List of findings: [{"category": "SECURITY", "severity": "HIGH", "file": "app.py", "line": 12, "message": "...", "suggested_fix": "...", "explanation": "..."}]
    summary = Column(Text, nullable=True)  # CTO-style executive summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="code_reviews")


class ArchitectureGraph(Base):
    __tablename__ = "architecture_graphs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True)
    graph_data = Column(JSON, nullable=False)  # {"nodes": [], "edges": []}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="architecture_graph")

from sqlalchemy import Integer

class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # SECURITY, PERFORMANCE, QUALITY, ARCHITECTURE
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    file_path = Column(String(255), nullable=False)
    line_number = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    code_before = Column(Text, nullable=True)
    code_after = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="review_findings")


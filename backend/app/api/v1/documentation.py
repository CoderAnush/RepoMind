from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import base64
import urllib.request
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.document import GeneratedDocumentation
from app.models.analysis import Diagram, Report

router = APIRouter()

@router.get("/{repository_id}/docs")
def get_all_documentation(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all generated documentation structures for a repository.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    docs = db.query(GeneratedDocumentation).filter(
        GeneratedDocumentation.repository_id == repository_id
    ).all()
    
    return [
        {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "title": doc.title,
            "content": doc.content,
            "updated_at": doc.updated_at
        }
        for doc in docs
    ]


@router.get("/{repository_id}/diagrams")
def get_diagrams(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all generated architecture, flow, or dependency diagrams for a repository.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    diagrams = db.query(Diagram).filter(Diagram.repository_id == repository_id).all()
    
    return [
        {
            "id": d.id,
            "diagram_type": d.diagram_type,
            "format": d.format,
            "code": d.code,
            "created_at": d.created_at
        }
        for d in diagrams
    ]


@router.get("/{repository_id}/reports/{report_type}")
def get_reports(
    repository_id: str,
    report_type: str,  # SECURITY, QUALITY
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve security audits or code quality analyses.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    report = db.query(Report).filter(
        Report.repository_id == repository_id,
        Report.report_type == report_type.upper()
    ).order_by(Report.created_at.desc()).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report of type {report_type} not found."
        )
        
    return {
        "id": report.id,
        "report_type": report.report_type,
        "score": report.score,
        "findings": report.findings,
        "created_at": report.created_at
    }


@router.get("/{repository_id}/diagrams/{diagram_id}/svg")
def export_diagram_svg(
    repository_id: str,
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a generated diagram as SVG.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    diagram = db.query(Diagram).filter(
        Diagram.id == diagram_id,
        Diagram.repository_id == repository_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram not found")
        
    try:
        # Encode diagram code to base64
        encoded = base64.b64encode(diagram.code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/svg/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            svg_data = resp.read()
        return Response(content=svg_data, media_type="image/svg+xml")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render SVG diagram: {str(e)}"
        )


@router.get("/{repository_id}/diagrams/{diagram_id}/png")
def export_diagram_png(
    repository_id: str,
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a generated diagram as PNG.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    diagram = db.query(Diagram).filter(
        Diagram.id == diagram_id,
        Diagram.repository_id == repository_id
    ).first()
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram not found")
        
    try:
        # Encode diagram code to base64
        encoded = base64.b64encode(diagram.code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            png_data = resp.read()
        return Response(content=png_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render PNG diagram: {str(e)}"
        )

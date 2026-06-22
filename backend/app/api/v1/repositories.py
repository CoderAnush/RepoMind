from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.job import ProcessingJob
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.schemas.job import JobResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_repository(
    repo_in: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a GitHub repository URL to be cloned, parsed, indexed, and analyzed.
    Triggers an asynchronous background worker task.
    """
    # 1. Parse repository name from GitHub URL
    url = repo_in.github_url.strip()
    if not url.startswith("http"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Git Repository URL. URL must start with http/https."
        )
        
    repo_name = url.split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
        
    # Check if this repository is already being tracked by this user
    existing_repo = db.query(Repository).filter(
        Repository.owner_id == current_user.id,
        Repository.github_url == url
    ).first()
    
    if existing_repo:
        if existing_repo.status in ["PENDING", "CLONING", "INDEXING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This repository is already being processed."
            )
        # Re-submit: reset status
        existing_repo.status = "PENDING"
        db.commit()
        db.refresh(existing_repo)
        background_tasks.add_task(AgentService.run_analysis_pipeline, existing_repo.id, db)
        return existing_repo

    # 2. Create Repository row
    repo = Repository(
        owner_id=current_user.id,
        name=repo_name,
        github_url=url,
        branch=repo_in.branch or "main",
        status="PENDING"
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    # 3. Add to background worker queue
    background_tasks.add_task(AgentService.run_analysis_pipeline, repo.id, db)
    
    return repo


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all repositories owned by the current logged-in user.
    """
    repos = db.query(Repository).filter(Repository.owner_id == current_user.id).all()
    return repos


@router.get("/{id}", response_model=RepositoryResponse)
def get_repository(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve repository metadata details by UUID.
    """
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
    return repo


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a repository, using direct SQL deletes and direct Qdrant connection to avoid ORM cascades and API timeouts.
    """
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
        
    # 1. Direct Qdrant delete using basic client (no collections initialization check overhead)
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from app.core.config import settings
        
        if settings.QDRANT_URL:
            client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        else:
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            
        repo_filter = Filter(
            must=[
                FieldCondition(
                    key="repository_id",
                    match=MatchValue(value=id)
                )
            ]
        )
        
        try:
            client.delete(
                collection_name=settings.QDRANT_COLLECTION_CODE,
                points_selector=repo_filter,
                wait=False
            )
        except Exception:
            pass
            
        try:
            client.delete(
                collection_name=settings.QDRANT_COLLECTION_DOCS,
                points_selector=repo_filter,
                wait=False
            )
        except Exception:
            pass
    except Exception as e:
        from app.core.logging import logger
        logger.warning(f"Error clean-up vector DB: {e}")
        
    # 2. Fast Bulk SQL Deletes (single network round trip per table, avoids loading thousands of rows into ORM)
    from sqlalchemy import text
    try:
        db.execute(text("DELETE FROM code_chunks WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM processing_jobs WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM generated_documentations WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM diagrams WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM reports WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM review_findings WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM architecture_graphs WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM chat_history WHERE repository_id = :id"), {"id": id})
        db.execute(text("DELETE FROM repositories WHERE id = :id"), {"id": id})
        db.commit()
    except Exception as e:
        db.rollback()
        from app.core.logging import logger
        logger.error(f"SQL bulk delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete repository due to a database error."
        )
    
    return status.HTTP_204_NO_CONTENT


@router.get("/{id}/jobs", response_model=List[JobResponse])
def get_repository_jobs(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve background processing jobs detail and status for a repository.
    """
    # Verify owner
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    jobs = db.query(ProcessingJob).filter(ProcessingJob.repository_id == id).all()
    return jobs


@router.post("/{id}/review")
def run_code_review(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers/generates an AI code review for the repository.
    """
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    from app.services.code_review_agent import CodeReviewAgentService
    review = CodeReviewAgentService.generate_review(id, db)
    
    from app.models.analysis import ReviewFinding
    db_findings = db.query(ReviewFinding).filter(ReviewFinding.repository_id == id).all()
    findings = [
        {
            "id": f.id,
            "category": f.category,
            "severity": f.severity,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "title": f.title,
            "description": f.description,
            "rule": getattr(f, 'rule', None) or f"{f.category} Scan",
            "suggested_fix": f.suggested_fix,
            "code_before": f.code_before,
            "code_after": f.code_after
        } for f in db_findings
    ]
    return {
        "id": review.id,
        "repository_id": review.repository_id,
        "overall_score": review.overall_score,
        "security_score": review.security_score,
        "quality_score": review.quality_score,
        "architecture_score": review.architecture_score,
        "performance_score": review.performance_score,
        "maintainability_score": round((review.quality_score + review.architecture_score) / 2, 1),
        "documentation_coverage": 85.0,
        "summary": review.summary,
        "findings": findings,
        "technical_debt_hours": len(findings) * 2.5,
        "engineering_effort": "High" if len(findings) > 10 else "Medium" if len(findings) > 4 else "Low",
        "refactoring_opportunities_count": sum(1 for f in findings if f.get("category") in ["QUALITY", "ARCHITECTURE"]),
        "created_at": review.created_at
    }


@router.get("/{id}/review")
def get_code_review(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the latest AI code review for the repository, generating one if it doesn't exist yet.
    """
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    from app.models.analysis import CodeReview
    review = db.query(CodeReview).filter(CodeReview.repository_id == id).first()
    
    # Auto-generate if not exists
    if not review:
        from app.services.code_review_agent import CodeReviewAgentService
        review = CodeReviewAgentService.generate_review(id, db)
        
    from app.models.analysis import ReviewFinding
    db_findings = db.query(ReviewFinding).filter(ReviewFinding.repository_id == id).all()
    findings = [
        {
            "id": f.id,
            "category": f.category,
            "severity": f.severity,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "title": f.title,
            "description": f.description,
            "rule": getattr(f, 'rule', None) or f"{f.category} Scan",
            "suggested_fix": f.suggested_fix,
            "code_before": f.code_before,
            "code_after": f.code_after
        } for f in db_findings
    ]
    return {
        "id": review.id,
        "repository_id": review.repository_id,
        "overall_score": review.overall_score,
        "security_score": review.security_score,
        "quality_score": review.quality_score,
        "architecture_score": review.architecture_score,
        "performance_score": review.performance_score,
        "maintainability_score": round((review.quality_score + review.architecture_score) / 2, 1),
        "documentation_coverage": 85.0,
        "summary": review.summary,
        "findings": findings,
        "technical_debt_hours": len(findings) * 2.5,
        "engineering_effort": "High" if len(findings) > 10 else "Medium" if len(findings) > 4 else "Low",
        "refactoring_opportunities_count": sum(1 for f in findings if f.get("category") in ["QUALITY", "ARCHITECTURE"]),
        "created_at": review.created_at
    }


@router.get("/{id}/architecture")
def get_architecture_graph(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the architecture visualization graph, generating one if it doesn't exist yet.
    """
    repo = db.query(Repository).filter(
        Repository.id == id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        
    from app.models.analysis import ArchitectureGraph
    graph = db.query(ArchitectureGraph).filter(ArchitectureGraph.repository_id == id).first()
    
    # Auto-generate if not exists
    if not graph:
        from app.services.architecture_visualizer import ArchitectureVisualizer
        graph = ArchitectureVisualizer.generate_graph(id, db)
        
    return graph.graph_data



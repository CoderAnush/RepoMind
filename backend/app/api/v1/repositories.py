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

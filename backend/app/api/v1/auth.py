import httpx
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        if settings.SUPABASE_URL:
            # Auto-create local user profile for validated Supabase JWT token
            user = User(
                id=user_id,
                email=f"{user_id}@supabase.io",
                hashed_password=get_password_hash("supabase-managed-password"),
                full_name="Supabase User",
                role="DEVELOPER",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the platform. Supports Supabase Auth and Local modes.
    """
    # 1. Supabase Signup Proxy
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            url = f"{settings.SUPABASE_URL}/auth/v1/signup"
            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            body = {
                "email": user_in.email,
                "password": user_in.password,
                "data": {
                    "full_name": user_in.full_name
                }
            }
            resp = httpx.post(url, headers=headers, json=body, timeout=10.0)
            if resp.status_code != 200:
                try:
                    err_data = resp.json()
                    detail_msg = err_data.get("msg") or err_data.get("error_description") or "Supabase signup failure"
                except Exception:
                    detail_msg = resp.text or "Supabase signup failure"
                raise HTTPException(status_code=resp.status_code, detail=detail_msg)
            
            data = resp.json()
            user_data = data.get("user") or data
            supabase_uid = user_data["id"]
            user_email = user_data["email"]

            # Save locally
            user_exists = db.query(User).filter(User.id == supabase_uid).first()
            if not user_exists:
                db_user = User(
                    id=supabase_uid,
                    email=user_email,
                    hashed_password=get_password_hash("supabase-managed-password"),
                    full_name=user_in.full_name,
                    role=user_in.role or "DEVELOPER",
                    is_active=True
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                return db_user
            return user_exists
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Auth service unreachable: {str(e)}"
            )

    # 2. Local Fallback
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "DEVELOPER",
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def seed_demo_data(db: Session, user_id: str):
    from app.models.repository import Repository
    from app.models.document import GeneratedDocumentation
    from app.models.analysis import Diagram, Report

    repo = db.query(Repository).filter(Repository.owner_id == user_id, Repository.name == "sampleproject").first()
    if repo:
        return repo.id

    repo_id = "demo-repo-id"
    db_repo = Repository(
        id=repo_id,
        owner_id=user_id,
        name="sampleproject",
        github_url="https://github.com/pypa/sampleproject",
        branch="main",
        status="COMPLETE",
        metadata_info={
            "total_files": 12,
            "total_loc": 370,
            "languages": {"Python": 5, "YAML": 2, "Markdown": 1, "Other": 4},
            "languages_loc_percentage": {"Python": 20.81, "YAML": 15.68, "Markdown": 10.54, "Other": 52.97}
        }
    )
    db.add(db_repo)

    docs = [
        ("README", "README.md", r"""# A sample Python project

This is a sample project to demonstrate Python packaging tools.

## Installation
```bash
pip install .
```"""),
        ("PROJECT_OVERVIEW", "Project Overview", r"""# Project Overview

Sample project showing standard Python setup using pyproject.toml.

## Stack
- Python 3.8+
- Hatchling build backend"""),
        ("INSTALLATION", "Installation Guide", r"""# Installation Guide

```bash
git clone https://github.com/pypa/sampleproject.git
cd sampleproject
pip install -e .
```"""),
        ("USAGE", "Usage Guide", r"""# Usage Guide

Importing the sample package:
```python
from sample import main
main()
```"""),
        ("API_DOCUMENTATION", "API Documentation", r"""# API Reference

### `add_one(number)`
Increments an integer by 1.

### `main()`
CLI entry point."""),
        ("DEVELOPER_ONBOARDING", "Developer Onboarding", r"""# Developer Onboarding

## Testing
Run `nox` or `pytest` to verify the codebase changes.""")
    ]
    for doc_type, title, content in docs:
        db.add(GeneratedDocumentation(
            repository_id=repo_id,
            doc_type=doc_type,
            title=title,
            content=content
        ))

    diagrams = [
        ("ARCHITECTURE", r"""graph TD
    User([CLI User]) -->|Invoke| Main[main entrypoint]
    Main -->|Call| Simple[simple add_one function]"""),
        ("CLASS", r"""classDiagram
    class SimpleModule {
        +add_one(number)
    }"""),
        ("SEQUENCE", r"""sequenceDiagram
    actor User
    User->>Main: run cli command
    Main->>Simple: add_one(number)
    Simple-->>Main: return result
    Main-->>User: print output"""),
        ("DEPENDENCY", r"""graph LR
    main.py --> simple.py""")
    ]
    for d_type, code in diagrams:
        db.add(Diagram(
            repository_id=repo_id,
            diagram_type=d_type,
            code=code
        ))

    db.add(Report(
        repository_id=repo_id,
        report_type="SECURITY",
        score=100.0,
        findings=[]
    ))
    db.add(Report(
        repository_id=repo_id,
        report_type="QUALITY",
        score=95.0,
        findings=[{"severity": "LOW", "message": "Missing docstrings in pyproject.toml configuration references", "file": "pyproject.toml"}]
    ))

    db.commit()
    return repo_id


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login. Supports Supabase Token validation, Demo mode, and Local modes.
    """
    # 0. Intercept Demo Mode Account
    if form_data.username == "demo@repomind.io" and form_data.password == "demouser123!":
        demo_user = db.query(User).filter(User.email == "demo@repomind.io").first()
        if not demo_user:
            demo_user = User(
                id="demo-user-uuid-123456",
                email="demo@repomind.io",
                hashed_password=get_password_hash("demouser123!"),
                full_name="Demo User",
                role="DEVELOPER",
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Seed demo data
        seed_demo_data(db, demo_user.id)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=demo_user.id, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": demo_user
        }

    # 1. Supabase Token Proxy
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
            headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            body = {
                "email": form_data.username,
                "password": form_data.password
            }
            resp = httpx.post(url, headers=headers, json=body, timeout=10.0)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect email or password from Supabase Auth"
                )
            
            data = resp.json()
            access_token = data["access_token"]
            user_data = data["user"]
            supabase_uid = user_data["id"]
            user_email = user_data["email"]
            metadata = user_data.get("user_metadata", {})
            full_name = metadata.get("full_name") or "Supabase User"

            # Check if user exists locally
            db_user = db.query(User).filter(User.id == supabase_uid).first()
            if not db_user:
                db_user = User(
                    id=supabase_uid,
                    email=user_email,
                    hashed_password=get_password_hash("supabase-managed-password"),
                    full_name=full_name,
                    role="DEVELOPER",
                    is_active=True
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": db_user
            }
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Auth service unreachable: {str(e)}"
            )

    # 2. Local Fallback
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged in user details.
    """
    return current_user


from pydantic import BaseModel

class GitHubLoginRequest(BaseModel):
    code: str

@router.get("/github/url")
def get_github_auth_url(redirect_uri: str):
    """
    Returns the GitHub OAuth login URL. Supports fallback to mock mode.
    """
    client_id = settings.GITHUB_CLIENT_ID
    if not client_id:
        return {
            "url": f"{redirect_uri}?code=mock_code_octocat",
            "is_mock": True
        }
    return {
        "url": f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=user,repo",
        "is_mock": False
    }

@router.post("/github/login", response_model=Token)
def github_login(payload: GitHubLoginRequest, db: Session = Depends(get_db)):
    """
    Exchanges code for GitHub user profile, creates/retrieves local user profile,
    and returns a JWT access token.
    """
    code = payload.code
    github_access_token = None
    
    if code.startswith("mock_code") or not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        email = "octocat@github.com"
        full_name = "The Octocat (Mock)"
        github_id = "583234"
        github_access_token = "mock_github_token_octocat"
    else:
        try:
            token_url = "https://github.com/login/oauth/access_token"
            headers = {"Accept": "application/json"}
            data = {
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code
            }
            resp = httpx.post(token_url, headers=headers, json=data, timeout=10.0)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange OAuth code with GitHub")
            
            token_data = resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=400, detail=token_data.get("error_description") or "OAuth code expired or invalid")
            
            github_access_token = access_token
            profile_url = "https://api.github.com/user"
            profile_headers = {"Authorization": f"Bearer {github_access_token}"}
            profile_resp = httpx.get(profile_url, headers=profile_headers, timeout=10.0)
            if profile_resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch user profile from GitHub")
            
            profile = profile_resp.json()
            github_id = str(profile.get("id"))
            full_name = profile.get("name") or profile.get("login") or "GitHub User"
            
            emails_url = "https://api.github.com/user/emails"
            emails_resp = httpx.get(emails_url, headers=profile_headers, timeout=10.0)
            email = None
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                for em in emails:
                    if em.get("primary") and em.get("verified"):
                        email = em.get("email")
                        break
            
            if not email:
                email = profile.get("email") or f"{profile.get('login')}@github.com"
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"GitHub OAuth error: {str(e)}")

    user = db.query(User).filter((User.email == email) | (User.id == f"github-{github_id}")).first()
    if not user:
        user = User(
            id=f"github-{github_id}",
            email=email,
            hashed_password=get_password_hash("github-oauth-managed-password"),
            full_name=full_name,
            role="DEVELOPER",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "github_access_token": github_access_token
    }


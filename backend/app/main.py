import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import engine, Base

# Import router modules
from app.api.v1.auth import router as auth_router
from app.api.v1.repositories import router as repo_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documentation import router as doc_router
from app.api.v1.health import router as health_router
from app.api.v1.collaboration import router as collab_router

# Setup structured logging
setup_logging()

# Auto-create SQLAlchemy Database tables at startup
try:
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables at startup: {str(e)}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    # ── Qdrant startup diagnostics ──────────────────────────────────────────
    logger.info("[Startup] Initializing Qdrant connection...")
    try:
        from app.services.vector_db import VectorDBService
        svc = VectorDBService()          # triggers _build_qdrant_client + logs
        collections = svc.get_collection_names()
        logger.info(f"[Startup] Qdrant ready. Collections: {collections}")
    except Exception as e:
        logger.error(f"[Startup] Qdrant initialization failed: {e}")
    yield
    # (shutdown hooks can go here if needed)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RepoMind API: Enterprise Code Intelligence & Documentation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS setup for frontend interface connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://repomind-beige.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )


# Register api version 1 routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(repo_router, prefix=f"{settings.API_V1_STR}/repositories", tags=["Repositories"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["RAG Chatbot"])
app.include_router(doc_router, prefix=f"{settings.API_V1_STR}/repositories", tags=["Repository Insights"])
app.include_router(health_router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])
app.include_router(collab_router, prefix=f"{settings.API_V1_STR}/collab", tags=["Collaboration"])

@app.get("/", tags=["Health"])
def health_check():
    """Service status health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "api_version": "1.0.0"
    }

if __name__ == "__main__":
    # Start ASGI Server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

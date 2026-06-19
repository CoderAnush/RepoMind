import uvicorn
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

# Setup structured logging
setup_logging()

# Auto-create SQLAlchemy Database tables at startup
# (Standard production-ready development shortcut for seamless startup)
try:
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables at startup: {str(e)}", exc_info=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RepoMind API: Enterprise Code Intelligence & Documentation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup for frontend interface connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to actual frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register api version 1 routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(repo_router, prefix=f"{settings.API_V1_STR}/repositories", tags=["Repositories"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["RAG Chatbot"])
app.include_router(doc_router, prefix=f"{settings.API_V1_STR}/repositories", tags=["Repository Insights"])

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

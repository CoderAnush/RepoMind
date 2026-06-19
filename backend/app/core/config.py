import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # API Configuration
    PROJECT_NAME: str = "RepoMind"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="SUPER_SECRET_SECURITY_KEY_FOR_REPOMIND_ENTERPRISE_SaaS_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: str = Field(default="5432")
    POSTGRES_DB: str = Field(default="repomind")
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Vector DB (Qdrant)
    # QDRANT_URL takes priority and is used for cloud deployments (e.g. Qdrant Cloud via Render env var).
    # QDRANT_HOST/PORT are used as local-only fallbacks when QDRANT_URL is not set.
    QDRANT_URL: Optional[str] = None          # e.g. https://xxxx.qdrant.io:6333
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_CODE: str = "repomind_code"
    QDRANT_COLLECTION_DOCS: str = "repomind_docs"
    QDRANT_TEST_COLLECTION: str = "repomind_test"

    # LLM & Embedding Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = Field(default="openai")  # openai or anthropic
    LLM_MODEL: str = "gpt-4-turbo"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # GitHub App Integration
    GITHUB_PERSONAL_ACCESS_TOKEN: Optional[str] = None

    # Supabase Deployment Configurations
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "repomind-artifacts"

    # Local Temp Storage for Cloned Repos
    REPO_CLONE_DIR: str = "/tmp/repomind_clones"

settings = Settings()

# Ensure clone dir exists
os.makedirs(settings.REPO_CLONE_DIR, exist_ok=True)

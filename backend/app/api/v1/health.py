"""
Health check endpoints for infrastructure components.

GET /api/v1/health/qdrant  — Qdrant connectivity, collection list, and smoke-test.
"""
from fastapi import APIRouter
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.get("/qdrant", tags=["Health"])
def qdrant_health():
    """
    Checks connectivity to the configured Qdrant instance and returns:
    - status: "healthy" | "degraded" | "error"
    - mode: "cloud" | "local" | "in-memory"
    - qdrant_url: the URL being used (or null)
    - collections: list of existing collection names
    - test_collection: smoke-test result (insert + retrieve a vector)
    """
    from app.services.vector_db import VectorDBService

    result = {
        "status": "error",
        "mode": "unknown",
        "qdrant_url": settings.QDRANT_URL or f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
        "qdrant_url_env_set": settings.QDRANT_URL is not None,
        "qdrant_api_key_set": settings.QDRANT_API_KEY is not None,
        "collections": [],
        "test_collection": {
            "name": settings.QDRANT_TEST_COLLECTION,
            "insert": False,
            "retrieve": False,
            "payload": None
        }
    }

    try:
        svc = VectorDBService()

        # ── Determine mode ──────────────────────────────────────────────────
        if settings.QDRANT_URL:
            result["mode"] = "cloud"
        elif settings.QDRANT_HOST != "localhost":
            result["mode"] = "remote-host"
        else:
            # Check if truly in-memory
            try:
                svc.client.get_collections()  # will succeed even in-memory
                result["mode"] = "local" if not svc.is_in_memory() else "in-memory"
            except Exception:
                result["mode"] = "in-memory"

        # ── Collections ─────────────────────────────────────────────────────
        collection_names = svc.get_collection_names()
        result["collections"] = collection_names

        # ── Smoke test: insert → retrieve ───────────────────────────────────
        test_id = svc.insert_test_vector()
        result["test_collection"]["insert"] = True

        payload = svc.retrieve_test_vector(test_id)
        if payload:
            result["test_collection"]["retrieve"] = True
            result["test_collection"]["payload"] = payload

        # ── Final status ────────────────────────────────────────────────────
        if result["mode"] == "in-memory":
            result["status"] = "degraded"
            result["warning"] = (
                "Running in in-memory mode. Data will NOT persist across restarts. "
                "Set QDRANT_URL and QDRANT_API_KEY in Render environment variables."
            )
        else:
            result["status"] = "healthy"

    except Exception as e:
        logger.error(f"[Qdrant Health] Check failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result

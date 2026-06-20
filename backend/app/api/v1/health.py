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
    Checks connectivity to Qdrant, verifies production collections, and payload indexes.
    """
    from app.services.vector_db import VectorDBService

    try:
        svc = VectorDBService()
        
        # 1. Connection check
        collections_info = svc.client.get_collections().collections
        collection_names = [c.name for c in collections_info]
        
        # 2. Check if required collections exist
        required_collections = [settings.QDRANT_COLLECTION_CODE, settings.QDRANT_COLLECTION_DOCS]
        collections_exist = all(col in collection_names for col in required_collections)
        
        # 3. Check payload index for both collections
        payload_indexes = []
        is_local_in_memory = "Local" in type(svc.client._client).__name__
        for col in required_collections:
            if col in collection_names:
                try:
                    col_info = svc.client.get_collection(collection_name=col)
                    schema = col_info.payload_schema or {}
                    if "repository_id" in schema or is_local_in_memory:
                        payload_indexes.append(f"{col}:repository_id")
                except Exception:
                    pass
                    
        indexes_exist = len(payload_indexes) == len(required_collections)
        
        status = "healthy"
        if not collections_exist or not indexes_exist:
            status = "degraded"
            
        return {
            "status": status,
            "collections": collection_names,
            "payload_indexes": payload_indexes
        }
    except Exception as e:
        logger.error(f"[Qdrant Health] Check failed: {e}")
        return {
            "status": "error",
            "collections": [],
            "payload_indexes": []
        }

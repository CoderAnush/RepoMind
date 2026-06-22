from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings
from app.core.logging import logger


def _build_qdrant_client() -> QdrantClient:
    """
    Builds and returns a connected QdrantClient.

    Priority order:
      1. QDRANT_URL env var (cloud / Render deployment)  →  QdrantClient(url=..., api_key=...)
      2. QDRANT_HOST != localhost                        →  QdrantClient(host=..., port=..., api_key=...)
      3. localhost reachable                             →  QdrantClient(host="localhost", port=...)
      4. Fallback                                        →  in-memory (dev only, data not persisted)

    On startup, diagnostics are always printed so problems are immediately visible in Render logs.
    """
    # ── Startup Diagnostics ──────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("[Qdrant] Startup Diagnostics")
    logger.info(f"[Qdrant] QDRANT_URL   : {'SET -> ' + settings.QDRANT_URL if settings.QDRANT_URL else 'NOT SET'}")
    logger.info(f"[Qdrant] QDRANT_HOST  : {settings.QDRANT_HOST}")
    logger.info(f"[Qdrant] QDRANT_PORT  : {settings.QDRANT_PORT}")
    logger.info(f"[Qdrant] QDRANT_API_KEY: {'SET (****' + settings.QDRANT_API_KEY[-4:] + ')' if settings.QDRANT_API_KEY else 'NOT SET'}")
    logger.info("=" * 60)

    # ── Case 1: QDRANT_URL is set (cloud / production) ───────────────────────
    if settings.QDRANT_URL:
        logger.info(f"[Qdrant] Connecting to cloud Qdrant: {settings.QDRANT_URL}")
        try:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            info = client.get_collections()
            collection_names = [c.name for c in info.collections]
            logger.info(f"[Qdrant] Connected successfully. Collections: {collection_names}")
            return client
        except Exception as e:
            logger.error(f"[Qdrant] ERROR connecting to QDRANT_URL={settings.QDRANT_URL}: {e}")
            logger.error("[Qdrant] Falling back to in-memory mode. Data will NOT persist.")
            return QdrantClient(location=":memory:")

    # ── Case 2: Non-localhost QDRANT_HOST set ────────────────────────────────
    if settings.QDRANT_HOST and settings.QDRANT_HOST != "localhost":
        logger.info(f"[Qdrant] Connecting to remote host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        try:
            client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
            )
            info = client.get_collections()
            collection_names = [c.name for c in info.collections]
            logger.info(f"[Qdrant] Connected successfully. Collections: {collection_names}")
            return client
        except Exception as e:
            logger.error(f"[Qdrant] ERROR connecting to {settings.QDRANT_HOST}:{settings.QDRANT_PORT}: {e}")
            logger.error("[Qdrant] Falling back to in-memory mode. Data will NOT persist.")
            return QdrantClient(location=":memory:")

    # ── Case 3: Try local Qdrant ─────────────────────────────────────────────
    logger.info(f"[Qdrant] No remote URL configured. Checking local Qdrant on port {settings.QDRANT_PORT}...")
    import socket
    local_reachable = False
    try:
        with socket.create_connection(("127.0.0.1", settings.QDRANT_PORT), timeout=1.0):
            local_reachable = True
    except Exception:
        pass

    if local_reachable:
        logger.info(f"[Qdrant] Local instance detected. Connecting to localhost:{settings.QDRANT_PORT}")
        try:
            client = QdrantClient(host="localhost", port=settings.QDRANT_PORT)
            info = client.get_collections()
            logger.info(f"[Qdrant] Connected to local Qdrant. Collections: {[c.name for c in info.collections]}")
            return client
        except Exception as e:
            logger.error(f"[Qdrant] Failed to connect to local Qdrant: {e}")

    # ── Case 4: In-memory fallback ───────────────────────────────────────────
    logger.warning("[Qdrant] No reachable Qdrant instance found. Using IN-MEMORY mode.")
    logger.warning("[Qdrant] WARNING: Data will NOT persist across restarts.")
    return QdrantClient(location=":memory:")


class VectorDBService:
    _client: Optional[QdrantClient] = None

    def __init__(self):
        from app.services.embedding import get_embedding_provider
        self.embedding_provider = get_embedding_provider()
        self.vector_dim = self.embedding_provider.get_dimension()

        if VectorDBService._client is None:
            VectorDBService._client = _build_qdrant_client()

        self.client = VectorDBService._client
        logger.info("[Qdrant] Connected")

        # Initialize production collections
        self._init_collection(settings.QDRANT_COLLECTION_CODE)
        self._init_collection(settings.QDRANT_COLLECTION_DOCS)
        self._init_payload_indexes()

    def _init_collection(self, collection_name: str) -> None:
        """Creates a Qdrant collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                logger.info(f"[Qdrant] Creating collection: '{collection_name}' (dim={self.vector_dim})")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
            logger.info(f"[Qdrant] Collection {collection_name} exists")
        except Exception as e:
            logger.error(f"[Qdrant] Error checking/creating collection '{collection_name}': {e}")

    def _init_payload_indexes(self) -> None:
        """Idempotently creates the payload index on repository_id for both collections."""
        from qdrant_client.models import PayloadSchemaType
        all_ok = True
        for col in [settings.QDRANT_COLLECTION_CODE, settings.QDRANT_COLLECTION_DOCS]:
            try:
                collection_info = self.client.get_collection(collection_name=col)
                payload_schema = collection_info.payload_schema or {}
                if "repository_id" not in payload_schema:
                    logger.info(f"[Qdrant] Creating payload index for 'repository_id' on collection '{col}'")
                    self.client.create_payload_index(
                        collection_name=col,
                        field_name="repository_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
            except Exception as e:
                logger.error(f"[Qdrant] Error creating payload index for '{col}': {e}", exc_info=True)
                all_ok = False
        if all_ok:
            logger.info("[Qdrant] Payload index repository_id verified")

    def get_client(self) -> QdrantClient:
        """Expose the underlying QdrantClient (used by health router)."""
        return self.client

    def get_collection_names(self) -> List[str]:
        """Returns list of all existing collection names."""
        try:
            return [c.name for c in self.client.get_collections().collections]
        except Exception as e:
            logger.error(f"[Qdrant] Failed to list collections: {e}")
            return []

    def is_in_memory(self) -> bool:
        """Returns True if the client is running in-memory (no persistence)."""
        return getattr(self.client, "_local", None) is not None or not (
            settings.QDRANT_URL or settings.QDRANT_HOST != "localhost"
        )

    # ── Test Collection Utilities ─────────────────────────────────────────────

    def ensure_test_collection(self) -> None:
        """Creates the repomind_test collection used for diagnostics."""
        self._init_collection(settings.QDRANT_TEST_COLLECTION)

    def insert_test_vector(self) -> str:
        """Inserts a known test vector into repomind_test. Returns point ID."""
        import uuid
        self.ensure_test_collection()
        test_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "repomind-test-vector-v1"))
        test_vector = [0.1] * self.vector_dim  # deterministic unit-like vector
        self.client.upsert(
            collection_name=settings.QDRANT_TEST_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=test_id,
                    vector=test_vector,
                    payload={"test": True, "label": "repomind-smoke-test"}
                )
            ]
        )
        logger.info(f"[Qdrant] Test vector inserted with id={test_id}")
        return test_id

    def retrieve_test_vector(self, point_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a test vector by ID. Returns payload or None."""
        try:
            results = self.client.retrieve(
                collection_name=settings.QDRANT_TEST_COLLECTION,
                ids=[point_id],
                with_payload=True
            )
            if results:
                return results[0].payload
            return None
        except Exception as e:
            logger.error(f"[Qdrant] Failed to retrieve test vector {point_id}: {e}")
            return None

    # ── Core Operations ───────────────────────────────────────────────────────

    def index_chunks(self, repository_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Embeds and indexes code chunks in Qdrant in batches to prevent rate limits and memory overflow.
        """
        if not chunks:
            return

        logger.info(f"[Qdrant] Indexing {len(chunks)} code chunks for repo: {repository_id} in batches.")

        batch_size = 50
        import uuid
        total_uploaded = 0

        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i:i + batch_size]
            batch_contents = [c["content"] for c in chunk_batch]
            
            try:
                # Generate embeddings for the batch
                batch_embeddings = self.embedding_provider.get_embeddings(batch_contents)
            except Exception as e:
                logger.error(f"[Qdrant] Error generating embeddings for batch: {str(e)}")
                # Skip batch or use mock embeddings fallback
                batch_embeddings = [self.embedding_provider._mock_embedding(c) for c in batch_contents]
                
            points = []
            for idx, (chunk, vector) in enumerate(zip(chunk_batch, batch_embeddings)):
                payload = {
                    "repository_id": repository_id,
                    "file_path": chunk["file_path"],
                    "symbol_name": chunk.get("symbol_name") or "",
                    "chunk_type": chunk["chunk_type"],
                    "language": chunk.get("language") or "",
                    "dependencies": chunk.get("dependencies") or [],
                    "content": chunk["content"]
                }
                # Create a deterministic UUID using repository_id, file_path, and indices
                point_id = chunk.get("id") or str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{repository_id}_{chunk['file_path']}_{i + idx}")
                )
                points.append(qmodels.PointStruct(id=point_id, vector=vector, payload=payload))

            try:
                self.client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_CODE,
                    points=points
                )
                total_uploaded += len(points)
            except Exception as e:
                logger.error(f"[Qdrant] Error uploading points to Qdrant: {str(e)}")

        logger.info(f"[Qdrant] Upload complete: {total_uploaded} vectors indexed.")

    def search_code(
        self,
        repository_id: str,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search on code chunks scoped to a repository.
        """
        query_vector = self.embedding_provider.get_embedding(query)

        must_filters = [
            qmodels.FieldCondition(
                key="repository_id",
                match=qmodels.MatchValue(value=repository_id)
            )
        ]

        if filters:
            for key, val in filters.items():
                must_filters.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=val)
                    )
                )

        search_result = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION_CODE,
            query=query_vector,
            query_filter=qmodels.Filter(must=must_filters),
            limit=limit
        )

        results = []
        for hit in search_result.points:
            p = dict(hit.payload or {})
            p["similarity_score"] = getattr(hit, "score", 0.85)
            # Make sure it has a fallback chunk ID
            p["id"] = getattr(hit, "id", None) or f"chunk_{abs(hash(p.get('content', '')) % 100000)}"
            results.append(p)
        return results

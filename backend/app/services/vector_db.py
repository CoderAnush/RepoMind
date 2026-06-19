from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings
from app.core.logging import logger
from app.services.embedding import get_embedding_provider

class VectorDBService:
    _client = None

    def __init__(self):
        self.embedding_provider = get_embedding_provider()
        self.vector_dim = self.embedding_provider.get_dimension()
        
        if VectorDBService._client is None:
            # Initialize client. Attempt connection to configured host; fallback to memory on failure.
            try:
                if settings.QDRANT_HOST == "localhost" and not self._is_qdrant_running_locally():
                    logger.warning("Local Qdrant instance not reachable. Initializing in-memory Qdrant client.")
                    VectorDBService._client = QdrantClient(location=":memory:")
                else:
                    VectorDBService._client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        api_key=settings.QDRANT_API_KEY
                    )
                    logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant cluster: {str(e)}. Falling back to in-memory Qdrant.")
                VectorDBService._client = QdrantClient(location=":memory:")
        
        self.client = VectorDBService._client

        # Initialize collections
        self._init_collection(settings.QDRANT_COLLECTION_CODE)
        self._init_collection(settings.QDRANT_COLLECTION_DOCS)

    def _is_qdrant_running_locally(self) -> bool:
        import socket
        try:
            with socket.create_connection(("127.0.0.1", settings.QDRANT_PORT), timeout=1.0):
                return True
        except Exception:
            return False

    def _init_collection(self, collection_name: str) -> None:
        """Creates collection if it doesn't already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection {collection_name}: {str(e)}")

    def index_chunks(self, repository_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Embeds and indexes code chunks in Qdrant.
        """
        if not chunks:
            return
            
        logger.info(f"Indexing {len(chunks)} code chunks in Qdrant for repo: {repository_id}")
        
        # Batch embedding generation
        contents = [c["content"] for c in chunks]
        embeddings = self.embedding_provider.get_embeddings(contents)
        
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            # Combine payload with metadata
            payload = {
                "repository_id": repository_id,
                "file_path": chunk["file_path"],
                "symbol_name": chunk.get("symbol_name") or "",
                "chunk_type": chunk["chunk_type"],
                "language": chunk.get("language") or "",
                "dependencies": chunk.get("dependencies") or [],
                "content": chunk["content"]
            }
            
            import uuid
            point_id = chunk.get("id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{repository_id}_{chunk['file_path']}_{idx}"))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
            
        # Upload in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION_CODE,
                points=points[i:i+batch_size]
            )
        logger.info("Upload of vectors completed successfully.")

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
        
        # Build filter criteria
        must_filters = [
            qmodels.FieldCondition(
                key="repository_id",
                match=qmodels.MatchValue(value=repository_id)
            )
        ]
        
        # Add additional metadata filters if supplied
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
        
        return [hit.payload for hit in search_result.points]

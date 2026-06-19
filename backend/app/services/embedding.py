from abc import ABC, abstractmethod
from typing import List, Optional
from openai import OpenAI
from app.core.config import settings
from app.core.logging import logger

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding for a single text string."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Returns the dimensionality of the generated vector."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No OPENAI_API_KEY provided. Embedding service will operate in mock fallback mode.")

    def get_embedding(self, text: str) -> List[float]:
        if not self.client:
            return self._mock_embedding(text)
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            return self._mock_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            return [self._mock_embedding(t) for t in texts]
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings batch: {str(e)}")
            return [self._mock_embedding(t) for t in texts]

    def get_dimension(self) -> int:
        # text-embedding-3-small defaults to 1536 dimensions
        return 1536

    def _mock_embedding(self, text: str) -> List[float]:
        """
        Deterministic mock generator for testing without credentials.
        Returns a mock unit vector based on text hash values.
        """
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        dim = self.get_dimension()
        vector = []
        for i in range(dim):
            # Deterministic pseudo-random generation from hash slice
            val = (h[i % len(h)] * (i + 1)) % 1000 - 500
            vector.append(float(val))
            
        # Normalize vector
        magnitude = sum(x**2 for x in vector)**0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        return vector


def get_embedding_provider() -> BaseEmbeddingProvider:
    return OpenAIEmbeddingProvider()

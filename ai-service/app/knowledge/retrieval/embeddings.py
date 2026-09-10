"""
Embedding generator interface for future RAG pipeline.
"""
from typing import List
from app.core.config import settings


class EmbeddingGenerator:
    """
    Embedding service interface supporting pgvector semantic retrieval.
    """
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self.dimension = settings.EMBEDDING_DIMENSION

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for input query/document.
        """
        # Placeholder vector
        return [0.0] * self.dimension

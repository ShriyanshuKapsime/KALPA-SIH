"""
Vector store interface for pgvector similarity search.
"""
from typing import List, Dict, Any, Optional
from app.core.config import settings


class PGVectorStore:
    """
    Interface for PostgreSQL + pgvector storage and cosine similarity retrieval.
    """
    def __init__(self):
        self.enabled = settings.PGVECTOR_ENABLED

    async def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute vector similarity search. Returns matching scheme or benchmark documents.
        """
        return []

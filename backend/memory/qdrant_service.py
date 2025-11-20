"""
Qdrant Vector Memory Service (Phase 9)

Provides semantic similarity search for memory retrieval.

**CRITICAL INVARIANTS:**
- Postgres is authoritative store for ALL memories
- Qdrant used ONLY for retrieval ranking and similarity
- No unique information exists only in Qdrant
- On Qdrant unavailability, falls back to Postgres-only retrieval
- Embeddings are deterministic (fixed embedding model)

Per Plan.md §9.6: Qdrant constraints.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import hashlib

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance
except ImportError:
    QdrantClient = None
    logger = logging.getLogger(__name__)
    logger.warning("qdrant-client not installed. Vector memory disabled.")

logger = logging.getLogger(__name__)


@dataclass
class MemoryHit:
    """Result from memory similarity search."""
    memory_id: int
    agent_id: int
    memory_type: str  # "episodic" or "biographical"
    description: str
    similarity_score: float  # 0-1, higher is more similar
    timestamp: Optional[str] = None


class QdrantService:
    """
    Qdrant vector database for semantic memory retrieval.
    
    Designed to fail gracefully:
    - If Qdrant unavailable, Postgres retrieval used
    - All data redundantly in Postgres
    - No data loss if Qdrant restarted
    """
    
    # Collection names
    COLLECTION_EPISODIC = "episodic_memories"
    COLLECTION_BIOGRAPHICAL = "biographical_memories"
    COLLECTION_PERSONALITY = "personality_summaries"
    
    # Vector dimension (for embeddings)
    VECTOR_DIM = 384  # Small model (e.g., all-MiniLM-L6-v2)
    
    def __init__(self):
        """Initialize Qdrant client."""
        if QdrantClient is None:
            logger.warning("qdrant-client not installed. Vector memory disabled.")
            self.enabled = False
            self.client = None
            return
        
        self.qdrant_url = os.environ.get("QDRANT_URL")
        self.qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        self.client: Optional[QdrantClient] = None
        self.enabled = bool(self.qdrant_url)
        
        if self.enabled:
            logger.info(f"Qdrant vector memory enabled: {self.qdrant_url}")
        else:
            logger.warning("Qdrant not configured (QDRANT_URL env var missing). Vector memory disabled.")
    
    async def connect(self) -> None:
        """
        Establish Qdrant connection and ensure collections exist.
        Failure is non-fatal.
        """
        if not self.enabled or not QdrantClient:
            return
        
        try:
            # Create client
            if self.qdrant_api_key:
                self.client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key,
                    timeout=10
                )
            else:
                self.client = QdrantClient(
                    url=self.qdrant_url,
                    timeout=10
                )
            
            # Test connection
            self.client.get_collections()
            logger.info("✓ Qdrant connection established")
            
            # Ensure collections exist
            await self._ensure_collections()
            
        except Exception as e:
            logger.warning(f"✗ Failed to connect to Qdrant: {e}. Vector memory disabled.")
            self.client = None
            self.enabled = False
    
    async def _ensure_collections(self) -> None:
        """Create collections if they don't exist."""
        if not self.client:
            return
        
        collections_to_create = [
            self.COLLECTION_EPISODIC,
            self.COLLECTION_BIOGRAPHICAL,
            self.COLLECTION_PERSONALITY,
        ]
        
        try:
            existing = {c.name for c in self.client.get_collections().collections}
            
            for collection_name in collections_to_create:
                if collection_name not in existing:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.VECTOR_DIM,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {collection_name}")
        
        except Exception as e:
            logger.warning(f"Failed to ensure collections: {e}")
    
    async def is_available(self) -> bool:
        """Check if Qdrant is currently available."""
        if not self.client:
            return False
        
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    # ========================================================================
    # MEMORY INDEXING
    # ========================================================================
    
    def _embed_text(self, text: str) -> List[float]:
        """
        Embed text to vector.
        
        For now, use a simple hash-based deterministic embedding.
        In production, would use a real embedding model (SentenceTransformers, etc).
        
        CRITICAL: Embeddings must be deterministic.
        Same text → same vector always.
        """
        # Hash-based deterministic embedding (placeholder)
        # In real system, use:
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # return model.encode(text).tolist()
        
        hash_val = hashlib.sha256(text.encode()).digest()
        vector = []
        for i in range(self.VECTOR_DIM):
            # Use bytes from hash cyclically
            byte_val = hash_val[i % len(hash_val)]
            # Map byte (0-255) to range (-1, 1)
            vector.append((byte_val / 255.0) * 2 - 1)
        
        # Normalize
        magnitude = sum(v ** 2 for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    async def index_episodic_memory(
        self,
        memory_id: int,
        agent_id: int,
        description: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Add episodic memory to vector index.
        
        Args:
            memory_id: Database ID of memory
            agent_id: Agent who owns the memory
            description: Memory description text
            timestamp: ISO 8601 timestamp
            
        Returns:
            True if indexed, False if unavailable
        """
        if not self.client:
            return False
        
        try:
            vector = self._embed_text(description)
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload={
                    "agent_id": agent_id,
                    "type": "episodic",
                    "description": description,
                    "timestamp": timestamp
                }
            )
            
            self.client.upsert(
                collection_name=self.COLLECTION_EPISODIC,
                points=[point]
            )
            return True
        
        except Exception as e:
            logger.debug(f"Failed to index episodic memory: {e}")
            return False
    
    async def index_biographical_memory(
        self,
        memory_id: int,
        agent_id: int,
        description: str
    ) -> bool:
        """
        Add biographical memory to vector index.
        
        Args:
            memory_id: Database ID of memory
            agent_id: Agent who owns the memory
            description: Biographical fact description
            
        Returns:
            True if indexed, False if unavailable
        """
        if not self.client:
            return False
        
        try:
            vector = self._embed_text(description)
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload={
                    "agent_id": agent_id,
                    "type": "biographical",
                    "description": description
                }
            )
            
            self.client.upsert(
                collection_name=self.COLLECTION_BIOGRAPHICAL,
                points=[point]
            )
            return True
        
        except Exception as e:
            logger.debug(f"Failed to index biographical memory: {e}")
            return False
    
    # ========================================================================
    # MEMORY RETRIEVAL
    # ========================================================================
    
    async def search_episodic_memories(
        self,
        agent_id: int,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.3
    ) -> List[MemoryHit]:
        """
        Search episodic memories for agent by semantic similarity.
        
        Args:
            agent_id: Agent whose memories to search
            query_text: Query text to find similar memories
            limit: Max results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of MemoryHit objects, sorted by similarity (highest first)
        """
        if not self.client:
            return []
        
        try:
            query_vector = self._embed_text(query_text)
            
            results = self.client.search(
                collection_name=self.COLLECTION_EPISODIC,
                query_vector=query_vector,
                query_filter=f"agent_id == {agent_id}",  # Filter by agent
                limit=limit
            )
            
            hits = []
            for scored_point in results:
                if scored_point.score >= threshold:
                    payload = scored_point.payload
                    hits.append(MemoryHit(
                        memory_id=scored_point.id,
                        agent_id=payload.get("agent_id", agent_id),
                        memory_type="episodic",
                        description=payload.get("description", ""),
                        similarity_score=scored_point.score,
                        timestamp=payload.get("timestamp")
                    ))
            
            return hits
        
        except Exception as e:
            logger.debug(f"Failed to search episodic memories: {e}")
            return []
    
    async def search_biographical_memories(
        self,
        agent_id: int,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.3
    ) -> List[MemoryHit]:
        """
        Search biographical memories for agent.
        
        Args:
            agent_id: Agent whose memories to search
            query_text: Query text to find similar facts
            limit: Max results
            threshold: Minimum similarity score
            
        Returns:
            List of MemoryHit objects
        """
        if not self.client:
            return []
        
        try:
            query_vector = self._embed_text(query_text)
            
            results = self.client.search(
                collection_name=self.COLLECTION_BIOGRAPHICAL,
                query_vector=query_vector,
                query_filter=f"agent_id == {agent_id}",
                limit=limit
            )
            
            hits = []
            for scored_point in results:
                if scored_point.score >= threshold:
                    payload = scored_point.payload
                    hits.append(MemoryHit(
                        memory_id=scored_point.id,
                        agent_id=payload.get("agent_id", agent_id),
                        memory_type="biographical",
                        description=payload.get("description", ""),
                        similarity_score=scored_point.score
                    ))
            
            return hits
        
        except Exception as e:
            logger.debug(f"Failed to search biographical memories: {e}")
            return []
    
    async def search_all_memories(
        self,
        agent_id: int,
        query_text: str,
        limit: int = 20,
        threshold: float = 0.3
    ) -> List[MemoryHit]:
        """
        Search both episodic and biographical memories.
        
        Results combined and sorted by similarity (highest first).
        """
        episodic = await self.search_episodic_memories(
            agent_id, query_text, limit=limit, threshold=threshold
        )
        biographical = await self.search_biographical_memories(
            agent_id, query_text, limit=limit, threshold=threshold
        )
        
        # Combine and sort by similarity
        combined = episodic + biographical
        combined.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Return top N
        return combined[:limit]
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    async def delete_memory(self, collection: str, memory_id: int) -> bool:
        """Delete memory from vector index."""
        if not self.client:
            return False
        
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=memory_id
            )
            return True
        except Exception as e:
            logger.debug(f"Failed to delete memory: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health."""
        return {
            "available": await self.is_available(),
            "connected": self.client is not None,
            "url_configured": self.enabled,
            "collections": [],  # Would populate with actual collections
            "error": None if self.client else "Qdrant not configured"
        }


# Global instance
_qdrant_service: Optional[QdrantService] = None


async def get_qdrant_service() -> QdrantService:
    """Get or create global Qdrant service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
        await _qdrant_service.connect()
    return _qdrant_service

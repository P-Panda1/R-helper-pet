"""Qdrant vector store implementation."""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
import uuid
from datetime import datetime
from src.config import get_config

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant-based vector store for document retrieval."""
    
    def __init__(self, config=None):
        """Initialize Qdrant vector store."""
        self.config = config or get_config()
        self.client: Optional[QdrantClient] = None
        self.collection_name = self.config.vector_store.collection_name
        self._connect()
        self._ensure_collection()
    
    def _connect(self):
        """Connect to Qdrant server."""
        try:
            self.client = QdrantClient(
                host=self.config.vector_store.host,
                port=self.config.vector_store.port,
                timeout=10
            )
            logger.info(f"Connected to Qdrant at {self.config.vector_store.host}:{self.config.vector_store.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            logger.info("Attempting to start local Qdrant instance...")
            # For local development, user should run Qdrant via Docker
            raise ConnectionError(
                "Qdrant server not available. Please start Qdrant:\n"
                "docker run -p 6333:6333 qdrant/qdrant"
            )
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_store.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info("Collection created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add documents to the vector store."""
        if len(texts) != len(embeddings):
            raise ValueError("Texts and embeddings must have the same length")
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        points = []
        ids = []
        
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    **metadata
                }
            )
            points.append(point)
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            # Build filter if provided
            query_filter = None
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold or self.config.vector_store.similarity_threshold
            )
            
            documents = []
            for result in results:
                documents.append({
                    "id": result.id,
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"}
                })
            
            return documents
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def delete_collection(self):
        """Delete the collection (use with caution)."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.name,
                "vectors_count": info.points_count,
                "config": info.config.dict() if hasattr(info.config, 'dict') else str(info.config)
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}


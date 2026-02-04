"""Embedding encoder for document vectorization."""

import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer
from src.config import get_config

logger = logging.getLogger(__name__)


class EmbeddingEncoder:
    """Generate embeddings for text using sentence transformers."""
    
    def __init__(self, config=None):
        """Initialize embedding encoder."""
        self.config = config or get_config()
        self.model: SentenceTransformer = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.config.embedding.model_name}")
            self.model = SentenceTransformer(
                self.config.embedding.model_name,
                device=self.config.embedding.device
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Encode text(s) into embeddings."""
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.config.embedding.batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
            
            # Convert to list format
            if len(embeddings.shape) == 1:
                embeddings = embeddings.tolist()
            else:
                embeddings = embeddings.tolist()
            
            return embeddings[0] if is_single else embeddings
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self.model is None:
            return self.config.vector_store.dimension
        return self.model.get_sentence_embedding_dimension()


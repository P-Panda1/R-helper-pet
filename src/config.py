"""Configuration management for the application."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration."""
    model_path: str
    model_name: str
    n_ctx: int = 4096
    n_threads: int = 4
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model_name: str
    batch_size: int = 32
    device: str = "cpu"


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    type: str = "qdrant"
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "history_knowledge_base"
    dimension: int = 384
    similarity_threshold: float = 0.7


class AgentConfig(BaseModel):
    """Agent configuration."""
    query_analyzer: Dict[str, Any] = Field(default_factory=lambda: {"max_keywords": 5, "min_keywords": 3})
    information_gatherer: Dict[str, Any] = Field(default_factory=lambda: {
        "max_urls_per_keyword": 10,
        "top_n_urls": 5,
        "crawl_timeout": 30,
        "max_concurrent_crawls": 5
    })
    answer_synthesizer: Dict[str, Any] = Field(default_factory=lambda: {
        "top_k_chunks": 5,
        "max_context_length": 3000
    })


class CrawlingConfig(BaseModel):
    """Web crawling configuration."""
    user_agent: str
    timeout: int = 30
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl_days: int = 7


class EvaluationConfig(BaseModel):
    """Evaluation metrics configuration."""
    rouge_types: list = Field(default_factory=lambda: ["rouge1", "rouge2", "rougeL"])
    precision_at_k: list = Field(default_factory=lambda: [1, 3, 5])


class UIConfig(BaseModel):
    """UI configuration."""
    window_width: int = 1200
    window_height: int = 800
    theme: str = "light"


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        self.llm = LLMConfig(**config_data.get('llm', {}))
        self.embedding = EmbeddingConfig(**config_data.get('embedding', {}))
        self.vector_store = VectorStoreConfig(**config_data.get('vector_store', {}))
        self.agents = AgentConfig(**config_data.get('agents', {}))
        self.crawling = CrawlingConfig(**config_data.get('crawling', {}))
        self.evaluation = EvaluationConfig(**config_data.get('evaluation', {}))
        self.ui = UIConfig(**config_data.get('ui', {}))
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(self.llm.model_path), exist_ok=True)


# Global config instance
_config: Config = None


def get_config(config_path: str = "config.yaml") -> Config:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


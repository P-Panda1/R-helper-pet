"""CPU-based LLM inference using llama.cpp."""

import os
from typing import List, Optional, Dict, Any
from llama_cpp import Llama
from pathlib import Path
import logging
from huggingface_hub import hf_hub_download
from src.config import get_config

logger = logging.getLogger(__name__)


class LLMInference:
    """CPU-optimized LLM inference engine using llama.cpp."""
    
    def __init__(self, config=None):
        """Initialize LLM inference engine."""
        self.config = config or get_config()
        self.model: Optional[Llama] = None
        self._ensure_model()
        self._load_model()
    
    def _ensure_model(self):
        """Download model if not present."""
        model_path = Path(self.config.llm.model_path)
        
        if not model_path.exists():
            logger.info(f"Model not found at {model_path}. Downloading from Hugging Face...")
            # Try to download GGUF model
            try:
                # For CPU, we'll use a smaller quantized model
                # User can specify their preferred model in config
                repo_id = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
                filename = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"  # 4-bit quantized for CPU
                
                logger.info(f"Downloading {filename} from {repo_id}...")
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=model_path.parent,
                    local_dir_use_symlinks=False
                )
                # Move to expected location
                if downloaded_path != str(model_path):
                    import shutil
                    shutil.move(downloaded_path, model_path)
                logger.info(f"Model downloaded to {model_path}")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                logger.info("Please download a GGUF model manually and place it at the configured path.")
                raise
    
    def _load_model(self):
        """Load the GGUF model."""
        try:
            logger.info(f"Loading model from {self.config.llm.model_path}...")
            self.model = Llama(
                model_path=self.config.llm.model_path,
                n_ctx=self.config.llm.n_ctx,
                n_threads=self.config.llm.n_threads,
                verbose=False
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate text from prompt."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Format prompt with system message if provided
        if system_prompt:
            formatted_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            formatted_prompt = prompt
        
        # Use config defaults if not specified
        max_tokens = max_tokens or self.config.llm.max_tokens
        temperature = temperature if temperature is not None else self.config.llm.temperature
        top_p = top_p if top_p is not None else self.config.llm.top_p
        
        try:
            response = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
                echo=False
            )
            
            # Extract text from response
            if isinstance(response, dict):
                text = response.get('choices', [{}])[0].get('text', '')
            else:
                text = str(response)
            
            return text.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate text with streaming output."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if system_prompt:
            formatted_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            formatted_prompt = prompt
        
        for chunk in self.model(
            formatted_prompt,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            stream=True
        ):
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('text', '')
                if delta:
                    yield delta


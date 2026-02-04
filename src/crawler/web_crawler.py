"""Web crawler using Crawl4AI for content extraction."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_config

logger = logging.getLogger(__name__)


class WebCrawler:
    """Web crawler for extracting historical content."""
    
    def __init__(self, config=None):
        """Initialize web crawler."""
        self.config = config or get_config()
        self.cache_dir = Path("cache/crawled_content")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.crawler: Optional[AsyncWebCrawler] = None
    
    async def _get_crawler(self):
        """Get or create crawler instance."""
        if self.crawler is None:
            self.crawler = AsyncWebCrawler(
                user_agent=self.config.crawling.user_agent,
                verbose=False
            )
        return self.crawler
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid."""
        if not self.config.crawling.cache_enabled:
            return False
        
        if not cache_path.exists():
            return False
        
        try:
            cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            return cache_age < timedelta(days=self.config.crawling.cache_ttl_days)
        except Exception:
            return False
    
    def _load_from_cache(self, cache_path: Path) -> Optional[Dict[str, Any]]:
        """Load content from cache."""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
    
    def _save_to_cache(self, cache_path: Path, data: Dict[str, Any]):
        """Save content to cache."""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def crawl_url(self, url: str, use_cache: bool = True) -> Dict[str, Any]:
        """Crawl a single URL and extract content."""
        cache_path = self._get_cache_path(url)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_path):
            logger.info(f"Loading {url} from cache")
            cached_data = self._load_from_cache(cache_path)
            if cached_data:
                return cached_data
        
        try:
            crawler = await self._get_crawler()
            
            logger.info(f"Crawling: {url}")
            result = await crawler.arun(
                url=url,
                wait_for="networkidle",
                timeout=self.config.crawling.timeout * 1000  # Convert to milliseconds
            )
            
            if result.success:
                # Extract clean text
                content = result.cleaned_html or result.markdown or result.text
                
                crawled_data = {
                    "url": url,
                    "content": content,
                    "title": result.metadata.get("title", ""),
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                
                # Save to cache
                if use_cache:
                    self._save_to_cache(cache_path, crawled_data)
                
                return crawled_data
            else:
                logger.warning(f"Failed to crawl {url}: {result.error_message}")
                return {
                    "url": url,
                    "content": "",
                    "title": "",
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": result.error_message
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout crawling {url}")
            return {
                "url": url,
                "content": "",
                "title": "",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return {
                "url": url,
                "content": "",
                "title": "",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    async def crawl_urls(self, urls: List[str], max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently."""
        max_concurrent = max_concurrent or self.config.agents.information_gatherer.get("max_concurrent_crawls", 5)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl_url(url)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception crawling {urls[i]}: {result}")
                processed_results.append({
                    "url": urls[i],
                    "content": "",
                    "title": "",
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def close(self):
        """Close crawler resources."""
        if self.crawler:
            await self.crawler.close()


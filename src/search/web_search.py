"""Web search integration for finding historical information."""

import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from googlesearch import search as google_search
from src.config import get_config

logger = logging.getLogger(__name__)


class WebSearch:
    """Web search interface for finding relevant URLs."""
    
    def __init__(self, config=None):
        """Initialize web search."""
        self.config = config or get_config()
        self.ddgs = DDGS()
    
    def search(self, query: str, num_results: int = 10, search_engine: str = "duckduckgo") -> List[Dict[str, Any]]:
        """Search the web for a query."""
        try:
            if search_engine == "duckduckgo":
                return self._search_duckduckgo(query, num_results)
            elif search_engine == "google":
                return self._search_google(query, num_results)
            else:
                raise ValueError(f"Unknown search engine: {search_engine}")
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            results = self.ddgs.text(
                query,
                max_results=num_results,
                safesearch='moderate'
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            logger.info(f"Found {len(formatted_results)} results for: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _search_google(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Google (fallback)."""
        try:
            results = list(google_search(query, num=num_results, stop=num_results))
            
            formatted_results = []
            for url in results:
                formatted_results.append({
                    "title": "",
                    "url": url,
                    "snippet": ""
                })
            
            logger.info(f"Found {len(formatted_results)} results for: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []


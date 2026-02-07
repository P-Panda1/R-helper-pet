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
        """Search the web for a query. Defaults to DuckDuckGo (more reliable)."""
        try:
            # Try DuckDuckGo first (more reliable, no rate limiting)
            if search_engine == "duckduckgo" or search_engine == "google":
                results = self._search_duckduckgo(query, num_results)
                # If DuckDuckGo fails, try Google
                if not results:
                    logger.info("DuckDuckGo search returned no results, trying Google...")
                    results = self._search_google(query, num_results)
                return results
            else:
                raise ValueError(f"Unknown search engine: {search_engine}")
        except Exception as e:
            logger.error(f"Search error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Try fallback
            return self._search_duckduckgo(query, num_results)
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            logger.debug(f"DuckDuckGo searching: {query}")
            
            # Create new DDGS instance for each search to avoid issues
            ddgs = DDGS()
            
            # DuckDuckGo returns an iterator, convert to list
            # Use text() method which is more reliable
            try:
                results_iter = ddgs.text(
                    query,
                    max_results=num_results,
                    safesearch='moderate'
                )
            except Exception as e:
                logger.error(f"Error creating DuckDuckGo search: {e}")
                return []
            
            # Convert iterator to list and process
            results = []
            try:
                # Try to get all results at once
                for item in results_iter:
                    results.append(item)
                    if len(results) >= num_results:
                        break
                logger.debug(f"DuckDuckGo raw results count: {len(results)}")
            except StopIteration:
                # Iterator exhausted, that's fine
                logger.debug(f"DuckDuckGo iterator exhausted after {len(results)} results")
            except Exception as e:
                logger.warning(f"Error iterating DuckDuckGo results: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                # Return what we have so far
                if not results:
                    return []
            
            formatted_results = []
            for i, result in enumerate(results):
                try:
                    # Handle different result formats
                    url = None
                    title = ""
                    snippet = ""
                    
                    if isinstance(result, dict):
                        # Try different possible keys
                        url = (result.get("href") or result.get("url") or 
                               result.get("link") or result.get("result"))
                        title = result.get("title", "")
                        snippet = (result.get("body") or result.get("snippet") or 
                                  result.get("description") or result.get("text", ""))
                    else:
                        # Handle object with attributes
                        url = (getattr(result, "href", None) or 
                              getattr(result, "url", None) or 
                              getattr(result, "link", None) or
                              getattr(result, "result", None))
                        title = getattr(result, "title", "")
                        snippet = (getattr(result, "body", None) or 
                                  getattr(result, "snippet", None) or 
                                  getattr(result, "description", None) or
                                  getattr(result, "text", ""))
                    
                    # If url is still None, try to extract from result dict/object
                    if not url and isinstance(result, dict):
                        # Sometimes the URL is nested or in a different format
                        for key in result.keys():
                            if 'url' in key.lower() or 'href' in key.lower() or 'link' in key.lower():
                                url = result.get(key)
                                break
                    
                    # Only add if we have a valid URL
                    if url:
                        if isinstance(url, str) and url.startswith(("http://", "https://")):
                            formatted_results.append({
                                "title": title or url,
                                "url": url,
                                "snippet": snippet or ""
                            })
                        else:
                            logger.debug(f"Skipping invalid URL format: {url} (type: {type(url)})")
                    else:
                        logger.debug(f"Result {i} has no URL. Result structure: {type(result)} - {str(result)[:100]}")
                        
                except Exception as e:
                    logger.debug(f"Error processing result {i}: {e}")
                    logger.debug(f"Result type: {type(result)}, content: {str(result)[:200]}")
                    continue
            
            logger.info(f"Found {len(formatted_results)} results for: {query}")
            if len(formatted_results) == 0 and len(results) > 0:
                logger.warning(f"DuckDuckGo returned {len(results)} raw results but none were formatted correctly")
                if results:
                    logger.warning(f"Sample raw result type: {type(results[0])}")
                    logger.warning(f"Sample raw result: {str(results[0])[:200]}")
            
            return formatted_results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _search_google(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Google (fallback method)."""
        try:
            logger.debug(f"Google searching: {query}")
            
            # Try different parameter combinations
            try:
                # Method 1: Using num parameter
                results = list(google_search(query, num=num_results, stop=num_results, pause=2.0))
            except TypeError:
                try:
                    # Method 2: Using num_results parameter
                    results = list(google_search(query, num_results=num_results))
                except Exception as e:
                    logger.warning(f"Google search parameter error: {e}")
                    # Method 3: Basic call
                    results = list(google_search(query, pause=2.0))
                    results = results[:num_results]
            
            formatted_results = []
            for url in results:
                if url and isinstance(url, str) and url.startswith(("http://", "https://")):
                    formatted_results.append({
                        "title": url,  # Use URL as title if no title available
                        "url": url,
                        "snippet": ""
                    })
            
            logger.info(f"Found {len(formatted_results)} results for: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Google search is often blocked, return empty rather than crashing
            return []


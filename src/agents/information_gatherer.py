"""Information Gatherer Agent - Searches web and crawls content."""

import logging
import asyncio
from typing import List, Dict, Any
from src.search.web_search import WebSearch
from src.crawler.web_crawler import WebCrawler
from src.embeddings.encoder import EmbeddingEncoder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config import get_config

logger = logging.getLogger(__name__)


class InformationGathererAgent:
    """Agent that gathers information from the web and stores it in vector database."""
    
    def __init__(self, config=None):
        """Initialize Information Gatherer Agent."""
        self.config = config or get_config()
        self.web_search = WebSearch(self.config)
        self.crawler = WebCrawler(self.config)
        self.encoder = EmbeddingEncoder(self.config)
        self.vector_store = QdrantVectorStore(self.config)
    
    async def gather(self, keywords: List[str], original_question: str) -> Dict[str, Any]:
        """Gather information for given keywords."""
        try:
            # Step 1: Search for URLs for each keyword
            all_urls = []
            search_results = {}
            
            for keyword in keywords:
                logger.info(f"Searching for keyword: {keyword}")
                results = self.web_search.search(
                    query=f"{keyword} history",
                    num_results=self.config.agents.information_gatherer.get("max_urls_per_keyword", 10)
                )
                search_results[keyword] = results
                urls = [r["url"] for r in results[:self.config.agents.information_gatherer.get("top_n_urls", 5)]]
                all_urls.extend(urls)
            
            # Remove duplicates while preserving order
            unique_urls = list(dict.fromkeys(all_urls))
            logger.info(f"Found {len(unique_urls)} unique URLs to crawl")
            
            # Step 2: Crawl URLs
            crawled_content = await self.crawler.crawl_urls(unique_urls)
            
            # Step 3: Process and store in vector database
            successful_crawls = [c for c in crawled_content if c.get("success") and c.get("content")]
            logger.info(f"Successfully crawled {len(successful_crawls)} URLs")
            
            if not successful_crawls:
                return {
                    "keywords": keywords,
                    "urls_searched": len(unique_urls),
                    "urls_crawled": 0,
                    "documents_stored": 0,
                    "success": False,
                    "error": "No content successfully crawled"
                }
            
            # Step 4: Chunk and embed content
            chunks, embeddings, metadatas = self._process_content(successful_crawls, keywords)
            
            # Step 5: Store in vector database
            if chunks and embeddings:
                doc_ids = self.vector_store.add_documents(
                    texts=chunks,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"Stored {len(doc_ids)} document chunks in vector store")
            else:
                doc_ids = []
            
            return {
                "keywords": keywords,
                "urls_searched": len(unique_urls),
                "urls_crawled": len(successful_crawls),
                "documents_stored": len(doc_ids),
                "search_results": search_results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Information gathering error: {e}")
            return {
                "keywords": keywords,
                "urls_searched": 0,
                "urls_crawled": 0,
                "documents_stored": 0,
                "success": False,
                "error": str(e)
            }
    
    def _process_content(self, crawled_content: List[Dict[str, Any]], keywords: List[str]) -> tuple:
        """Chunk content and generate embeddings."""
        chunks = []
        metadatas = []
        
        for item in crawled_content:
            content = item.get("content", "")
            if not content:
                continue
            
            # Simple chunking by paragraphs (can be improved with more sophisticated chunking)
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 100]
            
            for para in paragraphs:
                if len(para) > 5000:  # Split very long paragraphs
                    # Split by sentences
                    sentences = para.split(". ")
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) < 5000:
                            current_chunk += sentence + ". "
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                metadatas.append({
                                    "url": item.get("url", ""),
                                    "title": item.get("title", ""),
                                    "keywords": keywords,
                                    "source": "web_crawl"
                                })
                            current_chunk = sentence + ". "
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        metadatas.append({
                            "url": item.get("url", ""),
                            "title": item.get("title", ""),
                            "keywords": keywords,
                            "source": "web_crawl"
                        })
                else:
                    chunks.append(para)
                    metadatas.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "keywords": keywords,
                        "source": "web_crawl"
                    })
        
        # Generate embeddings
        if chunks:
            embeddings = self.encoder.encode(chunks)
            return chunks, embeddings, metadatas
        else:
            return [], [], []
    
    async def close(self):
        """Close resources."""
        await self.crawler.close()


"""Answer Synthesizer Agent - Generates answers using RAG."""

import logging
from typing import List, Dict, Any
from src.llm.inference import LLMInference
from src.embeddings.encoder import EmbeddingEncoder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config import get_config

logger = logging.getLogger(__name__)


class AnswerSynthesizerAgent:
    """Agent that synthesizes answers using RAG architecture."""
    
    def __init__(self, llm: LLMInference = None, config=None):
        """Initialize Answer Synthesizer Agent."""
        self.config = config or get_config()
        self.llm = llm or LLMInference(self.config)
        self.encoder = EmbeddingEncoder(self.config)
        self.vector_store = QdrantVectorStore(self.config)
        self.system_prompt = """You are an expert historian providing accurate, well-sourced answers to historical questions.
Use the provided context to answer the question comprehensively. Cite specific sources when possible.
If the context doesn't contain enough information, acknowledge this limitation.
Be precise with dates, names, and historical facts."""
    
    def synthesize(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Synthesize answer using RAG."""
        try:
            top_k = top_k or self.config.agents.answer_synthesizer.get("top_k_chunks", 5)
            
            # Step 1: Generate query embedding
            query_embedding = self.encoder.encode(question)
            
            # Step 2: Retrieve relevant chunks
            relevant_docs = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            if not relevant_docs:
                return {
                    "question": question,
                    "answer": "I couldn't find relevant information in the knowledge base to answer this question. Please try rephrasing or ensure information has been gathered first.",
                    "sources": [],
                    "context_used": False
                }
            
            # Step 3: Build context from retrieved documents
            context = self._build_context(relevant_docs)
            
            # Step 4: Generate answer with context
            answer = self._generate_answer(question, context)
            
            # Step 5: Extract sources
            sources = self._extract_sources(relevant_docs)
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "context_used": True,
                "num_chunks_used": len(relevant_docs)
            }
            
        except Exception as e:
            logger.error(f"Answer synthesis error: {e}")
            return {
                "question": question,
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "context_used": False,
                "error": str(e)
            }
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents."""
        max_length = self.config.agents.answer_synthesizer.get("max_context_length", 3000)
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            url = doc.get("metadata", {}).get("url", "")
            title = doc.get("metadata", {}).get("title", "")
            
            # Format context entry
            entry = f"[Source {i+1}]"
            if title:
                entry += f" {title}"
            if url:
                entry += f" ({url})"
            entry += f"\n{text}\n\n"
            
            if current_length + len(entry) > max_length:
                break
            
            context_parts.append(entry)
            current_length += len(entry)
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with context."""
        prompt = f"""Based on the following context, answer the historical question comprehensively.

Context:
{context}

Question: {question}

Provide a detailed, accurate answer based on the context. Include relevant dates, names, and events. 
If the context doesn't fully answer the question, acknowledge what information is missing."""
        
        answer = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_tokens=self.config.llm.max_tokens,
            temperature=0.5  # Lower temperature for more factual answers
        )
        
        return answer.strip()
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from documents."""
        sources = []
        seen_urls = set()
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            url = metadata.get("url", "")
            title = metadata.get("title", "")
            
            if url and url not in seen_urls:
                sources.append({
                    "url": url,
                    "title": title or url,
                    "relevance_score": doc.get("score", 0.0)
                })
                seen_urls.add(url)
        
        return sources


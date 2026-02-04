"""Query Analyzer Agent - Extracts search keywords from historical questions."""

import logging
import json
from typing import List, Dict, Any
from src.llm.inference import LLMInference
from src.config import get_config

logger = logging.getLogger(__name__)


class QueryAnalyzerAgent:
    """Agent that analyzes historical questions and extracts optimal search keywords."""
    
    def __init__(self, llm: LLMInference = None, config=None):
        """Initialize Query Analyzer Agent."""
        self.config = config or get_config()
        self.llm = llm or LLMInference(self.config)
        self.system_prompt = """You are an expert historian and information retrieval specialist. 
Your task is to analyze historical questions and extract 3-5 optimal search keywords that will help 
find the most relevant information to answer the question.

Consider:
- Key historical events, dates, people, places mentioned
- Important concepts and themes
- Temporal relationships (before/after, during)
- Geographic context if relevant

Return ONLY a JSON array of keywords, nothing else. Example format: ["keyword1", "keyword2", "keyword3"]"""
    
    def analyze(self, question: str) -> Dict[str, Any]:
        """Analyze question and extract keywords."""
        try:
            prompt = f"""Analyze this historical question and extract 3-5 optimal search keywords:

Question: {question}

Extract keywords that will help find comprehensive information to answer this question. 
Return a JSON array of keywords."""
            
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse JSON response
            keywords = self._parse_keywords(response)
            
            # Validate keyword count
            min_kw = self.config.agents.query_analyzer.get("min_keywords", 3)
            max_kw = self.config.agents.query_analyzer.get("max_keywords", 5)
            
            if len(keywords) < min_kw:
                logger.warning(f"Only {len(keywords)} keywords extracted, expected at least {min_kw}")
            elif len(keywords) > max_kw:
                keywords = keywords[:max_kw]
                logger.info(f"Truncated to {max_kw} keywords")
            
            result = {
                "question": question,
                "keywords": keywords,
                "keyword_count": len(keywords)
            }
            
            logger.info(f"Extracted {len(keywords)} keywords: {keywords}")
            return result
            
        except Exception as e:
            logger.error(f"Query analysis error: {e}")
            # Fallback: simple keyword extraction
            keywords = self._fallback_keyword_extraction(question)
            return {
                "question": question,
                "keywords": keywords,
                "keyword_count": len(keywords),
                "fallback": True
            }
    
    def _parse_keywords(self, response: str) -> List[str]:
        """Parse keywords from LLM response."""
        # Try to extract JSON array
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        
        # Try to find JSON array
        try:
            # Look for array pattern
            start_idx = response.find("[")
            end_idx = response.rfind("]")
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx+1]
                keywords = json.loads(json_str)
                if isinstance(keywords, list):
                    return [str(kw).strip() for kw in keywords if kw]
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract quoted strings
        import re
        keywords = re.findall(r'"([^"]+)"', response)
        if keywords:
            return keywords
        
        # Last resort: split by common delimiters
        keywords = [kw.strip() for kw in re.split(r'[,;]', response) if kw.strip()]
        return keywords[:5]  # Limit to 5
    
    def _fallback_keyword_extraction(self, question: str) -> List[str]:
        """Fallback keyword extraction using simple heuristics."""
        import re
        # Remove common stop words
        stop_words = {"what", "when", "where", "who", "why", "how", "the", "a", "an", "is", "was", "were", "did", "do", "does"}
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:5]


"""Evaluation metrics for retrieval and answer quality."""

import logging
from typing import List, Dict, Any, Optional
from rouge_score import rouge_scorer
import numpy as np
from src.config import get_config

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Evaluation metrics for the history helper system."""
    
    def __init__(self, config=None):
        """Initialize evaluation metrics."""
        self.config = config or get_config()
        self.rouge_scorer = rouge_scorer.RougeScorer(
            self.config.evaluation.rouge_types,
            use_stemmer=True
        )
    
    def evaluate_answer_quality(
        self,
        generated_answer: str,
        reference_answer: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate answer quality using ROUGE scores."""
        if reference_answer is None:
            return {
                "rouge1": 0.0,
                "rouge2": 0.0,
                "rougeL": 0.0,
                "note": "No reference answer provided"
            }
        
        scores = self.rouge_scorer.score(reference_answer, generated_answer)
        
        return {
            "rouge1": scores["rouge1"].fmeasure,
            "rouge2": scores["rouge2"].fmeasure,
            "rougeL": scores["rougeL"].fmeasure,
            "rouge1_precision": scores["rouge1"].precision,
            "rouge1_recall": scores["rouge1"].recall
        }
    
    def evaluate_retrieval_quality(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: Optional[List[str]] = None,
        k_values: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """Evaluate retrieval quality using precision@k."""
        k_values = k_values or self.config.evaluation.precision_at_k
        
        if relevant_doc_ids is None:
            return {
                f"precision@{k}": 0.0 for k in k_values
            }
        
        relevant_set = set(relevant_doc_ids)
        retrieved_ids = [doc.get("id", "") for doc in retrieved_docs]
        
        metrics = {}
        for k in k_values:
            top_k_ids = retrieved_ids[:k]
            relevant_retrieved = len([id for id in top_k_ids if id in relevant_set])
            precision = relevant_retrieved / k if k > 0 else 0.0
            metrics[f"precision@{k}"] = precision
        
        # Calculate overall precision and recall
        if retrieved_ids:
            relevant_retrieved = len([id for id in retrieved_ids if id in relevant_set])
            metrics["precision"] = relevant_retrieved / len(retrieved_ids)
            metrics["recall"] = relevant_retrieved / len(relevant_set) if relevant_set else 0.0
        
        return metrics
    
    def evaluate_keyword_relevance(
        self,
        extracted_keywords: List[str],
        question: str,
        retrieved_content: List[str]
    ) -> Dict[str, Any]:
        """Evaluate keyword extraction quality."""
        # Simple heuristic: check if keywords appear in retrieved content
        content_text = " ".join(retrieved_content).lower()
        keyword_scores = {}
        
        for keyword in extracted_keywords:
            keyword_lower = keyword.lower()
            # Count occurrences
            occurrences = content_text.count(keyword_lower)
            # Calculate relevance score (normalized)
            max_occurrences = max(len(content_text.split()) // 100, 1)  # Normalize by content length
            score = min(occurrences / max_occurrences, 1.0)
            keyword_scores[keyword] = {
                "occurrences": occurrences,
                "relevance_score": score
            }
        
        avg_relevance = np.mean([s["relevance_score"] for s in keyword_scores.values()]) if keyword_scores else 0.0
        
        return {
            "keyword_scores": keyword_scores,
            "average_relevance": avg_relevance,
            "total_keywords": len(extracted_keywords)
        }
    
    def comprehensive_evaluation(
        self,
        question: str,
        generated_answer: str,
        extracted_keywords: List[str],
        retrieved_docs: List[Dict[str, Any]],
        reference_answer: Optional[str] = None,
        relevant_doc_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Comprehensive evaluation of the entire pipeline."""
        results = {
            "question": question,
            "answer_quality": self.evaluate_answer_quality(generated_answer, reference_answer),
            "retrieval_quality": self.evaluate_retrieval_quality(retrieved_docs, relevant_doc_ids),
            "keyword_relevance": self.evaluate_keyword_relevance(
                extracted_keywords,
                question,
                [doc.get("text", "") for doc in retrieved_docs]
            )
        }
        
        # Calculate overall score (weighted average)
        answer_score = results["answer_quality"].get("rougeL", 0.0)
        retrieval_score = results["retrieval_quality"].get("precision@5", 0.0)
        keyword_score = results["keyword_relevance"].get("average_relevance", 0.0)
        
        overall_score = (answer_score * 0.5 + retrieval_score * 0.3 + keyword_score * 0.2)
        results["overall_score"] = overall_score
        
        return results


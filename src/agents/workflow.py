"""LangGraph workflow orchestrating the multi-agent system."""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from src.agents.query_analyzer import QueryAnalyzerAgent
from src.agents.information_gatherer import InformationGathererAgent
from src.agents.answer_synthesizer import AnswerSynthesizerAgent
from src.llm.inference import LLMInference
from src.config import get_config

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State for the agentic workflow."""
    question: str
    keywords: list
    gather_result: Dict[str, Any]
    answer: str
    sources: list
    metadata: Dict[str, Any]


class HistoryWorkflow:
    """Main workflow orchestrating all agents."""
    
    def __init__(self, config=None):
        """Initialize workflow."""
        self.config = config or get_config()
        self.llm = LLMInference(self.config)
        self.query_analyzer = QueryAnalyzerAgent(self.llm, self.config)
        self.information_gatherer = InformationGathererAgent(self.config)
        self.answer_synthesizer = AnswerSynthesizerAgent(self.llm, self.config)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("gather_information", self._gather_information_node)
        workflow.add_node("synthesize_answer", self._synthesize_answer_node)
        
        # Define edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "gather_information")
        workflow.add_edge("gather_information", "synthesize_answer")
        workflow.add_edge("synthesize_answer", END)
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: WorkflowState) -> WorkflowState:
        """Query analyzer node."""
        logger.info("Step 1: Analyzing query...")
        question = state["question"]
        result = self.query_analyzer.analyze(question)
        
        state["keywords"] = result["keywords"]
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["query_analysis"] = result
        
        return state
    
    async def _gather_information_node(self, state: WorkflowState) -> WorkflowState:
        """Information gatherer node."""
        logger.info("Step 2: Gathering information...")
        keywords = state["keywords"]
        question = state["question"]
        
        result = await self.information_gatherer.gather(keywords, question)
        state["gather_result"] = result
        
        return state
    
    def _synthesize_answer_node(self, state: WorkflowState) -> WorkflowState:
        """Answer synthesizer node."""
        logger.info("Step 3: Synthesizing answer...")
        question = state["question"]
        
        result = self.answer_synthesizer.synthesize(question)
        state["answer"] = result["answer"]
        state["sources"] = result["sources"]
        
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["answer_synthesis"] = result
        
        return state
    
    async def process(self, question: str) -> Dict[str, Any]:
        """Process a historical question through the workflow."""
        try:
            initial_state: WorkflowState = {
                "question": question,
                "keywords": [],
                "gather_result": {},
                "answer": "",
                "sources": [],
                "metadata": {}
            }
            
            # Run workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "question": final_state["question"],
                "answer": final_state["answer"],
                "sources": final_state["sources"],
                "keywords": final_state["keywords"],
                "metadata": final_state.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "keywords": [],
                "error": str(e)
            }
    
    async def close(self):
        """Close workflow resources."""
        await self.information_gatherer.close()


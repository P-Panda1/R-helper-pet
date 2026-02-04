#!/usr/bin/env python3
"""Test script for the History Helper system."""

import asyncio
import logging
from src.agents.workflow import HistoryWorkflow
from src.config import get_config
from src.utils.logger import setup_logging

# Set up logging
setup_logging(log_level=logging.INFO)

async def test_workflow():
    """Test the complete workflow."""
    config = get_config()
    workflow = HistoryWorkflow(config)
    
    test_questions = [
        "What were the main causes of World War I?",
        "Who was involved in the Battle of Gettysburg?",
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}\n")
        
        try:
            result = await workflow.process(question)
            
            print(f"Keywords: {result.get('keywords', [])}")
            print(f"\nAnswer:\n{result.get('answer', 'No answer')}")
            print(f"\nSources:")
            for i, source in enumerate(result.get('sources', []), 1):
                print(f"  {i}. {source.get('title', 'Untitled')}")
                print(f"     {source.get('url', '')}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    await workflow.close()

if __name__ == "__main__":
    asyncio.run(test_workflow())


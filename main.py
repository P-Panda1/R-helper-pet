#!/usr/bin/env python3
"""Main entry point for History Helper desktop application."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_logging
import logging

# Set up logging before importing other modules
setup_logging(log_level=logging.INFO)

from src.ui.main_window import main

if __name__ == "__main__":
    main()


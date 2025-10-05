"""
Testing framework for agent_flow.

This package provides CSV-based regression testing for OpenAI Agent SDK flows.
"""

from .discovery import find_csv_files, validate_csv
from .runner import run_tests

__all__ = [
    # Main entry point
    "run_tests",
    # Discovery
    "find_csv_files",
    "validate_csv",
]

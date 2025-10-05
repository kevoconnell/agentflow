"""
Calculator agent - directory-based structure.

Structure:
  calculator/
    __init__.py           # Makes it importable, exports main agent
    calculator_flow.py    # Agent logic and tools
    test.py               # Test cases (replaces meta.yaml)
"""

from .calculator_flow import calculator_agent, FLOW, CONTROLS

__all__ = ["calculator_agent", "FLOW", "CONTROLS"]

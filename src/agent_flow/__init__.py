"""
agent_flow: CSV-based regression testing for OpenAI Agents SDK.

Test your agents with CSV test definitions:

    from agents import Agent  # OpenAI Agents SDK

    # Create agents
    calculator = Agent(name="calculator", model="gpt-4o-mini",
                      instructions="You are a helpful calculator")

    # Define tests in CSV files
    # Run with: agent-flow test

Note: The openai-agents package (pip install openai-agents) provides the 'agents' module.
"""

from .loader import find_agent_files, load_agent, resolve_agent

__version__ = "0.1.0"

__all__ = [
    # Agent loading
    "load_agent",
    "find_agent_files",
    "resolve_agent",
    "get_shared_client",
]

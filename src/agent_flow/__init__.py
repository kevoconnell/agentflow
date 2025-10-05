"""
agent_flow: Minimal multi-agent workflow orchestration using OpenAI Agents SDK.

Import SDK agents directly and compose them into workflows:

    from agents import Agent  # OpenAI Agents SDK
    from agent_flow import FlowSpec, Handoff, Flow

    # Create agents using the OpenAI Agents SDK directly
    researcher = Agent(name="researcher", model="gpt-4", instructions="Research topics")
    writer = Agent(name="writer", model="gpt-4", instructions="Write content")

    # Compose into a workflow
    spec = FlowSpec(agents={"researcher": researcher, "writer": writer})

    flow = Flow(spec)

Note: The openai-agents package (pip install openai-agents) provides the 'agents' module.
"""

from .compat import get_shared_client  # Initialize client on import
from .flow import Flow
from .loader import find_workflow_files, load_workflow
from .types import FlowSpec

__version__ = "0.1.0"

__all__ = [
    # Core types
    "FlowSpec",
    # Flow execution
    "Flow",
    # Workflow loading
    "load_workflow",
    "find_workflow_files",
    # Client access
    "get_shared_client",
]

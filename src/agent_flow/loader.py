"""
Workflow and agent file discovery and loading.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

from . import compat  # Initialize client before importing Agent  # noqa: F401
from agents import Agent
from .types import FlowSpec

WORKFLOW_SUFFIX = "_flow.py"




def find_workflow_files(root: Path = Path.cwd()) -> List[Path]:
    """
    Find all workflow files in the given directory.
    Looks for *_flow.py files.

    Args:
        root: Root directory to search (defaults to current working directory)

    Returns:
        List of paths to workflow files, sorted alphabetically
    """
    return sorted(root.glob(f"**/*{WORKFLOW_SUFFIX}"))


def find_agent_files(root: Path = Path.cwd()) -> List[Path]:
    """
    Find all agent files in the given directory.

    Looks for *_flow.py files.

    Args:
        root: Root directory to search (defaults to current working directory)

    Returns:
        List of paths to agent flow files, sorted alphabetically
    """
    return sorted(root.glob(f"**/*{WORKFLOW_SUFFIX}"))


def load_workflow(path: Path) -> FlowSpec:
    """
    Load a workflow from a *_flow.py file.

    The file must define one of:
    - FLOW: FlowSpec instance
    - get_flow() -> FlowSpec: Function returning a FlowSpec
    - define_flow() -> dict: Function returning a dict coercible to FlowSpec

    Args:
        path: Path to the *_flow.py file

    Returns:
        FlowSpec instance

    Raises:
        ValueError: If no valid flow definition is found
        ImportError: If the workflow file cannot be loaded
    """
    if not path.is_file():
        raise ImportError(f"Workflow path must be a file, got {path}")

    module_name = f"workflow_module_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load workflow from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Try to find flow definition
    if hasattr(module, "FLOW"):
        flow = module.FLOW
        if isinstance(flow, FlowSpec):
            return flow
        elif isinstance(flow, dict):
            return _coerce_to_flowspec(flow)
        else:
            raise ValueError(f"FLOW must be a FlowSpec or dict, got {type(flow)}")

    elif hasattr(module, "get_flow"):
        result = module.get_flow()
        if isinstance(result, FlowSpec):
            return result
        elif isinstance(result, dict):
            return _coerce_to_flowspec(result)
        else:
            raise ValueError(
                f"get_flow() must return FlowSpec or dict, got {type(result)}"
            )

    elif hasattr(module, "define_flow"):
        result = module.define_flow()
        if isinstance(result, dict):
            return _coerce_to_flowspec(result)
        elif isinstance(result, FlowSpec):
            return result
        else:
            raise ValueError(
                f"define_flow() must return dict or FlowSpec, got {type(result)}"
            )

    raise ValueError(
        f"No flow definition found in {path}. "
        "Expected FLOW, get_flow(), or define_flow()"
    )


def _coerce_to_flowspec(data: Dict[str, Any]) -> FlowSpec:
    """
    Convert a dictionary to a FlowSpec.

    Args:
        data: Dictionary with key: agents

    Returns:
        FlowSpec instance

    Raises:
        ValueError: If required keys are missing or values are invalid
    """
    if "agents" not in data:
        raise ValueError("Flow definition missing 'agents'")

    # Validate agents dict contains Agent instances
    agents: Dict[str, Agent] = {}
    for name, agent in data["agents"].items():
        if isinstance(agent, Agent):
            agents[name] = agent
        else:
            raise ValueError(
                f"Agent '{name}' must be an Agent instance from OpenAI SDK, got {type(agent)}"
            )

    return FlowSpec(agents=agents)


def load_agent(path: Path) -> Agent:
    """
    Load an agent from a *_flow.py file.

    The file must export:
    - Any Agent instance (e.g., researcher_agent, calculator_agent, etc.)
    - The first Agent instance found will be returned

    Args:
        path: Path to the *_flow.py file

    Returns:
        Agent instance (first found if multiple)

    Raises:
        ValueError: If no valid agent definition is found
        ImportError: If the agent file cannot be loaded

    Example:
        # researcher_flow.py
        from agents import Agent

        research_agent = Agent(
            name="researcher",
            model="gpt-4o-mini",
            instructions="Research topics thoroughly"
        )
    """
    if not path.is_file():
        raise ImportError(f"Agent path must be a file, got {path}")

    module_name = f"agent_module_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load agent from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Try AGENT export first
    if hasattr(module, "AGENT"):
        agent = module.AGENT
        if isinstance(agent, Agent):
            return agent
        else:
            raise ValueError(f"AGENT must be Agent instance, got {type(agent)}")

    # Otherwise, look for any Agent exports
    for attr_name in dir(module):
        if not attr_name.startswith("_"):
            attr = getattr(module, attr_name)
            if isinstance(attr, Agent):
                return attr

    raise ValueError(
        f"No agent definition found in {path}. "
        "Expected AGENT or any Agent export"
    )


def load_all_agents(root: Path = Path.cwd()) -> Dict[str, Agent]:
    """
    Load all agent files from a directory into a registry.

    Args:
        root: Root directory to search

    Returns:
        Dictionary mapping agent names to their Agent instances

    Example:
        >>> agents = load_all_agents()
        >>> {'researcher': <Agent>, 'writer': <Agent>}
    """
    agent_files = find_agent_files(root)
    agents: Dict[str, Agent] = {}

    for agent_file in agent_files:
        try:
            agent = load_agent(agent_file)
            agents[agent.name] = agent
        except Exception as e:
            # Silently skip malformed agent files in discovery
            continue

    return agents

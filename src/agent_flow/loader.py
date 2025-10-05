"""
Agent file discovery and loading.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional

from agents import Agent



def find_agent_files(root: Path = Path.cwd()) -> list[Path]:
    """
    Find all agent files in the given directory.

    Looks for: agents/agent_name/index.py

    Args:
        root: Root directory to search (defaults to current working directory)

    Returns:
        List of paths to agent files, sorted alphabetically
    """
    agent_files = []

    # Look for agents/ directory
    agents_dir = root / "agents"
    if agents_dir.exists() and agents_dir.is_dir():
        # Find all subdirectories in agents/
        for agent_folder in agents_dir.iterdir():
            if agent_folder.is_dir():
                index_file = agent_folder / "index.py"
                if index_file.exists():
                    agent_files.append(index_file)

    return sorted(agent_files)




def load_agent(path: Path) -> Agent:
    """
    Load an agent from a Python file.

    The file must export:
    - Any Agent instance (e.g., researcher_agent, calculator_agent, etc.)
    - The first Agent instance found will be returned

    Args:
        path: Path to the agent .py file

    Returns:
        Agent instance (first found if multiple)

    Raises:
        ValueError: If no valid agent definition is found
        ImportError: If the agent file cannot be loaded

    Example:
        # agents/researcher/researcher.py
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


def resolve_agent(ref: str, default_agent_id: Optional[str] = None) -> Agent:
    """
    Load an agent by name from agents/agent_name/index.py.

    Args:
        ref: Agent name (e.g., "calculator")
        default_agent_id: Fallback agent ID if ref is empty

    Returns:
        Agent instance

    Raises:
        ValueError: If agent cannot be found
    """
    agent_id = ref.strip() or default_agent_id
    if not agent_id:
        raise ValueError("No agent reference or default agent_id provided")

    agent_path = Path.cwd() / "agents" / agent_id / "index.py"
    if not agent_path.exists():
        raise ValueError(f"Agent '{agent_id}' not found at {agent_path}")

    return load_agent(agent_path)

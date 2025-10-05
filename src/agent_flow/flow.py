"""
Flow orchestrator for multi-agent workflows.
"""

from typing import Iterator, List, Tuple


from .compat import Message, create_message
from .types import FlowSpec

from dotenv import load_dotenv

load_dotenv()


class Flow:
    """
    Orchestrates multi-agent workflows based on a FlowSpec.
    """

    def __init__(self, spec: FlowSpec) -> None:
        """
        Initialize a flow from a specification.

        Args:
            spec: FlowSpec defining the workflow
        """
        self.spec = spec
        self.messages: List[Message] = []


        self.agents = spec.agents

    def run(self, input_text: str, starting_agent: str | None = None) -> Iterator[Tuple[str, str]]:
        """
        Run the flow with the given user input.

        Args:
            input_text: User input to start the flow
            starting_agent: Name of the agent to start with (optional, uses first agent if not specified)

        Yields:
            Tuple[str, str]: (agent_name, text_chunk) for each streamed chunk

        Example:
            >>> flow = Flow(flow_spec)
            >>> for agent_name, chunk in flow.run("Research AI trends"):
            ...     print(f"[{agent_name}] {chunk}", end="", flush=True)
        """
        # Add user input to message history
        user_message = create_message(role="user", content=input_text)
        self.messages.append(user_message)

        # Determine starting agent
        if starting_agent:
            if starting_agent not in self.agents:
                raise ValueError(f"Starting agent '{starting_agent}' not found in agents")
            current_agent_name = starting_agent
        else:
            # Use first agent in the dict
            if not self.agents:
                return
            current_agent_name = next(iter(self.agents.keys()))

        agent = self.agents[current_agent_name]

        # Collect agent output while streaming
        agent_output_chunks: List[str] = []

        # Stream agent execution
        for chunk in agent.run(self.messages):
            agent_output_chunks.append(chunk)
            yield (current_agent_name, chunk)

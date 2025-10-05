"""
Flow graph types for agent_flow.
These types are specific to workflow orchestration.
"""

from dataclasses import dataclass

from agents import Agent


@dataclass(frozen=True)
class FlowSpec:
    """
    Complete specification of a multi-agent workflow.

    Attributes:
        agents: Mapping of agent names to their SDK Agent instances
        name: Optional name for the workflow
        controls: Optional list of UI controls/parameters
        test_file: Optional path to test file (e.g., "test.py") containing TESTS array

    Example:
        from agents import Agent, Runner
        from agent_flow import FlowSpec

        # Create agents with handoffs configured in SDK
        writer = Agent(name="writer", model="gpt-4")
        researcher = Agent(name="researcher", model="gpt-4", handoffs=[writer])

        # Define tests in test.py with TESTS array
        # TESTS = [{"id": "test_research", "name": "Research Test", ...}]
        
        spec = FlowSpec(
            agents={"researcher": researcher, "writer": writer},
            test_file="test.py"  # UI will load TESTS array from this file
        )

        # Run with any agent as starting point
        result = await Runner.run(spec.agents["researcher"], input="Research AI")
    """
    agents: dict[str, Agent]
    name: str | None = None
    controls: list[dict] | None = None
    test_file: str | None = None

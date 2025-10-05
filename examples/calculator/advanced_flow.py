"""
Advanced calculator flow showing parameterized tests with controls.
"""

from agent_flow import FlowSpec
from agents import Agent, function_tool


@function_tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


# Create calculator agent with dynamic instructions
def create_calculator_agent(precision: int = 2) -> Agent:
    """Create a calculator agent with custom configuration."""

    instructions = f"""You are a helpful calculator assistant.
    Use the available tools to perform calculations accurately.
    Round results to {precision} decimal places."""

    return Agent(
        name="calculator",
        model="gpt-4o-mini",
        instructions=instructions,
        tools=[add, multiply],
    )


# Base agent for default settings
calculator_agent = create_calculator_agent()

# Controls that modify agent behavior
CONTROLS = [
    {
        "name": "precision",
        "type": "number",
        "label": "Decimal Precision",
        "defaultValue": 2,
        "min": 0,
        "max": 10,
        "description": "Number of decimal places to show"
    }
]

# Dynamic flow that uses controls
class CalculatorFlow:
    """Flow with parameterizable behavior."""

    @staticmethod
    async def run(input: str, **controls):
        """Run calculator with custom controls."""
        from agents import Runner

        # Create agent with control values
        precision = controls.get("precision", 2)

        agent = create_calculator_agent(precision)
        result = await Runner.run(agent, input=input)

        return result


# FlowSpec with metadata
FLOW = FlowSpec(
    agents={"calculator": calculator_agent},
    name="advanced_calculator",
    controls=CONTROLS,
)

# Also export for different use cases
__controls__ = CONTROLS
__flow__ = CalculatorFlow

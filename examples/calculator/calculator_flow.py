"""
Calculator agent logic and tools.
"""

from agent_flow import FlowSpec
from agents import Agent, function_tool


# Define calculator tools
@function_tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@function_tool
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        return "Error: Division by zero"
    return a / b


# Create calculator agent
calculator_agent = Agent(
    name="calculator",
    model="gpt-4o-mini",
    instructions="""You are a helpful calculator assistant.
    Use the available tools to perform calculations accurately.
    Always show your work and provide clear results.""",
    tools=[add, multiply, divide],
)

# Define controls for the UI
CONTROLS = [
    {
        "name": "precision",
        "type": "number",
        "label": "Decimal Precision",
        "defaultValue": 2,
        "description": "Number of decimal places to show"
    },
    {
        "name": "show_work",
        "type": "boolean",
        "label": "Show Work",
        "defaultValue": True,
        "description": "Display calculation steps"
    }
]

# Compose workflow
FLOW = FlowSpec(
    agents={
        "calculator": calculator_agent,
    },
    name="calculator",
    controls=CONTROLS,
)



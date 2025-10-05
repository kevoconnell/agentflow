"""
Weather advisor agent.
"""

from agent_flow import FlowSpec
from agents import Agent, function_tool


@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Mock implementation
    return f"The weather in {location} is sunny and 72°F"


# Create weather agent
weather_agent = Agent(
    name="weather_advisor",
    model="gpt-4o-mini",
    instructions="""You are a helpful weather advisor.
    Use the get_weather tool to provide weather information.
    Always be friendly and provide helpful recommendations based on the weather.""",
    tools=[get_weather],
)

# Compose workflow
FLOW = FlowSpec(
    agents={
        "weather": weather_agent,
    }
)

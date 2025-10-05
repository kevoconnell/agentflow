# AgentFlow

Multi-agent workflow orchestration with a visual playground UI.

## What is AgentFlow?

A lightweight Python library for building and testing multi-agent AI workflows with an interactive web interface.

**Key Features:**
- 🎨 **Visual Playground** - Interactive UI for developing and testing agents
- 🔄 **Multi-Agent Orchestration** - Seamless handoffs between specialized agents
- ⚡ **Real-time Streaming** - Live agent responses with tool visibility
- 🎛️ **Dynamic Controls** - Configure agent parameters on the fly

## Quick Start

### 1. Install

```bash
pip install agent-flow
```

### 2. Configure API Keys

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Launch the Playground

```bash
agent-flow dev
```

Opens `http://localhost:4200` with an interactive UI.

## Commands

```bash
# Start the visual playground
agent-flow dev

# Start with custom host/port
agent-flow dev --host=0.0.0.0 --port=8000

# Force rebuild the UI
agent-flow dev --rebuild

# Open without browser
agent-flow dev --no-browser

# List all available agents
agent-flow list
```

## Creating Your First Agent

Create a file named `my_agent.agent.py`:

```python
from agent_flow import FlowSpec
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is sunny, 22°C"

weather_agent = Agent(
    name="weather",
    model="gpt-4o-mini",
    instructions="Use tools to get weather information.",
    tools=[get_weather],
)

FLOW = FlowSpec(agents={"weather": weather_agent})
```

Run `agent-flow dev` and your agent will appear in the playground!

## Adding Controls

Make your agents configurable with UI controls:

```python
from agent_flow import FlowSpec
from agents import Agent

CONTROLS = [
    {
        "name": "temperature",
        "type": "number",
        "label": "Response Temperature",
        "defaultValue": 0.7,
        "min": 0,
        "max": 1,
        "description": "Controls randomness of responses"
    },
    {
        "name": "language",
        "type": "select",
        "label": "Response Language",
        "options": ["English", "Spanish", "French"],
        "defaultValue": "English"
    }
]

my_agent = Agent(
    name="assistant",
    model="gpt-4o-mini",
    instructions="You are a helpful assistant.",
)

FLOW = FlowSpec(
    agents={"assistant": my_agent},
    controls=CONTROLS
)
```

Controls appear in the right sidebar and can be adjusted in real-time!

## Multi-Agent Workflows

Create complex workflows with agent handoffs:

```python
from agent_flow import FlowSpec
from agents import Agent

# Specialized research agent
researcher = Agent(
    name="researcher",
    model="gpt-4o-mini",
    instructions="Research topics and gather information.",
)

# Advisor that researcher can hand off to
advisor = Agent(
    name="advisor",
    model="gpt-4o-mini",
    instructions="Provide expert advice and recommendations.",
)

# Connect agents with handoffs
researcher.handoffs = [advisor]

FLOW = FlowSpec(
    agents={
        "researcher": researcher,
        "advisor": advisor
    }
)
```

## Examples

Check out the `examples/` directory:

- **`calculator/calculator_flow.py`** - Basic calculator with tools
- **`calculator/advanced_flow.py`** - Dynamic controls example
- **`weather.workflow.py`** - Weather agent with tools
- **`researcher.workflow.py`** - Multi-agent workflow

## Project Structure

```
agent_flow/
├── src/agent_flow/        # Core library
│   ├── api.py            # FastAPI server
│   ├── flow.py           # Workflow orchestrator
│   ├── loader.py         # Auto-discovery
│   └── cli.py            # CLI commands
├── ui/                    # React playground
├── examples/              # Example agents
└── .env                   # Your API keys (gitignored)
```

## File Naming Convention

AgentFlow automatically discovers files with these suffixes:
- `.agent.py` - Single agent definitions
- `.workflow.py` - Multi-agent workflows

Both formats work identically - choose based on your preference!

## Requirements

- Python 3.11+
- Node.js 18+ (for UI development)
- OpenAI API key or Anthropic API key

## Dependencies

- `openai-agents>=0.3,<0.4` - OpenAI Agents SDK
- `fastapi` - Web server
- `uvicorn` - ASGI server

## Tips

- **Live Reload**: The playground auto-reloads when you save `.agent.py` files
- **Markdown Support**: Agent responses support full markdown formatting
- **Tool Visibility**: See tool calls and outputs in real-time
- **Theme Toggle**: Switch between light/dark mode with the toggle in the header
- **Agent Editor**: Edit agent instructions directly in the UI (temporary changes)

## License

MIT

# Calculator Agent Example

This example demonstrates how to define tests and controls for agent workflows.

## Running Tests

Tests can be run in two ways:

### 1. Via pytest (for CI/CD and development)
```bash
pytest examples/calculator/test.py -v
```

### 2. Via the UI (interactive testing)
```bash
python -m agent_flow.ui
# Navigate to http://localhost:8000
# Select "calculator" workflow
# Use the test runner panel
```

## Defining Tests and Controls

There are **two approaches** to define tests and controls:

### Option 1: Include in FlowSpec (Recommended)

Pass tests and controls directly to the `FlowSpec` object:

```python
from agent_flow import FlowSpec
from agents import Agent

# Define tests
TESTS = [
    {
        "id": "test_basic_addition",
        "name": "Basic Addition",
        "input": "What is 5 + 3?",
        "expected": "8",
        "expectedTools": ["add"]
    }
]

# Define controls
CONTROLS = [
    {
        "name": "precision",
        "type": "number",
        "label": "Decimal Precision",
        "defaultValue": 2
    }
]

# Create flow with tests and controls
FLOW = FlowSpec(
    agents={"calculator": calculator_agent},
    tests=TESTS,
    controls=CONTROLS
)
```

### Option 2: Module-level exports (Legacy/Fallback)

Export tests and controls as module-level variables:

```python
from agent_flow import FlowSpec

TESTS = [...]  # test definitions
CONTROLS = [...]  # control definitions

FLOW = FlowSpec(agents={"calculator": calculator_agent})

# Export for UI discovery
__tests__ = TESTS
__controls__ = CONTROLS
```

## Test Format

Each test is a dictionary with:

- `id` (str): Unique identifier matching pytest test method name
- `name` (str): Human-readable test name for UI
- `input` (str): Input message to send to agent
- `expected` (str): Expected substring in output
- `expectedTools` (list[str], optional): Tools that should be called

## Control Format

Each control is a dictionary defining a UI parameter:

### Number Control
```python
{
    "name": "precision",
    "type": "number",
    "label": "Decimal Precision",
    "defaultValue": 2,
    "description": "Number of decimal places"
}
```

### Boolean Control
```python
{
    "name": "show_work",
    "type": "boolean",
    "label": "Show Work",
    "defaultValue": True
}
```

### Select Control
```python
{
    "name": "language",
    "type": "select",
    "label": "Response Language",
    "defaultValue": "English",
    "options": ["English", "Spanish", "French"]
}
```

## Using Controls in Agent Logic

Controls can be accessed in your agent's flow logic to modify behavior:

```python
async def run_calculator(input: str, controls: dict):
    precision = controls.get("precision", 2)
    language = controls.get("language", "English")

    result = await Runner.run(
        calculator_agent,
        input=f"[Language: {language}] {input}"
    )

    # Format output with precision
    return format_result(result, precision)
```

## Writing Pytest Tests

Tests in `test.py` should verify:

1. **Tool usage** - Check that expected tools were called
2. **Output content** - Verify the answer is in `result.final_output`

```python
@pytest.mark.asyncio
async def test_division(self, agent):
    result = await Runner.run(agent, input="Divide 100 by 4")

    # Check tool was called
    tool_calls = [item for item in result.new_items if item.type == "tool_call_item"]
    assert any("divide" in str(call) for call in tool_calls)

    # Check output
    assert "25" in result.final_output
```

## Test Discovery

The UI discovers tests through:

1. First checking `FlowSpec.tests` attribute
2. Falling back to module `__tests__` variable
3. Matching test IDs to pytest test method names

This allows tests to be:
- Run interactively in the UI
- Run programmatically via pytest
- Shared between both environments

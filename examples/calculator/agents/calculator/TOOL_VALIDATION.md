# Tool Call Validation Examples

This directory contains examples of how to validate tool calls in agent tests.

## Tool Count Validation Modes

The `tools_expected_json` field supports several count validation modes:

### 1. **Exact Count** (default)
```json
{
  "tools": [{"name": "add"}],
  "count_mode": "exact"
}
```
Expects exactly 1 tool call (the `add` tool).

### 2. **Minimum Count**
```json
{
  "tools": [{"name": "add"}, {"name": "multiply"}],
  "count_mode": "min"
}
```
Expects at least 2 tool calls (any tools, but checking that `add` and `multiply` were called).

### 3. **Maximum Count**
```json
{
  "tools": [{"name": "add"}],
  "count_mode": "max"
}
```
Expects at most 1 tool call.

### 4. **Any Tool**
```json
{
  "tools": [],
  "count_mode": "any"
}
```
Expects at least 1 tool call (any tool).

## Tool Arguments and Results Validation

You can also validate tool arguments and results:

```json
{
  "tools": [
    {
      "name": "divide",
      "arguments": {"a": 10, "b": 2},
      "result": 5.0
    }
  ],
  "count_mode": "exact"
}
```

This validates:
- Exactly 1 tool call
- The tool is named `divide`
- The arguments match `{"a": 10, "b": 2}`
- The result is `5.0`

## Running the Tests

```bash
# Run all tests including tool count validation
agent-flow test

# Run specific test file
agent-flow test agents/calculator/test_tool_count.csv
```

## Test Examples

See `test_tool_count.csv` for complete examples of:
- Simple single tool call validation
- Multi-step calculations with multiple tools
- Minimum/maximum tool count constraints
- Argument and result validation
- Any tool usage validation

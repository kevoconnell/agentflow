# CSV Test Runner for Agent Flow

Automated regression testing for OpenAI Agent SDK agents using CSV test definitions.

## Quick Start

```bash
pip install agent-flow 
# Run all tests
agent-flow test

# Run tests for specific agent
agent-flow test --filter=calculator

# Run with verbose output
agent-flow test --verbose

# Custom report location
agent-flow test --report=my_tests/results.json
```

## CSV Test Format

### Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `test_id` | string | Unique test identifier (e.g., `calc_001`) |
| `messages` | JSON | Array of chat messages: `[{"role":"user","content":"..."}]` |
| `expected_json` | JSON | Expected output specification |
| `match_mode` | string | How to match: `exact`, `contains`, `regex`, `any_of`, `all_of` |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `agent_refs` | JSON | Multi-agent test: `["agent1", "agent2"]` |
| `tools_expected_json` | JSON | Expected tool calls |
| `model` | string | Model override (e.g., `gpt-4o-mini`) |
| `temperature` | float | Sampling temperature (0-1) |
| `seed` | int | Random seed for deterministic runs |
| `max_latency_ms` | int | Fail if response exceeds this latency |
| `max_cost_usd` | float | Fail if cost exceeds this limit |
| `tags` | string | Comma-separated labels |
| `skip` | bool | Skip this test (`true`/`false`) |
| `notes` | string | Human-readable notes |

## Example CSV

```csv
test_id,messages,expected_json,match_mode,max_latency_ms,notes
calc_001,"[{""role"":""user"",""content"":""What is 2 + 3?""}]","{""contains"":[""5""]}",contains,5000,Basic addition
calc_002,"[{""role"":""user"",""content"":""Multiply 4 by 7""}]","{""contains"":[""28""]}",contains,5000,Multiplication test
```

## Match Modes

### `exact`
Response must match exactly:
```json
{"expected": "The answer is 5"}
```

### `contains`
Response must contain all substrings:
```json
{"contains": ["answer", "5", "correct"]}
```

### `regex`
Response must match regex patterns:
```json
{"regex": ["answer.*\\d+", "\\b5\\b"]}
```

### `any_of`
At least one condition must pass:
```json
{
  "any_of": [
    {"mode": "contains", "value": "5"},
    {"mode": "contains", "value": "five"}
  ]
}
```

### `all_of`
All conditions must pass:
```json
{
  "all_of": [
    {"mode": "contains", "value": "answer"},
    {"mode": "regex", "value": "\\d+"}
  ]
}
```

### Tests always pass
- Check `match_mode` is correct
- Verify `expected_json` format matches the mode
- Use `--verbose` to see full responses

## CI/CD Integration

### GitHub Actions

Add your OpenAI API key as a repository secret (`OPENAI_API_KEY`), then tests will run automatically on every push and PR.

The repository includes two workflows:
- **`.github/workflows/test.yml`** - Runs agent tests across Python 3.9-3.12
- **`.github/workflows/lint.yml`** - Lints code with ruff and mypy

Example workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: agent-flow test
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Requirements

- Python 3.9+
- OpenAI API key

## License

Apache 2.0

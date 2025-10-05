REQUIRED_COLUMNS = {"test_id", "messages", "expected_json", "match_mode"}
SEARCH_PATHS = ["."]  # Search from current directory
OPTIONAL_COLUMNS = {
    "agent_refs",
    "tools_expected_json",
    "model",
    "temperature",
    "seed",
    "max_latency_ms",
    "max_cost_usd",
    "tags",
    "skip",
    "notes",
}

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
GRAY = "\033[90m"

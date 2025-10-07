"""CSV test file discovery and validation."""

import csv
from pathlib import Path
from typing import Optional

from .constants import REQUIRED_COLUMNS


def find_csv_files(
    root: Path = Path.cwd(), filter_str: Optional[str] = None
) -> list[tuple[Path, Optional[str]]]:
    """
    Recursively find all CSV test files.

    Supports two patterns:
    1. agents/agent_name/agent_tests.csv -> agent_id = agent_name
    2. tests/cross_agent.csv -> agent_id = None (cross-agent tests)

    Args:
        root: Root directory to search (defaults to current working directory)
        filter_str: Filter pattern to match in filename (e.g., "calculator" matches "calculator.csv")

    Returns:
        list of (csv_path, agent_id) tuples where agent_id is derived from
        folder structure. Only returns valid CSV files.
    """
    results = []

    # Build glob pattern based on filter
    if filter_str:
        glob_pattern = f"**/*{filter_str}*.csv"
    else:
        glob_pattern = "**/*.csv"

    # Look for agent-specific test files in agents/agent_name/**/*.csv
    agents_dir = root / "agents"
    if agents_dir.exists() and agents_dir.is_dir():
        for agent_folder in agents_dir.iterdir():
            if agent_folder.is_dir():
                agent_id = agent_folder.name
                # Find all CSV files in the agent folder and subdirectories
                for csv_file in agent_folder.glob(glob_pattern):
                    is_valid, error_msg = validate_csv(csv_file)
                    if is_valid:
                        results.append((csv_file, agent_id))
                    else:
                        print(f"⚠️  Skipping {csv_file} ({error_msg})")

    # Look for cross-agent tests in tests/*.csv
    tests_dir = root / "tests"
    if tests_dir.exists() and tests_dir.is_dir():
        pattern = f"*{filter_str}*.csv" if filter_str else "*.csv"
        for csv_file in tests_dir.glob(pattern):
            is_valid, error_msg = validate_csv(csv_file)
            if is_valid:
                results.append((csv_file, None))
            else:
                print(f"⚠️  Skipping {csv_file} ({error_msg})")

    return sorted(results)


def validate_csv(csv_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate that CSV has required columns.

    Args:
        csv_path: Path to CSV file to validate

    Returns:
        (is_valid, error_message) tuple. error_message is None if valid.
    """
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            missing = REQUIRED_COLUMNS - headers
            if missing:
                return False, f"missing required columns: {', '.join(missing)}"

            return True, None
    except Exception as e:
        return False, f"failed to read: {e}"

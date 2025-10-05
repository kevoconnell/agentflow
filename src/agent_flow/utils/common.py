"""General utility functions for agent_flow."""

import csv
import json
from pathlib import Path
from typing import Any, Union


def read_file(file_path: Union[str, Path]) -> Any:
    """
    Read a file and return its contents based on file extension.

    Supported formats:
    - .json: Returns parsed JSON object
    - .csv: Returns list of dictionaries (one per row)
    - .txt, others: Returns string content

    Args:
        file_path: Path to the file

    Returns:
        Parsed content based on file type
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    elif suffix == ".csv":
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    else:
        with open(file_path, encoding="utf-8") as f:
            return f.read()


def write_file(file_path: Union[str, Path], content: Any, **kwargs):
    """
    Write content to a file based on file extension.

    Supported formats:
    - .json: Writes JSON with indentation (default indent=2)
    - .csv: Writes CSV from list of dicts (requires fieldnames kwarg)
    - .txt, others: Writes string content

    Args:
        file_path: Path to the file
        content: Content to write
        **kwargs: Additional options (e.g., fieldnames for CSV, indent for JSON)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = file_path.suffix.lower()

    if suffix == ".json":
        indent = kwargs.get("indent", 2)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=indent)

    elif suffix == ".csv":
        fieldnames = kwargs.get("fieldnames")
        if not fieldnames and content:
            # Auto-detect fieldnames from first row
            fieldnames = list(content[0].keys()) if isinstance(content, list) and content else []

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(content)

    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(content))

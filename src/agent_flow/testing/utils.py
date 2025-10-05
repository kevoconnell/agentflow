"""Validation and formatting utilities for test execution."""

import re
from pathlib import Path
from typing import Any, Dict, List

from .constants import GREEN, RED, YELLOW, RESET, GRAY


# ============================================================================
# VALIDATION
# ============================================================================

def validate_tool_data(actual: Any, expected: Any) -> Dict[str, Any]:
    """
    Validate tool arguments or results against expected values.

    Supports:
    - Exact match (primitives)
    - Partial dict match (subset of keys)
    - Regex patterns (dict with {"regex": "pattern"})
    - Contains checks (dict with {"contains": "substring"})

    Args:
        actual: Actual tool data (arguments or result)
        expected: Expected value or match specification

    Returns:
        Dict with {passed: bool, reason: str}
    """
    # If expected is a dict with special matchers
    if isinstance(expected, dict):
        if "regex" in expected:
            pattern = expected["regex"]
            try:
                if re.search(str(pattern), str(actual)):
                    return {"passed": True, "reason": "regex matched"}
                else:
                    return {"passed": False, "reason": "regex no match"}
            except re.error as e:
                return {"passed": False, "reason": f"invalid regex: {e}"}

        if "contains" in expected:
            substring = expected["contains"]
            if str(substring) in str(actual):
                return {"passed": True, "reason": "contains matched"}
            else:
                return {"passed": False, "reason": "substring not found"}

        # Partial dict match - all expected keys must match
        if isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual:
                    return {"passed": False, "reason": f"missing key '{key}'"}
                if actual[key] != value:
                    return {"passed": False, "reason": f"key '{key}' mismatch: expected {value}, got {actual[key]}"}
            return {"passed": True, "reason": "partial match"}

    # Exact match
    if actual == expected:
        return {"passed": True, "reason": "exact match"}
    else:
        return {"passed": False, "reason": f"expected {expected}, got {actual}"}


def evaluate_assertions(response: str, expected: Any, match_mode: str) -> List[Dict[str, Any]]:
    """
    Evaluate assertions based on match_mode.

    Args:
        response: The agent's response text
        expected: Expected value or pattern
        match_mode: How to match (exact, contains, regex, any_of, all_of)

    Returns:
        List of assertion results with {description, passed, reason}
    """
    assertions = []

    if match_mode == "exact":
        passed = response.strip() == str(expected).strip()
        assertions.append({
            "description": f"exact match: {expected}",
            "passed": passed,
            "reason": "matched" if passed else "response differs"
        })

    elif match_mode == "contains":
        # expected can be a string or list of strings
        if isinstance(expected, dict) and "contains" in expected:
            patterns = expected["contains"]
        elif isinstance(expected, list):
            patterns = expected
        else:
            patterns = [expected]

        for pattern in patterns:
            passed = str(pattern) in response
            assertions.append({
                "description": f'contains "{pattern}"',
                "passed": passed,
                "reason": "found" if passed else "not found"
            })

    elif match_mode == "regex":
        # expected can be a pattern or list of patterns
        if isinstance(expected, dict) and "regex" in expected:
            patterns = expected["regex"]
        elif isinstance(expected, list):
            patterns = expected
        else:
            patterns = [expected]

        for pattern in patterns:
            try:
                passed = bool(re.search(str(pattern), response))
                assertions.append({
                    "description": f'regex "{pattern}"',
                    "passed": passed,
                    "reason": "matched" if passed else "no match"
                })
            except re.error as e:
                assertions.append({
                    "description": f'regex "{pattern}"',
                    "passed": False,
                    "reason": f"invalid regex: {e}"
                })

    elif match_mode == "any_of":
        # At least one condition must pass
        if isinstance(expected, dict) and "any_of" in expected:
            sub_conditions = expected["any_of"]
            sub_results = []
            for cond in sub_conditions:
                sub_mode = cond.get("mode", "contains")
                sub_expected = cond.get("value")
                sub_assertions = evaluate_assertions(response, sub_expected, sub_mode)
                sub_results.extend(sub_assertions)

            any_passed = any(a["passed"] for a in sub_results)
            assertions.append({
                "description": "any_of conditions",
                "passed": any_passed,
                "reason": f"{sum(1 for a in sub_results if a['passed'])}/{len(sub_results)} passed"
            })

    elif match_mode == "all_of":
        # All conditions must pass
        if isinstance(expected, dict) and "all_of" in expected:
            sub_conditions = expected["all_of"]
            for cond in sub_conditions:
                sub_mode = cond.get("mode", "contains")
                sub_expected = cond.get("value")
                sub_assertions = evaluate_assertions(response, sub_expected, sub_mode)
                assertions.extend(sub_assertions)

    else:
        assertions.append({
            "description": f"unknown match_mode: {match_mode}",
            "passed": False,
            "reason": "unsupported match mode"
        })

    return assertions


# ============================================================================
# FORMATTING
# ============================================================================



def print_test_result(
    result: Dict[str, Any],
    csv_path: Path,
    row_num: int,
    verbose: bool = False
):
    """
    Print detailed test result to terminal.

    Args:
        result: Test result dictionary
        csv_path: Path to CSV file containing the test
        row_num: Row number in CSV file
        verbose: If True, show full response content instead of excerpt
    """
    status = result["status"]
    test_id = result["test_id"]
    agent_ref = result.get("agent_ref", "unknown")
    latency_ms = result.get("latency_ms", 0)

    # Handle skipped tests
    if status == "SKIPPED":
        print(f"\n⊘ {test_id} :: {agent_ref} [SKIPPED]")
        if result.get("notes"):
            print(f"  {result['notes']}")
        return

    # Status icon and color
    icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
    status_color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW

    print(f"\n{status_color}{icon} {test_id} :: {agent_ref} [{status}]{RESET} {latency_ms}ms")

    # Tool calls - show before response for better readability
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        print(f"\n{GRAY}┌ Tool Calls ┐{RESET}")
        for i, call in enumerate(tool_calls, 1):
            tool_name = call.get("name", "unknown")
            tool_args = call.get("arguments", {})
            tool_result = call.get("result")

            print(f"{GRAY}│{RESET} {i}. {tool_name}")

            # Show arguments
            if tool_args:
                args_str = ", ".join(f"{k}={v}" for k, v in tool_args.items())
                print(f"{GRAY}│{RESET}    args: {args_str}")

            # Show result
            if tool_result is not None:
                result_str = str(tool_result)
                if len(result_str) > 100:
                    result_str = result_str[:100] + "..."
                print(f"{GRAY}│{RESET}    result: {result_str}")
        print(f"{GRAY}└─────────────┘{RESET}")

    # Response - show full or excerpt based on verbose flag
    if verbose:
        # Show full response in verbose mode
        full_response = result.get("response", "")
        if full_response:
            print(f"\n{GRAY}┌ Full Response ┐{RESET}")
            for line in full_response.split("\n"):
                print(f"{GRAY}│{RESET} {line}")
            print(f"{GRAY}└────────────────┘{RESET}")
    else:
        # Show excerpt by default
        excerpt = result.get("response_excerpt", "")
        if excerpt:
            print(f"\n{GRAY}┌ Response excerpt ┐{RESET}")
            print(f"{GRAY}│{RESET} {excerpt}")
            print(f"{GRAY}└──────────────────┘{RESET}")

    # Assertions
    assertions = result.get("assertions", [])
    if assertions:
        print(f"\nAssertions:")
        for assertion in assertions:
            a_icon = "[✓]" if assertion["passed"] else "[✗]"
            a_color = GREEN if assertion["passed"] else RED
            print(f"  {a_color}{a_icon}{RESET} {assertion['description']} — {assertion.get('reason', '')}")

    # Tool validation results
    if result.get("tools_expected") is not None:
        tool_status = result.get("tool_status", "OK")
        tool_color = GREEN if tool_status == "OK" else RED
        print(f"\nTool Validation:")
        print(f"  expected count: {len(result.get('tools_expected', []))}")
        print(f"  actual count  : {len(result.get('tool_calls', []))}")
        print(f"  status        : {tool_color}{tool_status}{RESET}")

    # Notes
    notes = result.get("notes", "")
    if notes:
        print(f"\n{GRAY}Notes: {notes}{RESET}")

    # File location
    print(f"{GRAY}File : {csv_path} (row {row_num}){RESET}")

    # Error details
    if result.get("error"):
        print(f"\n{RED}Error: {result['error']}{RESET}")

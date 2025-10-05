"""Test execution logic."""

import time
from typing import Any, dict

from agents import Agent, Runner

from .utils import evaluate_assertions, validate_tool_data


async def run_test(test_row: dict[str, str], agent: Agent, agent_ref: str) -> dict[str, Any]:
    """
    Execute a single CSV test case and validate results.

    Args:
        test_row: CSV row containing test data (messages, expected_json, etc.)
        agent: Agent instance to test
        agent_ref: Reference string for the agent being tested

    Returns:
        dictionary with test results including:
        - status: "PASS", "FAIL", "ERROR", or "SKIPPED"
        - response: Full response text from agent
        - response_excerpt: Truncated response for display
        - assertions: List of assertion results
        - latency_ms: Execution time in milliseconds
        - tool_calls: List of tool calls made (if tools_expected is set)
        - tool_status: "OK" or "MISMATCH" (if tools_expected is set)
    """
    # Check if test should be skipped
    if test_row.get("skip", "").lower() in ["true", "1", "yes"]:
        return {
            "status": "SKIPPED",
            "test_id": test_row["test_id"],
            "agent_ref": agent_ref,
            "notes": test_row.get("notes", "Skipped"),
        }

    start_time = time.time()

    # Parse messages (list of messages)
    import json

    try:
        messages = json.loads(test_row["messages"])
    except json.JSONDecodeError as e:
        return {
            "status": "ERROR",
            "error": f"Invalid messages JSON: {e}",
            "latency_ms": 0,
            "test_id": test_row["test_id"],
            "agent_ref": agent_ref,
        }

    # Parse expected_json
    try:
        expected = json.loads(test_row["expected_json"])
    except json.JSONDecodeError as e:
        return {
            "status": "ERROR",
            "error": f"Invalid expected_json: {e}",
            "latency_ms": 0,
            "test_id": test_row["test_id"],
            "agent_ref": agent_ref,
        }

    # Parse tools expectations
    tools_expected = None
    tools_count_mode = "exact"  # default comparison mode
    if test_row.get("tools_expected_json"):
        try:
            tools_config = json.loads(test_row["tools_expected_json"])
            # Support both simple list and object with mode
            if isinstance(tools_config, dict) and "count_mode" in tools_config:
                tools_expected = tools_config.get("tools", [])
                tools_count_mode = tools_config.get("count_mode", "exact")
            else:
                tools_expected = tools_config
        except json.JSONDecodeError:
            pass

    # Extract user input from messages
    user_input = ""
    if messages and isinstance(messages, list):
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_input = msg.get("content", "")
                break

    # Run agent
    try:
        result = await Runner.run(agent, input=user_input)
        response_text = result.final_content if hasattr(result, "final_content") else str(result)

        # Collect run metadata
        run_metadata = {
            "new_items_count": len(result.new_items) if hasattr(result, "new_items") else 0,
            "responses_count": len(result.raw_responses) if hasattr(result, "raw_responses") else 0,
        }

        # Extract tool calls if available
        tool_calls = []
        tool_outputs = {}  # Map call_id to output

        if hasattr(result, "new_items"):
            # First pass: collect tool outputs
            for item in result.new_items:
                if hasattr(item, "type") and item.type == "tool_call_output_item":
                    # Get call_id from raw_item (could be dict or object)
                    raw = getattr(item, "raw_item", None)
                    call_id = None

                    if raw is not None:
                        if isinstance(raw, dict):
                            call_id = raw.get("call_id")
                        else:
                            call_id = getattr(raw, "call_id", None)

                    if call_id:
                        # Try to get the output value
                        output_value = getattr(item, "output", None)

                        # If output is a string, try to parse it
                        if isinstance(output_value, str):
                            try:
                                import json

                                # Try to parse as JSON first
                                output_value = json.loads(output_value)
                            except (json.JSONDecodeError, ValueError):
                                # If not JSON, keep as string
                                pass

                        tool_outputs[call_id] = output_value

            # Second pass: collect tool calls and match with outputs
            for item in result.new_items:
                if hasattr(item, "type") and item.type == "tool_call_item":
                    if hasattr(item, "raw_item"):
                        raw = item.raw_item

                        # Extract name - handle different tool call types
                        tool_name = getattr(raw, "name", None)
                        if not tool_name:
                            # Fall back to checking type-specific attributes
                            tool_name = "unknown"

                        # Extract arguments
                        tool_args = {}
                        if hasattr(raw, "arguments"):
                            # Arguments might be a JSON string
                            args_raw = raw.arguments
                            if isinstance(args_raw, str):
                                try:
                                    import json

                                    tool_args = json.loads(args_raw)
                                except json.JSONDecodeError:
                                    tool_args = {"raw": args_raw}
                            else:
                                tool_args = args_raw

                        # Get result from output mapping
                        call_id = getattr(raw, "call_id", None)
                        tool_result = tool_outputs.get(call_id) if call_id else None

                        tool_calls.append(
                            {"name": tool_name, "arguments": tool_args, "result": tool_result}
                        )
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "ERROR",
            "error": f"Agent execution failed: {e}",
            "latency_ms": latency_ms,
            "test_id": test_row["test_id"],
            "agent_ref": agent_ref,
        }

    latency_ms = int((time.time() - start_time) * 1000)

    # Evaluate assertions
    match_mode = test_row["match_mode"]
    assertions = evaluate_assertions(response_text, expected, match_mode)

    tool_status = "OK"
    # Check tools if validation is requested (either tools array or just count_mode)
    if tools_expected is not None:
        expected_count = len(tools_expected)
        actual_count = len(tool_calls)
        if tools_count_mode == "any" and expected_count == 0:
            expected_count = 1

        # Apply count comparison based on mode
        count_match = False
        if tools_count_mode == "exact":
            count_match = actual_count == expected_count
        elif tools_count_mode == "min":
            count_match = actual_count >= expected_count
        elif tools_count_mode == "max":
            count_match = actual_count <= expected_count
        elif tools_count_mode == "any":
            count_match = actual_count > 0
        else:
            count_match = actual_count == expected_count  # fallback to exact

        if not count_match:
            tool_status = "MISMATCH"
            mode_desc = {
                "exact": f"expected {expected_count} tools",
                "min": f"expected at least {expected_count} tools",
                "max": f"expected at most {expected_count} tools",
                "any": "expected at least 1 tool",
            }.get(tools_count_mode, f"expected {expected_count} tools")

            assertions.append(
                {
                    "description": f"{mode_desc}, got {actual_count}",
                    "passed": False,
                    "reason": f"tool count mismatch (mode: {tools_count_mode})",
                }
            )

        # Validate individual tool expectations
        for expected_tool in tools_expected:
            if isinstance(expected_tool, dict):
                # Expected tool has detailed validation
                tool_name = expected_tool.get("name")
                expected_args = expected_tool.get("arguments")
                expected_result = expected_tool.get("result")

                # Find matching tool call(s)
                matching_calls = [tc for tc in tool_calls if tc["name"] == tool_name]

                if not matching_calls:
                    tool_status = "MISMATCH"
                    assertions.append(
                        {
                            "description": f"tool '{tool_name}' was called",
                            "passed": False,
                            "reason": "tool not called",
                        }
                    )
                    continue

                # Validate arguments if specified
                if expected_args is not None:
                    for call in matching_calls:
                        args_match = validate_tool_data(call.get("arguments", {}), expected_args)
                        if args_match["passed"]:
                            assertions.append(
                                {
                                    "description": f"tool '{tool_name}' arguments match",
                                    "passed": True,
                                    "reason": "arguments validated",
                                }
                            )
                            break
                    else:
                        tool_status = "MISMATCH"
                        assertions.append(
                            {
                                "description": f"tool '{tool_name}' arguments match",
                                "passed": False,
                                "reason": f"expected {expected_args}, got {[c.get('arguments') for c in matching_calls]}",
                            }
                        )

                # Validate result if specified
                if expected_result is not None:
                    for call in matching_calls:
                        result_match = validate_tool_data(call.get("result"), expected_result)
                        if result_match["passed"]:
                            assertions.append(
                                {
                                    "description": f"tool '{tool_name}' result matches",
                                    "passed": True,
                                    "reason": "result validated",
                                }
                            )
                            break
                    else:
                        tool_status = "MISMATCH"
                        assertions.append(
                            {
                                "description": f"tool '{tool_name}' result matches",
                                "passed": False,
                                "reason": f"expected {expected_result}, got {[c.get('result') for c in matching_calls]}",
                            }
                        )

    # Check latency limit
    max_latency = test_row.get("max_latency_ms")
    if max_latency:
        try:
            limit = int(max_latency)
            if latency_ms > limit:
                assertions.append(
                    {
                        "description": f"latency <= {limit}ms",
                        "passed": False,
                        "reason": f"exceeded: {latency_ms}ms",
                    }
                )
        except ValueError:
            pass

    # Determine overall status
    passed = all(a["passed"] for a in assertions)
    status = "PASS" if passed else "FAIL"

    # Extract response excerpt with metadata
    excerpt_parts = []
    excerpt_parts.append("RunResult:")
    excerpt_parts.append(f'- Last agent: Agent(name="{agent.name}", ...)')
    excerpt_parts.append(f"- Final output ({type(response_text).__name__}):")

    # Add response preview
    response_preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
    for line in response_preview.split("\n"):
        excerpt_parts.append(f"    {line}")

    excerpt_parts.append(f"- {run_metadata['new_items_count']} new item(s)")
    excerpt_parts.append(f"- {run_metadata['responses_count']} raw response(s)")

    # Add guardrail info (always 0 for now, but shows structure)
    excerpt_parts.append("- 0 input guardrail result(s)")
    excerpt_parts.append("- 0 output guar...")

    excerpt = "\n".join(excerpt_parts)

    return {
        "status": status,
        "response": response_text,
        "response_excerpt": excerpt,
        "assertions": assertions,
        "latency_ms": latency_ms,
        "agent_ref": agent_ref,
        "test_id": test_row["test_id"],
        "notes": test_row.get("notes", ""),
        "tool_calls": tool_calls,  # Always include tool calls
        "tools_expected": tools_expected,
        "tools_count_mode": tools_count_mode,  # Include validation mode
        "tool_status": tool_status if tools_expected is not None else None,
        "run_metadata": run_metadata,
    }

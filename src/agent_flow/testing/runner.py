"""Main test orchestration and reporting."""

import json
import sys
from collections import defaultdict
from datetime import datetime
from typing import Optional

from ..loader import resolve_agent
from ..utils.common import read_file, write_file
from .constants import GRAY, GREEN, RED, RESET, YELLOW
from .discovery import find_csv_files
from .executor import run_test
from .utils import print_test_result


async def run_tests(
    filter_str: Optional[str] = None,
    agent_filter: Optional[list[str]] = None,
    report_path: Optional[str] = None,
    verbose: bool = False,
):
    """
    Main test runner function. Discovers and executes CSV-based regression tests.

    Args:
        filter_str: Filter tests by filename or test_id substring
        agent_filter: list of agent IDs to test (None = all agents)
        report_path: Path to save JSON report (None = no report)
        verbose: If True, show full response content instead of excerpts

    Returns:
        None (exits process with code 0 on success, 1 on failure)
    """

    csv_files = find_csv_files(filter_str=filter_str)

    if not csv_files:
        print("No CSV test files found")
        return

    total_tests = 0
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    all_results = []

    for csv_path, default_agent_id in csv_files:
        print(f"📄 Running tests from: {csv_path}")

        rows = read_file(csv_path)

        for i, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
            test_id = row.get("test_id", f"test_{i}")

            # Check if multi-agent test
            agent_refs_str = row.get("agent_refs", "")
            if agent_refs_str:
                try:
                    agent_refs = json.loads(agent_refs_str)
                except json.JSONDecodeError:
                    agent_refs = [agent_refs_str]
            else:
                agent_refs = [default_agent_id or ""]

            for agent_ref in agent_refs:
                # Apply agent filter
                if agent_filter and agent_ref not in agent_filter:
                    continue

                total_tests += 1

                try:
                    # Load agent
                    agent = resolve_agent(agent_ref, default_agent_id)

                    # Run test
                    result = await run_test(row, agent, agent_ref)

                    # Add CSV file path to result
                    result["csv_file"] = str(csv_path)

                    # Update stats
                    if result["status"] == "PASS":
                        passed += 1
                    elif result["status"] == "FAIL":
                        failed += 1
                    else:
                        errors += 1

                    # Print result
                    print_test_result(result, csv_path, i, verbose)

                    # Store for report
                    all_results.append(result)

                except Exception as e:
                    errors += 1
                    print(f"\n✗ {test_id} :: {agent_ref} [ERROR]")
                    print(f"  Error loading/running: {e}")

                    all_results.append(
                        {
                            "test_id": test_id,
                            "agent_ref": agent_ref,
                            "status": "ERROR",
                            "error": str(e),
                            "latency_ms": 0,
                            "csv_file": str(csv_path),
                        }
                    )

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Total:   {total_tests}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"⚠ Errors: {errors}")
    print(f"⊘ Skipped: {skipped}")
    print("=" * 60)

    # Detailed breakdown by file
    results_by_file = defaultdict(lambda: {"passed": [], "failed": [], "errors": []})

    for result in all_results:
        status = result.get("status", "ERROR")
        file_key = result.get("csv_file", "unknown")

        if status == "PASS":
            results_by_file[file_key]["passed"].append(result)
        elif status == "FAIL":
            results_by_file[file_key]["failed"].append(result)
        elif status == "ERROR":
            results_by_file[file_key]["errors"].append(result)

    if results_by_file:
        print("\n" + "=" * 60)
        print("📋 Detailed Results by File")
        print("=" * 60)

        for csv_file in sorted(results_by_file.keys()):
            file_results = results_by_file[csv_file]
            passed_tests = file_results["passed"]
            failed_tests = file_results["failed"]
            error_tests = file_results["errors"]

            total_for_file = len(passed_tests) + len(failed_tests) + len(error_tests)

            print(f"\n{GRAY}File: {csv_file}{RESET}")
            print(
                f"  Total: {total_for_file} | Passed: {len(passed_tests)} | Failed: {len(failed_tests)} | Errors: {len(error_tests)}"
            )

            if passed_tests:
                print(f"\n  {GREEN}✓ Passed Tests:{RESET}")
                for test in passed_tests:
                    test_id = test.get("test_id", "unknown")
                    latency = test.get("latency_ms", 0)
                    notes = test.get("notes", "")
                    assertions = test.get("assertions", [])
                    num_assertions = len([a for a in assertions if a.get("passed")])

                    note_str = f" - {notes}" if notes else ""
                    print(f"    • {test_id} ({latency}ms, {num_assertions} assertions){note_str}")

            if failed_tests:
                print(f"\n  {RED}✗ Failed Tests:{RESET}")
                for test in failed_tests:
                    test_id = test.get("test_id", "unknown")
                    latency = test.get("latency_ms", 0)
                    notes = test.get("notes", "")
                    assertions = test.get("assertions", [])
                    failed_assertions = [a for a in assertions if not a.get("passed")]

                    note_str = f" - {notes}" if notes else ""
                    print(f"    • {test_id} ({latency}ms){note_str}")

                    if failed_assertions:
                        for assertion in failed_assertions:
                            desc = assertion.get("description", "unknown")
                            reason = assertion.get("reason", "")
                            print(f"      ↳ {desc}: {reason}")

            # Show error tests
            if error_tests:
                print(f"\n  {YELLOW}⚠ Error Tests:{RESET}")
                for test in error_tests:
                    test_id = test.get("test_id", "unknown")
                    error_msg = test.get("error", "Unknown error")
                    print(f"    • {test_id}")
                    print(f"      ↳ {error_msg}")

        print("\n" + "=" * 60)

    # Generate JSON report
    if report_path:
        report = {
            "run_id": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
            },
            "results": all_results,
        }

        write_file(report_path, report)

        print(f"\n📝 Report saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if failed == 0 and errors == 0 else 1)

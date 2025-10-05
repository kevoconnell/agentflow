"""
CLI for agent_flow CSV test runner.
"""

import argparse
import asyncio
import csv
import sys

from .loader import load_all_agents
from .testing import find_csv_files, run_tests


def main() -> None:
    """
    Main CLI entry point for agent_flow.

    Supports:
        agent-flow test [options]   - Run CSV regression tests
        agent-flow list             - List available agents
    """
    # Create main parser
    parser = argparse.ArgumentParser(
        prog="agent-flow",
        description="Agent Flow - CSV-based regression testing for OpenAI Agent SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Run CSV regression tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  agent-flow test

  # Run tests for specific agent
  agent-flow test --agents calculator

  # Run tests matching pattern
  agent-flow test --filter "basic_math"

  # Run with custom report path
  agent-flow test --report ./my-report.json

  # Show full verbose output
  agent-flow test --verbose

  # List available test files without running
  agent-flow test --list

CSV Column Reference:
  Required: test_id, messages, expected_json, match_mode
  Optional: agent_refs, tools_expected_json, model, temperature, seed,
            max_latency_ms, max_cost_usd, tags, skip, notes

Tool Validation Modes (count_mode):
  exact - Tool count must equal expected (default)
  min   - Tool count must be >= expected
  max   - Tool count must be <= expected
  any   - At least one tool must be called
        """
    )

    # Test selection arguments
    test_parser.add_argument(
        "--filter",
        metavar="PATTERN",
        help="Filter tests by filename or test_id substring"
    )
    test_parser.add_argument(
        "--agents",
        metavar="AGENT1,AGENT2",
        help="Comma-separated list of agent IDs to test"
    )
    test_parser.add_argument(
        "--tags",
        metavar="TAG1,TAG2",
        help="Run only tests with specific tags (comma-separated)"
    )

    # Output control arguments
    test_parser.add_argument(
        "--report",
        metavar="PATH",
        default="reports/test_report.json",
        help="Path to JSON report output (default: reports/test_report.json)"
    )
    test_parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating JSON report"
    )
    test_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show full responses for all tests"
    )
    test_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output, only show summary"
    )
    test_parser.add_argument(
        "--list",
        action="store_true",
        help="List all test files without running them"
    )

    # Tool validation arguments
    test_parser.add_argument(
        "--validate-tools",
        action="store_true",
        default=True,
        help="Enable tool call validation (default: enabled)"
    )
    test_parser.add_argument(
        "--no-validate-tools",
        action="store_true",
        help="Disable tool call validation"
    )

    # Performance arguments
    test_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first test failure"
    )
    test_parser.add_argument(
        "--timeout",
        type=int,
        metavar="SECONDS",
        help="Global timeout for each test in seconds"
    )

    # List command
    subparsers.add_parser(
        "list",
        help="List available agents"
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "test":
        run_csv_tests(args)
    elif args.command == "list":
        list_resources()
    else:
        parser.print_help()
        sys.exit(1)


def run_csv_tests(args: argparse.Namespace) -> None:
    """
    Run CSV-based regression tests.

    Args:
        args: Parsed command-line arguments
    """
    # List mode
    if args.list:
        csv_files = find_csv_files()
        if not csv_files:
            print("No CSV test files found")
            return

        print("📋 Available test files:\n")
        for csv_path, agent_id in csv_files:
            agent_str = f"(agent: {agent_id})" if agent_id else "(cross-agent)"
            print(f"  • {csv_path} {agent_str}")

            # Count tests
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    test_count = sum(1 for _ in reader)
                print(f"    └─ {test_count} test(s)")
            except Exception:
                pass

        print(f"\nTotal: {len(csv_files)} test file(s)")
        return

    # Parse filters
    agent_filter = None
    if args.agents:
        agent_filter = [a.strip() for a in args.agents.split(",")]

    # Determine report path
    report_path = None if args.no_report else args.report

    # Run async
    asyncio.run(run_tests(
        filter_str=args.filter,
        agent_filter=agent_filter,
        report_path=report_path,
        verbose=args.verbose
    ))


def list_resources() -> None:
    """List all available agents."""
    print("📦 Available Agents\n")

    # Load all agents
    agents = load_all_agents()

    if agents:
        print("🤖 Agents:")
        for name, agent in sorted(agents.items()):
            model = getattr(agent, "model", "unknown")
            print(f"  - {name} (model: {model})")
        print()
    else:
        print("No agents found in current directory.")


if __name__ == "__main__":
    main()

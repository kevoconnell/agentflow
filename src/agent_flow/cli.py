"""
CLI for agent_flow with dev mode and hot-reload.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from .flow import Flow
from .loader import (
    WORKFLOW_SUFFIX,
    find_workflow_files,
    load_all_agents,
    load_workflow,
)


def main() -> None:
    """
    Main CLI entry point.

    Usage:
        agent-flow dev
        agent-flow list
        agent-flow test [test_file.test.py]
    """
    args = sys.argv[1:]

    if not args:
        print("Usage: agent-flow <command> [options]")
        print("\nCommands:")
        print("  dev              Start web UI playground (default)")
        print("                   Options: --host=HOST --port=PORT --rebuild --no-browser")
        print("  test             Run tests with pytest")
        print("  list             List agents and workflows")
        sys.exit(1)

    command = args[0]
    if command == "dev":
        run_ui(args[1:])
    elif command == "test":
        run_tests(args[1:])
    elif command == "list":
        list_resources()
    else:
        print(f"Unknown command: {command}")
        print("Run 'agent-flow' for usage")
        sys.exit(1)

def run_dev_mode(args: list[str]) -> None:
    """
    Run dev mode with a workflow.

    Args:
        args: Command-line arguments after 'dev'
    """

    # Parse workflow file argument
    workflow_path: Optional[Path] = None
    if len(args) > 0:
        workflow_path = Path(args[0])
        if not workflow_path.exists():
            print(f"Error: Workflow file not found: {workflow_path}")
            sys.exit(1)
    else:
        # Auto-discover workflow file
        workflow_files = find_workflow_files()
        if not workflow_files:
            print(f"Error: No *{WORKFLOW_SUFFIX} files found in current directory")
            sys.exit(1)


        preferred = [f for f in workflow_files if f.name == f"app{WORKFLOW_SUFFIX}"]
        workflow_path = preferred[0] if preferred else workflow_files[0]

        if len(workflow_files) > 1:
            print(f"Multiple workflow files found. Using: {workflow_path}")
            print("Available workflows:")
            for wf in workflow_files:
                marker = " (active)" if wf == workflow_path else ""
                print(f"  - {wf}{marker}")
            print("\nTo switch workflows, run: agent-flow dev <workflow_file>\n")

    # Show available agents
    agents = load_all_agents()
    if agents:
        print(f"📦 Loaded {len(agents)} agent(s): {', '.join(agents.keys())}\n")

    # Run dev loop
    dev_loop(workflow_path)


def run_ui(args: list[str]) -> None:
    """
    Start the web UI playground.

    Args:
        args: Command-line arguments after 'dev'
    """
    from .api import start_ui

    # Parse optional host, port, rebuild, and browser flag
    host = "127.0.0.1"
    port = 4200
    open_browser = True
    rebuild = False

    for arg in args:
        if arg.startswith("--host="):
            host = arg.split("=")[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--no-browser":
            open_browser = False
        elif arg == "--rebuild":
            rebuild = True

    # Show what workflows were found
    workflow_files = find_workflow_files()
    if workflow_files:
        print(f"📦 Found {len(workflow_files)} workflow(s):")
        for wf in workflow_files:
            print(f"  - {wf.name}")
        print()

    start_ui(host=host, port=port, rebuild=rebuild, open_browser=open_browser)


def dev_loop(workflow_path: Path) -> None:
    """
    Development loop with hot-reload.

    Args:
        workflow_path: Path to the workflow file to run
    """
    print(f"Running workflow: {workflow_path}")
    print(f"Watching for changes... (Ctrl+C to exit)\n")

    current_flow: Optional[Flow] = None
    last_mtime = 0.0

    try:
        while True:
            # Check if file has been modified
            current_mtime = workflow_path.stat().st_mtime

            if current_mtime > last_mtime:
                try:
                    # Reload workflow
                    spec = load_workflow(workflow_path)
                    current_flow = Flow(spec)
                    last_mtime = current_mtime

                    if last_mtime > 0:  # Not the first load
                        print(f"\n🔄 Workflow reloaded from {workflow_path}\n")

                except Exception as e:
                    print(f"\n❌ Error loading workflow: {e}\n")
                    time.sleep(1)
                    continue

            # Only prompt if we have a valid flow
            if current_flow is None:
                time.sleep(0.5)
                continue

            # Prompt for input
            try:
                user_input = input("Enter prompt> ").strip()
            except EOFError:
                print("\nExiting...")
                break

            if not user_input:
                continue

            # Run the flow
            print()  # Blank line before output
            try:
                current_agent = None
                for agent_name, chunk in current_flow.run(user_input):
                    # Print agent name when switching agents
                    if agent_name != current_agent:
                        if current_agent is not None:
                            print()  # Blank line between agents
                        print(f"[{agent_name}]", end=" ", flush=True)
                        current_agent = agent_name

                    # Print chunk
                    sys.stdout.write(chunk)
                    sys.stdout.flush()

                print("\n")  # Blank line after output

            except KeyboardInterrupt:
                print("\n\nInterrupted. Ready for next prompt.\n")
                continue
            except Exception as e:
                print(f"\n❌ Error running flow: {e}\n")
                continue

    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


def run_tests(args: list[str]) -> None:
    """
    Run tests with pytest.

    Args:
        args: Command-line arguments after 'test'
    """
    import subprocess
    from pathlib import Path

    # Find test files
    test_files = list(Path.cwd().rglob("*.test.py"))

    if not test_files:
        print("No test files found (*.test.py)")
        sys.exit(1)

    print(f"📝 Found {len(test_files)} test file(s):")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()

    # Determine which tests to run
    if args:
        # Run specific test file
        test_path = Path(args[0])
        if not test_path.exists():
            print(f"Error: Test file not found: {test_path}")
            sys.exit(1)
        cmd = ["pytest", str(test_path), "-v"]
    else:
        # Run all tests
        cmd = ["pytest"] + [str(f) for f in test_files] + ["-v"]

    print("🧪 Running tests...\n")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def list_resources() -> None:
    """List all available agents and workflows."""
    from pathlib import Path

    print("📦 Available Resources\n")

    # Find agent files
    agent_files = list(Path.cwd().rglob("*.agent.py"))
    if agent_files:
        print("🤖 Agents:")
        for agent_file in sorted(agent_files):
            print(f"  - {agent_file.stem.replace('.agent', '')} ({agent_file})")
        print()

    # Find workflow files
    workflow_files = find_workflow_files()
    if workflow_files:
        print("🔄 Workflows:")
        for wf in sorted(workflow_files):
            print(f"  - {wf.name}")
        print()

    # Find test files
    test_files = list(Path.cwd().rglob("*.test.py"))
    if test_files:
        print("🧪 Tests:")
        for test_file in sorted(test_files):
            print(f"  - {test_file.stem.replace('.test', '')} ({test_file})")
        print()

    if not agent_files and not workflow_files and not test_files:
        print("No resources found in current directory.")


if __name__ == "__main__":
    main()

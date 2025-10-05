"""
Utility functions for building the React UI.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_ui_dir() -> Path:
    """Get the UI source directory."""
    # From src/agent_flow/build_ui.py -> ../../ui
    return Path(__file__).parent.parent.parent / "ui"


def get_static_dir() -> Path:
    """Get the static build output directory."""
    return Path(__file__).parent / "static"


def check_npm_installed() -> bool:
    """Check if npm is installed."""
    try:
        subprocess.run(
            ["npm", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_ui_built() -> bool:
    """Check if the UI has been built."""
    static_dir = get_static_dir()
    index_path = static_dir / "index.html"
    return index_path.exists()


def needs_npm_install() -> bool:
    """Check if npm install needs to be run."""
    ui_dir = get_ui_dir()
    node_modules = ui_dir / "node_modules"
    package_json = ui_dir / "package.json"

    if not package_json.exists():
        return False  # No package.json, nothing to install

    if not node_modules.exists():
        return True  # node_modules doesn't exist

    # Check if package.json is newer than node_modules
    return package_json.stat().st_mtime > node_modules.stat().st_mtime


def needs_rebuild() -> bool:
    """Check if the UI needs to be rebuilt."""
    if not is_ui_built():
        return True

    ui_dir = get_ui_dir()
    static_dir = get_static_dir()

    # Get the most recent build time
    index_path = static_dir / "index.html"
    build_time = index_path.stat().st_mtime

    # Check if any source file is newer than the build
    src_dir = ui_dir / "src"
    if not src_dir.exists():
        return False

    for src_file in src_dir.rglob("*"):
        if src_file.is_file() and src_file.stat().st_mtime > build_time:
            return True

    # Check if package.json or vite.config.ts changed
    for config_file in ["package.json", "vite.config.ts", "index.html"]:
        config_path = ui_dir / config_file
        if config_path.exists() and config_path.stat().st_mtime > build_time:
            return True

    return False


def run_npm_install() -> bool:
    """Run npm install in the UI directory."""
    ui_dir = get_ui_dir()

    if not ui_dir.exists():
        print(f"⚠️  UI directory not found at {ui_dir}", file=sys.stderr)
        return False

    print(f"📦 Installing npm dependencies in {ui_dir}...")

    try:
        subprocess.run(
            ["npm", "install"],
            cwd=ui_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ npm install completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ npm install failed:", file=sys.stderr)
        print(f"Exit code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def build_ui() -> bool:
    """Build the React UI."""
    ui_dir = get_ui_dir()
    static_dir = get_static_dir()

    if not ui_dir.exists():
        print(f"⚠️  UI directory not found at {ui_dir}", file=sys.stderr)
        return False

    print(f"🔨 Building React UI from {ui_dir}...")

    try:
        # Build the UI
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=ui_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Copy dist to static directory
        import shutil
        dist_dir = ui_dir / "dist"
        if dist_dir.exists():
            # Remove old static files
            if static_dir.exists():
                shutil.rmtree(static_dir)
            # Copy new build
            shutil.copytree(dist_dir, static_dir)
            print(f"✅ React UI built successfully to {static_dir}")
            return True
        else:
            print(f"❌ Build output not found at {dist_dir}", file=sys.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed:", file=sys.stderr)
        print(f"Exit code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def ensure_ui_built(force: bool = False) -> Optional[str]:
    """
    Ensure the UI is built and ready to serve.

    Args:
        force: Force a rebuild even if not needed

    Returns:
        Error message if build failed, None if successful
    """
    # Check if npm is installed
    if not check_npm_installed():
        return (
            "npm is not installed. Please install Node.js and npm to use the UI.\n"
            "Visit https://nodejs.org/ for installation instructions."
        )

    ui_dir = get_ui_dir()
    if not ui_dir.exists():
        return f"UI source directory not found at {ui_dir}"

    # Run npm install if needed
    if needs_npm_install():
        print("📦 npm dependencies need to be installed...")
        if not run_npm_install():
            return "Failed to install npm dependencies"

    # Build if needed or forced
    if force or needs_rebuild():
        if needs_rebuild():
            print("🔄 React source files have changed, rebuilding...")
        if not build_ui():
            return "Failed to build React UI"
    else:
        print("✨ UI is already up to date")

    return None

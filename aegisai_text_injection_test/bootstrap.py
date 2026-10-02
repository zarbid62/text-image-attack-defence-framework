"""Check local prerequisites, request permission to install packages, then run a command."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MIN_PYTHON = (3, 10)
MIN_NODE = 18


def executable_version(executable, args):
    try:
        result = subprocess.run(
            [executable, *args], capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    text = (result.stdout or result.stderr).strip()
    try:
        return tuple(int(part) for part in text.lstrip("v").split(".")[:3])
    except ValueError:
        return None


def ask_permission(message):
    if not sys.stdin.isatty():
        print(f"{message} Use an interactive terminal or install it manually.", file=sys.stderr)
        return False
    answer = input(f"{message} [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def ensure_node_dependencies():
    if not (ROOT / "package.json").exists() or (ROOT / "node_modules").exists():
        return True
    if not shutil.which("npm"):
        print("npm is required but was not found on PATH.", file=sys.stderr)
        return False
    if not ask_permission("Node packages are missing. Run 'npm ci' now?"):
        return False
    return subprocess.run(["npm", "ci"], cwd=ROOT, check=False).returncode == 0


def check_prerequisites(command):
    if sys.version_info < MIN_PYTHON:
        print(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required; "
            f"found {sys.version.split()[0]}.",
            file=sys.stderr,
        )
        return False

    executable = Path(command[0]).name.lower() if command else ""
    if executable in {"node", "node.exe"}:
        node_version = executable_version("node", ["--version"])
        if node_version is None or node_version[0] < MIN_NODE:
            found = ".".join(map(str, node_version)) if node_version else "not installed"
            print(f"Node.js {MIN_NODE} or newer is required; found {found}.", file=sys.stderr)
            return False
        if not ensure_node_dependencies():
            return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify project prerequisites, then run a project command."
    )
    parser.add_argument("--check", action="store_true", help="Only verify prerequisites")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after '--'")
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]

    if not check_prerequisites(command):
        return 1
    if args.check or not command:
        print("Prerequisites are available.")
        return 0
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
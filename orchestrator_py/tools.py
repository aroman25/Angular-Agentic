from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = (REPO_ROOT / "generated-app").resolve()


def reject_unsafe_agent_command(command: str) -> str | None:
    normalized = command.strip().lower()
    banned_patterns: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"\bnpm(\.cmd)?\s+(run\s+)?start\b"),
            "Do not run the dev server from the agent tool; it is long-running and can lock generated-app files.",
        ),
        (
            re.compile(r"\bng\s+serve\b"),
            "Do not run 'ng serve' from the agent tool; use build/test commands only.",
        ),
        (
            re.compile(r"\btsx\b.*\borchestrator\b"),
            "Do not invoke the orchestrator recursively from inside the generated app.",
        ),
    ]

    for pattern, reason in banned_patterns:
        if pattern.search(normalized):
            return f"Command rejected: {reason} Command: {command}"

    if "--watch" in normalized and "--watch=false" not in normalized:
        return (
            "Command rejected: Do not run watch-mode commands from the agent tool; "
            "use one-shot build/test commands (e.g., '--watch=false'). "
            f"Command: {command}"
        )

    return None


def write_code(file_path: str, content: str, *, target_dir: Path = TARGET_DIR) -> str:
    full_path = (target_dir / file_path).resolve()
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return f"Successfully wrote to {file_path}"


def read_file(file_path: str, *, target_dir: Path = TARGET_DIR) -> str:
    full_path = (target_dir / file_path).resolve()
    if not full_path.exists():
        return f"Error: File {file_path} does not exist."
    return full_path.read_text(encoding="utf-8")


def run_command(command: str, *, target_dir: Path = TARGET_DIR) -> str:
    command_rejection = reject_unsafe_agent_command(command)
    if command_rejection:
        return command_rejection

    try:
        output = subprocess.run(
            command,
            cwd=target_dir,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        return f"Command succeeded:\n{output.stdout}"
    except subprocess.CalledProcessError as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return f"Command failed:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"


def build_langchain_tools(*, target_dir: Path = TARGET_DIR) -> list[object]:
    """Create LangChain tool objects lazily so self-tests can run without LangChain installed."""
    try:
        from langchain_core.tools import tool
    except Exception as exc:  # pragma: no cover - exercised only when full runtime is used
        raise RuntimeError(
            "LangChain dependencies are required for full orchestrator execution. "
            "Install Python deps for orchestrator_py first."
        ) from exc

    @tool("write_code")
    def write_code_tool(filePath: str, content: str) -> str:  # noqa: N803 - keep parity with Node tool schema
        """Write code to a file in the generated Angular app."""
        return write_code(filePath, content, target_dir=target_dir)

    @tool("read_file")
    def read_file_tool(filePath: str) -> str:  # noqa: N803 - keep parity with Node tool schema
        """Read the contents of a file in the generated Angular app."""
        return read_file(filePath, target_dir=target_dir)

    @tool("run_command")
    def run_command_tool(command: str) -> str:
        """Run a shell command in the generated app directory (e.g., npm run build, npm run test -- --watch=false)."""
        return run_command(command, target_dir=target_dir)

    return [write_code_tool, read_file_tool, run_command_tool]


__all__ = [
    "TARGET_DIR",
    "build_langchain_tools",
    "read_file",
    "reject_unsafe_agent_command",
    "run_command",
    "write_code",
]


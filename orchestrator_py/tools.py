from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = (REPO_ROOT / "generated-app").resolve()
MAX_READ_FILE_CHARS = int(os.getenv("ORCH_TOOL_READ_FILE_MAX_CHARS", "18000"))
MAX_COMMAND_SUCCESS_CHARS = int(os.getenv("ORCH_TOOL_COMMAND_SUCCESS_MAX_CHARS", "5000"))
MAX_COMMAND_FAILURE_CHARS = int(os.getenv("ORCH_TOOL_COMMAND_FAILURE_MAX_CHARS", "9000"))
MAX_COMMAND_IMPORTANT_LINES = int(os.getenv("ORCH_TOOL_COMMAND_IMPORTANT_LINES", "120"))


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


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    marker = "\n...[truncated]...\n"
    tail_budget = min(1200, max_chars // 3)
    head_budget = max_chars - len(marker) - tail_budget
    if head_budget < 200:
        return text[: max(0, max_chars - len(marker))] + marker.strip()
    return f"{text[:head_budget]}{marker}{text[-tail_budget:]}"


def _is_high_volume_command(command: str) -> bool:
    normalized = command.lower()
    return "npm" in normalized and ("run build" in normalized or "run test" in normalized or "ng build" in normalized)


def _extract_important_lines(stdout: str, stderr: str) -> str:
    important_line_pattern = re.compile(
        r"\b(error|failed|warning|exception|traceback|ng\d{4,}|ts\d{4,}|npm err|vitest|x\s+\d+)\b",
        flags=re.IGNORECASE,
    )
    lines: list[str] = []
    seen: set[str] = set()
    for line in f"{stdout}\n{stderr}".splitlines():
        candidate = line.strip()
        if not candidate or candidate in seen:
            continue
        if important_line_pattern.search(candidate):
            lines.append(candidate)
            seen.add(candidate)
        if len(lines) >= MAX_COMMAND_IMPORTANT_LINES:
            break
    return "\n".join(lines)


def _summarize_success_output(command: str, stdout: str) -> str:
    if not stdout.strip():
        return "No stdout output."
    if not _is_high_volume_command(command):
        return _truncate_text(stdout, MAX_COMMAND_SUCCESS_CHARS)

    tail_lines = stdout.splitlines()[-80:]
    tail = "\n".join(tail_lines)
    return _truncate_text(tail, MAX_COMMAND_SUCCESS_CHARS)


def write_code(file_path: str, content: str, *, target_dir: Path = TARGET_DIR) -> str:
    full_path = (target_dir / file_path).resolve()
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return f"Successfully wrote to {file_path}"


def read_file(file_path: str, *, target_dir: Path = TARGET_DIR) -> str:
    full_path = (target_dir / file_path).resolve()
    if not full_path.exists():
        return f"Error: File {file_path} does not exist."
    return _truncate_text(full_path.read_text(encoding="utf-8"), MAX_READ_FILE_CHARS)


def run_command(command: str, *, target_dir: Path = TARGET_DIR) -> str:
    command_rejection = reject_unsafe_agent_command(command)
    if command_rejection:
        return command_rejection

    result = subprocess.run(
        command,
        cwd=target_dir,
        shell=True,
        check=False,
        text=True,
        capture_output=True,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if result.returncode == 0:
        return f"Command succeeded:\n{_summarize_success_output(command, stdout)}"

    important_lines = _extract_important_lines(stdout, stderr)
    details: list[str] = [f"Command failed (exit code {result.returncode})."]
    if important_lines:
        details.append(f"Important lines:\n{important_lines}")
    if stdout.strip():
        details.append(f"STDOUT (truncated):\n{_truncate_text(stdout, MAX_COMMAND_FAILURE_CHARS)}")
    if stderr.strip():
        details.append(f"STDERR (truncated):\n{_truncate_text(stderr, MAX_COMMAND_FAILURE_CHARS)}")
    return "\n\n".join(details)


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


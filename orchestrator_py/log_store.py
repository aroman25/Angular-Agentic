from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

for _candidate in [
    (Path(__file__).resolve().parent / ".env").resolve(),
    (Path(__file__).resolve().parents[1] / "orchestrator" / ".env").resolve(),
]:
    try:
        if _candidate.exists():
            from dotenv import load_dotenv as _load_dotenv

            _load_dotenv(_candidate)
            break
    except Exception:
        break

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_ROOT = (REPO_ROOT / "orchestrator_py" / "logs").resolve()

LOGS_ENABLED = os.getenv("ORCH_LOGS_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
LOGS_MAX_RUNS = int(os.getenv("ORCH_LOGS_MAX_RUNS", "20"))
LOGS_MAX_AGE_DAYS = int(os.getenv("ORCH_LOGS_MAX_AGE_DAYS", "14"))
LOGS_TAIL_LINES_DEFAULT = int(os.getenv("ORCH_LOGS_TAIL_LINES_DEFAULT", "120"))


class LogStoreError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _sanitize_log_slug(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\-_.]+", "-", text.strip())
    normalized = normalized.strip("-._")
    return normalized[:80] or "command"


def start_run() -> str:
    run_id = _utc_now().strftime("%Y%m%dT%H%M%S")
    if not LOGS_ENABLED:
        return run_id
    run_dir = LOG_ROOT / run_id / "commands"
    run_dir.mkdir(parents=True, exist_ok=True)
    (LOG_ROOT / "latest-run.txt").write_text(f"{run_id}\n", encoding="utf-8")
    _prune_runs()
    return run_id


def _parse_run_id_datetime(run_id: str) -> datetime | None:
    try:
        return datetime.strptime(run_id, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _prune_runs() -> None:
    if not LOG_ROOT.exists():
        return
    run_dirs = [entry for entry in LOG_ROOT.iterdir() if entry.is_dir()]
    run_dirs.sort(key=lambda path: path.name, reverse=True)

    cutoff = _utc_now() - timedelta(days=max(1, LOGS_MAX_AGE_DAYS))
    retained: list[Path] = []
    for run_dir in run_dirs:
        parsed = _parse_run_id_datetime(run_dir.name)
        if parsed is None:
            continue
        if parsed >= cutoff:
            retained.append(run_dir)

    keep_set = {path.name for path in retained[: max(1, LOGS_MAX_RUNS)]}
    for run_dir in run_dirs:
        if run_dir.name in keep_set:
            continue
        try:
            for child in run_dir.rglob("*"):
                if child.is_file():
                    child.unlink(missing_ok=True)
            for child in sorted(run_dir.rglob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            run_dir.rmdir()
        except Exception:
            # best effort pruning
            pass


def _index_path(run_id: str) -> Path:
    return LOG_ROOT / run_id / "commands" / "index.json"


def _load_index(run_id: str) -> list[dict[str, Any]]:
    index_path = _index_path(run_id)
    if not index_path.exists():
        return []
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def _write_index(run_id: str, records: list[dict[str, Any]]) -> None:
    index_path = _index_path(run_id)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def append_command_log(
    *,
    run_id: str,
    command: str,
    cwd: Path,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> dict[str, str]:
    if not LOGS_ENABLED:
        return {"logId": "", "path": ""}
    log_id = _utc_now().strftime("%H%M%S_%f")
    slug = _sanitize_log_slug(command)
    filename = f"{log_id}_{slug}.log"

    run_dir = LOG_ROOT / run_id / "commands"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / filename

    log_text = "\n".join(
        [
            f"Run ID: {run_id}",
            f"Log ID: {log_id}",
            f"Timestamp (UTC): {_utc_now().isoformat()}",
            f"Command: {command}",
            f"CWD: {cwd}",
            f"Exit Code: {exit_code}",
            "",
            "--- STDOUT ---",
            stdout or "",
            "",
            "--- STDERR ---",
            stderr or "",
        ]
    )
    log_path.write_text(log_text + "\n", encoding="utf-8")

    records = _load_index(run_id)
    records.insert(
        0,
        {
            "logId": log_id,
            "file": str(log_path),
            "command": command,
            "exitCode": exit_code,
            "timestamp": _utc_now().isoformat(),
        },
    )
    _write_index(run_id, records)

    return {"logId": log_id, "path": str(log_path)}


def _ensure_safe_log_path(candidate: Path) -> Path:
    resolved = candidate.resolve()
    root = LOG_ROOT.resolve()
    if root not in resolved.parents and resolved != root:
        raise LogStoreError("Requested log path is outside orchestrator_py/logs")
    return resolved


def list_command_logs(*, run_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if not LOGS_ENABLED:
        return []
    active_run = run_id or get_latest_run_id()
    if not active_run:
        return []
    records = _load_index(active_run)
    return records[: max(1, limit)]


def read_command_log(
    *,
    log_id: str,
    run_id: str | None = None,
    tail_lines: int | None = None,
    pattern: str | None = None,
) -> str:
    if not LOGS_ENABLED:
        raise LogStoreError("Command logs are disabled (ORCH_LOGS_ENABLED=false).")
    active_run = run_id or get_latest_run_id()
    if not active_run:
        raise LogStoreError("No available run logs.")

    records = _load_index(active_run)
    match = next((record for record in records if record.get("logId") == log_id), None)
    if not match:
        raise LogStoreError(f"Log ID not found: {log_id}")

    log_path = _ensure_safe_log_path(Path(str(match.get("file", ""))))
    if not log_path.exists():
        raise LogStoreError(f"Log file missing: {log_path}")

    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tail = max(1, tail_lines or LOGS_TAIL_LINES_DEFAULT)
    if len(lines) > tail:
        lines = lines[-tail:]

    if pattern:
        try:
            regex = re.compile(pattern, flags=re.IGNORECASE)
            lines = [line for line in lines if regex.search(line)]
        except re.error as exc:
            raise LogStoreError(f"Invalid regex pattern: {exc}") from exc

    output = "\n".join(lines)
    return output if output.strip() else "No matching lines in requested log segment."


def get_latest_run_id() -> str | None:
    if not LOGS_ENABLED:
        return None
    latest_path = LOG_ROOT / "latest-run.txt"
    if latest_path.exists():
        value = latest_path.read_text(encoding="utf-8").strip()
        if value:
            return value

    if not LOG_ROOT.exists():
        return None
    runs = sorted([entry.name for entry in LOG_ROOT.iterdir() if entry.is_dir()], reverse=True)
    return runs[0] if runs else None


def summarize_changed_files(
    *,
    previous_snapshot: dict[str, str],
    current_snapshot: dict[str, str],
    max_files: int = 30,
) -> str:
    added = sorted(set(current_snapshot).difference(previous_snapshot))
    deleted = sorted(set(previous_snapshot).difference(current_snapshot))
    modified = sorted(path for path in set(current_snapshot).intersection(previous_snapshot) if current_snapshot[path] != previous_snapshot[path])

    def classify(path: str) -> str:
        normalized = path.lower()
        if "routes" in normalized or "app.routes" in normalized:
            return "routing"
        if any(key in normalized for key in ("form", "validator", "input", "textarea", "checkbox", "radio")):
            return "forms"
        if normalized.endswith(".spec.ts"):
            return "tests"
        if "shared/ui" in normalized:
            return "shared-ui"
        return "ui"

    lines: list[str] = []
    for label, paths in (("added", added), ("modified", modified), ("deleted", deleted)):
        if not paths:
            continue
        for path in paths[:max_files]:
            lines.append(f"- {label}: {path} [{classify(path)}]")

    omitted = max(0, (len(added) + len(modified) + len(deleted)) - len(lines))
    if omitted > 0:
        lines.append(f"- ... +{omitted} additional file changes omitted")

    if not lines:
        return "- No file changes detected since previous attempt."
    return "\n".join(lines)


def snapshot_files_hashes(*, root: Path, relative_prefix: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not root.exists():
        return snapshot
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if not re.search(r"\.(ts|html|css)$", path.name, flags=re.IGNORECASE):
            continue
        relative = path.relative_to(relative_prefix).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        snapshot[relative] = str(hash(content))
    return snapshot

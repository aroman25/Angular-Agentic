from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None

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

Role = Literal["planner", "developer", "validator"]

TOKEN_BUDGET: dict[Role, int] = {
    "planner": int(os.getenv("ORCH_TOKEN_BUDGET_PLANNER", "14000")),
    "developer": int(os.getenv("ORCH_TOKEN_BUDGET_DEVELOPER", "12000")),
    "validator": int(os.getenv("ORCH_TOKEN_BUDGET_VALIDATOR", "10000")),
}
TOKEN_BUDGET_RESERVE = int(os.getenv("ORCH_TOKEN_BUDGET_RESERVE", "800"))


@dataclass(frozen=True)
class BudgetBlock:
    key: str
    title: str
    content: str
    required: bool
    priority: int


def estimate_tokens(text: str, model: str) -> int:
    normalized = text or ""
    if not normalized:
        return 0
    if tiktoken is not None:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(normalized))
        except Exception:
            pass
    # fallback heuristic
    return max(1, int(len(normalized) / 4))


def compress_block(content: str) -> str:
    if not content.strip():
        return ""
    seen: set[str] = set()
    lines: list[str] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = " ".join(line.split())
        if line in seen:
            continue
        seen.add(line)
        lines.append(line)
    if not lines:
        return ""

    # prioritize key-value and bullet style lines first
    prioritized = [line for line in lines if line.startswith("-") or ":" in line]
    remainder = [line for line in lines if line not in prioritized]
    compact = prioritized + remainder
    return "\n".join(compact)


def allocate_blocks(*, blocks: list[BudgetBlock], role: Role, model: str) -> str:
    total_budget = max(1000, TOKEN_BUDGET[role] - TOKEN_BUDGET_RESERVE)
    required = sorted((b for b in blocks if b.required), key=lambda b: b.priority)
    optional = sorted((b for b in blocks if not b.required), key=lambda b: b.priority)

    rendered: list[str] = []
    used = 0

    for block in required:
        compressed = compress_block(block.content)
        text = f"{block.title}\n{compressed}".strip()
        cost = estimate_tokens(text, model)
        rendered.append(text)
        used += cost

    for block in optional:
        compressed = compress_block(block.content)
        if not compressed:
            continue
        text = f"{block.title}\n{compressed}".strip()
        cost = estimate_tokens(text, model)
        if used + cost > total_budget:
            # attempt stronger compression via line cap
            lines = compressed.splitlines()
            limited = "\n".join(lines[: max(4, min(40, len(lines) // 2))])
            text = f"{block.title}\n{limited}".strip()
            cost = estimate_tokens(text, model)
        if used + cost > total_budget:
            continue
        rendered.append(text)
        used += cost

    return "\n\n".join(rendered).strip()

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Role = Literal["planner", "developer", "validator"]

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


@dataclass(frozen=True)
class ModelRoutingDecision:
    role: Role
    model: str
    escalated: bool


PLAN_BASE = os.getenv("ORCH_MODEL_PLAN_BASE", "gpt-5-nano")
DEV_BASE = os.getenv("ORCH_MODEL_DEV_BASE", "gpt-5-nano")
VALIDATE_BASE = os.getenv("ORCH_MODEL_VALIDATE_BASE", "gpt-5-nano")
PLAN_ESCALATED = os.getenv("ORCH_MODEL_PLAN_ESCALATED", "gpt-5-mini")
VALIDATE_ESCALATED = os.getenv("ORCH_MODEL_VALIDATE_ESCALATED", "gpt-5-mini")

PLAN_ESCALATE_AFTER = int(os.getenv("ORCH_MODEL_ESCALATE_AFTER_PLANNER_FAILURES", "2"))
VALIDATOR_ESCALATE_AFTER = int(os.getenv("ORCH_MODEL_ESCALATE_AFTER_VALIDATOR_FAILURES", "2"))


def get_base_model_for_role(role: Role) -> str:
    if role == "planner":
        return PLAN_BASE
    if role == "validator":
        return VALIDATE_BASE
    return DEV_BASE


def get_model_for_role(
    *,
    role: Role,
    planner_structured_failures: int,
    validator_failure_streak: int,
) -> ModelRoutingDecision:
    if role == "planner":
        escalated = planner_structured_failures >= PLAN_ESCALATE_AFTER
        return ModelRoutingDecision(role=role, model=PLAN_ESCALATED if escalated else PLAN_BASE, escalated=escalated)

    if role == "validator":
        escalated = validator_failure_streak >= VALIDATOR_ESCALATE_AFTER
        return ModelRoutingDecision(role=role, model=VALIDATE_ESCALATED if escalated else VALIDATE_BASE, escalated=escalated)

    return ModelRoutingDecision(role=role, model=DEV_BASE, escalated=False)

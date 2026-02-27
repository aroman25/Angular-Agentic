from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class UserStoryDataPoints(BaseModel):
    routes: list[str] = Field(default_factory=list)
    selectors: list[str] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)


class RequirementTraceabilityEntry(BaseModel):
    requirement: str
    tasks: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)

    @field_validator("requirement")
    @classmethod
    def requirement_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("requirement must be non-empty")
        return normalized


class WorkOrderContract(BaseModel):
    feature_name: str
    feature_goal: str
    assumptions: list[str] = Field(default_factory=list)
    user_story_data_points: UserStoryDataPoints
    requirement_traceability: list[RequirementTraceabilityEntry]
    file_structure: list[str]
    state_management: list[str]
    form_model_validation: list[str]
    ui_ux_requirements: list[str]
    template_pattern_references: list[str]
    deviation_notes: str = ""
    acceptance_criteria: list[str]

    @field_validator("feature_name", "feature_goal")
    @classmethod
    def non_empty_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must be non-empty")
        return normalized

    @field_validator(
        "assumptions",
        "file_structure",
        "state_management",
        "form_model_validation",
        "ui_ux_requirements",
        "template_pattern_references",
        "acceptance_criteria",
    )
    @classmethod
    def normalize_string_lists(cls, values: list[str]) -> list[str]:
        normalized = [item.strip() for item in values if isinstance(item, str) and item.strip()]
        return normalized

    @model_validator(mode="after")
    def ensure_required_lists(self) -> "WorkOrderContract":
        required_lists = {
            "requirement_traceability": self.requirement_traceability,
            "file_structure": self.file_structure,
            "state_management": self.state_management,
            "ui_ux_requirements": self.ui_ux_requirements,
            "acceptance_criteria": self.acceptance_criteria,
        }
        for field_name, value in required_lists.items():
            if not value:
                raise ValueError(f"{field_name} must include at least one item")
        return self


def validate_work_order_contract(payload: Any) -> WorkOrderContract:
    if isinstance(payload, WorkOrderContract):
        return payload
    return WorkOrderContract.model_validate(payload)


def parse_work_order_contract_json(raw_json: str) -> WorkOrderContract:
    payload = json.loads(raw_json)
    return validate_work_order_contract(payload)


def to_pretty_json(contract: WorkOrderContract) -> str:
    return contract.model_dump_json(indent=2)


def format_validation_error_messages(error: Exception) -> list[str]:
    if isinstance(error, ValidationError):
        messages: list[str] = []
        for issue in error.errors():
            location = ".".join(str(part) for part in issue.get("loc", []))
            msg = issue.get("msg", "validation error")
            messages.append(f"{location}: {msg}" if location else str(msg))
        return messages or [str(error)]
    return [str(error)]

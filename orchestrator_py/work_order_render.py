from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from orchestrator_py.work_order_schema import WorkOrderContract
except ModuleNotFoundError:
    from work_order_schema import WorkOrderContract


@dataclass(frozen=True)
class ExecutionBriefOptions:
    max_chars: int = 5500
    max_acceptance_items: int = 14
    max_traceability_items: int = 8


def render_work_order_markdown(contract: WorkOrderContract) -> str:
    data = contract.user_story_data_points

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- None"

    traceability_blocks: list[str] = []
    for entry in contract.requirement_traceability:
        lines = [f"- Requirement: {entry.requirement}", "  Tasks:"]
        if entry.tasks:
            lines.extend(f"  - {task}" for task in entry.tasks)
        else:
            lines.append("  - None")
        lines.append("  Acceptance Criteria Mapping:")
        if entry.acceptance_criteria:
            lines.extend(f"  - {criterion}" for criterion in entry.acceptance_criteria)
        else:
            lines.append("  - None")
        traceability_blocks.append("\n".join(lines))

    sections = [
        "# Work Order",
        "",
        "## Feature Name & Goal",
        f"- Feature Name: {contract.feature_name}",
        f"- Goal: {contract.feature_goal}",
        "",
        "## User Story Data Points",
        "- Routes:",
        bullets(data.routes),
        "- Required Selectors:",
        bullets(data.selectors),
        "- Fields:",
        bullets(data.fields),
        "- Constraints:",
        bullets(data.constraints),
        "- Options:",
        bullets(data.options),
        "- Limits:",
        bullets(data.limits),
        "",
        "## Requirement Traceability",
        "\n\n".join(traceability_blocks) if traceability_blocks else "- None",
        "",
        "## File Structure",
        bullets(contract.file_structure),
        "",
        "## State Management",
        bullets(contract.state_management),
        "",
        "## Form Model & Validation",
        bullets(contract.form_model_validation),
        "",
        "## UI/UX Requirements",
        bullets(contract.ui_ux_requirements),
        f"Template Pattern References: {', '.join(contract.template_pattern_references) if contract.template_pattern_references else 'none'}",
    ]

    if contract.deviation_notes:
        sections.append(f"Deviation Notes: {contract.deviation_notes}")

    sections.extend(
        [
            "",
            "## Acceptance Criteria",
            bullets(contract.acceptance_criteria),
            "",
            "## Assumptions",
            bullets(contract.assumptions),
        ]
    )

    return "\n".join(sections).strip() + "\n"


def build_execution_brief_from_contract(contract: WorkOrderContract, *, options: ExecutionBriefOptions | None = None) -> str:
    opts = options or ExecutionBriefOptions()
    data = contract.user_story_data_points

    required_sections = [
        _section("Feature", [f"Name: {contract.feature_name}", f"Goal: {contract.feature_goal}"]),
        _section("Routes", data.routes or ["No explicit routes listed"]),
        _section("Required Selectors", data.selectors or ["No explicit selectors listed"]),
        _section(
            "Acceptance Criteria Summary",
            contract.acceptance_criteria[: opts.max_acceptance_items]
            + ([f"... +{len(contract.acceptance_criteria) - opts.max_acceptance_items} more"] if len(contract.acceptance_criteria) > opts.max_acceptance_items else []),
        ),
    ]

    optional_sections = [
        _section("File Structure", contract.file_structure[:10]),
        _section("State Management", contract.state_management[:10]),
        _section("Form Model & Validation", contract.form_model_validation[:10]),
        _section("UI/UX Requirements", contract.ui_ux_requirements[:12]),
        _section(
            "Requirement Traceability",
            [entry.requirement for entry in contract.requirement_traceability[: opts.max_traceability_items]],
        ),
    ]

    content = "\n\n".join(required_sections)
    for section in optional_sections:
        projected = f"{content}\n\n{section}"
        if len(projected) > opts.max_chars:
            continue
        content = projected

    if len(content) > opts.max_chars:
        content = content[: opts.max_chars]
    return content


def build_execution_brief_from_markdown(markdown: str, *, max_chars: int = 5500) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", markdown.strip())
    return compact if len(compact) <= max_chars else compact[: max_chars - 16] + "\n...[truncated]"


def _section(title: str, items: list[str]) -> str:
    lines = [f"{title}:"]
    lines.extend(f"- {item}" for item in items if item)
    return "\n".join(lines)

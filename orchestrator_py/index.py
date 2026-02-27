from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, TypedDict

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

try:
    from orchestrator_py.tools import (
        TARGET_DIR,
        build_langchain_tools,
        read_file,
        reject_unsafe_agent_command,
        run_command,
        set_active_run_id,
        write_code,
    )
except ModuleNotFoundError:  # Allows `python orchestrator_py/index.py`
    from tools import (
        TARGET_DIR,
        build_langchain_tools,
        read_file,
        reject_unsafe_agent_command,
        run_command,
        set_active_run_id,
        write_code,
    )

try:
    from orchestrator_py.context_retrieval import (
        ContextCard,
        RetrievalResult,
        Role,
        SourceDocument,
        build_card_index,
        infer_story_signals,
        retrieve_context_for_role,
    )
    from orchestrator_py.work_order_render import (
        ExecutionBriefOptions,
        build_execution_brief_from_contract,
        build_execution_brief_from_markdown,
        render_work_order_markdown,
    )
    from orchestrator_py.work_order_schema import (
        WorkOrderContract,
        format_validation_error_messages,
        to_pretty_json,
        validate_work_order_contract,
    )
except ModuleNotFoundError:  # Allows `python orchestrator_py/index.py`
    from context_retrieval import (
        ContextCard,
        RetrievalResult,
        Role,
        SourceDocument,
        build_card_index,
        infer_story_signals,
        retrieve_context_for_role,
    )
    from work_order_render import (
        ExecutionBriefOptions,
        build_execution_brief_from_contract,
        build_execution_brief_from_markdown,
        render_work_order_markdown,
    )
    from work_order_schema import (
        WorkOrderContract,
        format_validation_error_messages,
        to_pretty_json,
        validate_work_order_contract,
    )

try:
    from orchestrator_py.deterministic_checks import (
        DeterministicCommandResult,
        DeterministicValidationResult,
        run_deterministic_validation_checks,
    )
    from orchestrator_py.log_store import (
        snapshot_files_hashes,
        start_run,
        summarize_changed_files,
    )
    from orchestrator_py.model_router import get_base_model_for_role, get_model_for_role
    from orchestrator_py.token_budget import BudgetBlock, allocate_blocks
except ModuleNotFoundError:  # Allows `python orchestrator_py/index.py`
    from deterministic_checks import DeterministicCommandResult, DeterministicValidationResult, run_deterministic_validation_checks
    from log_store import snapshot_files_hashes, start_run, summarize_changed_files
    from model_router import get_base_model_for_role, get_model_for_role
    from token_budget import BudgetBlock, allocate_blocks

REPO_ROOT = Path(__file__).resolve().parents[1]
PY_ORCHESTRATOR_DIR = Path(__file__).resolve().parent
NODE_ORCHESTRATOR_DIR = REPO_ROOT / "orchestrator"

TEMPLATE_DIR = (REPO_ROOT / "automate-angular-template").resolve()
BLUEPRINT_PATH = (REPO_ROOT / "ai-angular-blueprint.txt").resolve()
INSTRUCTIONS_PATH = (REPO_ROOT / "instructions.md").resolve()
ORCHESTRATOR_SKILL_ROOT = (NODE_ORCHESTRATOR_DIR / "skills" / "angular-orchestrator-v20-v21").resolve()
ORCHESTRATOR_SKILL_COMPAT_PATH = ORCHESTRATOR_SKILL_ROOT / "references" / "version-compatibility.md"
ORCHESTRATOR_SKILL_PLANNER_PATH = ORCHESTRATOR_SKILL_ROOT / "references" / "planner-workorders.md"
ORCHESTRATOR_SKILL_DEVELOPER_PATH = ORCHESTRATOR_SKILL_ROOT / "references" / "developer-execution.md"
ORCHESTRATOR_SKILL_VALIDATOR_PATH = ORCHESTRATOR_SKILL_ROOT / "references" / "validator-audit.md"
ORCHESTRATOR_SKILL_PATTERN_CATALOG_PATH = ORCHESTRATOR_SKILL_ROOT / "references" / "template-pattern-catalog.md"
TEMPLATE_PATTERN_CATALOG_INDEX_PATH = TEMPLATE_DIR / "docs" / "agent-patterns" / "README.md"

USER_STORY_PATH = (NODE_ORCHESTRATOR_DIR / "user-story.md").resolve()
LAST_WORK_ORDER_PATH = (PY_ORCHESTRATOR_DIR / "last-work-order.md").resolve()
LAST_WORK_ORDER_JSON_PATH = (PY_ORCHESTRATOR_DIR / "last-work-order.json").resolve()
LAST_VALIDATION_PATH = (PY_ORCHESTRATOR_DIR / "last-validation-feedback.md").resolve()
RULE_CATALOG_PATH = (PY_ORCHESTRATOR_DIR / "rules" / "catalog.json").resolve()

TEMPLATE_COPY_IGNORES = {"node_modules", "dist", ".angular", ".git"}

DEFAULT_MODEL = os.getenv("ORCH_MODEL_DEV_BASE", "gpt-5-nano")
WORK_ORDER_MODE = os.getenv("ORCH_WORK_ORDER_MODE", "dual").strip().lower()
if WORK_ORDER_MODE not in {"dual", "strict", "observe"}:
    WORK_ORDER_MODE = "dual"
RETRIEVAL_ENABLED = os.getenv("ORCH_RETRIEVAL_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
RETRIEVAL_MAX_CHARS: dict[Role, int] = {
    "planner": int(os.getenv("ORCH_RETRIEVAL_MAX_CHARS_PLANNER", "5200")),
    "developer": int(os.getenv("ORCH_RETRIEVAL_MAX_CHARS_DEVELOPER", "4200")),
    "validator": int(os.getenv("ORCH_RETRIEVAL_MAX_CHARS_VALIDATOR", "3600")),
}
RULE_MAX_COUNT: dict[Role, int] = {
    "planner": int(os.getenv("ORCH_RULE_MAX_COUNT_PLANNER", "18")),
    "developer": int(os.getenv("ORCH_RULE_MAX_COUNT_DEVELOPER", "20")),
    "validator": int(os.getenv("ORCH_RULE_MAX_COUNT_VALIDATOR", "16")),
}
PROMPT_MAX_CHARS: dict[Role, int] = {
    "planner": int(os.getenv("ORCH_PROMPT_MAX_CHARS_PLANNER", "22000")),
    "developer": int(os.getenv("ORCH_PROMPT_MAX_CHARS_DEVELOPER", "20000")),
    "validator": int(os.getenv("ORCH_PROMPT_MAX_CHARS_VALIDATOR", "18000")),
}
RETRY_DELTA_ONLY = os.getenv("ORCH_RETRY_DELTA_ONLY", "true").strip().lower() not in {"0", "false", "no", "off"}
RETRY_INCLUDE_FULL_WORKORDER_ON_FIRST_ATTEMPT = (
    os.getenv("ORCH_RETRY_INCLUDE_FULL_WORKORDER_ON_FIRST_ATTEMPT", "true").strip().lower()
    not in {"0", "false", "no", "off"}
)
VALIDATOR_HYBRID_CONFIDENCE_THRESHOLD = float(os.getenv("ORCH_VALIDATOR_HYBRID_CONFIDENCE_THRESHOLD", "0.85"))
EXECUTION_BRIEF_MAX_CHARS = int(os.getenv("ORCH_EXECUTION_BRIEF_MAX_CHARS", "5500"))
PROMPT_USER_STORY_MAX_CHARS = int(os.getenv("ORCH_PROMPT_USER_STORY_MAX_CHARS", "8000"))
PROMPT_VALIDATION_FEEDBACK_MAX_CHARS = int(os.getenv("ORCH_PROMPT_VALIDATION_FEEDBACK_MAX_CHARS", "4000"))
@dataclass(frozen=True)
class RuleCard:
    id: str
    roles: tuple[Role, ...]
    priority: Literal["required", "default", "conditional"]
    tags: tuple[str, ...]
    text: str


@dataclass
class NormalizedValidatorFeedback:
    normalized: str
    warning: str | None = None


@dataclass
class TokenCounters:
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


TOKENS = TokenCounters()


class AgentStateDict(TypedDict):
    userStory: str
    plannerContext: str
    developerContext: str
    validatorContext: str
    plannerRules: str
    developerRules: str
    validatorRules: str
    angularVersionContext: str
    workOrder: str
    workOrderDataJson: str
    workOrderFormat: Literal["json", "markdown"]
    validationFeedback: str
    deterministicViolations: list[str]
    deterministicCoverage: dict[str, bool]
    deterministicConfidence: float
    retryChangedFilesSummary: str
    developerAttemptInCycle: int
    plannerStructuredFailures: int
    validatorFailureStreak: int
    lastRunId: str
    iterations: int


def load_dotenv() -> None:
    try:
        from dotenv import load_dotenv as _load_dotenv
    except Exception:
        return

    for candidate in [(PY_ORCHESTRATOR_DIR / ".env").resolve(), (NODE_ORCHESTRATOR_DIR / ".env").resolve()]:
        if candidate.exists():
            _load_dotenv(candidate)
            break


def read_text_if_exists(file_path: Path) -> str:
    try:
        if not file_path.exists():
            return ""
        return file_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def truncate_prompt_text(text: str, max_chars: int) -> str:
    normalized = text.strip()
    if max_chars <= 0 or len(normalized) <= max_chars:
        return normalized

    # Keep mostly the beginning (instructions/context) and a smaller tail (often contains useful final notes).
    marker = "\n...[truncated for token budget]...\n"
    tail_budget = min(1200, max_chars // 4)
    head_budget = max_chars - len(marker) - tail_budget
    if head_budget < 200:
        return normalized[: max(0, max_chars - len(marker))] + marker.strip()
    return f"{normalized[:head_budget]}{marker}{normalized[-tail_budget:]}"


@dataclass(frozen=True)
class PromptSection:
    key: str
    title: str
    content: str
    required: bool = False
    priority: int = 100


def detect_angular_major_version_from_package_json(package_json_path: Path) -> int | None:
    try:
        if not package_json_path.exists():
            return None
        package_json = json.loads(package_json_path.read_text(encoding="utf-8"))
        version_string = (
            package_json.get("dependencies", {}).get("@angular/core")
            or package_json.get("devDependencies", {}).get("@angular/core")
            or ""
        )
        match = re.search(r"(\d{2})", str(version_string))
        return int(match.group(1)) if match else None
    except Exception:
        return None


def build_angular_version_context(template_package_json_path: Path) -> str:
    major = detect_angular_major_version_from_package_json(template_package_json_path)

    if major in {20, 21}:
        zoneless_note = (
            "Prefer zoneless-compatible patterns; do not assume Zone.js-based behavior."
            if major == 21
            else "Do not require zoneless unless the template explicitly configures it."
        )
        return " ".join(
            [
                f"Angular target detected from template package.json: v{major}.",
                "Prompt rules must stay compatible with Angular v20 and v21 unless the user story requires a narrower target.",
                zoneless_note,
                "Standalone components are default in both v20 and v21; do not require 'standalone: true'.",
            ]
        )

    return " ".join(
        [
            "Angular target major version could not be detected from template package.json.",
            "Assume v20/v21 compatibility and avoid version-fragile instructions.",
        ]
    )


def build_retrieval_sources() -> list[SourceDocument]:
    return [
        SourceDocument(
            source_id="BLUEPRINT",
            path=BLUEPRINT_PATH,
            tags=("routing", "form", "validation", "shared-ui", "tailwind"),
        ),
        SourceDocument(
            source_id="INSTRUCTIONS",
            path=INSTRUCTIONS_PATH,
            tags=("routing", "form", "validation", "shared-ui", "tailwind", "template"),
        ),
        SourceDocument(
            source_id="VERSION_COMPAT",
            path=ORCHESTRATOR_SKILL_COMPAT_PATH,
            tags=("angular-version", "routing"),
            mandatory_for=("planner", "developer", "validator"),
        ),
        SourceDocument(
            source_id="PLANNER_WORKORDERS",
            path=ORCHESTRATOR_SKILL_PLANNER_PATH,
            tags=("work-order", "traceability", "selectors", "form"),
            mandatory_for=("planner",),
        ),
        SourceDocument(
            source_id="DEVELOPER_EXECUTION",
            path=ORCHESTRATOR_SKILL_DEVELOPER_PATH,
            tags=("build", "shared-ui", "form", "validation"),
            mandatory_for=("developer",),
        ),
        SourceDocument(
            source_id="VALIDATOR_AUDIT",
            path=ORCHESTRATOR_SKILL_VALIDATOR_PATH,
            tags=("validation", "shared-ui", "testing"),
            mandatory_for=("validator",),
        ),
        SourceDocument(
            source_id="PATTERN_CATALOG",
            path=ORCHESTRATOR_SKILL_PATTERN_CATALOG_PATH,
            tags=("layout", "form", "shared-ui"),
        ),
        SourceDocument(
            source_id="PATTERN_INDEX",
            path=TEMPLATE_PATTERN_CATALOG_INDEX_PATH,
            tags=("layout", "form", "shared-ui"),
            mandatory_for=("planner",),
        ),
    ]


def _score_rule_for_story(rule: RuleCard, story_signals: set[str], user_story: str) -> float:
    score = 0.0
    if rule.priority == "default":
        score += 30.0
    if rule.priority == "conditional":
        score += 20.0
    if set(rule.tags).intersection(story_signals):
        score += 40.0
    matches = len(set(re.findall(r"[a-z][a-z0-9-]{2,}", user_story.lower())).intersection(set(rule.tags)))
    score += float(matches)
    return score


def load_rule_catalog(*, catalog_path: Path = RULE_CATALOG_PATH) -> list[RuleCard]:
    raw_catalog = (read_text_if_exists(catalog_path) or "{}").lstrip("\ufeff")
    payload = json.loads(raw_catalog)
    rules_payload = payload.get("rules")
    if not isinstance(rules_payload, list):
        raise RuntimeError(f"Invalid rule catalog at {catalog_path}: missing 'rules' array")

    rules: list[RuleCard] = []
    for item in rules_payload:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("id", "")).strip()
        if not rule_id or not re.match(r"^[A-Z0-9_]+$", rule_id):
            raise RuntimeError(f"Invalid rule id in catalog: {rule_id}")
        roles_raw = item.get("roles", [])
        roles: tuple[Role, ...] = tuple(role for role in roles_raw if role in {"planner", "developer", "validator"})
        if not roles:
            continue
        priority = str(item.get("priority", "default")).strip().lower()
        if priority not in {"required", "default", "conditional"}:
            priority = "default"
        tags_raw = item.get("tags", [])
        tags = tuple(str(tag).strip().lower() for tag in tags_raw if str(tag).strip())
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        rules.append(
            RuleCard(
                id=rule_id,
                roles=roles,
                priority=priority,  # type: ignore[arg-type]
                tags=tags,
                text=text,
            )
        )
    return rules


def select_rule_cards_for_role(
    *,
    role: Role,
    rules: list[RuleCard],
    user_story: str,
    max_count: int,
) -> list[RuleCard]:
    role_rules = [rule for rule in rules if role in rule.roles]
    story_signals = infer_story_signals(user_story)
    required = [rule for rule in role_rules if rule.priority == "required"]
    defaults = [rule for rule in role_rules if rule.priority == "default"]
    conditionals = [
        rule
        for rule in role_rules
        if rule.priority == "conditional" and bool(set(rule.tags).intersection(story_signals))
    ]

    defaults_sorted = sorted(
        defaults,
        key=lambda rule: (-_score_rule_for_story(rule, story_signals, user_story), rule.id),
    )
    conditionals_sorted = sorted(
        conditionals,
        key=lambda rule: (-_score_rule_for_story(rule, story_signals, user_story), rule.id),
    )

    selected: list[RuleCard] = sorted(required, key=lambda rule: rule.id)
    for candidate in defaults_sorted + conditionals_sorted:
        if candidate.id in {rule.id for rule in selected}:
            continue
        if len(selected) >= max_count:
            break
        selected.append(candidate)
    return selected


def render_rule_context(*, selected_rules: list[RuleCard]) -> str:
    if not selected_rules:
        return "Applicable Rule IDs: none\nRule Text: none"
    ids = "\n".join(f"- {rule.id}" for rule in selected_rules)
    text = "\n".join(f"- {rule.id}: {rule.text}" for rule in selected_rules)
    return f"Applicable Rule IDs:\n{ids}\n\nRule Text:\n{text}"


def build_prompt_with_budget(*, sections: list[PromptSection], role: Role, model: str) -> str:
    blocks = [
        BudgetBlock(
            key=section.key,
            title=section.title,
            content=section.content,
            required=section.required,
            priority=section.priority,
        )
        for section in sections
    ]
    return allocate_blocks(blocks=blocks, role=role, model=model)


def cleanup_generated_app_processes(*, target_dir: Path = TARGET_DIR) -> None:
    if os.name != "nt":
        return
    try:
        target_for_match = str(target_dir).replace("\\", "\\\\")
        script = "; ".join(
            [
                f"$target = '{target_for_match}'",
                "$procs = Get-CimInstance Win32_Process | Where-Object {",
                "  $_.CommandLine -and",
                "  $_.ProcessId -ne $PID -and",
                "  $_.CommandLine -like \"*$target*\" -and",
                "  ($_.Name -match 'node|esbuild')",
                "}",
                "foreach ($p in $procs) {",
                "  try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}",
                "}",
            ]
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        pass


def reset_generated_app_preserving_node_modules(*, target_dir: Path = TARGET_DIR) -> None:
    if not target_dir.exists():
        return
    for entry in target_dir.iterdir():
        if entry.name == "node_modules":
            continue
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink(missing_ok=True)
        except Exception:
            pass


def _copytree_ignore(_dir: str, names: list[str]) -> set[str]:
    return {name for name in names if name in TEMPLATE_COPY_IGNORES}


def setup_project(*, target_dir: Path = TARGET_DIR) -> None:
    print("Cloning template to fresh generated-app directory...")
    cleanup_generated_app_processes(target_dir=target_dir)
    if target_dir.exists():
        try:
            shutil.rmtree(target_dir)
        except Exception:
            try:
                stamp = datetime.utcnow().isoformat().replace(":", "-").replace(".", "-")
                fallback_path = target_dir.with_name(f"{target_dir.name}-stale-{stamp}")
                print(f"Could not remove generated-app cleanly. Archiving to: {fallback_path}")
                if fallback_path.exists():
                    shutil.rmtree(fallback_path)
                shutil.move(str(target_dir), str(fallback_path))
            except Exception:
                print("Archive fallback also failed (likely folder root lock). Falling back to emptyDir on generated-app.")
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for entry in list(target_dir.iterdir()):
                        if entry.is_dir():
                            shutil.rmtree(entry)
                        else:
                            entry.unlink(missing_ok=True)
                except Exception:
                    print(
                        "emptyDir fallback failed (likely locked node_modules). Resetting generated-app while preserving node_modules."
                    )
                    reset_generated_app_preserving_node_modules(target_dir=target_dir)

    shutil.copytree(TEMPLATE_DIR, target_dir, ignore=_copytree_ignore)

    print("Installing dependencies in generated-app...")
    subprocess.run("npm install", cwd=target_dir, shell=True, check=True)
    print("Template ready!")


def requires_reactive_form_validation(user_story: str, work_order: str) -> bool:
    combined = f"{user_story}\n{work_order}".lower()
    mentions_form = bool(re.search(r"\bform(s)?\b", combined))
    mentions_validation = bool(
        re.search(r"\bvalidat(e|ion|ions|ing)\b", combined) or re.search(r"\berror message(s)?\b", combined)
    )
    return mentions_form and mentions_validation


def extract_required_shared_ui_selectors(text: str) -> list[str]:
    matches = [m.group(1).lower() for m in re.finditer(r"`(app-[a-z0-9-]+)`", text, flags=re.IGNORECASE)]
    aliases = {"app-menu": "app-dropdown-menu"}
    normalized = [aliases.get(selector, selector) for selector in matches]
    return list(dict.fromkeys(normalized))


def extract_explicit_route_data_points(text: str) -> list[str]:
    matches = [
        m.group(1).lower()
        for m in re.finditer(
            r"""(?:route should be|redirect(?:ed)? to|accessible at)\s+[`'"]?(\/[a-z0-9\-\/]+)[`'"]?""",
            text,
            flags=re.IGNORECASE,
        )
    ]
    return list(dict.fromkeys(matches))


def extract_form_field_data_points(user_story: str) -> list[str]:
    lines = user_story.splitlines()
    fields: set[str] = set()
    in_form_fields_section = False

    for raw_line in lines:
        line = raw_line.strip()
        if re.match(r"^\d+\.\s+form fields\b", line, flags=re.IGNORECASE):
            in_form_fields_section = True
            continue
        if in_form_fields_section and re.match(r"^\d+\.\s+", line):
            break
        if (not in_form_fields_section) or (not line.startswith("-")):
            continue

        without_bullet = re.sub(r"^-+\s*", "", line)
        payload = without_bullet.split(":", 1)[1] if ":" in without_bullet else without_bullet
        for part in payload.split(","):
            normalized = part.strip()
            normalized = re.sub(r"^[`'\"]|[`'\"]$", "", normalized)
            normalized = re.sub(r"\s+", " ", normalized)
            normalized = re.sub(r"[.;]$", "", normalized)
            normalized = normalized.lower()
            if normalized:
                fields.add(normalized)
    return list(fields)


def has_markdown_heading(markdown: str, heading_regex: re.Pattern[str]) -> bool:
    return any(
        (re.match(r"^\s{0,3}#{1,6}\s+", line) or re.match(r"^\s*\d+[\)\.\:]\s+", line))
        and heading_regex.search(line)
        for line in markdown.splitlines()
    )


def work_order_has_template_pattern_references(work_order: str) -> bool:
    return bool(re.search(r"(?:template\s+)?pattern references?\s*:", work_order, flags=re.IGNORECASE))


def user_story_likely_needs_template_pattern_references(user_story: str) -> bool:
    normalized = user_story.lower()
    selector_count = len(re.findall(r"\bapp-[a-z0-9-]+\b", normalized))
    has_form_terms = bool(
        re.search(r"\bform(s)?\b", normalized)
        or re.search(r"\bfield(s)?\b", normalized)
        or re.search(r"\bsubmit\b", normalized)
        or re.search(r"\bvalidation\b", normalized)
        or re.search(r"\bfilter(s|ing)?\b", normalized)
    )
    has_layout_terms = bool(
        re.search(r"\blayout\b", normalized)
        or re.search(r"\bpage\b", normalized)
        or re.search(r"\bdashboard\b", normalized)
        or re.search(r"\blist\b", normalized)
        or re.search(r"\btable\b", normalized)
        or re.search(r"\bgrid\b", normalized)
        or re.search(r"\btabs?\b", normalized)
        or re.search(r"\bdrawer\b", normalized)
        or re.search(r"\bdialog\b", normalized)
        or re.search(r"\bwizard\b", normalized)
    )
    return has_form_terms or has_layout_terms or selector_count >= 2


def validate_work_order_quality(user_story: str, work_order: str) -> list[str]:
    issues: list[str] = []
    normalized_work_order = work_order.lower()
    required_sections: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"feature name|goal", re.IGNORECASE), "Feature Name & Goal section"),
        (re.compile(r"file structure", re.IGNORECASE), "File Structure section"),
        (re.compile(r"state management", re.IGNORECASE), "State Management section"),
        (re.compile(r"ui\/ux requirements|ui requirements|ux requirements", re.IGNORECASE), "UI/UX Requirements section"),
        (re.compile(r"acceptance criteria", re.IGNORECASE), "Acceptance Criteria section"),
        (
            re.compile(r"user story data points|data points extracted from user story|data points from user story", re.IGNORECASE),
            "User Story Data Points section",
        ),
        (re.compile(r"traceability|requirement mapping|user story.*work order", re.IGNORECASE), "Requirement Traceability section"),
    ]

    for regex, label in required_sections:
        if not has_markdown_heading(work_order, regex):
            issues.append(f"Missing required Work Order section: {label}")

    if user_story_likely_needs_template_pattern_references(user_story) and not work_order_has_template_pattern_references(
        work_order
    ):
        issues.append("Form/layout-heavy Work Order is missing a `Template Pattern References:` line in UI/UX Requirements.")

    for route in extract_explicit_route_data_points(user_story):
        if route not in normalized_work_order:
            issues.append(f"Work Order is missing explicit route data point from user story: {route}")

    required_selectors = extract_required_shared_ui_selectors(user_story)
    if required_selectors:
        missing_selectors = [selector for selector in required_selectors if selector not in normalized_work_order]
        if missing_selectors:
            preview = ", ".join(missing_selectors[:10])
            suffix = " ..." if len(missing_selectors) > 10 else ""
            issues.append(
                "Work Order is missing shared UI selectors from user story (must map all required selectors): "
                f"{preview}{suffix}"
            )

    if requires_reactive_form_validation(user_story, work_order):
        required_form_planning_signals: list[tuple[re.Pattern[str], str]] = [
            (
                re.compile(r"validation matrix|field-by-field validation|validation rules", re.IGNORECASE),
                "field-by-field validation matrix",
            ),
            (re.compile(r"reactive form", re.IGNORECASE), "typed Reactive Form planning"),
            (re.compile(r"valuechange|valuechange\)|non-cva|controlvalueaccessor", re.IGNORECASE), "non-CVA shared control binding strategy"),
        ]
        for regex, label in required_form_planning_signals:
            if not regex.search(work_order):
                issues.append(f"Form-centric Work Order is missing: {label}")

        field_labels = extract_form_field_data_points(user_story)
        missing_field_labels = [field for field in field_labels if field not in normalized_work_order]
        max_allowed_missing = max(2, int(len(field_labels) * 0.2)) if field_labels else 0
        if field_labels and len(missing_field_labels) > max_allowed_missing:
            preview = ", ".join(missing_field_labels[:10])
            suffix = " ..." if len(missing_field_labels) > 10 else ""
            issues.append(
                "Work Order does not preserve enough form field data points from the user story. "
                f"Missing examples: {preview}{suffix}"
            )

    return issues


def detect_shared_ui_projection_provider_risks(relative_path: str, content: str) -> list[str]:
    if not relative_path.startswith("src/app/shared/ui/"):
        return []
    if "<ng-content" not in content.lower():
        return []

    violations: list[str] = []
    if (
        re.search(r"accordion/accordion\.component\.ts$", relative_path, flags=re.IGNORECASE)
        and re.search(r"\bngaccordiongroup\b", content, flags=re.IGNORECASE)
        and "hostDirectives" not in content
    ):
        violations.append(
            f"{relative_path}:1 - Template/Agent-level issue: projected shared UI wrapper uses ngAccordionGroup on an internal element without hostDirectives. "
            "This can cause runtime NG0201 (ACCORDION_GROUP) for projected accordion items. Attach AccordionGroup to the component host."
        )
    return violations


def get_max_workflow_iterations(state: AgentStateDict) -> int:
    required_selectors = extract_required_shared_ui_selectors(state["userStory"])
    complex_coverage_story = len(required_selectors) >= 15
    form_validation_story = requires_reactive_form_validation(state["userStory"], state["workOrder"])
    if complex_coverage_story and form_validation_story:
        return 8
    if complex_coverage_story:
        return 7
    return 5


def is_known_shared_ui_path_false_positive(feedback: str, *, target_dir: Path = TARGET_DIR) -> bool:
    if not re.search(r"shared ui component files are missing", feedback, flags=re.IGNORECASE):
        return False

    bogus_path_matches = list(
        re.finditer(r"src/app/shared/ui/app-([a-z0-9-]+)/app-\1\.component\.ts", feedback, flags=re.IGNORECASE)
    )
    if not bogus_path_matches:
        return False

    shared_ui_barrel_path = target_dir / "src" / "app" / "shared" / "ui" / "index.ts"
    if not shared_ui_barrel_path.exists():
        return False

    barrel_content = shared_ui_barrel_path.read_text(encoding="utf-8")
    return all(f"./{match.group(1).lower()}/{match.group(1).lower()}.component" in barrel_content for match in bogus_path_matches)


def normalize_validator_feedback(raw_final_message: str, *, target_dir: Path = TARGET_DIR) -> NormalizedValidatorFeedback:
    trimmed = raw_final_message.strip()
    ends_with_pass = bool(re.match(r"^([\s\S]*\n)?PASS$", trimmed))
    has_failure_language = bool(re.search(r"\b(fail|failed|missing|violation|error)\b", trimmed, flags=re.IGNORECASE))

    if trimmed == "PASS" or (ends_with_pass and not has_failure_language):
        return NormalizedValidatorFeedback(normalized="PASS")

    if is_known_shared_ui_path_false_positive(trimmed, target_dir=target_dir):
        return NormalizedValidatorFeedback(
            normalized="PASS",
            warning="Validation agent false-positive normalized: selector names (app-*) were incorrectly treated as shared/ui folder names.",
        )

    return NormalizedValidatorFeedback(normalized=raw_final_message)




def build_planner_prompt(
    state: AgentStateDict,
    *,
    structured_output: bool,
    model: str,
    retry_supplement: str = "",
) -> str:
    output_instruction = (
        "Return a JSON object matching the WorkOrderContract schema exactly. Do not include markdown."
        if structured_output
        else "Return a complete markdown Work Order."
    )
    sections = [
        PromptSection(
            key="planner_role",
            title="Planner Role",
            content=(
                "You are the Planning Agent (The Architect). "
                "Produce a decision-complete vertical slice work order."
            ),
            required=True,
            priority=40,
        ),
        PromptSection(
            key="planner_output_contract",
            title="Output Contract",
            content=output_instruction,
            required=True,
            priority=2,
        ),
        PromptSection(
            key="planner_user_story",
            title="User Story",
            content=state["userStory"],
            required=True,
            priority=1,
        ),
        PromptSection(
            key="planner_angular_version",
            title="Angular Version Context",
            content=state["angularVersionContext"],
            required=True,
            priority=30,
        ),
        PromptSection(
            key="planner_rules",
            title="Applicable Rules",
            content=state["plannerRules"],
            required=True,
            priority=60,
        ),
        PromptSection(
            key="planner_retrieved_context",
            title="Retrieved Context Cards",
            content=state["plannerContext"],
            required=False,
            priority=80,
        ),
    ]
    if retry_supplement.strip():
        sections.append(
            PromptSection(
                key="planner_retry_fixes",
                title="Planner Retry Fixes",
                content=retry_supplement,
                required=True,
                priority=3,
            )
        )
    return build_prompt_with_budget(sections=sections, role="planner", model=model)


def build_developer_system_prompt(state: AgentStateDict, retry_focus_instructions: str, *, model: str) -> str:
    sections = [
        PromptSection(
            key="developer_role",
            title="Developer Role",
            content=(
                "You are the Development Agent (The Engineer). Implement the provided work order in generated-app "
                "using available tools. Build must pass with zero Angular warnings."
            ),
            required=True,
            priority=20,
        ),
        PromptSection(
            key="developer_angular_version",
            title="Angular Version Context",
            content=state["angularVersionContext"],
            required=True,
            priority=30,
        ),
        PromptSection(
            key="developer_rules",
            title="Applicable Rules",
            content=state["developerRules"],
            required=True,
            priority=60,
        ),
        PromptSection(
            key="developer_context_cards",
            title="Retrieved Context Cards",
            content=state["developerContext"],
            required=False,
            priority=80,
        ),
    ]
    if retry_focus_instructions.strip():
        sections.append(
            PromptSection(
                key="developer_retry_focus",
                title="Retry Focus",
                content=retry_focus_instructions,
                required=True,
                priority=10,
            )
        )
    return build_prompt_with_budget(sections=sections, role="developer", model=model)


def build_validator_system_prompt(state: AgentStateDict, *, model: str) -> str:
    sections = [
        PromptSection(
            key="validator_role",
            title="Validator Role",
            content=(
                "You are the Validation Agent (The Tester). Deterministic prechecks already ran. "
                "Run tests and verify semantic correctness against required criteria."
            ),
            required=True,
            priority=20,
        ),
        PromptSection(
            key="validator_angular_version",
            title="Angular Version Context",
            content=state["angularVersionContext"],
            required=True,
            priority=30,
        ),
        PromptSection(
            key="validator_rules",
            title="Applicable Rules",
            content=state["validatorRules"],
            required=True,
            priority=60,
        ),
        PromptSection(
            key="validator_context_cards",
            title="Retrieved Context Cards",
            content=state["validatorContext"],
            required=False,
            priority=80,
        ),
    ]
    return build_prompt_with_budget(sections=sections, role="validator", model=model)


def extract_unresolved_criteria_from_feedback(feedback: str, *, max_items: int = 8) -> list[str]:
    if not feedback.strip() or feedback.strip() == "PASS":
        return []
    candidates = [
        line.strip().lstrip("-").strip()
        for line in feedback.splitlines()
        if re.match(r"^\s*-\s+", line)
    ]
    if not candidates:
        candidates = [
            line.strip()
            for line in feedback.splitlines()
            if any(keyword in line.lower() for keyword in ("failed", "missing", "violation", "requires"))
        ]
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
        if len(deduped) >= max_items:
            break
    return deduped


def _ensure_langchain_runtime() -> None:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage  # noqa: F401
        from langchain_openai import ChatOpenAI  # noqa: F401
        from langgraph.prebuilt import create_react_agent  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "Full orchestrator_py execution requires Python LangChain/LangGraph/OpenAI packages. "
            "Run self-test mode if you only want local smoke checks."
        ) from exc


def _extract_token_usage(payload: object) -> tuple[int, int, int]:
    if isinstance(payload, dict):
        total = int(payload.get("total_tokens") or payload.get("totalTokens") or 0)
        prompt = int(payload.get("prompt_tokens") or payload.get("promptTokens") or 0)
        completion = int(payload.get("completion_tokens") or payload.get("completionTokens") or 0)
        return total, prompt, completion
    return 0, 0, 0


def _build_llm(*, model: str):
    _ensure_langchain_runtime()
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_openai import ChatOpenAI

    class TokenCallback(BaseCallbackHandler):
        def on_llm_end(self, response, **kwargs):  # type: ignore[override]
            llm_output = getattr(response, "llm_output", None) or {}
            usage = None
            if isinstance(llm_output, dict):
                usage = llm_output.get("token_usage") or llm_output.get("tokenUsage")
            total, prompt, completion = _extract_token_usage(usage or {})
            TOKENS.total_tokens += total
            TOKENS.prompt_tokens += prompt
            TOKENS.completion_tokens += completion

    return ChatOpenAI(model=model, temperature=0, callbacks=[TokenCallback()])


def _get_role_llm(state: AgentStateDict, role: Role, *, force_base: bool = False):
    if force_base:
        base_model = get_base_model_for_role(role)
        return _build_llm(model=base_model), base_model, False
    decision = get_model_for_role(
        role=role,
        planner_structured_failures=state.get("plannerStructuredFailures", 0),
        validator_failure_streak=state.get("validatorFailureStreak", 0),
    )
    return _build_llm(model=decision.model), decision.model, decision.escalated


def _create_react_agent_compat(*, llm, tools, message_modifier):
    from langgraph.prebuilt import create_react_agent

    attempts = [
        lambda: create_react_agent(llm, tools, state_modifier=message_modifier),
        lambda: create_react_agent(llm=llm, tools=tools, message_modifier=message_modifier),
        lambda: create_react_agent(model=llm, tools=tools, prompt=message_modifier),
        lambda: create_react_agent(model=llm, tools=tools, state_modifier=message_modifier),
    ]
    last_error: Exception | None = None
    for attempt in attempts:
        try:
            return attempt()
        except Exception as exc:
            last_error = exc
    raise RuntimeError("Unable to construct create_react_agent with current langgraph version.") from last_error


def _invoke_agent_compat(agent, payload: dict, recursion_limit: int):
    configs = [{"recursion_limit": recursion_limit}, {"recursionLimit": recursion_limit}]
    last_error: Exception | None = None
    for cfg in configs:
        try:
            return agent.invoke(payload, cfg)
        except TypeError as exc:
            last_error = exc
        except Exception:
            raise
    try:
        return agent.invoke(payload)
    except Exception as exc:
        raise RuntimeError("Agent invocation failed") from (exc if last_error is None else last_error)


def _extract_final_message_content(response) -> str:
    messages = response.get("messages") if isinstance(response, dict) else getattr(response, "messages", None)
    if not messages:
        return str(response)
    last_message = messages[-1]
    content = getattr(last_message, "content", None)
    if content is None:
        return str(last_message)
    if isinstance(content, list):
        return "".join(str(part) for part in content)
    return str(content)


def _persist_work_order_outputs(
    *,
    work_order_markdown: str,
    contract: WorkOrderContract | None,
    work_order_format: Literal["json", "markdown"],
) -> tuple[str, str]:
    LAST_WORK_ORDER_PATH.write_text(work_order_markdown, encoding="utf-8")
    if contract is None:
        LAST_WORK_ORDER_JSON_PATH.write_text("{}\n", encoding="utf-8")
        return "", work_order_format
    json_payload = to_pretty_json(contract)
    LAST_WORK_ORDER_JSON_PATH.write_text(f"{json_payload}\n", encoding="utf-8")
    return json_payload, work_order_format


def _invoke_planner_structured_once(llm, prompt: str) -> WorkOrderContract:
    if hasattr(llm, "with_structured_output"):
        structured_llm = llm.with_structured_output(WorkOrderContract)
        response = structured_llm.invoke(prompt)
        return validate_work_order_contract(response)

    response = llm.invoke(prompt)
    raw_content = str(getattr(response, "content", "") or "")
    payload = json.loads(raw_content)
    return validate_work_order_contract(payload)


def _invoke_structured_with_model_fallback(state: AgentStateDict, prompt: str) -> WorkOrderContract:
    llm, selected_model, _ = _get_role_llm(state, "planner")
    try:
        return _invoke_planner_structured_once(llm, prompt)
    except Exception:
        base_model = get_base_model_for_role("planner")
        if selected_model == base_model:
            raise
        fallback_llm, _, _ = _get_role_llm(state, "planner", force_base=True)
        return _invoke_planner_structured_once(fallback_llm, prompt)


def _invoke_message_with_model_fallback(*, state: AgentStateDict, role: Role, message):
    llm, selected_model, _ = _get_role_llm(state, role)
    try:
        return llm.invoke([message])
    except Exception:
        base_model = get_base_model_for_role(role)
        if selected_model == base_model:
            raise
        fallback_llm, _, _ = _get_role_llm(state, role, force_base=True)
        return fallback_llm.invoke([message])


def resolve_work_order_mode_after_structured_failure(mode: str) -> Literal["markdown", "strict_error"]:
    return "strict_error" if mode == "strict" else "markdown"


def _planner_node(state: AgentStateDict, system_message_cls) -> dict[str, object]:
    print("\n--- PLANNING AGENT ---")
    quality_issues: list[str] = []
    planner_structured_failures = int(state.get("plannerStructuredFailures", 0))
    state["plannerStructuredFailures"] = planner_structured_failures

    if WORK_ORDER_MODE in {"dual", "strict"}:
        for attempt in range(1, 4):
            state["plannerStructuredFailures"] = planner_structured_failures
            retry_supplement = "" if attempt == 1 else "\n".join(
                [
                    f"Structured planning attempt {attempt}/3 failed.",
                    "Fix these issues in the next full response:",
                    *[f"- {issue}" for issue in quality_issues],
                ]
            )
            routing_model = get_model_for_role(
                role="planner",
                planner_structured_failures=planner_structured_failures,
                validator_failure_streak=state.get("validatorFailureStreak", 0),
            ).model
            prompt = build_planner_prompt(
                state,
                structured_output=True,
                model=routing_model,
                retry_supplement=retry_supplement,
            )
            try:
                contract = _invoke_structured_with_model_fallback(state, prompt)
                rendered = render_work_order_markdown(contract)
                quality_issues = validate_work_order_quality(state["userStory"], rendered)
                if not quality_issues:
                    work_order_data_json, work_order_format = _persist_work_order_outputs(
                        work_order_markdown=rendered,
                        contract=contract,
                        work_order_format="json",
                    )
                    print("Work Order Generated (JSON-first).")
                    return {
                        "workOrder": rendered,
                        "workOrderDataJson": work_order_data_json,
                        "workOrderFormat": work_order_format,
                        "plannerStructuredFailures": planner_structured_failures,
                    }
            except Exception as exc:
                quality_issues = format_validation_error_messages(exc)

            planner_structured_failures += 1
            state["plannerStructuredFailures"] = planner_structured_failures
            print(
                f"Planner structured output quality check failed (attempt {attempt}/3):\n- "
                + "\n- ".join(quality_issues)
            )

        if resolve_work_order_mode_after_structured_failure(WORK_ORDER_MODE) == "strict_error":
            raise RuntimeError("Planner failed to produce valid structured WorkOrderContract in strict mode.")

    markdown_attempts = 3 if WORK_ORDER_MODE == "observe" else 1
    work_order_markdown = ""
    markdown_issues: list[str] = []
    for attempt in range(1, markdown_attempts + 1):
        state["plannerStructuredFailures"] = planner_structured_failures
        retry_supplement = "" if attempt == 1 else "\n".join(
            [
                f"Markdown planning attempt {attempt}/{markdown_attempts} failed.",
                "Fix these issues and return a full corrected markdown work order:",
                *[f"- {issue}" for issue in markdown_issues],
            ]
        )
        routing_model = get_model_for_role(
            role="planner",
            planner_structured_failures=planner_structured_failures,
            validator_failure_streak=state.get("validatorFailureStreak", 0),
        ).model
        prompt = build_planner_prompt(
            state,
            structured_output=False,
            model=routing_model,
            retry_supplement=retry_supplement,
        )
        response = _invoke_message_with_model_fallback(
            state=state,
            role="planner",
            message=system_message_cls(content=prompt),
        )
        work_order_markdown = str(getattr(response, "content", "") or "")
        markdown_issues = validate_work_order_quality(state["userStory"], work_order_markdown)
        if not markdown_issues:
            break

        print(
            f"Planner markdown output quality check failed (attempt {attempt}/{markdown_attempts}):\n- "
            + "\n- ".join(markdown_issues)
        )

    contract_sidecar: WorkOrderContract | None = None
    if WORK_ORDER_MODE == "observe":
        try:
            observe_model = get_model_for_role(
                role="planner",
                planner_structured_failures=planner_structured_failures,
                validator_failure_streak=state.get("validatorFailureStreak", 0),
            ).model
            observe_prompt = build_planner_prompt(state, structured_output=True, model=observe_model)
            contract_sidecar = _invoke_structured_with_model_fallback(state, observe_prompt)
        except Exception:
            contract_sidecar = None

    work_order_data_json, work_order_format = _persist_work_order_outputs(
        work_order_markdown=work_order_markdown,
        contract=contract_sidecar,
        work_order_format="markdown",
    )
    print("Work Order Generated (markdown fallback).")
    return {
        "workOrder": work_order_markdown,
        "workOrderDataJson": work_order_data_json,
        "workOrderFormat": work_order_format,
        "plannerStructuredFailures": planner_structured_failures,
    }


def _build_execution_brief_for_state(state: AgentStateDict) -> str:
    if state.get("workOrderFormat") == "json" and state.get("workOrderDataJson", "").strip():
        try:
            payload = json.loads(state["workOrderDataJson"])
            contract = validate_work_order_contract(payload)
            return build_execution_brief_from_contract(
                contract,
                options=ExecutionBriefOptions(max_chars=EXECUTION_BRIEF_MAX_CHARS),
            )
        except Exception:
            pass
    return build_execution_brief_from_markdown(state["workOrder"], max_chars=EXECUTION_BRIEF_MAX_CHARS)


def _build_acceptance_excerpt_for_state(state: AgentStateDict, *, max_items: int = 12) -> str:
    if state.get("workOrderFormat") == "json" and state.get("workOrderDataJson", "").strip():
        try:
            payload = json.loads(state["workOrderDataJson"])
            contract = validate_work_order_contract(payload)
            items = contract.acceptance_criteria[:max_items]
            if len(contract.acceptance_criteria) > max_items:
                items.append(f"... +{len(contract.acceptance_criteria) - max_items} more")
            return "\n".join(f"- {item}" for item in items) if items else "- None"
        except Exception:
            pass

    capture = False
    items: list[str] = []
    for raw_line in state["workOrder"].splitlines():
        line = raw_line.strip()
        if re.match(r"^#{1,6}\s+acceptance criteria\b", line, flags=re.IGNORECASE):
            capture = True
            continue
        if capture and re.match(r"^#{1,6}\s+", line):
            break
        if capture and re.match(r"^-\s+", line):
            items.append(re.sub(r"^-\s+", "", line))
        if len(items) >= max_items:
            break
    if not items:
        return "- Acceptance criteria not explicitly parsed from markdown."
    return "\n".join(f"- {item}" for item in items)


def _format_bullets(items: list[str], *, fallback: str = "- None", max_items: int = 20) -> str:
    if not items:
        return fallback
    trimmed = items[:max_items]
    if len(items) > max_items:
        trimmed.append(f"... +{len(items) - max_items} more")
    return "\n".join(f"- {item}" for item in trimmed)


def _build_requirement_summary(state: AgentStateDict) -> str:
    combined = f"{state['userStory']}\n{state['workOrder']}"
    routes = extract_explicit_route_data_points(combined)
    selectors = extract_required_shared_ui_selectors(combined)
    acceptance = _build_acceptance_excerpt_for_state(state, max_items=10)
    route_block = _format_bullets(routes, fallback="- Route requirements not explicitly parsed.")
    selector_block = _format_bullets(selectors, fallback="- No explicit selector requirements parsed.")
    return (
        "Primary Route Requirements:\n"
        f"{route_block}\n\n"
        "Required Selectors:\n"
        f"{selector_block}\n\n"
        "Acceptance Criteria Summary:\n"
        f"{acceptance}"
    )


def _is_visual_quality_only_story(user_story: str) -> bool:
    normalized = user_story.lower()
    has_visual_words = bool(
        re.search(r"\b(pixel|spacing|alignment|visual|look|feel|polish|theme|color|typography|layout)\b", normalized)
    )
    has_deterministicable = bool(
        re.search(r"\b(route|selector|form|validation|aria|keyboard|onpush|inject|signal|test|build)\b", normalized)
    )
    return has_visual_words and not has_deterministicable


def _should_force_llm_validator(state: AgentStateDict, deterministic: DeterministicValidationResult) -> bool:
    required_selectors = extract_required_shared_ui_selectors(state["userStory"])
    complex_selector_story = len(required_selectors) >= 12
    accessibility_heavy = bool(re.search(r"\baria|accessib|keyboard|screen reader\b", state["userStory"], flags=re.IGNORECASE))
    visual_only = _is_visual_quality_only_story(state["userStory"])
    previous_feature_miss = bool(
        re.search(r"\bfeature-level\b", state.get("validationFeedback", ""), flags=re.IGNORECASE)
    )
    if complex_selector_story or accessibility_heavy or visual_only or previous_feature_miss:
        return True
    return deterministic.confidence < VALIDATOR_HYBRID_CONFIDENCE_THRESHOLD


def _build_developer_task_prompt(state: AgentStateDict, *, model: str) -> str:
    attempt = int(state.get("developerAttemptInCycle", 0)) + 1
    is_retry = attempt > 1
    execution_brief = _build_execution_brief_for_state(state)
    requirement_summary = _build_requirement_summary(state)
    validation_feedback_prompt = truncate_prompt_text(
        state["validationFeedback"] or "None. This is the first attempt.",
        PROMPT_VALIDATION_FEEDBACK_MAX_CHARS,
    )
    unresolved = extract_unresolved_criteria_from_feedback(validation_feedback_prompt)
    unresolved_block = _format_bullets(unresolved, fallback="- None")
    deterministic_block = _format_bullets(state.get("deterministicViolations", []), fallback="- None")
    changed_files_summary = state.get("retryChangedFilesSummary", "").strip() or "- No file change summary available yet."

    include_execution_brief = (
        (attempt == 1 and RETRY_INCLUDE_FULL_WORKORDER_ON_FIRST_ATTEMPT)
        or (not unresolved and state.get("deterministicConfidence", 0.0) < VALIDATOR_HYBRID_CONFIDENCE_THRESHOLD)
        or (not RETRY_DELTA_ONLY)
        or (not is_retry)
    )

    blocks: list[BudgetBlock] = [
        BudgetBlock(
            key="developer_task_instruction",
            title="Task",
            content="Implement the feature, write code, and run `npm run build` until it succeeds with zero Angular warnings.",
            required=True,
            priority=1,
        ),
        BudgetBlock(
            key="developer_requirement_summary",
            title="Requirement Summary",
            content=requirement_summary,
            required=True,
            priority=2,
        ),
        BudgetBlock(
            key="developer_unresolved",
            title="Unresolved Criteria",
            content=unresolved_block,
            required=True,
            priority=3,
        ),
    ]
    if RETRY_DELTA_ONLY and is_retry:
        blocks.extend(
            [
                BudgetBlock(
                    key="developer_retry_mode",
                    title="Developer Retry Delta Mode",
                    content="Apply minimal targeted edits. Keep correct code unchanged.",
                    required=True,
                    priority=1,
                ),
                BudgetBlock(
                    key="developer_retry_violations",
                    title="Deterministic Violations (latest)",
                    content=deterministic_block,
                    required=True,
                    priority=3,
                ),
                BudgetBlock(
                    key="developer_retry_changed_files",
                    title="Changed Files Summary",
                    content=changed_files_summary,
                    required=True,
                    priority=3,
                ),
            ]
        )
        if include_execution_brief:
            blocks.append(
                BudgetBlock(
                    key="developer_execution_brief_retry",
                    title="Execution Brief (compact re-include)",
                    content=execution_brief,
                    required=False,
                    priority=2,
                )
            )
    else:
        blocks.extend(
            [
                BudgetBlock(
                    key="developer_execution_brief",
                    title="Execution Brief",
                    content=execution_brief,
                    required=True,
                    priority=1,
                ),
                BudgetBlock(
                    key="developer_validation_feedback",
                    title="Feedback from Validator (if any)",
                    content=validation_feedback_prompt,
                    required=False,
                    priority=4,
                ),
            ]
        )

    return allocate_blocks(blocks=blocks, role="developer", model=model)


def _build_validator_task_prompt(state: AgentStateDict, deterministic: DeterministicValidationResult, *, model: str) -> str:
    execution_brief = _build_execution_brief_for_state(state)
    acceptance_excerpt = _build_acceptance_excerpt_for_state(state)
    unresolved = extract_unresolved_criteria_from_feedback(state.get("validationFeedback", ""))
    unresolved_block = _format_bullets(unresolved, fallback="- None")
    deterministic_delta = _format_bullets(deterministic.violations, fallback="- None")
    changed_files_summary = state.get("retryChangedFilesSummary", "").strip() or "- No file change summary available."
    is_retry = int(state.get("developerAttemptInCycle", 0)) > 1

    blocks: list[BudgetBlock] = [
        BudgetBlock(
            key="validator_task_instruction",
            title="Task",
            content='Run tests and code review. Reply with exactly "PASS" if all criteria are met, else return a focused failure report.',
            required=True,
            priority=1,
        ),
        BudgetBlock(
            key="validator_execution_brief",
            title="Execution Brief",
            content=execution_brief,
            required=True,
            priority=1,
        ),
        BudgetBlock(
            key="validator_acceptance",
            title="Acceptance Criteria Excerpt",
            content=acceptance_excerpt,
            required=True,
            priority=2,
        ),
    ]
    if RETRY_DELTA_ONLY and is_retry:
        blocks.extend(
            [
                BudgetBlock(
                    key="validator_retry_mode",
                    title="Validator Retry Delta Mode",
                    content="Focus on unresolved criteria and recent file changes.",
                    required=True,
                    priority=1,
                ),
                BudgetBlock(
                    key="validator_deterministic_delta",
                    title="Deterministic Violations Delta",
                    content=deterministic_delta,
                    required=True,
                    priority=3,
                ),
                BudgetBlock(
                    key="validator_changed_files",
                    title="Changed Files Summary",
                    content=changed_files_summary,
                    required=True,
                    priority=3,
                ),
                BudgetBlock(
                    key="validator_unresolved",
                    title="Unresolved Criteria",
                    content=unresolved_block,
                    required=True,
                    priority=3,
                ),
            ]
        )
    else:
        blocks.append(
            BudgetBlock(
                key="validator_deterministic_conf",
                title="Deterministic Coverage Summary",
                content=f"- confidence: {deterministic.confidence}",
                required=True,
                priority=3,
            )
        )
    return allocate_blocks(blocks=blocks, role="validator", model=model)


def _developer_node(state: AgentStateDict, human_message_cls, system_message_cls) -> dict[str, object]:
    attempt = int(state.get("developerAttemptInCycle", 0)) + 1
    print(f"\n--- DEVELOPMENT AGENT (Iteration {state['iterations'] + 1}, Attempt {attempt}) ---")
    is_deterministic_retry = bool(
        re.match(r"^Deterministic validator checks FAILED\.", state.get("validationFeedback", "").strip())
    )
    dev_recursion_limit = 320 if is_deterministic_retry else 220
    retry_focus_instructions = (
        "\nRETRY MODE:\n"
        "- Use deterministic violations, changed-file summary, and unresolved criteria as the primary fix set.\n"
        "- Apply minimal edits first.\n"
        "- Re-run `npm run build` after each focused change."
        if attempt > 1
        else ""
    )

    selected_llm, selected_model, _ = _get_role_llm(state, "developer")
    system_prompt = build_developer_system_prompt(state, retry_focus_instructions, model=selected_model)
    task_prompt = _build_developer_task_prompt(state, model=selected_model)
    tools = build_langchain_tools(target_dir=TARGET_DIR)

    def _invoke_with_llm(llm, prompt_text: str):
        dev_agent = _create_react_agent_compat(
            llm=llm,
            tools=tools,
            message_modifier=system_message_cls(content=prompt_text),
        )
        _invoke_agent_compat(dev_agent, {"messages": [human_message_cls(content=task_prompt)]}, dev_recursion_limit)

    try:
        _invoke_with_llm(selected_llm, system_prompt)
    except Exception:
        base_model = get_base_model_for_role("developer")
        if selected_model == base_model:
            raise
        fallback_llm, _, _ = _get_role_llm(state, "developer", force_base=True)
        fallback_prompt = build_developer_system_prompt(state, retry_focus_instructions, model=base_model)
        task_prompt = _build_developer_task_prompt(state, model=base_model)
        _invoke_with_llm(fallback_llm, fallback_prompt)

    print("Development Complete.")
    return {"iterations": 1, "developerAttemptInCycle": attempt}


def _validator_node(state: AgentStateDict, human_message_cls, system_message_cls) -> dict[str, object]:
    print("\n--- VALIDATION AGENT ---")
    deterministic = run_deterministic_validation_checks(
        user_story=state["userStory"],
        work_order=state["workOrder"],
        run_id=state.get("lastRunId", ""),
        target_dir=TARGET_DIR,
    )

    deterministic_update: dict[str, object] = {
        "deterministicViolations": deterministic.violations,
        "deterministicCoverage": deterministic.coverage,
        "deterministicConfidence": deterministic.confidence,
    }
    if not deterministic.ok:
        LAST_VALIDATION_PATH.write_text(deterministic.report, encoding="utf-8")
        preview = deterministic.report[:6000] + ("\n...[truncated]" if len(deterministic.report) > 6000 else "")
        print(f"Validator Feedback (Deterministic):\n{preview}")
        print("Validation Complete.")
        deterministic_update.update(
            {
                "validationFeedback": deterministic.report,
                "validatorFailureStreak": int(state.get("validatorFailureStreak", 0)) + 1,
            }
        )
        return deterministic_update

    print(deterministic.report)

    if not _should_force_llm_validator(state, deterministic):
        LAST_VALIDATION_PATH.write_text("PASS\n", encoding="utf-8")
        print("Validator Gate: deterministic confidence high, LLM validator skipped.")
        print("Validation Complete.")
        deterministic_update.update({"validationFeedback": "PASS", "validatorFailureStreak": 0})
        return deterministic_update

    selected_llm, selected_model, _ = _get_role_llm(state, "validator")
    system_prompt = build_validator_system_prompt(state, model=selected_model)
    task_prompt = _build_validator_task_prompt(state, deterministic, model=selected_model)
    tools = build_langchain_tools(target_dir=TARGET_DIR)

    def _invoke_with_llm(llm, prompt_text: str):
        val_agent = _create_react_agent_compat(
            llm=llm,
            tools=tools,
            message_modifier=system_message_cls(content=prompt_text),
        )
        return _invoke_agent_compat(val_agent, {"messages": [human_message_cls(content=task_prompt)]}, 150)

    try:
        response = _invoke_with_llm(selected_llm, system_prompt)
    except Exception:
        base_model = get_base_model_for_role("validator")
        if selected_model == base_model:
            raise
        fallback_llm, _, _ = _get_role_llm(state, "validator", force_base=True)
        fallback_prompt = build_validator_system_prompt(state, model=base_model)
        task_prompt = _build_validator_task_prompt(state, deterministic, model=base_model)
        response = _invoke_with_llm(fallback_llm, fallback_prompt)

    raw_final_message = _extract_final_message_content(response)
    normalized = normalize_validator_feedback(raw_final_message, target_dir=TARGET_DIR)

    if normalized.warning:
        print(normalized.warning)

    LAST_VALIDATION_PATH.write_text(normalized.normalized, encoding="utf-8")
    if normalized.normalized == "PASS":
        print("Validator Result: PASS")
        next_streak = 0
    else:
        preview = normalized.normalized[:4000] + ("\n...[truncated]" if len(normalized.normalized) > 4000 else "")
        print(f"Validator Feedback:\n{preview}")
        next_streak = int(state.get("validatorFailureStreak", 0)) + 1
    print("Validation Complete.")
    deterministic_update.update(
        {
            "validationFeedback": normalized.normalized,
            "validatorFailureStreak": next_streak,
        }
    )
    return deterministic_update


def _should_continue(state: AgentStateDict) -> Literal["developer", "END"]:
    if state["validationFeedback"].strip() == "PASS":
        print("\nWorkflow Complete! App is ready.")
        return "END"
    max_iterations = get_max_workflow_iterations(state)
    if state["iterations"] >= max_iterations:
        print("\nMax iterations reached. Stopping.")
        return "END"
    print("\nValidation failed. Routing back to Developer...")
    return "developer"


def run_full_workflow() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required. Set it in orchestrator_py/.env or orchestrator/.env.")

    _ensure_langchain_runtime()
    from langchain_core.messages import HumanMessage, SystemMessage

    setup_project(target_dir=TARGET_DIR)
    run_id = start_run()
    set_active_run_id(run_id)
    print(f"Run ID: {run_id}")

    user_story = truncate_prompt_text(USER_STORY_PATH.read_text(encoding="utf-8"), PROMPT_USER_STORY_MAX_CHARS)
    retrieval_sources = build_retrieval_sources()
    retrieval_source_map = {source.source_id: source for source in retrieval_sources}
    retrieval_cards = build_card_index(retrieval_sources)

    role_contexts: dict[Role, str] = {"planner": "", "developer": "", "validator": ""}
    if RETRIEVAL_ENABLED:
        for role in ("planner", "developer", "validator"):
            result: RetrievalResult = retrieve_context_for_role(
                role=role,
                user_story=user_story,
                cards=retrieval_cards,
                source_map=retrieval_source_map,
                max_chars=RETRIEVAL_MAX_CHARS[role],
            )
            role_contexts[role] = result.context
            print(
                f"Context retrieval [{role}]: selected={len(result.selected_card_ids)} "
                f"dropped={len(result.dropped_card_ids)} truncated={result.truncated}"
            )

    rule_catalog = load_rule_catalog(catalog_path=RULE_CATALOG_PATH)
    role_rules: dict[Role, str] = {}
    for role in ("planner", "developer", "validator"):
        selected = select_rule_cards_for_role(
            role=role,
            rules=rule_catalog,
            user_story=user_story,
            max_count=RULE_MAX_COUNT[role],
        )
        role_rules[role] = render_rule_context(selected_rules=selected)

    angular_version_context = build_angular_version_context(TARGET_DIR / "package.json")

    state: AgentStateDict = {
        "userStory": user_story,
        "plannerContext": role_contexts["planner"],
        "developerContext": role_contexts["developer"],
        "validatorContext": role_contexts["validator"],
        "plannerRules": role_rules["planner"],
        "developerRules": role_rules["developer"],
        "validatorRules": role_rules["validator"],
        "angularVersionContext": angular_version_context,
        "workOrder": "",
        "workOrderDataJson": "",
        "workOrderFormat": "markdown",
        "validationFeedback": "",
        "deterministicViolations": [],
        "deterministicCoverage": {},
        "deterministicConfidence": 0.0,
        "retryChangedFilesSummary": "",
        "developerAttemptInCycle": 0,
        "plannerStructuredFailures": 0,
        "validatorFailureStreak": 0,
        "lastRunId": run_id,
        "iterations": 0,
    }

    print("\nStarting Agentic Workflow...")

    state.update(_planner_node(state, SystemMessage))
    previous_snapshot = snapshot_files_hashes(
        root=TARGET_DIR / "src" / "app",
        relative_prefix=TARGET_DIR,
    )
    while True:
        dev_update = _developer_node(state, HumanMessage, SystemMessage)
        state["iterations"] += int(dev_update.get("iterations", 0))
        state.update({key: value for key, value in dev_update.items() if key != "iterations"})

        current_snapshot = snapshot_files_hashes(
            root=TARGET_DIR / "src" / "app",
            relative_prefix=TARGET_DIR,
        )
        state["retryChangedFilesSummary"] = summarize_changed_files(
            previous_snapshot=previous_snapshot,
            current_snapshot=current_snapshot,
            max_files=30,
        )
        previous_snapshot = current_snapshot

        state.update(_validator_node(state, HumanMessage, SystemMessage))
        if _should_continue(state) == "END":
            break

    print("\n--- TOKEN USAGE ---")
    print(f"Prompt Tokens:     {TOKENS.prompt_tokens}")
    print(f"Completion Tokens: {TOKENS.completion_tokens}")
    print(f"Total Tokens:      {TOKENS.total_tokens}")


def run_self_test() -> None:
    print("Running orchestrator_py self-test (piecewise, no full workflow)...")
    try:
        from orchestrator_py.log_store import LOG_ROOT, LogStoreError, append_command_log, list_command_logs as list_logs, read_command_log as read_log
    except ModuleNotFoundError:
        from log_store import LOG_ROOT, LogStoreError, append_command_log, list_command_logs as list_logs, read_command_log as read_log

    assert "ng serve" in (reject_unsafe_agent_command("ng serve") or "")
    assert "watch-mode" in (reject_unsafe_agent_command("npm run test -- --watch") or "")
    assert reject_unsafe_agent_command("npm run build") is None

    selectors = extract_required_shared_ui_selectors("Use `app-menu`, `app-card`, and `app-card`.")
    assert selectors == ["app-dropdown-menu", "app-card"], selectors
    routes = extract_explicit_route_data_points("Feature route should be `/demo`. Default route redirected to /demo.")
    assert routes == ["/demo"], routes

    quality_issues = validate_work_order_quality("Create a page with form and validation", "# Foo\n## Bar\n")
    assert any("Feature Name & Goal" in issue for issue in quality_issues)
    assert any("Acceptance Criteria" in issue for issue in quality_issues)

    loaded_rules = load_rule_catalog(catalog_path=RULE_CATALOG_PATH)
    assert any(rule.id == "PLANNER_WORK_ORDER_HEADINGS" for rule in loaded_rules)
    assert any("developer" in rule.roles for rule in loaded_rules)

    with tempfile.TemporaryDirectory(prefix="orchestrator_py_retrieval_") as tmp:
        tmp_dir = Path(tmp)
        form_doc = tmp_dir / "form.md"
        selector_doc = tmp_dir / "selectors.md"
        compat_doc = tmp_dir / "compat.md"
        form_doc.write_text("# Form Guidance\nUse reactive form validators and submit handling.\n", encoding="utf-8")
        selector_doc.write_text("# Selector Guidance\nEnsure required app-card and app-button selectors are present.\n", encoding="utf-8")
        compat_doc.write_text("# Compatibility\nAngular v20/v21 compatibility notes.\n", encoding="utf-8")

        sources = [
            SourceDocument("FORM_DOC", form_doc, tags=("form", "validation")),
            SourceDocument("SELECTOR_DOC", selector_doc, tags=("selectors", "shared-ui")),
            SourceDocument("VERSION_COMPAT", compat_doc, tags=("angular-version",), mandatory_for=("developer",)),
        ]
        cards = build_card_index(sources)
        source_map = {source.source_id: source for source in sources}

        form_result = retrieve_context_for_role(
            role="developer",
            user_story="Build a form with validation and submit behavior.",
            cards=cards,
            source_map=source_map,
            max_chars=2400,
        )
        selector_result = retrieve_context_for_role(
            role="developer",
            user_story="Use required selectors app-card and app-button in templates.",
            cards=cards,
            source_map=source_map,
            max_chars=2400,
        )
        assert any(card_id.startswith("FORM_DOC_") for card_id in form_result.selected_card_ids)
        assert any(card_id.startswith("SELECTOR_DOC_") for card_id in selector_result.selected_card_ids)

    valid_contract_payload = {
        "feature_name": "Demo Feature",
        "feature_goal": "Deliver a demo feature.",
        "assumptions": ["Mock data only"],
        "user_story_data_points": {
            "routes": ["/demo"],
            "selectors": ["app-card"],
            "fields": ["title"],
            "constraints": ["title required"],
            "options": ["All", "Active", "Completed"],
            "limits": ["title max 80"],
        },
        "requirement_traceability": [
            {
                "requirement": "Route setup",
                "tasks": ["Add route"],
                "acceptance_criteria": ["Route is reachable"],
            }
        ],
        "file_structure": ["src/app/features/demo/demo.component.ts"],
        "state_management": ["Use signal and computed."],
        "form_model_validation": ["Typed FormControl with Validators.required."],
        "ui_ux_requirements": ["Use app-card and Tailwind utilities."],
        "template_pattern_references": ["layout-page-shell-header-toolbar"],
        "deviation_notes": "",
        "acceptance_criteria": ["Route works", "Build passes"],
    }
    contract = validate_work_order_contract(valid_contract_payload)
    assert render_work_order_markdown(contract) == render_work_order_markdown(contract)
    try:
        validate_work_order_contract({"feature_name": "Invalid"})
        raise AssertionError("Expected schema validation to fail for incomplete contract.")
    except Exception:
        pass

    assert resolve_work_order_mode_after_structured_failure("dual") == "markdown"
    assert resolve_work_order_mode_after_structured_failure("strict") == "strict_error"

    # Token allocator required-first behavior
    blocks = [
        BudgetBlock(key="required", title="Required", content="must-keep", required=True, priority=1),
        BudgetBlock(
            key="optional_low",
            title="OptionalLow",
            content="\n".join(f"line-{i}" for i in range(20000)),
            required=False,
            priority=999,
        ),
    ]
    allocated = allocate_blocks(blocks=blocks, role="validator", model=DEFAULT_MODEL)
    assert "Required" in allocated

    # Model routing escalation
    assert get_model_for_role(role="planner", planner_structured_failures=0, validator_failure_streak=0).escalated is False
    assert get_model_for_role(role="planner", planner_structured_failures=99, validator_failure_streak=0).escalated is True
    assert get_model_for_role(role="validator", planner_structured_failures=0, validator_failure_streak=99).escalated is True

    # Changed files summary add/modify/delete
    changed_summary = summarize_changed_files(
        previous_snapshot={"src/app/a.ts": "1", "src/app/b.ts": "2"},
        current_snapshot={"src/app/a.ts": "9", "src/app/c.ts": "3"},
    )
    assert "added: src/app/c.ts" in changed_summary
    assert "modified: src/app/a.ts" in changed_summary
    assert "deleted: src/app/b.ts" in changed_summary

    run_id = start_run()
    set_active_run_id(run_id)
    log_meta = append_command_log(
        run_id=run_id,
        command="echo hi",
        cwd=REPO_ROOT,
        exit_code=0,
        stdout="hi",
        stderr="",
    )
    assert log_meta.get("logId")
    records = list_logs(run_id=run_id)
    assert any(record.get("logId") == log_meta.get("logId") for record in records)
    read_back = read_log(log_id=str(log_meta.get("logId")), run_id=run_id, tail_lines=20)
    assert "echo hi" in read_back and "hi" in read_back

    # Path traversal guard for log reads
    outside_file = (Path(tempfile.gettempdir()) / "orchestrator_py_outside.log").resolve()
    outside_file.write_text("outside\n", encoding="utf-8")
    malicious_index = [
        {
            "logId": "evil",
            "file": str(outside_file),
            "command": "malicious",
            "exitCode": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]
    index_path = LOG_ROOT / run_id / "commands" / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(malicious_index), encoding="utf-8")
    try:
        read_log(log_id="evil", run_id=run_id, tail_lines=10)
        raise AssertionError("Expected traversal guard to reject outside log path")
    except LogStoreError:
        pass

    with tempfile.TemporaryDirectory(prefix="orchestrator_py_tools_") as tmp:
        tmp_dir = Path(tmp)
        assert "Successfully wrote" in write_code("src/test.txt", "hello", target_dir=tmp_dir)
        assert read_file("src/test.txt", target_dir=tmp_dir) == "hello"
        cmd_result = run_command('python -c "print(\'ok\')"', target_dir=tmp_dir)
        assert "Command succeeded" in cmd_result and "id=" in cmd_result

    with tempfile.TemporaryDirectory(prefix="orchestrator_py_deterministic_") as tmp:
        fake_target = Path(tmp)
        (fake_target / "src" / "app" / "features" / "demo").mkdir(parents=True, exist_ok=True)
        (fake_target / "src" / "app" / "shared" / "ui").mkdir(parents=True, exist_ok=True)
        (fake_target / "src" / "app" / "shared" / "ui" / "index.ts").write_text(
            "export * from './radio-group/radio-group.component';\n"
            "export * from './card/card.component';\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "app.html").write_text("<router-outlet />\n", encoding="utf-8")
        (fake_target / "src" / "app" / "app.ts").write_text("export class App {}\n", encoding="utf-8")
        (fake_target / "src" / "app" / "app.routes.ts").write_text(
            "export const routes = [\n"
            "  { path: '', redirectTo: 'demo', pathMatch: 'full' },\n"
            "  { path: 'demo', loadComponent: () => import('./features/demo/demo.component').then(m => m.DemoComponent) },\n"
            "];\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.ts").write_text(
            "import { ChangeDetectionStrategy, Component } from '@angular/core';\n"
            "import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';\n"
            "@Component({ selector: 'app-demo', imports: [ReactiveFormsModule], templateUrl: './demo.component.html', "
            "styleUrl: './demo.component.css', changeDetection: ChangeDetectionStrategy.OnPush })\n"
            "export class DemoComponent { readonly form = new FormGroup({ type: new FormControl('', { nonNullable: true, validators: [Validators.required] }) }); }\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.html").write_text(
            "<main>\n"
            "  <form>\n"
            "    <app-radio-group aria-label=\"Type\" [value]=\"form.controls.type.value\" (valueChange)=\"form.controls.type.setValue($event)\"></app-radio-group>\n"
            "    <div>touched errors invalid submitted required</div>\n"
            "    <button type=\"submit\" [disabled]=\"form.invalid\">Submit</button>\n"
            "  </form>\n"
            "</main>\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.css").write_text("", encoding="utf-8")
        (fake_target / "src" / "app" / "app.spec.ts").write_text(
            "import { TestBed } from '@angular/core/testing';\n"
            "import { App } from './app';\n"
            "describe('App', () => { beforeEach(async () => { await TestBed.configureTestingModule({ imports: [App] }).compileComponents(); }); });\n",
            encoding="utf-8",
        )

        def fake_runner(command: str) -> DeterministicCommandResult:
            return DeterministicCommandResult(command=command, ok=True, output="OK")

        pass_result = run_deterministic_validation_checks(
            user_story="Feature route should be /demo. Use a form with validation and error messages. Required selector: `app-radio-group`.",
            work_order="Reactive form validation plan for /demo with app-radio-group and error messages.",
            run_id=run_id,
            target_dir=fake_target,
            command_runner=fake_runner,
        )
        assert pass_result.ok, pass_result.report
        assert pass_result.confidence > 0.8

        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.html").write_text(
            "<form><button type=\"submit\">Submit</button><div *ngIf=\"true\">x</div></form>\n",
            encoding="utf-8",
        )
        fail_result = run_deterministic_validation_checks(
            user_story="Feature route should be /demo.",
            work_order="Feature route should be /demo.",
            run_id=run_id,
            target_dir=fake_target,
            command_runner=fake_runner,
        )
        assert not fail_result.ok
        assert fail_result.confidence == 0.0

        false_positive_text = (
            "shared ui component files are missing:\n"
            "- src/app/shared/ui/app-card/app-card.component.ts\n"
        )
        normalized = normalize_validator_feedback(false_positive_text, target_dir=fake_target)
        assert normalized.normalized == "PASS"

    fake_state: AgentStateDict = {
        "userStory": "Build /demo route with app-card selector and form validation.",
        "plannerContext": "",
        "developerContext": "",
        "validatorContext": "",
        "plannerRules": "",
        "developerRules": "",
        "validatorRules": "",
        "angularVersionContext": "",
        "workOrder": "Work order body",
        "workOrderDataJson": "",
        "workOrderFormat": "markdown",
        "validationFeedback": "- Missing route redirect\n- Missing selector usage",
        "deterministicViolations": ["src/app/app.routes.ts:1 - missing redirect"],
        "deterministicCoverage": {"routing": False},
        "deterministicConfidence": 0.95,
        "retryChangedFilesSummary": "- modified: src/app/app.routes.ts [routing]",
        "developerAttemptInCycle": 1,
        "plannerStructuredFailures": 0,
        "validatorFailureStreak": 0,
        "lastRunId": run_id,
        "iterations": 1,
    }
    retry_prompt = _build_developer_task_prompt(fake_state, model=DEFAULT_MODEL)
    assert "Developer Retry Delta Mode" in retry_prompt
    assert "Work order body" not in retry_prompt
    assert "Changed Files Summary" in retry_prompt

    # Hybrid gate decisions
    assert _should_force_llm_validator(
        fake_state,
        DeterministicValidationResult(
            ok=True,
            report="",
            violations=[],
            coverage={"routing": True},
            confidence=0.95,
        ),
    ) is False
    assert _should_force_llm_validator(
        fake_state,
        DeterministicValidationResult(
            ok=True,
            report="",
            violations=[],
            coverage={"routing": True},
            confidence=0.2,
        ),
    ) is True
    selector_heavy_story = " ".join(f"`app-x-{i}`" for i in range(13))
    selector_state = dict(fake_state)
    selector_state["userStory"] = selector_heavy_story
    assert _should_force_llm_validator(
        selector_state,  # type: ignore[arg-type]
        DeterministicValidationResult(ok=True, report="", violations=[], coverage={"routing": True}, confidence=0.99),
    ) is True

    angular_context = build_angular_version_context(TEMPLATE_DIR / "package.json")
    assert "Angular target" in angular_context
    retrieval_sources = build_retrieval_sources()
    retrieval_cards = build_card_index(retrieval_sources)
    retrieval_source_map = {source.source_id: source for source in retrieval_sources}
    planner_context = retrieve_context_for_role(
        role="planner",
        user_story="Build a form-heavy page with routing.",
        cards=retrieval_cards,
        source_map=retrieval_source_map,
        max_chars=RETRIEVAL_MAX_CHARS["planner"],
    ).context
    assert isinstance(planner_context, str) and len(planner_context) > 0

    print("Self-test checks passed:")
    print("- command safety guards")
    print("- retrieval/rule/schema/renderer basics")
    print("- token-budget allocator required-first behavior")
    print("- model router escalation behavior")
    print("- delta-only retry prompt builder")
    print("- changed-file summary add/modify/delete")
    print("- disk log store write/list/read + traversal guard")
    print("- run_command compact diagnostics with log id/path")
    print("- deterministic checks confidence + failure behavior")
    print("- hybrid validator gate decision logic")
    print("orchestrator_py self-test: PASS")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python port of the Angular agentic orchestrator (matches Node orchestrator flow)."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run piecewise smoke tests only (no OpenAI calls, no full workflow).",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only run template setup (clone template to generated-app + npm install), then exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        load_dotenv()
        if args.self_test:
            run_self_test()
            return 0
        if args.setup_only:
            setup_project(target_dir=TARGET_DIR)
            return 0
        run_full_workflow()
        return 0
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

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
from typing import Callable, Literal, TypedDict

try:
    from orchestrator_py.tools import (
        TARGET_DIR,
        build_langchain_tools,
        read_file,
        reject_unsafe_agent_command,
        run_command,
        write_code,
    )
except ModuleNotFoundError:  # Allows `python orchestrator_py/index.py`
    from tools import TARGET_DIR, build_langchain_tools, read_file, reject_unsafe_agent_command, run_command, write_code


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
LAST_VALIDATION_PATH = (PY_ORCHESTRATOR_DIR / "last-validation-feedback.md").resolve()

TEMPLATE_COPY_IGNORES = {"node_modules", "dist", ".angular", ".git"}
DEFAULT_MODEL = "gpt-4.1-nano"
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


PLANNER_RULES_BLOCK = """Create a detailed Work Order (Markdown) for the Development Agent following the Vertical Slicing Architecture.
Include File Structure, State Management, UI/UX Requirements, and Acceptance Criteria.
WORK ORDER STRUCTURE RULE (required headings):
- Feature Name & Goal
- User Story Data Points (extract exact routes, field lists/options, required selectors, validation rules, and acceptance-critical constraints from the user story)
- Requirement Traceability (map each user-story requirement/data point to implementation tasks + acceptance criteria)
- File Structure
- State Management
- Form Model & Validation (when applicable)
- UI/UX Requirements
- Acceptance Criteria
TEMPLATE PATTERN RULE: For form/layout-heavy features, the Work Order 'UI/UX Requirements' section MUST include a 'Template Pattern References:' line citing selected pattern IDs from the template docs catalog (for example 'layout-page-shell-header-toolbar', 'form-mixed-controls-create-edit').
TEMPLATE PATTERN RULE: If no catalog pattern fits, include 'Template Pattern References: none' and a 'Deviation Notes:' line explaining why.
DATA FIDELITY RULE: All concrete data points (routes, field names, options, limits, required selectors, validation requirements) must come from the user story unless explicitly marked as an assumption.
ASSUMPTION RULE: If you add any assumption, place it in a short "Assumptions" section and label each assumption clearly.
CRITICAL: Explicitly instruct the Developer to overwrite 'src/app/app.html' and 'src/app/app.routes.ts' so the new feature is the default view and the Angular boilerplate is removed.
CRITICAL UI RULE: You MUST utilize the pre-built UI components located in 'src/app/shared/ui/' whenever these patterns are needed. Do not instruct the developer to build these from scratch.
CRITICAL UI RULE: Before listing custom UI work, require the Developer to inspect 'src/app/shared/ui/index.ts' and the top usage comments in the selected shared UI component files.
CRITICAL IMPORT RULE: The template supports the TypeScript path alias 'src/*'. Prefer shared UI barrel imports from 'src/app/shared/ui' unless a relative import is clearer.
TEMPLATE-FIRST RULE: If a likely reusable issue is identified (template config, shared UI component behavior, boilerplate app shell issue, path alias/import problem), call it out as a Template/Agent-level issue in the Work Order/notes so it can be fixed upstream.
SCOPE RULE: Do NOT add new mandatory tools/process requirements (e.g., AXE, Playwright, Lighthouse, e2e suites) unless the user story explicitly requires them.
FORM RULE: If the user story is form-centric, you MUST include a typed Reactive Forms schema, a field-by-field validation matrix (required/min/max/pattern/custom), validation message behavior (when errors appear), submit/disable rules, and the exact shared-ui control binding strategy for non-CVA controls.
PATTERN SELECTION RULE: Use the template pattern catalog in 'automate-angular-template/docs/agent-patterns/' to choose one primary 'layout-*' pattern and 0-2 'form-*' patterns before proposing custom UI structure.
SHARED UI COVERAGE RULE: If the user story lists specific 'app-*' selectors, include a checklist in the Work Order mapping every listed selector to a concrete feature location/interaction.
SHARED UI COVERAGE IMPLEMENTATION TIP: If the selector list is long, explicitly plan a "Shared UI Coverage" section/panel in the feature so every required component is demonstrated meaningfully without cluttering the primary form path.
You MUST explicitly list the exact shared UI imports/selectors the Developer should use (e.g., app-card, app-button, app-tabs, app-select, app-text-input, app-checkbox, app-empty-state, app-icon)."""

DEVELOPER_RULES_BLOCK_PREFIX = """You are the Development Agent (The Engineer).
Your job is to execute the Work Order by writing code and ensuring the app compiles.
You MUST use the provided tools to write files and run 'npm run build'.
Do not stop until 'npm run build' succeeds with ZERO errors and ZERO warnings (e.g., fix NG8103 warnings by using @for).
Before coding, use read_file to inspect:
1) 'src/app/shared/ui/index.ts'
2) The shared UI component files you plan to use (read the top usage comments)
3) 'src/app/app.ts', 'src/app/app.html', 'src/app/app.routes.ts', and 'src/app/app.spec.ts'
4) If the Work Order cites pattern IDs, read 'automate-angular-template/docs/agent-patterns/README.md' and the cited pattern docs in 'forms-core.md' / 'layouts-core.md'

CRITICAL ROUTING RULE:
You MUST overwrite 'src/app/app.html' to remove the default Angular boilerplate and replace it with your own layout or just '<router-outlet />'.
You MUST update 'src/app/app.routes.ts' to set the default route (path: '') to redirect to your new feature, or load your feature directly. The main page of the feature MUST be the first page to appear.
You MUST update 'src/app/app.ts' to remove 'NgOptimizedImage' from the imports array if you are no longer using it in 'app.html'.
You MUST update 'src/app/app.spec.ts' to remove the test that checks for the 'h1' element, and ensure there are no duplicate 'imports' keys in 'TestBed.configureTestingModule'. Also, ensure 'App' is in 'imports' and NOT in 'declarations' since it is a standalone component.
NEVER use '[(ngModel)]' or Template-driven forms. ALWAYS use Reactive Forms ('FormControl', 'FormGroup', 'ReactiveFormsModule').
CRITICAL ANGULAR RULES (hard validation failures):
- Use 'ChangeDetectionStrategy.OnPush' on all new components.
- Use 'inject()' instead of constructor injection.
- Use 'input()', 'output()', and 'model()' instead of '@Input()' and '@Output()' decorators.
- Use Signals ('signal', 'computed') for feature state. Do not store core feature state as plain mutable class fields.
- Use native control flow (@if/@for/@switch). Do not use *ngIf/*ngFor.
CRITICAL UI RULE: You MUST use the pre-built UI components in 'src/app/shared/ui/' instead of building custom versions for covered patterns.
Prefer: <app-card>, <app-button>, <app-badge>, <app-tabs>, <app-select>, <app-text-input>, <app-textarea>, <app-checkbox>, <app-empty-state>, <app-icon>.
SHARED UI COVERAGE RULE: If the Work Order/user story lists required selectors, you MUST track them and ensure each one appears in the feature templates at least once.
SHARED UI COVERAGE IMPLEMENTATION TIP: For large selector lists, create a dedicated "UI coverage/demo" section using realistic mock content so all required components are present while keeping the main form usable.
TEMPLATE PATTERN IMPLEMENTATION RULE: If the Work Order includes 'Template Pattern References', follow the cited pattern skeletons and shared UI composition maps first. Only deviate if the Work Order includes a justified 'Deviation Notes' explanation.
TAILWIND RULE: Style feature UIs with Tailwind utility classes in templates. Do NOT recreate Tailwind utilities in feature component CSS (e.g., '.container', '.grid', '.grid-cols-*', '.flex').
TAILWIND RULE: Keep feature component CSS empty/minimal unless there is a justified non-utility styling need.
TEMPLATE EXPRESSION RULE: Do NOT use inline arrow functions in templates. Do NOT invent complex inline object/function literals for component APIs when the shape is non-trivial; define typed arrays/options/config in component TypeScript instead.
API SHAPE RULE: Do not guess shared UI inputs/outputs. Read the component usage comment and component code first, then match the documented API exactly.
CRITICAL IMPORT RULE: Import shared UI components from 'src/app/shared/ui' (barrel import supported by template tsconfig path alias 'src/*'), or use explicit relative imports if you choose not to use the alias.
Do NOT create duplicate files under 'src/app/shared/ui/' for components that already exist in the template.
NOTE: These custom UI components do NOT implement ControlValueAccessor. You CANNOT use 'formControlName' on them. You MUST bind to their model inputs (e.g., '[value]=\"form.controls.myControl.value\" (valueChange)=\"updateControl($event)\"').
FORM VALIDATION RULES (required when the feature includes forms):
- Build a typed Reactive Form ('FormGroup'/'FormControl', '{ nonNullable: true }' where appropriate) and import 'ReactiveFormsModule'.
- Define explicit validators ('Validators.required', 'Validators.email', 'Validators.minLength', custom validators, etc.) according to the Work Order.
- Show validation feedback in the template (error text/hint states) based on 'touched', 'dirty', or submitted state.
- Include inline error messages for multiple fields and a form-level validation summary/alert after submit attempt.
- Disable submit while the form is invalid/pending and surface a success/error result state after submit.
- For shared UI controls without CVA support, create explicit bridge methods between form controls and component 'value'/'valueChange' APIs.
RADIO GROUP RULE: If 'app-radio-group' is in the required selector list, use it in the actual inquiry form flow (not only in a detached coverage/demo section).
IMPORTANT: If the Validator reports issues, fix those exact issues first, rerun build/tests, and then stop.
If the Validator or build output suggests a reusable template/orchestration issue, explicitly state "Template/Agent-level issue" in your response with the file path and root cause.
RUNTIME DI RULE: If you encounter runtime Angular DI errors like 'NG0201 No provider found' from shared UI wrappers (especially Angular Aria wrappers under 'src/app/shared/ui/'), treat it as a likely Template/Agent-level issue. Inspect whether provider/group directives are attached to an internal wrapper instead of the shared component host when children are projected via '<ng-content>'.
TESTING RULE: This workspace uses Vitest. Do NOT use Jasmine-only matchers like toBeTrue()/toBeFalse(); use toBe(true/false) or toBeTruthy()/toBeFalsy().
ANGULAR TEMPLATE RULE: Do NOT use TypeScript 'as' casts inside Angular template expressions/event bindings. Normalize or narrow values in component TypeScript methods instead.
"""

VALIDATOR_RULES_BLOCK = """You are the Validation Agent (The Tester).
Your job is to verify the Developer's output against the Work Order's Acceptance Criteria.
Deterministic prechecks (build/test + rule scans) already passed. You should still inspect the code for semantic correctness.
You MUST use the tools to run 'npm run test -- --watch=false' and read files to check for Zoneless compliance, Signals, and OnPush.
You MUST verify that the Developer reused the pre-built UI components in 'src/app/shared/ui/' where applicable (not only Accordion/Autocomplete/Menu/Select/Tabs, but also Button/Card/Badge/TextInput/Checkbox/etc. when relevant).
CRITICAL SHARED UI PATH RULE: Selectors like '<app-card>' map to component selectors, not necessarily folder names. In this template, '<app-card>' is implemented at 'src/app/shared/ui/card/card.component.ts' (not 'src/app/shared/ui/app-card/app-card.component.ts'). Verify reuse by checking actual imports (preferably from 'src/app/shared/ui') and selector usage, not guessed 'app-*' file paths.
You MUST verify that the Developer implemented ALL features requested in the Work Order (e.g., forms, buttons, lists).
FORM VALIDATION RULE: If the feature is form-centric, verify the code contains a typed Reactive Form model, validators, validation/error UI states, and proper submit handling. For shared UI controls, verify 'value'/'valueChange' bridging is used instead of unsupported 'formControlName'.
SHARED UI COVERAGE RULE: If the user story explicitly lists required 'app-*' selectors, verify each listed selector is present in the feature templates and used meaningfully (not just imported).
TEMPLATE PATTERN RULE: If the Work Order is form/layout-heavy, verify 'UI/UX Requirements' includes 'Template Pattern References' (or 'Template Pattern References: none' plus 'Deviation Notes').
TEMPLATE PATTERN RULE: Check that the implementation broadly reflects the cited pattern IDs, or that any deviation is documented and still satisfies acceptance criteria.
Only fail on requirements that are explicitly REQUIRED by the Work Order / user story.
Do NOT fail the app for "Nice to Have", "Optional", or "Consider adding" items.
Do NOT fail because "information is not provided" if you can read the relevant files with tools. Inspect the actual HTML/CSS/TS before claiming uncertainty.
Do NOT require automated AXE/Lighthouse/Playwright runs unless the user story explicitly requires those exact tools. Validate accessibility by code inspection when automation is not explicitly required.
Do NOT claim missing features unless you inspected the actual HTML/TS and can cite the file path and concrete missing element/logic.
Do NOT fail for zoneless configuration unless you find a concrete violation in code or missing required provider setup explicitly requested by the Work Order.
Do NOT fail solely because a cited template pattern was adapted, if the Work Order documents the deviation and the implementation remains correct.
Classify each failure in your report as either "Feature-level" or "Template/Agent-level". Mark issues as Template/Agent-level when they are reusable across generated apps (template defaults, tsconfig/path alias, shared UI component defects, boilerplate app shell issues, validator/prompt gaps).
RUNTIME DI CLASSIFICATION RULE: If you find an Angular runtime DI error (e.g., NG0201 No provider found) caused by a shared UI wrapper in 'src/app/shared/ui/' using content projection with Angular Aria/provider directives, classify it as "Template/Agent-level" and cite the shared UI wrapper file(s), not only the feature component that rendered it.
If it passes ALL checks with no caveats or uncertainties, output exactly "PASS" and nothing else.
If it fails ANY check, output a concise detailed feedback report with:
- Build/test failures first (exact command + error summary)
- Then architecture/style violations (file paths)
- Then missing features vs acceptance criteria
- Concrete fixes the Developer should make next.
If you are uncertain whether any acceptance criterion is implemented, treat that as a failure and do NOT output PASS."""


@dataclass
class DeterministicCommandResult:
    command: str
    ok: bool
    output: str


@dataclass
class DeterministicValidationResult:
    ok: bool
    report: str


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
MAX_TOTAL_TOKENS_BUDGET: int | None = None


class TokenBudgetExceededError(RuntimeError):
    pass


class AgentStateDict(TypedDict):
    userStory: str
    blueprint: str
    blueprintSummary: str
    instructions: str
    instructionsSummary: str
    orchestratorSkills: str
    orchestratorSkillsSummary: str
    angularVersionContext: str
    workOrder: str
    validationFeedback: str
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


def build_orchestrator_skill_context() -> str:
    sections = [
        ("Version Compatibility", read_text_if_exists(ORCHESTRATOR_SKILL_COMPAT_PATH)),
        ("Template Pattern Catalog", read_text_if_exists(ORCHESTRATOR_SKILL_PATTERN_CATALOG_PATH)),
        ("Template Pattern Examples Index", read_text_if_exists(TEMPLATE_PATTERN_CATALOG_INDEX_PATH)),
        ("Planner Work Orders", read_text_if_exists(ORCHESTRATOR_SKILL_PLANNER_PATH)),
        ("Developer Execution", read_text_if_exists(ORCHESTRATOR_SKILL_DEVELOPER_PATH)),
        ("Validator Audit", read_text_if_exists(ORCHESTRATOR_SKILL_VALIDATOR_PATH)),
    ]
    sections = [(title, content) for title, content in sections if content.strip()]
    if not sections:
        return "No orchestrator skill pack content found."
    return "\n\n".join(f"## {title}\n{content.strip()}" for title, content in sections)


SUMMARY_PRIORITY_KEYWORDS = re.compile(
    r"\b("
    r"critical|must|never|always|required|rule|template-first|template pattern|"
    r"signal|signals|reactive form|forms|validation|validator|planner|developer|"
    r"onpush|inject\(\)|@if|@for|ngif|ngfor|shared/ui|tailwind|aria|accessibility|"
    r"route|routing|router|vitest|build|test"
    r")\b",
    flags=re.IGNORECASE,
)


def summarize_context_for_prompt(text: str, *, max_chars: int) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    if len(normalized) <= max_chars:
        return normalized

    raw_lines = [line.rstrip() for line in normalized.splitlines()]
    head_lines = raw_lines[:28]
    tail_lines = raw_lines[-10:]
    priority_lines = [
        line
        for line in raw_lines
        if line.strip()
        and (
            re.match(r"^\s{0,3}#{1,6}\s+", line)
            or re.match(r"^\s*\d+[\.\)]\s+", line)
            or SUMMARY_PRIORITY_KEYWORDS.search(line)
        )
    ]

    selected: list[str] = []
    seen: set[str] = set()
    reserve = 96  # Leave room for truncation metadata.

    def try_add(line: str) -> None:
        stripped = line.strip()
        if not stripped:
            return
        key = re.sub(r"\s+", " ", stripped)
        if key in seen:
            return
        preview_lines = selected + [stripped]
        if len("\n".join(preview_lines)) > max_chars - reserve:
            return
        selected.append(stripped)
        seen.add(key)

    for bucket in (head_lines, priority_lines, tail_lines):
        for line in bucket:
            try_add(line)

    if not selected:
        truncated = normalized[: max_chars - reserve].rstrip()
        selected = [truncated] if truncated else []

    summary = "\n".join(selected).strip()
    suffix = f"\n\n[summary: trimmed from {len(normalized)} chars for token efficiency]"
    if len(summary) + len(suffix) <= max_chars:
        return f"{summary}{suffix}"
    return summary[: max(0, max_chars - len(suffix))].rstrip() + suffix


def build_static_context_summaries(*, blueprint: str, instructions: str, orchestrator_skills: str) -> tuple[str, str, str]:
    return (
        summarize_context_for_prompt(blueprint, max_chars=3500),
        summarize_context_for_prompt(instructions, max_chars=5000),
        summarize_context_for_prompt(orchestrator_skills, max_chars=4500),
    )


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

    shutil.copytree(TEMPLATE_DIR, target_dir, ignore=_copytree_ignore, dirs_exist_ok=True)

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


def infer_expected_primary_route(user_story: str, work_order: str) -> str | None:
    combined = f"{user_story}\n{work_order}"
    explicit = re.search(
        r"""(?:Feature route should be|route should be|accessible at)\s+[`'"]?(\/[a-z0-9\-\/]*)[`'"]?""",
        combined,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1)

    default_redirect = re.search(
        r"""redirect(?:ed)? to\s+[`'"]?(\/[a-z0-9\-\/]+)[`'"]?""",
        combined,
        flags=re.IGNORECASE,
    )
    return default_redirect.group(1) if default_redirect else None


def walk_files(dir_path: Path) -> list[Path]:
    if not dir_path.exists():
        return []
    files: list[Path] = []
    for entry in dir_path.iterdir():
        if entry.is_dir():
            files.extend(walk_files(entry))
        elif entry.is_file():
            files.append(entry)
    return files


def collect_line_violations(relative_path: str, content: str, regex: re.Pattern[str], label: str) -> list[str]:
    violations: list[str] = []
    for index, line in enumerate(content.splitlines(), start=1):
        if regex.search(line):
            violations.append(f"{relative_path}:{index} - {label}")
    return violations


def _sanitize_subprocess_text(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", (text or "").replace("\r\n", "\n").replace("\r", "\n"))


def run_deterministic_command(command: str, *, target_dir: Path = TARGET_DIR) -> DeterministicCommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=target_dir,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            timeout=180,
        )
        stdout = _sanitize_subprocess_text(result.stdout or "")
        stderr = _sanitize_subprocess_text(result.stderr or "")
        combined = stdout if not stderr.strip() else f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        return DeterministicCommandResult(command=command, ok=True, output=combined)
    except subprocess.CalledProcessError as exc:
        stdout = _sanitize_subprocess_text(exc.stdout or "")
        stderr = _sanitize_subprocess_text(exc.stderr or "")
        return DeterministicCommandResult(
            command=command,
            ok=False,
            output=f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}".strip(),
        )


def run_deterministic_validation_checks(
    state: AgentStateDict,
    *,
    target_dir: Path = TARGET_DIR,
    command_runner: Callable[[str], DeterministicCommandResult] | None = None,
) -> DeterministicValidationResult:
    violations: list[str] = []
    src_app_dir = target_dir / "src" / "app"
    files = [file for file in walk_files(src_app_dir) if re.search(r"\.(ts|html|css)$", str(file))]
    expected_primary_route = infer_expected_primary_route(state["userStory"], state["workOrder"])
    should_enforce_reactive_form_validation = requires_reactive_form_validation(state["userStory"], state["workOrder"])
    required_shared_ui_selectors = extract_required_shared_ui_selectors(state["userStory"])
    feature_component_ts_contents: list[tuple[str, str]] = []
    feature_html_contents: list[tuple[str, str]] = []
    feature_markup_contents: list[tuple[str, str]] = []

    banned_html_template_patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\*ngIf\b"), "Use @if instead of *ngIf"),
        (re.compile(r"\*ngFor\b"), "Use @for instead of *ngFor"),
        (re.compile(r"\*ngSwitch\b"), "Use @switch instead of *ngSwitch"),
        (re.compile(r"\*ngSwitchCase\b"), "Use @switch/@case instead of *ngSwitchCase"),
        (re.compile(r"\*ngSwitchDefault\b"), "Use @switch/@default instead of *ngSwitchDefault"),
        (re.compile(r"\[\(ngModel\)\]"), "Do not use [(ngModel)]; use Reactive Forms"),
        (re.compile(r"=>"), "Do not use arrow functions in Angular templates"),
    ]

    for file_path in files:
        relative_path = file_path.relative_to(target_dir).as_posix()
        content = file_path.read_text(encoding="utf-8")
        is_feature_file = relative_path.startswith("src/app/features/")
        is_feature_component_ts = is_feature_file and file_path.name.endswith(".component.ts")
        is_shared_ui_file = relative_path.startswith("src/app/shared/ui/")
        violations.extend(detect_shared_ui_projection_provider_risks(relative_path, content))

        if is_feature_component_ts:
            feature_component_ts_contents.append((relative_path, content))
            # Inline `template: \`...\`` content lives in the TS file; scanning the TS text is sufficient
            # for deterministic checks that only need to detect tags/patterns.
            feature_markup_contents.append((relative_path, content))
        if is_feature_file and file_path.suffix == ".html":
            feature_html_contents.append((relative_path, content))
            feature_markup_contents.append((relative_path, content))

        if file_path.suffix == ".html":
            for regex, label in banned_html_template_patterns:
                violations.extend(collect_line_violations(relative_path, content, regex, label))

        if file_path.suffix == ".ts" and (is_feature_file or relative_path == "src/app/app.spec.ts"):
            violations.extend(
                collect_line_violations(relative_path, content, re.compile(r"@Input\b"), "Use input() instead of @Input")
            )
            violations.extend(
                collect_line_violations(relative_path, content, re.compile(r"@Output\b"), "Use output() instead of @Output")
            )
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\bany\b"), "Avoid any; use strict types or unknown"))
            if file_path.name.endswith(".spec.ts"):
                violations.extend(
                    collect_line_violations(
                        relative_path,
                        content,
                        re.compile(r"\.toBeTrue\(\)"),
                        "Vitest does not support toBeTrue(); use toBe(true) or toBeTruthy()",
                    )
                )
                violations.extend(
                    collect_line_violations(
                        relative_path,
                        content,
                        re.compile(r"\.toBeFalse\(\)"),
                        "Vitest does not support toBeFalse(); use toBe(false) or toBeFalsy()",
                    )
                )

        if is_feature_component_ts:
            if "ChangeDetectionStrategy.OnPush" not in content:
                violations.append(f"{relative_path}:1 - Component missing ChangeDetectionStrategy.OnPush")
            if "changeDetection:" not in content:
                violations.append(f"{relative_path}:1 - Component missing explicit changeDetection config")

        if re.search(r"\.(html|ts)$", file_path.name):
            custom_control_tag_regex = re.compile(
                r"<app-(select|autocomplete|text-input|textarea|checkbox|switch|radio-group)\b[^>]*\bformControlName\s*="
            )
            if custom_control_tag_regex.search(content):
                violations.append(f"{relative_path}:1 - Shared UI controls in app-* do not support formControlName unless explicitly documented")

        if file_path.name.endswith(".component.css") and relative_path.startswith("src/app/features/"):
            tailwind_utility_redefinitions: list[tuple[re.Pattern[str], str]] = [
                (re.compile(r"^\s*\.container\b", re.MULTILINE), "Do not redefine Tailwind utility '.container' in feature CSS"),
                (re.compile(r"^\s*\.grid\b", re.MULTILINE), "Do not redefine Tailwind utility '.grid' in feature CSS"),
                (re.compile(r"^\s*\.grid-cols-\d+\b", re.MULTILINE), "Do not redefine Tailwind grid-cols-* utilities in feature CSS"),
                (re.compile(r"^\s*\.flex\b", re.MULTILINE), "Do not redefine Tailwind utility '.flex' in feature CSS"),
            ]
            for regex, label in tailwind_utility_redefinitions:
                if regex.search(content):
                    violations.append(f"{relative_path}:1 - {label}")

    app_html_path = src_app_dir / "app.html"
    if app_html_path.exists():
        app_html = app_html_path.read_text(encoding="utf-8")
        if "<router-outlet" not in app_html:
            violations.append("src/app/app.html:1 - app shell should include <router-outlet />")

    app_routes_path = src_app_dir / "app.routes.ts"
    if app_routes_path.exists():
        app_routes = app_routes_path.read_text(encoding="utf-8")
        if expected_primary_route:
            if expected_primary_route == "/":
                if not re.search(r"path:\s*''", app_routes):
                    violations.append("src/app/app.routes.ts:1 - root route ('') is missing for primary route '/'")
            else:
                route_without_slash = re.escape(expected_primary_route.lstrip("/"))
                if not re.search(rf"path:\s*''[\s\S]*redirectTo:\s*['\"]/?{route_without_slash}['\"]", app_routes):
                    violations.append(f"src/app/app.routes.ts:1 - default route must redirect to {expected_primary_route}")
                if not re.search(rf"path:\s*['\"]{route_without_slash}['\"]", app_routes):
                    violations.append(f"src/app/app.routes.ts:1 - {expected_primary_route} route is missing")
        else:
            if not re.search(r"path:\s*''[\s\S]*redirectTo:\s*['\"]\/?[a-z0-9\-\/]+['\"]", app_routes, flags=re.IGNORECASE):
                violations.append("src/app/app.routes.ts:1 - default route should redirect to the generated feature route")

    if should_enforce_reactive_form_validation:
        has_reactive_forms_module_import = any(re.search(r"\bReactiveFormsModule\b", c) for _, c in feature_component_ts_contents)
        has_form_model_usage = any(re.search(r"\b(FormGroup|FormControl|FormBuilder|NonNullableFormBuilder)\b", c) for _, c in feature_component_ts_contents)
        has_validator_usage = any(re.search(r"\bValidators\b|\bValidatorFn\b|\bAsyncValidatorFn\b", c) for _, c in feature_component_ts_contents)
        form_markup_files = [(p, c) for p, c in feature_markup_contents if re.search(r"<form\b", c, flags=re.IGNORECASE)]
        has_validation_ui_in_form = any(re.search(r"\b(invalid|errors|touched|dirty|submitted|error)\b", c) for _, c in form_markup_files)
        has_submit_button = any(re.search(r'type\s*=\s*"submit"', c, flags=re.IGNORECASE) for _, c in form_markup_files)

        if not has_reactive_forms_module_import:
            violations.append("src/app/features/*:1 - Form/validation story requires ReactiveFormsModule in at least one feature component imports array")
        if not has_form_model_usage:
            violations.append("src/app/features/*:1 - Form/validation story requires typed Reactive Forms model usage (FormGroup/FormControl/FormBuilder)")
        if not has_validator_usage:
            violations.append("src/app/features/*:1 - Form/validation story requires validation rules (e.g., Validators.* or custom validator functions)")
        if not form_markup_files:
            violations.append("src/app/features/*:1 - Form/validation story requires at least one <form> element in feature templates")
        else:
            if not has_validation_ui_in_form:
                violations.append("src/app/features/*:1 - Form/validation story requires visible validation/error UI in form templates (invalid/touched/errors/submitted states)")
            if not has_submit_button:
                violations.append('src/app/features/*:1 - Form/validation story requires a submit button (type="submit")')

    if required_shared_ui_selectors:
        combined_feature_html = "\n".join(content for _, content in feature_markup_contents)
        for selector in required_shared_ui_selectors:
            if not re.search(rf"<{re.escape(selector)}\b", combined_feature_html, flags=re.IGNORECASE):
                violations.append(f"src/app/features/*:1 - User story requires shared UI selector '{selector}' to be used at least once in feature templates")

    command_runner_impl = command_runner or (lambda command: run_deterministic_command(command, target_dir=target_dir))
    deterministic_commands = [
        command_runner_impl("npm.cmd run build"),
        command_runner_impl("npm.cmd run test -- --watch=false"),
    ]

    for result in deterministic_commands:
        if not result.ok:
            output = result.output
            truncated_suffix = "\n...[truncated]" if len(output) > 6000 else ""
            violations.append(f"{result.command} failed.\n{output[:6000]}{truncated_suffix}")
            continue

        if re.search(r"run build", result.command, flags=re.IGNORECASE):
            has_angular_warning = bool(re.search(r"\bWARNING\b", result.output, flags=re.IGNORECASE)) and bool(
                re.search(r"\bNG\d{4,}\b", result.output) or re.search(r"\[plugin angular-compiler\]", result.output, flags=re.IGNORECASE)
            )
            if has_angular_warning:
                output = result.output
                truncated_suffix = "\n...[truncated]" if len(output) > 6000 else ""
                violations.append(
                    f"{result.command} produced Angular build warnings (warnings are disallowed).\n{output[:6000]}{truncated_suffix}"
                )

    if not violations:
        return DeterministicValidationResult(ok=True, report="Deterministic validator checks: PASS")

    report = "\n".join(["Deterministic validator checks FAILED.", "", "Violations:"] + [f"- {v}" for v in violations])
    return DeterministicValidationResult(ok=False, report=report)


def build_planner_prompt(state: AgentStateDict) -> str:
    return "".join(
        [
            "You are the Planning Agent (The Architect).\n",
            "Blueprint (summarized once for token efficiency):\n",
            state["blueprintSummary"],
            "\n\nInstructions (summarized once for token efficiency):\n",
            state["instructionsSummary"],
            "\n\nOrchestrator Angular Skills (summarized once for token efficiency):\n",
            state["orchestratorSkillsSummary"],
            "\n\nAngular Version Context:\n",
            state["angularVersionContext"],
            "\n\nUser Story:\n",
            state["userStory"],
            "\n\n",
            PLANNER_RULES_BLOCK,
        ]
    )


def build_developer_system_prompt(state: AgentStateDict, retry_focus_instructions: str) -> str:
    return "".join(
        [
            DEVELOPER_RULES_BLOCK_PREFIX,
            retry_focus_instructions,
            "\n\nBlueprint (summarized once for token efficiency):\n",
            state["blueprintSummary"],
            "\n\nInstructions (summarized once for token efficiency):\n",
            state["instructionsSummary"],
            "\n\nOrchestrator Angular Skills (summarized once for token efficiency):\n",
            state["orchestratorSkillsSummary"],
            "\n\nAngular Version Context:\n",
            state["angularVersionContext"],
        ]
    )


def build_validator_system_prompt(state: AgentStateDict) -> str:
    return "".join(
        [
            VALIDATOR_RULES_BLOCK,
            "\n\nBlueprint (summarized once for token efficiency):\n",
            state["blueprintSummary"],
            "\n\nInstructions (summarized once for token efficiency):\n",
            state["instructionsSummary"],
            "\n\nOrchestrator Angular Skills (summarized once for token efficiency):\n",
            state["orchestratorSkillsSummary"],
            "\n\nAngular Version Context:\n",
            state["angularVersionContext"],
        ]
    )


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


def _build_llm():
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
            if MAX_TOTAL_TOKENS_BUDGET is not None and TOKENS.total_tokens > MAX_TOTAL_TOKENS_BUDGET:
                raise TokenBudgetExceededError(
                    "Token budget exceeded. "
                    f"Limit={MAX_TOTAL_TOKENS_BUDGET}, "
                    f"observed_total={TOKENS.total_tokens}, "
                    f"prompt={TOKENS.prompt_tokens}, completion={TOKENS.completion_tokens}. "
                    "The current LLM call may push slightly past the cap before the workflow can stop."
                )

    return ChatOpenAI(model=DEFAULT_MODEL, temperature=0, callbacks=[TokenCallback()])


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


def _planner_node(state: AgentStateDict, llm, system_message_cls) -> dict[str, str]:
    print("\n--- PLANNING AGENT ---")
    base_prompt = build_planner_prompt(state)
    work_order = ""
    quality_issues: list[str] = []

    for attempt in range(1, 4):
        if attempt == 1:
            retry_supplement = ""
        else:
            retry_supplement = (
                f"\n\nPLANNER SELF-CORRECTION (attempt {attempt} of 3):\n"
                "Previous Work Order quality issues that MUST be fixed:\n"
                + "\n".join(f"- {issue}" for issue in quality_issues)
                + "\n\nReturn a complete corrected Work Order (full markdown), not a diff."
            )

        response = llm.invoke([system_message_cls(content=f"{base_prompt}{retry_supplement}")])
        work_order = str(getattr(response, "content", "") or "")
        quality_issues = validate_work_order_quality(state["userStory"], work_order)

        if not quality_issues:
            break

        print(
            f"Planner Work Order quality check failed (attempt {attempt}/3):\n- "
            + "\n- ".join(quality_issues)
        )

    if quality_issues:
        print(
            "Planner Work Order quality check still has issues after retries. Proceeding with latest Work Order.\n- "
            + "\n- ".join(quality_issues)
        )

    LAST_WORK_ORDER_PATH.write_text(work_order, encoding="utf-8")
    print("Work Order Generated.")
    return {"workOrder": work_order}


def _developer_node(state: AgentStateDict, llm, human_message_cls, system_message_cls) -> dict[str, int]:
    print(f"\n--- DEVELOPMENT AGENT (Iteration {state['iterations'] + 1}) ---")
    is_deterministic_retry = bool(
        re.match(r"^Deterministic validator checks FAILED\.", state.get("validationFeedback", "").strip())
    )
    dev_recursion_limit = 320 if is_deterministic_retry else 220
    retry_focus_instructions = (
        "\nRETRY MODE (deterministic fixes only):\n"
        "- The Validator already identified exact violations. Fix ONLY the cited files/patterns first.\n"
        "- Do not rewrite the feature from scratch.\n"
        "- Prefer minimal edits in the file paths listed in Validator feedback.\n"
        "- Re-run 'npm run build' after each focused change and stop once build passes."
        if is_deterministic_retry
        else ""
    )

    dev_agent = _create_react_agent_compat(
        llm=llm,
        tools=build_langchain_tools(target_dir=TARGET_DIR),
        message_modifier=system_message_cls(content=build_developer_system_prompt(state, retry_focus_instructions)),
    )

    prompt = (
        "Here is your Work Order:\n"
        f"{state['workOrder']}\n\n"
        "Feedback from Validator (if any):\n"
        f"{state['validationFeedback'] or 'None. This is the first attempt.'}\n\n"
        "Please implement the feature, write the files, and run 'npm run build'."
    )

    _invoke_agent_compat(dev_agent, {"messages": [human_message_cls(content=prompt)]}, dev_recursion_limit)
    print("Development Complete.")
    return {"iterations": 1}


def _validator_node(state: AgentStateDict, llm, human_message_cls, system_message_cls) -> dict[str, str]:
    print("\n--- VALIDATION AGENT ---")

    deterministic = run_deterministic_validation_checks(state, target_dir=TARGET_DIR)
    if not deterministic.ok:
        LAST_VALIDATION_PATH.write_text(deterministic.report, encoding="utf-8")
        preview = deterministic.report[:6000] + ("\n...[truncated]" if len(deterministic.report) > 6000 else "")
        print(f"Validator Feedback (Deterministic):\n{preview}")
        print("Validation Complete.")
        return {"validationFeedback": deterministic.report}

    print(deterministic.report)

    val_agent = _create_react_agent_compat(
        llm=llm,
        tools=build_langchain_tools(target_dir=TARGET_DIR),
        message_modifier=system_message_cls(content=build_validator_system_prompt(state)),
    )

    prompt = (
        "Work Order:\n"
        f"{state['workOrder']}\n\n"
        "Please validate the implementation. Run tests and check the code. "
        'If everything is perfect, respond with "PASS". Otherwise, provide a detailed feedback report.'
    )

    response = _invoke_agent_compat(val_agent, {"messages": [human_message_cls(content=prompt)]}, 150)
    raw_final_message = _extract_final_message_content(response)
    normalized = normalize_validator_feedback(raw_final_message, target_dir=TARGET_DIR)

    if normalized.warning:
        print(normalized.warning)

    LAST_VALIDATION_PATH.write_text(normalized.normalized, encoding="utf-8")
    if normalized.normalized == "PASS":
        print("Validator Result: PASS")
    else:
        preview = normalized.normalized[:4000] + ("\n...[truncated]" if len(normalized.normalized) > 4000 else "")
        print(f"Validator Feedback:\n{preview}")
    print("Validation Complete.")
    return {"validationFeedback": normalized.normalized}


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


def _reset_token_counters() -> None:
    TOKENS.total_tokens = 0
    TOKENS.prompt_tokens = 0
    TOKENS.completion_tokens = 0


def _print_token_usage() -> None:
    print("\n--- TOKEN USAGE ---")
    print(f"Prompt Tokens:     {TOKENS.prompt_tokens}")
    print(f"Completion Tokens: {TOKENS.completion_tokens}")
    print(f"Total Tokens:      {TOKENS.total_tokens}")


def run_full_workflow(*, max_total_tokens: int | None = None) -> None:
    global MAX_TOTAL_TOKENS_BUDGET
    _reset_token_counters()
    MAX_TOTAL_TOKENS_BUDGET = max_total_tokens
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required. Set it in orchestrator_py/.env or orchestrator/.env.")

    _ensure_langchain_runtime()
    from langchain_core.messages import HumanMessage, SystemMessage

    setup_project(target_dir=TARGET_DIR)

    user_story = USER_STORY_PATH.read_text(encoding="utf-8")
    blueprint = BLUEPRINT_PATH.read_text(encoding="utf-8")
    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    orchestrator_skills = build_orchestrator_skill_context()
    blueprint_summary, instructions_summary, orchestrator_skills_summary = build_static_context_summaries(
        blueprint=blueprint,
        instructions=instructions,
        orchestrator_skills=orchestrator_skills,
    )
    angular_version_context = build_angular_version_context(TARGET_DIR / "package.json")

    state: AgentStateDict = {
        "userStory": user_story,
        "blueprint": blueprint,
        "blueprintSummary": blueprint_summary,
        "instructions": instructions,
        "instructionsSummary": instructions_summary,
        "orchestratorSkills": orchestrator_skills,
        "orchestratorSkillsSummary": orchestrator_skills_summary,
        "angularVersionContext": angular_version_context,
        "workOrder": "",
        "validationFeedback": "",
        "iterations": 0,
    }

    if max_total_tokens is not None:
        print(f"Token budget enabled for this run: max total tokens = {max_total_tokens}")

    try:
        llm = _build_llm()
        print("\nStarting Agentic Workflow...")

        state.update(_planner_node(state, llm, SystemMessage))
        while True:
            dev_update = _developer_node(state, llm, HumanMessage, SystemMessage)
            state["iterations"] += int(dev_update.get("iterations", 0))
            state.update(_validator_node(state, llm, HumanMessage, SystemMessage))
            if _should_continue(state) == "END":
                break
    finally:
        _print_token_usage()
        MAX_TOTAL_TOKENS_BUDGET = None


def run_self_test() -> None:
    print("Running orchestrator_py self-test (piecewise, no full workflow)...")

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

    with tempfile.TemporaryDirectory(prefix="orchestrator_py_tools_") as tmp:
        tmp_dir = Path(tmp)
        assert "Successfully wrote" in write_code("src/test.txt", "hello", target_dir=tmp_dir)
        assert read_file("src/test.txt", target_dir=tmp_dir) == "hello"
        cmd_result = run_command('python -c "print(\'ok\')"', target_dir=tmp_dir)
        assert "Command succeeded" in cmd_result and "ok" in cmd_result

    with tempfile.TemporaryDirectory(prefix="orchestrator_py_deterministic_") as tmp:
        fake_target = Path(tmp)
        (fake_target / "src" / "app" / "features" / "demo").mkdir(parents=True, exist_ok=True)
        (fake_target / "src" / "app" / "shared" / "ui").mkdir(parents=True, exist_ok=True)
        (fake_target / "src" / "app" / "shared" / "ui" / "index.ts").write_text(
            "export * from './card/card.component';\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "app.html").write_text("<router-outlet />\n", encoding="utf-8")
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
            "export class DemoComponent { readonly form = new FormGroup({ email: new FormControl('', { nonNullable: true, validators: [Validators.required] }) }); }\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.html").write_text(
            "<form>\n"
            "  <app-radio-group></app-radio-group>\n"
            "  <div>touched errors invalid submitted</div>\n"
            "  <button type=\"submit\">Submit</button>\n"
            "</form>\n",
            encoding="utf-8",
        )
        (fake_target / "src" / "app" / "features" / "demo" / "demo.component.css").write_text("", encoding="utf-8")
        (fake_target / "src" / "app" / "app.spec.ts").write_text("describe('x', () => {});\n", encoding="utf-8")

        fake_state: AgentStateDict = {
            "userStory": "Feature route should be /demo. Use a form with validation and error messages. Required selector: `app-radio-group`.",
            "blueprint": "",
            "instructions": "",
            "orchestratorSkills": "",
            "angularVersionContext": "",
            "workOrder": "Reactive form validation plan for /demo with app-radio-group and error messages.",
            "validationFeedback": "",
            "iterations": 0,
        }

        def fake_runner(command: str) -> DeterministicCommandResult:
            return DeterministicCommandResult(command=command, ok=True, output="OK")

        deterministic = run_deterministic_validation_checks(
            fake_state,
            target_dir=fake_target,
            command_runner=fake_runner,
        )
        assert deterministic.ok, deterministic.report

        false_positive_text = (
            "shared ui component files are missing:\n"
            "- src/app/shared/ui/app-card/app-card.component.ts\n"
        )
        normalized = normalize_validator_feedback(false_positive_text, target_dir=fake_target)
        assert normalized.normalized == "PASS"

    angular_context = build_angular_version_context(TEMPLATE_DIR / "package.json")
    assert "Angular target" in angular_context
    skills_context = build_orchestrator_skill_context()
    assert isinstance(skills_context, str) and len(skills_context) > 0

    print("Self-test checks passed:")
    print("- command safety guards")
    print("- selector/route extraction helpers")
    print("- work-order quality checker")
    print("- local file tool functions")
    print("- deterministic validator (stubbed build/test commands)")
    print("- validator false-positive normalization")
    print("- context loaders (Angular version + skill pack)")
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
    parser.add_argument(
        "--max-total-tokens",
        "--max-tokens",
        dest="max_total_tokens",
        type=int,
        default=None,
        help=(
            "Optional hard-stop budget for observed total LLM tokens across the workflow. "
            "If exceeded, the orchestrator aborts after the current model call."
        ),
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
        if args.max_total_tokens is not None and args.max_total_tokens <= 0:
            raise RuntimeError("--max-total-tokens must be a positive integer")
        run_full_workflow(max_total_tokens=args.max_total_tokens)
        return 0
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    except TokenBudgetExceededError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

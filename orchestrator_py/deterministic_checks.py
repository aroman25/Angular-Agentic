from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from orchestrator_py.log_store import append_command_log
except ModuleNotFoundError:  # Allows `python orchestrator_py/index.py`
    from log_store import append_command_log

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = (REPO_ROOT / "generated-app").resolve()
LAST_DETERMINISTIC_REPORT_PATH = (REPO_ROOT / "orchestrator_py" / "last-deterministic-report.md").resolve()


@dataclass
class DeterministicCommandResult:
    command: str
    ok: bool
    output: str
    log_id: str | None = None
    log_path: str | None = None


@dataclass
class DeterministicValidationResult:
    ok: bool
    report: str
    violations: list[str]
    coverage: dict[str, bool]
    confidence: float


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


def extract_required_shared_ui_selectors(text: str) -> list[str]:
    matches = [m.group(1).lower() for m in re.finditer(r"`(app-[a-z0-9-]+)`", text, flags=re.IGNORECASE)]
    aliases = {"app-menu": "app-dropdown-menu"}
    normalized = [aliases.get(selector, selector) for selector in matches]
    return list(dict.fromkeys(normalized))


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


def requires_reactive_form_validation(user_story: str, work_order: str) -> bool:
    combined = f"{user_story}\n{work_order}".lower()
    mentions_form = bool(re.search(r"\bform(s)?\b", combined))
    mentions_validation = bool(
        re.search(r"\bvalidat(e|ion|ions|ing)\b", combined) or re.search(r"\berror message(s)?\b", combined)
    )
    return mentions_form and mentions_validation


def _story_mentions_accessibility(user_story: str, work_order: str) -> bool:
    combined = f"{user_story}\n{work_order}".lower()
    return bool(re.search(r"\baria|accessib|keyboard|screen reader\b", combined))


def _story_requires_state_signals(user_story: str, work_order: str) -> bool:
    combined = f"{user_story}\n{work_order}".lower()
    return bool(re.search(r"\bsignal|state management|computed|store|list|filter\b", combined))


def run_deterministic_command(
    command: str,
    *,
    target_dir: Path,
    run_id: str,
) -> DeterministicCommandResult:
    result = subprocess.run(
        command,
        cwd=target_dir,
        shell=True,
        check=False,
        text=True,
        capture_output=True,
        timeout=180,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    log_meta = append_command_log(
        run_id=run_id,
        command=command,
        cwd=target_dir,
        exit_code=result.returncode,
        stdout=stdout,
        stderr=stderr,
    )

    output = stdout if result.returncode == 0 else f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}".strip()
    return DeterministicCommandResult(
        command=command,
        ok=result.returncode == 0,
        output=output,
        log_id=log_meta.get("logId"),
        log_path=log_meta.get("path"),
    )


def _detect_shared_ui_projection_provider_risks(relative_path: str, content: str) -> list[str]:
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


def _compute_confidence(violations: list[str], coverage: dict[str, bool]) -> float:
    if violations:
        return 0.0
    covered = sum(1 for value in coverage.values() if value)
    total = max(1, len(coverage))
    ratio = covered / total
    return round(min(1.0, max(0.4, 0.4 + ratio * 0.6)), 3)


def run_deterministic_validation_checks(
    *,
    user_story: str,
    work_order: str,
    run_id: str,
    target_dir: Path = TARGET_DIR,
    command_runner: Callable[[str], DeterministicCommandResult] | None = None,
) -> DeterministicValidationResult:
    violations: list[str] = []
    coverage: dict[str, bool] = {
        "routing": False,
        "onpush": False,
        "signals": False,
        "forms": False,
        "form_validation_ui": False,
        "non_cva_bridge": False,
        "shared_ui_required_selectors": False,
        "accessibility": False,
        "app_shell_cleanup": False,
        "tests_boilerplate": False,
    }

    src_app_dir = target_dir / "src" / "app"
    files = [file for file in walk_files(src_app_dir) if re.search(r"\.(ts|html|css)$", str(file))]
    expected_primary_route = infer_expected_primary_route(user_story, work_order)
    enforce_form = requires_reactive_form_validation(user_story, work_order)
    required_selectors = extract_required_shared_ui_selectors(user_story)
    story_accessibility = _story_mentions_accessibility(user_story, work_order)
    story_requires_signals = _story_requires_state_signals(user_story, work_order)

    feature_component_ts_contents: list[tuple[str, str]] = []
    feature_html_contents: list[tuple[str, str]] = []
    feature_markup_contents: list[tuple[str, str]] = []

    for file_path in files:
        relative_path = file_path.relative_to(target_dir).as_posix()
        content = file_path.read_text(encoding="utf-8")
        is_feature = relative_path.startswith("src/app/features/")
        is_feature_component_ts = is_feature and file_path.name.endswith(".component.ts")

        violations.extend(_detect_shared_ui_projection_provider_risks(relative_path, content))

        if file_path.suffix == ".html":
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\*ngIf\b"), "Use @if instead of *ngIf"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\*ngFor\b"), "Use @for instead of *ngFor"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\*ngSwitch\b"), "Use @switch instead of *ngSwitch"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\[\(ngModel\)\]"), "Do not use [(ngModel)]; use Reactive Forms"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"=>"), "Do not use arrow functions in Angular templates"))

        if file_path.suffix == ".ts" and (is_feature or relative_path == "src/app/app.spec.ts"):
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"@Input\b"), "Use input() instead of @Input"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"@Output\b"), "Use output() instead of @Output"))
            violations.extend(collect_line_violations(relative_path, content, re.compile(r"\bany\b"), "Avoid any; use strict types or unknown"))

        if is_feature_component_ts:
            feature_component_ts_contents.append((relative_path, content))
            feature_markup_contents.append((relative_path, content))
            if "ChangeDetectionStrategy.OnPush" not in content:
                violations.append(f"{relative_path}:1 - Component missing ChangeDetectionStrategy.OnPush")
            if "changeDetection:" not in content:
                violations.append(f"{relative_path}:1 - Component missing explicit changeDetection config")
            if re.search(r"constructor\s*\(", content):
                violations.append(f"{relative_path}:1 - Prefer inject() over constructor DI in feature components")

        if is_feature and file_path.suffix == ".html":
            feature_html_contents.append((relative_path, content))
            feature_markup_contents.append((relative_path, content))

        if re.search(r"\.(html|ts)$", file_path.name):
            custom_control_tag_regex = re.compile(r"<app-(select|autocomplete|text-input|textarea|checkbox|switch|radio-group)\b[^>]*\bformControlName\s*=")
            if custom_control_tag_regex.search(content):
                violations.append(f"{relative_path}:1 - Shared UI controls in app-* do not support formControlName unless explicitly documented")

    app_html_path = src_app_dir / "app.html"
    app_ts_path = src_app_dir / "app.ts"
    app_spec_path = src_app_dir / "app.spec.ts"
    app_routes_path = src_app_dir / "app.routes.ts"

    if app_html_path.exists():
        app_html = app_html_path.read_text(encoding="utf-8")
        if "<router-outlet" not in app_html:
            violations.append("src/app/app.html:1 - app shell should include <router-outlet />")

        if app_ts_path.exists():
            app_ts = app_ts_path.read_text(encoding="utf-8")
            if "NgOptimizedImage" in app_ts and "ngSrc" not in app_html and "ngOptimizedImage" not in app_html:
                violations.append("src/app/app.ts:1 - remove NgOptimizedImage import when app.html no longer uses it")
            else:
                coverage["app_shell_cleanup"] = True

    if app_spec_path.exists():
        app_spec = app_spec_path.read_text(encoding="utf-8")
        h1_assertion_present = bool(re.search(r"h1", app_spec, flags=re.IGNORECASE))
        app_in_declarations = bool(re.search(r"declarations\s*:\s*\[[^\]]*\bApp\b", app_spec, flags=re.IGNORECASE | re.DOTALL))
        app_in_imports = bool(re.search(r"imports\s*:\s*\[[^\]]*\bApp\b", app_spec, flags=re.IGNORECASE | re.DOTALL))
        duplicate_imports_keys = len(re.findall(r"\bimports\s*:", app_spec)) > 1
        if h1_assertion_present:
            violations.append("src/app/app.spec.ts:1 - remove default h1 boilerplate assertion")
        if app_in_declarations:
            violations.append("src/app/app.spec.ts:1 - App should be in imports, not declarations")
        if not app_in_imports:
            violations.append("src/app/app.spec.ts:1 - App should be included in imports")
        if duplicate_imports_keys:
            violations.append("src/app/app.spec.ts:1 - duplicate imports keys in TestBed config")
        if not h1_assertion_present and app_in_imports and (not app_in_declarations) and (not duplicate_imports_keys):
            coverage["tests_boilerplate"] = True

    if app_routes_path.exists():
        app_routes = app_routes_path.read_text(encoding="utf-8")
        route_ok = False
        if expected_primary_route:
            if expected_primary_route == "/":
                route_ok = bool(re.search(r"path:\s*''", app_routes))
            else:
                route_without_slash = re.escape(expected_primary_route.lstrip("/"))
                route_ok = bool(re.search(rf"path:\s*''[\s\S]*redirectTo:\s*['\"]/?{route_without_slash}['\"]", app_routes)) and bool(re.search(rf"path:\s*['\"]{route_without_slash}['\"]", app_routes))
                if not route_ok:
                    violations.append(f"src/app/app.routes.ts:1 - default route and explicit route for {expected_primary_route} are required")
        else:
            route_ok = bool(re.search(r"path:\s*''[\s\S]*redirectTo:\s*['\"]/?[a-z0-9\-/]+['\"]", app_routes, flags=re.IGNORECASE))
            if not route_ok:
                violations.append("src/app/app.routes.ts:1 - default route should redirect to generated feature route")

        coverage["routing"] = route_ok

    if feature_component_ts_contents:
        coverage["onpush"] = all("ChangeDetectionStrategy.OnPush" in content and "changeDetection:" in content for _, content in feature_component_ts_contents)
        if story_requires_signals:
            has_signals = any(re.search(r"\bsignal\(|\bcomputed\(|\beffect\(", content) for _, content in feature_component_ts_contents)
            coverage["signals"] = has_signals
            if not has_signals:
                violations.append("src/app/features/*:1 - story implies stateful behavior; expected signal/computed usage in feature components")
        else:
            coverage["signals"] = True

    if enforce_form:
        has_reactive_forms_module_import = any(re.search(r"\bReactiveFormsModule\b", c) for _, c in feature_component_ts_contents)
        has_form_model_usage = any(re.search(r"\b(FormGroup|FormControl|FormBuilder|NonNullableFormBuilder)\b", c) for _, c in feature_component_ts_contents)
        has_validator_usage = any(re.search(r"\bValidators\b|\bValidatorFn\b|\bAsyncValidatorFn\b", c) for _, c in feature_component_ts_contents)
        form_markup_files = [(p, c) for p, c in feature_markup_contents if re.search(r"<form\b", c, flags=re.IGNORECASE)]
        has_validation_ui_in_form = any(re.search(r"\b(invalid|errors|touched|dirty|submitted|error|required|min|max|pattern)\b", c) for _, c in form_markup_files)
        has_submit_button = any(re.search(r'type\s*=\s*"submit"', c, flags=re.IGNORECASE) for _, c in form_markup_files)
        has_submit_disable = any(re.search(r"\[disabled\]\s*=\s*\"[^\"]*(invalid|pending)", c, flags=re.IGNORECASE) for _, c in form_markup_files)

        if not has_reactive_forms_module_import:
            violations.append("src/app/features/*:1 - form story requires ReactiveFormsModule")
        if not has_form_model_usage:
            violations.append("src/app/features/*:1 - form story requires typed Reactive Forms model usage")
        if not has_validator_usage:
            violations.append("src/app/features/*:1 - form story requires explicit validator usage")
        if not form_markup_files:
            violations.append("src/app/features/*:1 - form story requires at least one <form>")
        if form_markup_files and not has_validation_ui_in_form:
            violations.append("src/app/features/*:1 - form story requires visible validation/error UI")
        if form_markup_files and not has_submit_button:
            violations.append("src/app/features/*:1 - form story requires submit button")
        if form_markup_files and not has_submit_disable:
            violations.append("src/app/features/*:1 - form story should disable submit while invalid/pending")

        has_non_cva_bridge = any(re.search(r"\(valueChange\)\s*=|\[value\]\s*=", c) for _, c in feature_markup_contents)
        coverage["non_cva_bridge"] = has_non_cva_bridge
        if not has_non_cva_bridge:
            violations.append("src/app/features/*:1 - expected non-CVA value/valueChange bridge for shared form controls")

        coverage["forms"] = has_reactive_forms_module_import and has_form_model_usage and has_validator_usage and bool(form_markup_files)
        coverage["form_validation_ui"] = has_validation_ui_in_form and has_submit_button and has_submit_disable
    else:
        coverage["forms"] = True
        coverage["form_validation_ui"] = True
        coverage["non_cva_bridge"] = True

    if required_selectors:
        combined_feature_html = "\n".join(content for _, content in feature_markup_contents)
        missing_selectors: list[str] = []
        for selector in required_selectors:
            if not re.search(rf"<{re.escape(selector)}\b", combined_feature_html, flags=re.IGNORECASE):
                missing_selectors.append(selector)
                violations.append(f"src/app/features/*:1 - user story requires selector '{selector}' in feature templates")

        # Heuristic meaningful usage: selector should appear with nearby text/action attrs
        if not missing_selectors:
            meaningful = bool(re.search(r"<(app-[a-z0-9-]+)[^>]*(aria-label|title|\(click\)|\[routerLink\]|valueChange)", combined_feature_html, flags=re.IGNORECASE))
            coverage["shared_ui_required_selectors"] = meaningful
            if not meaningful:
                violations.append("src/app/features/*:1 - required selectors present but usage appears non-meaningful; add actionable/accessible context")
        else:
            coverage["shared_ui_required_selectors"] = False
    else:
        coverage["shared_ui_required_selectors"] = True

    if story_accessibility:
        combined_feature_html = "\n".join(content for _, content in feature_html_contents)
        has_landmark = bool(re.search(r"<(header|main|section|nav)\b", combined_feature_html, flags=re.IGNORECASE))
        has_accessible_label = bool(re.search(r"\b(aria-label|aria-labelledby)\s*=\s*\"[^\"]+\"", combined_feature_html, flags=re.IGNORECASE))
        coverage["accessibility"] = has_landmark and has_accessible_label
        if not has_landmark:
            violations.append("src/app/features/*:1 - accessibility story requires semantic landmarks (header/main/section/nav)")
        if not has_accessible_label:
            violations.append("src/app/features/*:1 - accessibility story requires explicit accessible labels on interactive controls")
    else:
        coverage["accessibility"] = True

    command_runner_impl = command_runner or (lambda command: run_deterministic_command(command, target_dir=target_dir, run_id=run_id))
    deterministic_commands = [
        command_runner_impl("npm.cmd run build"),
        command_runner_impl("npm.cmd run test -- --watch=false"),
    ]

    for result in deterministic_commands:
        if not result.ok:
            output = result.output
            truncated_suffix = "\n...[truncated]" if len(output) > 4000 else ""
            log_suffix = f"\nLog: {result.log_path} (id={result.log_id})" if result.log_path else ""
            violations.append(f"{result.command} failed.\n{output[:4000]}{truncated_suffix}{log_suffix}")
            continue

        if re.search(r"run build", result.command, flags=re.IGNORECASE):
            has_angular_warning = bool(re.search(r"\bWARNING\b", result.output, flags=re.IGNORECASE)) and bool(
                re.search(r"\bNG\d{4,}\b", result.output) or re.search(r"\[plugin angular-compiler\]", result.output, flags=re.IGNORECASE)
            )
            if has_angular_warning:
                output = result.output
                truncated_suffix = "\n...[truncated]" if len(output) > 4000 else ""
                log_suffix = f"\nLog: {result.log_path} (id={result.log_id})" if result.log_path else ""
                violations.append(
                    f"{result.command} produced Angular warnings (disallowed).\n{output[:4000]}{truncated_suffix}{log_suffix}"
                )

    confidence = _compute_confidence(violations, coverage)
    report_lines = [
        "Deterministic validator checks: PASS" if not violations else "Deterministic validator checks FAILED.",
        "",
        "Coverage:",
    ]
    for key in sorted(coverage.keys()):
        report_lines.append(f"- {key}: {'PASS' if coverage[key] else 'FAIL'}")
    report_lines.append(f"- confidence: {confidence}")

    if violations:
        report_lines.extend(["", "Violations:"])
        report_lines.extend(f"- {violation}" for violation in violations)

    report = "\n".join(report_lines)
    LAST_DETERMINISTIC_REPORT_PATH.write_text(report + "\n", encoding="utf-8")

    return DeterministicValidationResult(
        ok=not violations,
        report=report,
        violations=violations,
        coverage=coverage,
        confidence=confidence,
    )

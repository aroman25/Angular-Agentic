# Angular v20/v21 Compatibility (Orchestrator)

## Targeting rule

- Default assumption: generated apps may be Angular `v20` or `v21`.
- Planner/Developer/Validator must detect or read the actual major version from `package.json` before enforcing version-specific expectations.

## Rules valid in both v20 and v21

- Standalone components are the default: do not add `standalone: true`.
- Prefer signals for local UI state (`signal`, `computed`, `effect`, `linkedSignal` when useful).
- Prefer native control flow (`@if`, `@for`, `@switch`) over structural directives.
- Prefer `inject()` over constructor injection for services/utilities.
- Use `ChangeDetectionStrategy.OnPush` explicitly on generated components.
- Use Reactive Forms for form-centric features; avoid `[(ngModel)]`.
- Tailwind should be applied primarily via utility classes in templates.
- Vitest matcher syntax applies (`toBe`, `toBeTruthy`) instead of Jasmine-only helpers.

## v20 vs v21 nuance

- Zoneless:
  - v21: strongly preferred / often template-default expectation.
  - v20: may be enabled or not depending on template configuration; do not fail only because zoneless is not configured unless the user story or template explicitly requires it.
- Feature planning:
  - Do not use APIs that are experimental or version-fragile unless guarded by explicit template support.
  - Prefer stable Angular APIs shared by v20 and v21.

## Shared UI + Angular Aria wrapper safety

- When a shared UI wrapper uses Angular Aria/provider directives and projects children via `<ng-content>`, provider/group directives must be attached to the wrapper host (or otherwise be visible to projected children).
- Treat runtime `NG0201 No provider found` from shared UI wrappers as likely `Template/Agent-level`.

## Forms + non-CVA custom controls

- Assume most `src/app/shared/ui` controls are not `ControlValueAccessor` unless documented.
- Bridge via `[value]` / `(valueChange)` and update the `FormControl` in component TS methods.

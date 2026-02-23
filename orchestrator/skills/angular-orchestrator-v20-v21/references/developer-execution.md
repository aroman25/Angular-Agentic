# Developer Guide (Execution)

## Pre-implementation checklist

- Read the Work Order fully.
- If the Work Order includes `Template Pattern References`, read:
  - `automate-angular-template/docs/agent-patterns/README.md`
  - the cited pattern docs in `forms-core.md` / `layouts-core.md`
- Read `src/app/shared/ui/index.ts`.
- Read top usage comments for each shared UI component you plan to use.
- Read `src/app/app.ts`, `src/app/app.html`, `src/app/app.routes.ts`, and `src/app/app.spec.ts`.
- Confirm Angular major version from `package.json` (v20 or v21).

## Implementation rules (v20/v21-safe)

- Use standalone components (implicit) and omit `standalone: true`.
- Use `OnPush`, `inject()`, signals, and native control flow.
- Use Reactive Forms for forms; never `[(ngModel)]`.
- Keep Tailwind in templates; avoid redefining utility classes in feature CSS.
- Use Vitest-compatible tests/matchers.

## Shared UI + forms integration

- Do not assume `formControlName` support on custom `app-*` controls.
- Use explicit bridge methods for `[value]` and `(valueChange)`.
- Normalize values in TS (avoid template casts and complex inline expressions).
- Follow the cited pattern skeleton/shared UI composition map first; only deviate when the Work Order documents a justified reason.

## Build/test loop

- Run `npm run build`.
- Fix compile errors/warnings before moving on.
- When validator feedback is deterministic, make focused edits instead of rewriting the feature.

## Template-first rule

- If the issue is reusable (shared UI bug, template config, base shell, path alias, tooling defaults), fix template/agent/orchestrator guidance first.
- Shared UI runtime DI errors (e.g., Angular Aria provider tokens) are usually template-level wrapper defects unless feature API usage is clearly wrong.

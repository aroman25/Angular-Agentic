# Validator Guide (Audit + Acceptance)

## Validation order

1. Deterministic checks (build/test/rule scans)
2. Code inspection against Work Order
3. Acceptance criteria verification
4. Classification (`Feature-level` vs `Template/Agent-level`)

## What to verify in complex features

- Work Order fidelity:
  - Are user-story data points preserved (routes, fields, constraints, selectors)?
  - Did the planner invent requirements without marking assumptions?
  - If the feature is form/layout-heavy, does `UI/UX Requirements` include `Template Pattern References` (or a documented `none` + `Deviation Notes`)?
- Forms:
  - typed Reactive Form model present
  - validators are explicit
  - validation UI is visible
  - invalid submit prevented
  - result state shown if required
  - non-CVA shared UI bridge patterns are used
- Shared UI reuse:
  - selectors used meaningfully in templates (not just imports)
  - shared UI wrappers not replaced by custom duplicates
- Pattern alignment:
  - does the implementation generally follow the cited template form/layout pattern(s)?
  - if it deviates, is the deviation documented and still acceptance-criteria compliant?
- Accessibility:
  - labels, keyboard interactions, focus states, aria relationships

## Runtime DI / Angular Aria wrapper rule

- If runtime errors indicate missing providers from shared UI wrappers (e.g., `NG0201` + Angular Aria tokens), inspect the shared wrapper component first.
- If provider directives are attached to internal wrapper elements while children are projected, classify as `Template/Agent-level`.

## Failure report format

- Build/test failures first
- Then architecture/style violations
- Then missing acceptance criteria
- Do not fail solely because a cited pattern was adapted, if the Work Order documents the deviation and the implementation satisfies acceptance criteria.
- Each item must include file path and concrete fix direction

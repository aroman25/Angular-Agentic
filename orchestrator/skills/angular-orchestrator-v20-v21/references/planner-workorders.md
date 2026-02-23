# Planner Guide (Work Orders)

## Goal

Produce a Work Order that is executable without guesswork and preserves user-story data points.

## Required sections

- `Feature Name & Goal`
- `User Story Data Points`
- `Requirement Traceability`
- `File Structure`
- `State Management`
- `Form Model & Validation` (when forms are in scope)
- `UI/UX Requirements`
- `Acceptance Criteria`

## Template pattern references (required for form/layout-heavy features)

- Before custom UI planning, select a template pattern reference set from:
  - `automate-angular-template/docs/agent-patterns/README.md`
  - `automate-angular-template/docs/agent-patterns/forms-core.md`
  - `automate-angular-template/docs/agent-patterns/layouts-core.md`
- In `UI/UX Requirements`, include a line in this format:
  - `Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit`
- If no pattern fits, include:
  - `Template Pattern References: none`
  - `Deviation Notes: <why the catalog does not fit>`

## User-story data fidelity

- Extract concrete items directly from the user story:
  - routes and redirects
  - field names and options
  - validation constraints
  - required shared UI selectors/components
  - limits, thresholds, and explicit UX rules
- Mark anything invented as an `Assumption`.

## Complexity handling patterns

- Long selector lists:
  - Plan a dedicated "Shared UI Coverage" section/panel so primary UX remains clean.
- Form-heavy stories:
  - Include typed Reactive Form schema and validation matrix.
  - Specify non-CVA shared control bridge methods.
- Multi-panel interactions:
  - Define drawer/dialog ownership, open/close state signals, and keyboard expectations.
- Large mock datasets:
  - Define file-local mock data typing and pagination/filtering behavior.

## Shared UI planning rule

- Map each required `app-*` selector to a concrete location and purpose.
- Require developer to inspect `src/app/shared/ui/index.ts` and top usage comments before implementation.
- Prefer the selected pattern's shared UI composition map before inventing a custom structure.

## Template-first planning rule

- If the user story likely exposes reusable template/shared UI defects, call them out as `Template/Agent-level` candidates in the Work Order notes.

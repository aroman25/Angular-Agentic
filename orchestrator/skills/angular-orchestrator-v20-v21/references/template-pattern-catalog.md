# Template Pattern Catalog (Orchestrator Adapter)

## Why this exists

The template stores a docs-only catalog of reusable form and layout recipes under:

- `automate-angular-template/docs/agent-patterns/README.md`
- `automate-angular-template/docs/agent-patterns/forms-core.md`
- `automate-angular-template/docs/agent-patterns/layouts-core.md`

This reference tells Planner/Developer/Validator agents how to use that catalog consistently without duplicating the full recipes inside the orchestrator skill pack.

## Required agent behavior by role

### Planner

- Select one primary `layout-*` pattern for page structure when the feature has a page-level UI.
- Select zero to two `form-*` patterns when the feature includes forms/filter panels/overlay forms.
- Cite selected pattern IDs in the Work Order `UI/UX Requirements` section using the required line format.
- If no pattern fits, explicitly write `Template Pattern References: none` and include a `Deviation Notes:` line explaining why.

### Developer

- Read the cited pattern docs in the template before implementing UI structure.
- Follow the pattern shared UI composition map and Tailwind skeleton first.
- Deviate only when the Work Order documents a justified reason.
- Preserve shared UI reuse and non-CVA form control bridging rules.

### Validator

- Check that the implementation reflects the cited pattern IDs (layout + form patterns as applicable).
- If the implementation deviates, verify the Work Order includes `Deviation Notes` and that acceptance criteria remain satisfied.
- Do not fail solely for a deviation when the deviation is documented and defensible.

## Pattern citation format (required)

Use this exact Work Order line in `UI/UX Requirements`:

```md
Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit
```

If no catalog pattern applies:

```md
Template Pattern References: none
Deviation Notes: No catalog pattern fits because <specific feature constraint>.
```

## Catalog links / paths

- Template index: `automate-angular-template/docs/agent-patterns/README.md`
- Form recipes: `automate-angular-template/docs/agent-patterns/forms-core.md`
- Layout recipes: `automate-angular-template/docs/agent-patterns/layouts-core.md`

## Pattern selection guidance

- Prefer `1` primary `layout-*` pattern per feature page.
- Add `0-2` `form-*` patterns depending on scope:
  - no forms: layout only
  - standard create/edit page: one layout + one form pattern
  - list/filter + overlay edit: one layout + two form patterns
- Keep the selected patterns aligned to actual user story constraints and required `app-*` selectors.

## Deviation handling rule

A deviation is acceptable when:

- the user story requires an interaction not covered by the catalog,
- the shared UI component APIs impose a different structure, or
- a template-level defect blocks the canonical pattern.

When deviating, the Work Order must document the reason and the Validator should assess the implementation against acceptance criteria plus the documented rationale.

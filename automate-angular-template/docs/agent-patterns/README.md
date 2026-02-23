# Agent Pattern Catalog (Template Reference)

## What This Is

This folder contains docs-only reference patterns for common Angular v20/v21 feature layouts and forms using the template shared UI library (`src/app/shared/ui`) and Tailwind CSS.

These are canonical recipes for agents to reuse when building generated apps. They are not runnable demo pages and do not add routes/components to the template app shell.

## How Agents Must Use This Catalog

- Planner: select one primary `layout-*` pattern and zero to two `form-*` patterns (when applicable), then cite them in the Work Order `UI/UX Requirements` section.
- Developer: follow the selected pattern skeleton(s) and shared UI composition map before inventing a custom layout/form structure.
- Validator: verify the implementation reflects the cited pattern IDs, or that the Work Order includes a justified `Deviation Notes` entry.

## Pattern Selection Matrix

| Pattern ID | Type | Best Use Case | Primary Shared UI Components |
| --- | --- | --- | --- |
| `form-single-column-submit` | Form | Simple transactional create/update form | `app-card`, `app-text-input`, `app-button`, `app-alert`, `app-toast` |
| `form-mixed-controls-create-edit` | Form | Entity create/edit with mixed input types and validation | `app-card`, `app-text-input`, `app-textarea`, `app-select`, `app-radio-group`, `app-checkbox`, `app-switch`, `app-divider`, `app-button`, `app-alert` |
| `form-filter-panel-results` | Form | Filter/search controls paired with list/grid results | `app-text-input`, `app-autocomplete`, `app-select`, `app-switch`, `app-toolbar`, `app-button`, `app-table`/`app-data-grid`, `app-pagination`, `app-empty-state`, `app-skeleton` |
| `form-overlay-edit-drawer-dialog` | Form | Inline edit/create or confirmation flows in overlays | `app-drawer`, `app-dialog`, `app-text-input`, `app-textarea`, `app-select`, `app-button`, `app-alert`, `app-toast` |
| `layout-page-shell-header-toolbar` | Layout | Standard feature page shell with header actions | `app-breadcrumb`, `app-toolbar`, `app-card`, `app-button`, `app-dropdown-menu` |
| `layout-dashboard-card-grid` | Layout | Dashboard/overview page with cards and summary table | `app-card`, `app-badge`, `app-progress`, `app-table`/`app-data-grid`, `app-empty-state`, `app-skeleton` |
| `layout-list-detail-drawer` | Layout | List/detail admin screen with drawer editing | `app-table`/`app-data-grid`, `app-drawer`, `app-card`, `app-button`, `app-dropdown-menu`, `app-pagination` |
| `layout-settings-tabs-sections` | Layout | Settings/admin configuration grouped by tabs | `app-tabs`, `app-card`, `app-switch`, `app-checkbox`, `app-radio-group`, `app-alert`, `app-button` |
| `layout-wizard-progress-steps` | Layout | Multi-step workflow shell (desktop tabs/mobile accordion) | `app-progress`, `app-tabs`, `app-accordion`, `app-card`, `app-button`, `app-alert` |

## Pattern Citation Format

Use this exact line inside the Work Order `UI/UX Requirements` section:

```md
Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit
```

If no pattern fits, include both lines:

```md
Template Pattern References: none
Deviation Notes: No catalog pattern fits because the feature requires <specific reason>.
```

## General Rules

- Reuse `src/app/shared/ui` components before creating custom UI.
- Read `src/app/shared/ui/index.ts` and the top usage comments in the selected component files.
- Keep Tailwind utility classes in templates; avoid recreating utilities in feature CSS.
- Use typed Reactive Forms for form-centric features and render visible validation feedback.
- Assume shared UI form controls are non-CVA unless explicitly documented; use `[value]`/`(valueChange)` or `[(value)]`/`[(checked)]` bridge methods in TS.
- Use Angular native control flow (`@if`, `@for`, `@switch`) and signals for state ownership.

## Links to Detailed Recipes

- [Core Form Patterns](./forms-core.md)
- [Core Layout Patterns](./layouts-core.md)
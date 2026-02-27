# Rule Catalog

This folder contains compact prompt rules used by `orchestrator_py/index.py`.

## Format
- File: `catalog.json`
- Top-level keys:
  - `version`: integer
  - `rules`: array of rule cards
- Rule card fields:
  - `id`: stable uppercase snake-case identifier
  - `roles`: one or more of `planner`, `developer`, `validator`
  - `priority`: `required` | `default` | `conditional`
  - `tags`: relevance tags used for conditional selection
  - `text`: concise instruction text (1-3 lines)

## Selection behavior
- Required rules are always included for the role.
- Default rules are included by priority/relevance until role max count.
- Conditional rules are included only when user-story signals match tags.

## Maintenance rules
- Keep IDs stable; do not rename existing IDs without migration.
- Prefer adding new rules instead of expanding existing rule text.
- Keep rule text short and atomic.
- Avoid embedding large prose blocks in `index.py`; this catalog is the source of truth.

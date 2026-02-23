# Agent / Instructions / Skills Audit (Angular v20-v21)

Date: 2026-02-23

## Scope

- `AGENTS.md`
- `instructions.md`
- `ai-angular-blueprint.txt`
- `orchestrator/src/index.ts` prompts and workflow glue
- Codex Angular skills (referenced conceptually via local skill set) -> recreated as orchestrator-native skill pack

## Findings (before remediation)

1. **Cross-version gap (Medium)**
   - Workflow/docs were mostly written as Angular v21-only, while generated apps may need to be compatible with Angular v20 or v21.
   - Risk: planners/validators over-enforce v21-specific expectations (especially zoneless assumptions).

2. **No orchestrator-native skill layer (Medium)**
   - The orchestrator prompts had many hardcoded rules but no reusable, role-oriented skill pack derived from the Codex Angular skills.
   - Risk: prompt drift and duplicated guidance across planner/developer/validator.

3. **Complexity guidance inconsistent (Medium)**
   - Complex form/shared-UI stories needed clearer role-specific handling (planner traceability, developer execution checklists, validator audit order).
   - Risk: Work Orders and validation feedback become inconsistent across runs.

4. **User-story data fidelity depended mainly on prompt behavior (Low/Medium)**
   - Work Order quality checks existed, but no explicit skill-based checklist documenting data-point extraction and traceability patterns.
   - Risk: future prompt edits regress planning quality.

## Remediations Applied

- Added local orchestrator skill pack derived from Codex Angular skills:
  - `orchestrator/skills/angular-orchestrator-v20-v21/SKILL.md`
  - `orchestrator/skills/angular-orchestrator-v20-v21/references/*.md`
- Added source mapping from Codex Angular skills -> orchestrator skill pack:
  - `orchestrator/skills/angular-orchestrator-v20-v21/references/source-skill-map.md`
- Wired orchestrator to load skill context and inject it into planner/developer/validator prompts:
  - `orchestrator/src/index.ts`
- Added Angular version detection (`package.json`) and prompt context so agents remain v20/v21 compatible:
  - `orchestrator/src/index.ts`
- Updated docs to explicitly support Angular v20/v21 and reference the orchestrator skill pack:
  - `AGENTS.md`
  - `instructions.md`
  - `ai-angular-blueprint.txt`

## Residual Risks / Follow-up

- The orchestrator still relies on LLM reasoning for some semantic validation gaps (beyond deterministic checks).
- If the template changes to Angular v22+, version compatibility guidance should be extended and prompt context updated accordingly.

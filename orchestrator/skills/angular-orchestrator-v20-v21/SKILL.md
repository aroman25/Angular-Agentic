---
name: angular-orchestrator-v20-v21
description: Version-aware Angular (v20/v21) planning, development, and validation guidance for the local multi-agent orchestrator. Use when generating or auditing Angular features from user stories with shared UI, forms, Tailwind, Angular Aria, and Vitest.
---

# Angular Orchestrator (v20/v21)

Use this skill as the orchestrator's reusable guidance layer for Planner/Developer/Validator agents.

## When to use

- Generating Angular features from user stories
- Building form-heavy flows with validation
- Reusing shared UI libraries with Angular Aria wrappers
- Auditing generated apps for regressions
- Supporting Angular v20 and v21 templates

## Workflow

1. Read `references/version-compatibility.md` for Angular v20/v21 rules.
2. Read `references/template-pattern-catalog.md` for the template-hosted form/layout pattern catalog usage rules.
3. Read the role-specific guide:
   - Planner: `references/planner-workorders.md`
   - Developer: `references/developer-execution.md`
   - Validator: `references/validator-audit.md`
4. Use `references/source-skill-map.md` to understand which Codex Angular skills were synthesized into this orchestrator skill pack.

## Notes

- This skill pack is intentionally concise and orchestration-focused.
- It complements (not replaces) `AGENTS.md`, `instructions.md`, and `ai-angular-blueprint.txt`.

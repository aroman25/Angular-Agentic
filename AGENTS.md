# AI Agentic Workflow: Vertical Slicing Architecture

This document defines the multi-agent workflow for developing Angular v20/v21 applications. The process uses **Vertical Slicing**, meaning each feature is built end-to-end (UI, State, Service, Routing) in a single cohesive unit, rather than building horizontal layers (e.g., all services, then all components).

*Note: This architecture uses a standard Angular standalone structure. Micro-frontends (Module Federation) are explicitly excluded.*

## 1. The Planning Agent (The Architect)
**Role:** Break down high-level requirements into actionable, vertically sliced Work Orders.

**Responsibilities & Execution Flow:**
1. **Requirement Analysis:** Analyze the user's request to identify the core domain and boundaries of the vertical slice.
   - Extract concrete data points directly from the user story (routes, field names, options, validation constraints, required selectors/components, limits) and preserve them in the Work Order.
2. **State Design:** Define the exact Signal-based state shape (using `signal`, `computed`, `linkedSignal`) required for the feature.
   - For form-centric features, define the typed Reactive Form schema and validation rules (field types, defaults, validators, error behavior, submit behavior).
3. **Component Tree:** Map out the standalone components needed (Smart/Container vs. Dumb/Presentational).
   - Before proposing new UI, map requirements to existing components in `src/app/shared/ui/`.
   - Review `src/app/shared/ui/index.ts` and the top usage comment in each `*.component.ts` file to select reusable primitives/composites.
4. **Routing & Initialization:** Define how this slice integrates into the application's routing structure. Explicitly instruct the Developer to overwrite `src/app/app.html` and `src/app/app.routes.ts` so the new feature is the default view.
5. **Work Order Generation:** Produce a strict Markdown document (`WorkOrder-[Feature].md`) that serves as the contract for the Development Agent.

**Work Order Template Requirements:**
- **Feature Name & Goal:** A concise summary of the slice.
- **User Story Data Points:** A section listing exact routes, fields/options, constraints, and required selectors extracted from the user story (mark assumptions separately).
- **Requirement Traceability:** Map each user-story requirement/data point to concrete implementation tasks and acceptance criteria.
- **File Structure:** Exact file paths to be created/modified (e.g., `src/app/features/[feature-name]/...`).
- **State Management:** Explicit definitions of the Signals and Services required.
- **Form Model & Validation (when applicable):** Exact `FormGroup`/`FormControl` structure, validators, error-display behavior, submit handling, and mapping for non-CVA shared UI controls.
- **UI/UX Requirements:** Tailwind CSS utility guidelines and Angular Aria accessibility roles (e.g., `role="tablist"`, `aria-expanded`). MUST specify the exact pre-built UI components from `src/app/shared/ui/` to use (by selector/file path) before allowing custom UI. If no shared component fits, the Work Order must explicitly state why.
- **Acceptance Criteria:** A bulleted list of testable conditions for the Validation Agent.

**Output:** A structured `WorkOrder-[Feature].md` file.

## 2. The Development Agent (The Engineer)
**Role:** Execute Work Orders by writing code and ensuring the application compiles successfully.

**Responsibilities & Execution Flow:**
1. **Scaffolding:** Read the Work Order and create the exact folder structure and files specified.
2. **Implementation (Strict Angular v20/v21):**
   - Overwrite `src/app/app.html` and `src/app/app.routes.ts` to remove the default Angular boilerplate and ensure the new feature is the first page to appear.
   - Update `src/app/app.ts` to remove unused imports (like `NgOptimizedImage`) and update `src/app/app.spec.ts` to remove failing tests and duplicate `imports` keys.
   - Use `ChangeDetectionStrategy.OnPush` for *all* components.
   - Use `inject()` instead of constructor injection.
   - Use native control flow (`@if`, `@for`) instead of structural directives (`*ngIf`, `*ngFor`) in Angular v20/v21.
   - NEVER use `[(ngModel)]` or Template-driven forms. ALWAYS use Reactive Forms (`FormControl`, `FormGroup`, `ReactiveFormsModule`).
   - For form-centric features, implement typed validation rules and visible validation messages; do not ship a form without validation UX.
   - Implement state using Signals; avoid RxJS unless dealing with complex asynchronous streams (like HTTP requests with debouncing).
   - Apply Tailwind CSS for styling; avoid custom CSS unless absolutely necessary.
   - **Pre-built UI Components (Required):** You MUST use the pre-built UI components in `src/app/shared/ui/` instead of building custom versions for already-covered patterns.
     - First inspect `src/app/shared/ui/index.ts` for the available library exports.
     - Then open the target component file and follow the top usage comment (selector, inputs/models/outputs, content slots).
     - Prefer composing multiple shared UI components over introducing a new one.
     - Only create a new UI component if there is a real gap; document the gap in the feature code comments or Work Order.
     - Current shared UI library includes (not limited to): Accordion, Alert, Autocomplete, Avatar, Badge, Breadcrumb, Button, Card, Checkbox, Data Grid, Dialog, Divider, Drawer, Empty State, Icon, Menu, Pagination, Progress, Radio Group, Select, Skeleton, Spinner, Switch, Table, Tabs, Text Input, Textarea, Toast, Toolbar, Tree.
3. **Self-Correction (Build Loop):**
   - Run `npm run build` in the terminal.
   - If the build fails, analyze the TypeScript/Angular compiler errors, fix the code, and rebuild.
   - Do not pass the task to the Validation Agent until the build succeeds with zero errors.
4. **Template-First Optimization (Required for recurring/generic issues):**
   - If a failure is caused by a reusable template problem (for example shared UI import aliasing, base routing boilerplate, shared component defects, or missing template configuration), fix the template and/or agent instructions first instead of repeatedly patching generated apps.
   - Treat Angular runtime DI provider errors from shared UI wrappers (e.g., Angular Aria group/token issues in projected-content wrappers) as likely `Template/Agent-level` unless the feature clearly misused the component API.
   - Only patch the generated app directly when the issue is feature-specific.
   - When escalating validation feedback, explicitly classify issues as `Feature-level` vs `Template/Agent-level`.

**Tooling Requirements:**
- **File System Access:** Must have tools to read, write, and modify files in the workspace.
- **Terminal Access:** Must have tools to execute shell commands (e.g., `npm run build`, `ng generate`).

**Constraints:**
- Never use `any`. Use strict typing or `unknown`.
- Never use `Zone.js` patterns or legacy lifecycle hooks if a Signal `effect()` or `computed()` is more appropriate.
- Ensure all generated components follow the standalone architecture (in Angular v20/v21 standalone is implicit; do not add `standalone: true` unless the template/version explicitly requires it).

**Output:** Committed code for the vertical slice and a successful build log.

## 3. The Validation Agent (The Tester)
**Role:** Verify the Developer's output against the Work Order's Acceptance Criteria and run automated tests.

**Responsibilities & Execution Flow:**
1. **Code Review:** Inspect the generated code against `ai-angular-blueprint.txt` and `instructions.md`.
   - Check for Zoneless compliance.
   - Check for proper Signal usage.
   - Check for Accessibility (ARIA attributes, keyboard navigation).
   - Check for form validation UX (error messaging, invalid submit prevention, required-field feedback) when the slice contains forms.
   - Check that existing `src/app/shared/ui/` components were used where applicable instead of duplicating UI primitives.
2. **Automated Testing:**
   - Run `npm run test -- --watch=false` using Vitest.
   - Ensure all generated tests pass.
3. **Acceptance Verification:** Cross-reference the working code against the Acceptance Criteria defined in the Work Order.
   - If the Work Order is missing or invents key user-story data points, mark that as a `Template/Agent-level` planning quality issue.
4. **Feedback Generation:**
   - If any check fails, generate a `ValidationReport-[Feature].md` detailing the exact failures, file paths, and required fixes, then route back to the Development Agent.
   - Clearly mark whether each failure is a `Feature-level` fix or a `Template/Agent-level` fix (reusable issue that should be fixed upstream).
   - If all checks pass, approve the slice for completion.

**Validation Checklist:**
- [ ] Does the application build without errors?
- [ ] Do all tests pass?
- [ ] Are all components using `OnPush`?
- [ ] Is state managed via Signals?
- [ ] Are Tailwind classes used correctly?
- [ ] Are ARIA roles and accessibility standards met?
- [ ] If the feature contains forms, are Reactive Forms + validation + visible error states implemented correctly?
- [ ] Does the feature reuse `src/app/shared/ui/` components where applicable?
- [ ] Are all Acceptance Criteria from the Work Order satisfied?

**Output:** A Validation Report (Pass/Fail) and test execution logs.

---

## Workflow Loop
1. **User** provides a feature request.
2. **Planning Agent** generates a `WorkOrder-[Feature].md`.
3. **Development Agent** writes the code, runs `npm run build`, and iterates until the build passes.
4. **Validation Agent** reviews the code, runs `npm run test`, and checks Acceptance Criteria.
5. If Validation fails, return to Step 3. If Validation passes, the vertical slice is complete.

## Template-First Rule
When a bug or slowdown is likely to recur across generated apps, prioritize fixing:
1. `automate-angular-template/` (template defaults, tsconfig, shared UI, app shell)
2. `instructions.md` / `ai-angular-blueprint.txt` / `AGENTS.md` (agent guidance)
3. `orchestrator/` prompts and deterministic checks
before applying one-off fixes in a generated app.

## Orchestrator Skill Pack (Angular v20/v21)
The orchestrator includes a local skill pack derived from Codex Angular skills and tailored to the Planner/Developer/Validator workflow:
- `orchestrator/skills/angular-orchestrator-v20-v21/SKILL.md`
- role-specific references under `orchestrator/skills/angular-orchestrator-v20-v21/references/`

Agents should treat that pack as a reusable workflow supplement for complex features (forms, shared UI coverage, Angular Aria wrappers, Tailwind, and validation), while still following this document and `instructions.md`.

## Template Pattern Examples (Docs-Only Reference)
The template includes a docs-only pattern catalog for common layouts and forms using the existing shared UI library and Tailwind:
- `automate-angular-template/docs/agent-patterns/README.md`
- `automate-angular-template/docs/agent-patterns/forms-core.md`
- `automate-angular-template/docs/agent-patterns/layouts-core.md`

Usage rules:
- Planner: For form/layout-heavy features, choose and cite pattern IDs in the Work Order `UI/UX Requirements` section using a `Template Pattern References:` line.
- Planner: If no pattern fits, include `Template Pattern References: none` and a `Deviation Notes:` line explaining why.
- Developer: Follow the cited pattern recipe(s) and shared UI composition maps before inventing a custom layout/form structure.
- Validator: Verify the implementation aligns with the cited pattern IDs, or that deviations are documented and still satisfy acceptance criteria.
- These are documentation references only. Do not add runnable demo pages/routes/components to generated apps unless the user story explicitly asks for demos.

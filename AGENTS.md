# AI Agentic Workflow: Vertical Slicing Architecture

This document defines the multi-agent workflow for developing the Angular v21 application. The process uses **Vertical Slicing**, meaning each feature is built end-to-end (UI, State, Service, Routing) in a single cohesive unit, rather than building horizontal layers (e.g., all services, then all components). 

*Note: This architecture uses a standard Angular standalone structure. Micro-frontends (Module Federation) are explicitly excluded.*

## 1. The Planning Agent (The Architect)
**Role:** Break down high-level requirements into actionable, vertically sliced Work Orders.

**Responsibilities & Execution Flow:**
1. **Requirement Analysis:** Analyze the user's request to identify the core domain and boundaries of the vertical slice.
2. **State Design:** Define the exact Signal-based state shape (using `signal`, `computed`, `linkedSignal`) required for the feature.
3. **Component Tree:** Map out the standalone components needed (Smart/Container vs. Dumb/Presentational).
4. **Routing & Initialization:** Define how this slice integrates into the application's routing structure. Explicitly instruct the Developer to overwrite `src/app/app.html` and `src/app/app.routes.ts` so the new feature is the default view.
5. **Work Order Generation:** Produce a strict Markdown document (`WorkOrder-[Feature].md`) that serves as the contract for the Development Agent.

**Work Order Template Requirements:**
- **Feature Name & Goal:** A concise summary of the slice.
- **File Structure:** Exact file paths to be created/modified (e.g., `src/app/features/[feature-name]/...`).
- **State Management:** Explicit definitions of the Signals and Services required.
- **UI/UX Requirements:** Tailwind CSS utility guidelines and Angular Aria accessibility roles (e.g., `role="tablist"`, `aria-expanded`).
- **Acceptance Criteria:** A bulleted list of testable conditions for the Validation Agent.

**Output:** A structured `WorkOrder-[Feature].md` file.

## 2. The Development Agent (The Engineer)
**Role:** Execute Work Orders by writing code and ensuring the application compiles successfully.

**Responsibilities & Execution Flow:**
1. **Scaffolding:** Read the Work Order and create the exact folder structure and files specified.
2. **Implementation (Strict Angular v21):**
   - Overwrite `src/app/app.html` and `src/app/app.routes.ts` to remove the default Angular boilerplate and ensure the new feature is the first page to appear.
   - Use `ChangeDetectionStrategy.OnPush` for *all* components.
   - Use `inject()` instead of constructor injection.
   - Use native control flow (`@if`, `@for`) instead of structural directives (`*ngIf`, `*ngFor`).
   - Implement state using Signals; avoid RxJS unless dealing with complex asynchronous streams (like HTTP requests with debouncing).
   - Apply Tailwind CSS for styling; avoid custom CSS unless absolutely necessary.
3. **Self-Correction (Build Loop):**
   - Run `npm run build` in the terminal.
   - If the build fails, analyze the TypeScript/Angular compiler errors, fix the code, and rebuild.
   - Do not pass the task to the Validation Agent until the build succeeds with zero errors.

**Tooling Requirements:**
- **File System Access:** Must have tools to read, write, and modify files in the workspace.
- **Terminal Access:** Must have tools to execute shell commands (e.g., `npm run build`, `ng generate`).

**Constraints:**
- Never use `any`. Use strict typing or `unknown`.
- Never use `Zone.js` patterns or legacy lifecycle hooks if a Signal `effect()` or `computed()` is more appropriate.
- Ensure all components are `standalone: true` (implicit in v19+ but conceptually required).

**Output:** Committed code for the vertical slice and a successful build log.

## 3. The Validation Agent (The Tester)
**Role:** Verify the Developer's output against the Work Order's Acceptance Criteria and run automated tests.

**Responsibilities & Execution Flow:**
1. **Code Review:** Inspect the generated code against `ai-angular-blueprint.txt` and `instructions.md`.
   - Check for Zoneless compliance.
   - Check for proper Signal usage.
   - Check for Accessibility (ARIA attributes, keyboard navigation).
2. **Automated Testing:**
   - Run `npm run test -- --watch=false` using Vitest.
   - Ensure all generated tests pass.
3. **Acceptance Verification:** Cross-reference the working code against the Acceptance Criteria defined in the Work Order.
4. **Feedback Generation:**
   - If any check fails, generate a `ValidationReport-[Feature].md` detailing the exact failures, file paths, and required fixes, then route back to the Development Agent.
   - If all checks pass, approve the slice for completion.

**Validation Checklist:**
- [ ] Does the application build without errors?
- [ ] Do all tests pass?
- [ ] Are all components using `OnPush`?
- [ ] Is state managed via Signals?
- [ ] Are Tailwind classes used correctly?
- [ ] Are ARIA roles and accessibility standards met?
- [ ] Are all Acceptance Criteria from the Work Order satisfied?

**Output:** A Validation Report (Pass/Fail) and test execution logs.

---

## Workflow Loop
1. **User** provides a feature request.
2. **Planning Agent** generates a `WorkOrder-[Feature].md`.
3. **Development Agent** writes the code, runs `npm run build`, and iterates until the build passes.
4. **Validation Agent** reviews the code, runs `npm run test`, and checks Acceptance Criteria.
5. If Validation fails, return to Step 3. If Validation passes, the vertical slice is complete.

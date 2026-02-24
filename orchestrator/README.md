# Angular Agentic Orchestrator README

This document explains how the local `orchestrator/` works, what it requires, what it reads/writes, and how to run/debug it safely.

It is based on the actual implementation in `orchestrator/src/index.ts` and `orchestrator/src/tools.ts` (not just intended behavior).

## What This Orchestrator Does

The orchestrator is a local multi-agent workflow runner that:

1. Resets and clones the Angular template into `generated-app/`
2. Installs the generated app dependencies
3. Runs a **Planner agent** to create a Work Order from `orchestrator/user-story.md`
4. Runs a **Developer agent** to implement the feature in `generated-app/`
5. Runs a **Validator agent** to verify the result
6. Loops Developer -> Validator until validation passes or max iterations are reached

It uses:

- LangGraph (`@langchain/langgraph`) for the state graph
- OpenAI chat model via `@langchain/openai`
- A local tool layer (`read_file`, `write_code`, `run_command`) scoped to `generated-app/`
- Deterministic pre-validation checks (build/test + code scans) before the LLM validator

## Repository Assumptions (Required)

The orchestrator code assumes this repo structure exists:

- `automate-angular-template/` (source Angular template)
- `ai-angular-blueprint.txt` (global build guidance)
- `instructions.md` (global workflow instructions)
- `orchestrator/user-story.md` (feature request input)
- `orchestrator/skills/angular-orchestrator-v20-v21/...` (local skill pack + references)

The pathing is relative and hardcoded in `orchestrator/src/index.ts`, so moving folders will break runs unless you update the code.

## What Is Required To Run It

### 1. Node.js + npm

You need a modern Node.js version compatible with:

- `tsx` (used by `orchestrator`)
- Angular 21 template tooling in `automate-angular-template`

Practical recommendation:

- Node.js 20+ (recommended)
- npm available on PATH

Notes:

- `orchestrator/package.json` uses `tsx src/index.ts`
- The generated Angular app runs `ng build` / `ng test` via npm scripts
- The template `package.json` currently declares `packageManager: npm@11.6.0`

### 2. OpenAI API Key (Required)

The orchestrator loads environment variables from `orchestrator/.env` using `dotenv`.

Required variable:

- `OPENAI_API_KEY`

`orchestrator/.env.example` currently contains:

```env
OPENAI_API_KEY=xxx
```

Create `orchestrator/.env` and set a real key:

```env
OPENAI_API_KEY=your_real_key_here
```

Important:

- Do not commit real API keys.
- The orchestrator code does not currently expose model selection via env; the model is hardcoded in `orchestrator/src/index.ts`.

### 3. Network Access (Required)

The run requires internet access for:

- OpenAI API calls (Planner, Developer, Validator agents)
- `npm install` inside `generated-app/`

If your network uses a proxy, you may need npm/OpenAI proxy configuration outside this repo.

### 4. File System Permissions (Required)

The orchestrator needs permission to:

- Delete/recreate `generated-app/`
- Write to:
  - `generated-app/**`
  - `orchestrator/last-work-order.md`
  - `orchestrator/last-validation-feedback.md`
- Install npm dependencies in `generated-app/node_modules`

### 5. Runtime Cost/Time Budget (Practical Requirement)

This workflow can be expensive/slow because it may:

- Call the LLM multiple times across multiple agents and retries
- Run `npm install`
- Run `npm run build`
- Run `npm run test -- --watch=false`
- Iterate several times if validation fails

The orchestrator prints token usage totals at the end of a run.

## Quick Start (Recommended)

From the repo root:

1. Install orchestrator dependencies

```powershell
cd orchestrator
npm install
```

2. Create your env file

```powershell
Copy-Item .env.example .env
```

3. Edit `orchestrator/.env` and set `OPENAI_API_KEY`

4. Edit `orchestrator/user-story.md` with the feature request

5. Run the orchestrator

```powershell
npm start
```

6. Inspect outputs

- Generated app: `generated-app/`
- Last work order: `orchestrator/last-work-order.md`
- Last validation feedback: `orchestrator/last-validation-feedback.md`

## How The Orchestrator Works (Detailed)

## High-Level Flow

The orchestrator builds a LangGraph state machine with these nodes:

- `planner`
- `developer`
- `validator`

Graph flow:

- `START -> planner -> developer -> validator`
- `validator -> END` on PASS or max iterations reached
- `validator -> developer` on failure (retry loop)

The graph is compiled and invoked in `main()` from `orchestrator/src/index.ts`.

## Step 1: Template Setup (`setupProject()`)

Before any agent runs, the orchestrator prepares a fresh generated app.

Behavior:

1. Attempts to clean up processes that might be locking `generated-app/` (Windows only)
2. Removes `generated-app/`
3. Falls back to archive/empty/reset strategies if deletion fails
4. Copies `automate-angular-template/` to `generated-app/`
5. Runs `npm install` in `generated-app/`

### Windows Process Cleanup (Best Effort)

On Windows, it runs a PowerShell cleanup that:

- Enumerates `Win32_Process`
- Finds `node`/`esbuild` processes whose command line references `generated-app`
- Stops them forcefully

This is to prevent file-lock issues from previous `ng serve` / build processes.

### Template Copy Ignore Rules

The copy excludes these directories when cloning the template:

- `node_modules`
- `dist`
- `.angular`
- `.git`

This is controlled by `TEMPLATE_COPY_IGNORES` in `orchestrator/src/index.ts`.

### Cleanup Fallbacks (If `generated-app` Is Locked)

If full folder removal fails, the orchestrator attempts:

1. Move `generated-app` to a timestamped `generated-app-stale-*` archive
2. `emptyDir` on `generated-app`
3. Reset the folder while preserving `node_modules` (best-effort fallback)

## Step 2: Input/Context Loading

After template setup, `main()` reads:

- `orchestrator/user-story.md`
- `ai-angular-blueprint.txt`
- `instructions.md`
- Orchestrator skill-pack references under `orchestrator/skills/angular-orchestrator-v20-v21/references/`
- Template pattern docs index at `automate-angular-template/docs/agent-patterns/README.md`

It also builds an Angular version context by reading `generated-app/package.json` and detecting `@angular/core` major version.

Current behavior:

- If Angular major is `20` or `21`, prompts include version-aware guidance
- Otherwise it falls back to a generic “assume v20/v21 compatibility” message

## Step 3: LLM Initialization

The orchestrator creates a single `ChatOpenAI` instance and reuses it across agents.

Current hardcoded config in `orchestrator/src/index.ts`:

- Model: `gpt-5-nano`
- Temperature: `0`

Token usage is tracked via LangChain callbacks and printed after the workflow completes.

Important limitation:

- There is no CLI flag or env var for model selection yet.
- To change the model, edit `orchestrator/src/index.ts`.

## Step 4: Planner Agent (`plannerNode`)

The Planner agent receives:

- User story
- Blueprint
- Instructions
- Orchestrator skill-pack content
- Angular version context

It must produce a Markdown Work Order for vertical-slice implementation.

### Planner Output

The planner writes the final Work Order to:

- `orchestrator/last-work-order.md`

### Planner Self-Correction Loop (Built In)

The planner can retry up to 3 times if the generated Work Order fails local quality checks.

The orchestrator validates the Work Order for:

- Required sections (Feature Goal, Data Points, Traceability, File Structure, State, UI/UX, Acceptance Criteria)
- Template pattern references for form/layout-heavy stories
- Explicit route preservation from the user story
- Shared UI selector preservation (e.g. required `app-*` selectors)
- Form planning quality for form-centric stories:
  - typed Reactive Forms planning
  - field-by-field validation matrix
  - non-CVA control binding strategy (`value` / `valueChange`)
- Form field fidelity (preserve enough user-story field names)

If quality checks fail, the orchestrator feeds the issues back into the planner prompt and requests a corrected full Work Order.

## Step 5: Developer Agent (`developerNode`)

The Developer agent is a LangGraph React agent (`createReactAgent`) with local tools.

It receives:

- The Work Order
- Optional validator feedback (on retries)
- Blueprint/instructions/skills/version context

It is explicitly instructed to:

- Read shared UI docs/comments before using components
- Overwrite `src/app/app.html` and `src/app/app.routes.ts`
- Update `src/app/app.ts` and `src/app/app.spec.ts`
- Use Angular Signals
- Use `ChangeDetectionStrategy.OnPush`
- Use `inject()` (not constructor DI)
- Use native Angular control flow (`@if`, `@for`, `@switch`)
- Use Reactive Forms (no `[(ngModel)]`)
- Reuse `src/app/shared/ui/` components
- Build with zero Angular warnings (not just zero errors)

### Developer Iteration / Recursion Limits

The developer agent recursion limit changes based on retry type:

- Normal run: `220`
- Deterministic-validator retry: `320` (more room for focused fixes)

When retrying after deterministic validation failures, the prompt instructs the Developer to make minimal targeted fixes instead of rewriting the feature.

### Developer Output Location

The Developer can only write inside:

- `generated-app/` (via the orchestrator tools)

## Step 6: Validator Phase (`validatorNode`)

Validation happens in two layers:

1. Deterministic validator checks (always first)
2. LLM Validator agent (only if deterministic checks pass)

This design reduces wasted LLM calls when basic checks are failing.

## Deterministic Validator (Important)

The deterministic validator scans files in:

- `generated-app/src/app/**/*.(ts|html|css)`

It also runs commands in `generated-app/`:

- `npm.cmd run build`
- `npm.cmd run test -- --watch=false`

### What It Enforces

The deterministic validator checks for all of the following (based on user story + work order context):

- Angular template rules:
  - no `*ngIf`, `*ngFor`, `*ngSwitch*`
  - no `[(ngModel)]`
  - no arrow functions in templates
- TypeScript rules:
  - no `@Input`
  - no `@Output`
  - no `any`
- Component rules:
  - every `.component.ts` must include explicit `changeDetection`
  - every `.component.ts` must include `ChangeDetectionStrategy.OnPush`
- Form/shared-control rule:
  - blocks `formControlName` on shared UI controls like `app-select`, `app-text-input`, `app-checkbox`, etc. (unless explicitly supported)
- Tailwind hygiene in feature CSS:
  - no redefinition of utility classes like `.container`, `.grid`, `.grid-cols-*`, `.flex`
- App shell/routing checks:
  - `src/app/app.html` should include `<router-outlet />`
  - `src/app/app.routes.ts` must include default redirect and expected feature route
- Form validation requirements (when the story/work order is form-centric):
  - ReactiveFormsModule usage
  - typed form model usage (`FormGroup`/`FormControl`/`FormBuilder`)
  - validators present
  - at least one `<form>`
  - visible validation UI
  - submit button (`type="submit"`)
- Shared UI coverage requirements:
  - if the user story explicitly lists required `app-*` selectors, each selector must appear at least once in feature HTML
- Build/test commands:
  - build must pass
  - tests must pass
  - Angular build warnings are treated as failures

### Template-Level Risk Detection (Reusable Defects)

The deterministic validator also includes a targeted check for a known Angular Aria content-projection risk in shared UI wrappers (example: accordion group provider placement issues).

If detected, it classifies the issue as:

- `Template/Agent-level`

This helps push reusable fixes upstream into the template instead of patching every generated app.

## LLM Validator Agent

If deterministic checks pass, the LLM Validator agent performs semantic review against the Work Order and user story.

It is instructed to:

- Run tests and inspect code
- Verify shared UI reuse (based on actual imports/selectors, not guessed folder names)
- Verify forms/validation UX where required
- Check acceptance criteria compliance
- Classify failures as:
  - `Feature-level`
  - `Template/Agent-level`

If it passes with full confidence, it must return exactly:

- `PASS`

Otherwise it returns a failure report with concrete fixes.

### Validator Feedback Normalization

The orchestrator normalizes one known validator false-positive pattern:

- Confusing `app-*` selectors with literal folder paths under `src/app/shared/ui/`

If that specific false-positive pattern is detected, the orchestrator can convert the validator result to `PASS`.

The normalized validator result is written to:

- `orchestrator/last-validation-feedback.md`

## Looping / Retry Behavior

After validation:

- If validator feedback is `PASS` -> workflow ends
- Otherwise -> route back to Developer (retry)

Max workflow iterations are dynamic:

- Default: `5`
- Complex shared UI coverage stories: `7`
- Complex shared UI + form validation stories: `8`

Complexity is inferred from user-story selector count and form-validation requirements.

## Agent State (LangGraph State)

The orchestrator stores this shared state in the graph:

- `userStory`
- `blueprint`
- `instructions`
- `orchestratorSkills`
- `angularVersionContext`
- `workOrder`
- `validationFeedback`
- `iterations` (reducer increments across developer retries)

## Local Tooling Available To Developer/Validator Agents

Defined in `orchestrator/src/tools.ts`:

- `write_code`
- `read_file`
- `run_command`

All tools operate relative to:

- `generated-app/` (via `TARGET_DIR`)

### `write_code`

- Writes arbitrary file content under `generated-app/`
- Ensures parent directories exist

### `read_file`

- Reads files under `generated-app/`
- Returns a readable error message if the file does not exist

### `run_command`

- Runs shell commands inside `generated-app/`
- Captures stdout/stderr
- Returns success/failure output as a string

#### Safety Guardrails In `run_command`

Some commands are explicitly rejected to avoid long-running locks or recursive orchestration:

- `npm start`
- `ng serve`
- recursive orchestrator invocation (`tsx ... orchestrator ...`)
- watch-mode commands unless they explicitly use `--watch=false`

This is especially important because `ng serve` can lock files and break template reset/delete behavior.

## Files The Orchestrator Reads

At orchestrator startup:

- `orchestrator/user-story.md`
- `ai-angular-blueprint.txt`
- `instructions.md`
- `generated-app/package.json` (after template copy, for Angular version detection)

Skill-pack and template docs context:

- `orchestrator/skills/angular-orchestrator-v20-v21/references/version-compatibility.md`
- `orchestrator/skills/angular-orchestrator-v20-v21/references/template-pattern-catalog.md`
- `orchestrator/skills/angular-orchestrator-v20-v21/references/planner-workorders.md`
- `orchestrator/skills/angular-orchestrator-v20-v21/references/developer-execution.md`
- `orchestrator/skills/angular-orchestrator-v20-v21/references/validator-audit.md`
- `automate-angular-template/docs/agent-patterns/README.md`

During agent execution:

- Files under `generated-app/` as requested via `read_file`

## Files The Orchestrator Writes

Generated app and build outputs:

- `generated-app/**`

Planner/validator artifacts:

- `orchestrator/last-work-order.md`
- `orchestrator/last-validation-feedback.md`

Potential fallback archive on deletion failure:

- `generated-app-stale-<timestamp>/`

## How To Prepare `user-story.md` (Input Contract)

The orchestrator does not take CLI arguments for the feature request. It reads:

- `orchestrator/user-story.md`

Best results come from a structured user story that includes explicit:

- Feature goal
- Required route(s)
- Required fields/options
- Validation requirements
- Shared UI selectors (`app-*`) if coverage is required
- Accessibility expectations
- Accept/reject constraints

The current sample `orchestrator/user-story.md` is a good reference for level of detail.

## Run Commands (Exact)

### First-time setup (or after dependency changes)

```powershell
cd orchestrator
npm install
```

### Run the orchestrator

```powershell
cd orchestrator
npm start
```

Under the hood, this executes:

```powershell
tsx src/index.ts
```

## Expected Console Output (High-Level)

A typical run logs phases like:

- `Cloning template to fresh generated-app directory...`
- `Installing dependencies in generated-app...`
- `Template ready!`
- `Starting Agentic Workflow...`
- `--- PLANNING AGENT ---`
- `--- DEVELOPMENT AGENT (Iteration X) ---`
- `--- VALIDATION AGENT ---`
- `Workflow Complete! App is ready.` (on success)
- Token usage summary

## Troubleshooting

## 1) `OPENAI_API_KEY` errors / auth failures

Symptoms:

- OpenAI request failures
- Authentication/authorization errors

Fixes:

- Ensure `orchestrator/.env` exists
- Ensure `OPENAI_API_KEY` is valid
- Restart the run after updating `.env`

## 2) `npm install` fails in `generated-app`

Symptoms:

- Setup fails before planner starts

Fixes:

- Check internet/proxy access
- Retry manually in `generated-app/` to inspect environment issues
- Verify Node/npm versions compatible with Angular template

## 3) `generated-app` cannot be deleted (Windows file lock)

Symptoms:

- Cleanup warnings
- Archive fallback messages
- Repeated stale folders

Fixes:

- Close any running `ng serve`, editors, or terminals pinned to `generated-app`
- Kill stray `node`/`esbuild` processes
- Delete `generated-app` / `generated-app-stale-*` manually and rerun

Note:

- The orchestrator already performs a best-effort PowerShell cleanup on Windows.

## 4) Build passes locally but deterministic validator fails

Symptoms:

- `Deterministic validator checks FAILED`

Cause:

- The deterministic validator enforces style/architecture rules beyond TypeScript correctness (examples: `@Input`, `*ngIf`, Angular warnings, missing `OnPush`, missing route redirect, no visible form validation UI).

Fix:

- Read `orchestrator/last-validation-feedback.md`
- Fix cited file paths/issues in `generated-app/`
- Rerun orchestrator (or patch the template/prompt if the issue is reusable)

## 5) Validator loops repeatedly / max iterations reached

Symptoms:

- `Max iterations reached. Stopping.`

Fixes:

- Inspect `orchestrator/last-work-order.md` for planning gaps
- Inspect `orchestrator/last-validation-feedback.md` for recurring failure patterns
- If the failure is reusable, patch:
  - `automate-angular-template/`
  - `instructions.md`
  - `ai-angular-blueprint.txt`
  - `orchestrator` prompts/checks

## 6) LLM validator false-positive on shared UI paths

The orchestrator already normalizes one known false-positive where selectors (`app-*`) are treated as folder names.

If you see similar path-assumption issues:

- Improve validator prompt wording in `orchestrator/src/index.ts`
- Prefer validating imports/selectors instead of guessed filesystem paths

## Current Limitations / Design Constraints

### Hardcoded model

- `gpt-5-nano` is hardcoded in `orchestrator/src/index.ts`
- No env var override yet

### Windows-specific command assumptions in deterministic checks

Deterministic validation uses:

- `npm.cmd run build`
- `npm.cmd run test -- --watch=false`

This is Windows-friendly, but if you run cross-platform and encounter issues, you may need to make command selection OS-aware in `orchestrator/src/index.ts`.

### No CLI flags for run-time options

The orchestrator currently does not accept CLI args for:

- alternate user-story path
- model selection
- max iterations override
- skipping setup/install
- skipping deterministic validation

All of these would require code changes.

### Full reset behavior on each run

Each run starts by rebuilding `generated-app/` from the template and running `npm install`. This is intentional for clean reproducibility, but slower.

## Customization Guide (Where To Edit)

If you want to change behavior, these are the key files:

- `orchestrator/src/index.ts`
  - graph flow
  - prompts
  - deterministic checks
  - model config
  - iteration logic
  - setup/reset behavior
- `orchestrator/src/tools.ts`
  - tool definitions
  - command restrictions
- `orchestrator/user-story.md`
  - feature request input
- `instructions.md` and `ai-angular-blueprint.txt`
  - cross-cutting agent behavior
- `orchestrator/skills/angular-orchestrator-v20-v21/references/*`
  - reusable planner/dev/validator guidance
- `automate-angular-template/`
  - template defaults and shared UI behaviors

## Security / Privacy Notes

Be aware that the orchestrator may send substantial project context to the LLM, including:

- user story contents
- blueprint/instructions
- skill-pack text
- selected generated app file contents read by agents
- validation feedback

Do not place secrets in:

- `orchestrator/user-story.md`
- template source files
- prompt/reference docs

Keep secrets in `.env` only (and never commit real values).

## Minimal Pre-Run Checklist

Before running:

- `orchestrator/.env` exists with `OPENAI_API_KEY`
- `orchestrator/node_modules` installed (`npm install` in `orchestrator/`)
- `orchestrator/user-story.md` updated
- `automate-angular-template/` is in a good state
- No running dev server locking `generated-app/`

## Post-Run Checklist

After running:

- Inspect `generated-app/`
- Inspect `orchestrator/last-work-order.md`
- Inspect `orchestrator/last-validation-feedback.md`
- Review console token usage summary
- If failures recur, classify as `Feature-level` vs `Template/Agent-level` and patch upstream where appropriate


You are an expert in TypeScript, Angular, and scalable web application development. You write functional, maintainable, performant, and accessible code following Angular and TypeScript best practices.
This workflow must remain compatible with Angular v20 and v21 templates unless a user story explicitly narrows the target version.
## TypeScript Best Practices
- Use strict type checking
- Prefer type inference when the type is obvious
- Avoid the `any` type; use `unknown` when type is uncertain
## Angular Best Practices
- Always use standalone components over NgModules
- Must NOT set `standalone: true` inside Angular decorators. It's the default in Angular v20+.
- Use signals for state management
- Implement lazy loading for feature routes
- Do NOT use the `@HostBinding` and `@HostListener` decorators. Put host bindings inside the `host` object of the `@Component` or `@Directive` decorator instead
- Use `NgOptimizedImage` for all static images.
  - `NgOptimizedImage` does not work for inline base64 images.
## Accessibility Requirements
- It MUST pass all AXE checks.
- It MUST follow all WCAG AA minimums, including focus management, color contrast, and ARIA attributes.
### Components
- Keep components small and focused on a single responsibility
- Use `input()` and `output()` functions instead of decorators
- Use `computed()` for derived state
- Set `changeDetection: ChangeDetectionStrategy.OnPush` in `@Component` decorator
- Prefer inline templates for small components
- NEVER use `[(ngModel)]` or Template-driven forms. ALWAYS use Reactive Forms (`FormControl`, `FormGroup`, `ReactiveFormsModule`).
- Do NOT use `ngClass`, use `class` bindings instead
- Do NOT use `ngStyle`, use `style` bindings instead
- When using external templates/styles, use paths relative to the component TS file.
- Tailwind CSS styling must be applied primarily via utility classes in templates.
- Do NOT recreate Tailwind utility classes in feature component CSS (e.g., `.container`, `.grid`, `.grid-cols-*`, `.flex`).
- Keep feature component CSS empty/minimal unless there is a clear non-utility styling need.
- **Pre-built UI Components:** You MUST use the pre-built UI components located in `src/app/shared/ui/` instead of building custom versions.
  - Discovery workflow (mandatory before writing custom UI):
    - Open `src/app/shared/ui/index.ts` to see available exports.
    - Open the chosen component file and read the top usage comment (selector + inputs/models/outputs + slots).
    - Compose with shared components first; only create a new UI component when no shared component fits.
  - Prefer barrel imports from `src/app/shared/ui` when practical in feature code.
    - The template supports the TypeScript path alias `src/*` (for example: `import { ButtonComponent } from 'src/app/shared/ui';`).
    - If a future template removes that alias, use relative imports instead.
  - Current shared UI library includes (not limited to):
    - `AccordionComponent`, `AccordionItemComponent`
    - `AlertComponent`, `ToastComponent`
    - `AutocompleteComponent`, `SelectComponent`
    - `AvatarComponent`, `BadgeComponent`, `CardComponent`, `DividerComponent`, `SkeletonComponent`, `SpinnerComponent`
    - `ButtonComponent`, `CheckboxComponent`, `RadioGroupComponent`, `SwitchComponent`, `TextInputComponent`, `TextareaComponent`
    - `BreadcrumbComponent`, `PaginationComponent`, `TabsComponent`, `DropdownMenuComponent`, `ToolbarComponent`
    - `TableComponent`, `DataGridComponent`, `TreeComponent`
  - `DialogComponent`, `DrawerComponent`, `EmptyStateComponent`, `ProgressComponent`
  - `IconComponent` (all `<svg>` must be wrapped in `app-icon`)
  - If you build a custom UI component that overlaps with `src/app/shared/ui/`, you MUST explain why the shared component was not suitable.
- **Template Pattern Catalog Rule (Forms/Layouts):**
  - For form-heavy or layout-heavy features, consult the template pattern catalog docs:
    - `automate-angular-template/docs/agent-patterns/README.md`
    - `automate-angular-template/docs/agent-patterns/forms-core.md`
    - `automate-angular-template/docs/agent-patterns/layouts-core.md`
  - In Work Orders/implementation notes, cite selected pattern IDs using a `Template Pattern References:` line.
  - Prefer the selected pattern's shared UI composition and Tailwind skeleton before inventing a custom structure.
  - If no pattern fits, document a short `Deviation Notes:` rationale.
- **Template-First Optimization Rule (Important):**
- If a problem is generic/reusable (for example shared UI import path issues, template configuration gaps, shared UI defects, boilerplate app shell issues, or repeated build/test failures caused by template defaults), treat it as a template/agent issue first.
  - Prefer fixing `automate-angular-template/`, `instructions.md`, `ai-angular-blueprint.txt`, or `orchestrator/` prompts/checks instead of repeatedly patching generated apps.
  - Angular runtime DI/provider errors coming from shared UI wrappers (for example Angular Aria token/group providers with projected children) should be treated as likely `Template/Agent-level` issues first. Inspect provider placement on the shared wrapper host vs internal wrapper elements.
  - Only apply a one-off generated-app fix when the issue is specific to that feature implementation.
  - When reporting failures, explicitly label them as `Feature-level` or `Template/Agent-level`.
  - When producing a Work Order, include a **User Story Data Points** section and a **Requirement Traceability** section. Routes, field names/options, limits, and required selectors must come from the user story unless clearly labeled as assumptions.

## Orchestrator Skill Pack (Derived From Codex Angular Skills)
- The orchestrator now maintains a local Angular skill pack at `orchestrator/skills/angular-orchestrator-v20-v21/`.
- It is a synthesis of the Codex Angular skills (forms, testing, accessibility, routing, state, tailwind, auditing) adapted for Planner/Developer/Validator prompts.
- When working on complex stories, consult the role-specific references in that folder to keep prompts, work orders, and validation checks aligned.

CRITICAL REACTIVE FORMS RULE FOR UI COMPONENTS:
Most custom UI components in `src/app/shared/ui/` (for example `app-select`, `app-autocomplete`, `app-text-input`, `app-checkbox`, `app-switch`, etc.) do NOT implement `ControlValueAccessor`. You CANNOT use `formControlName` on them unless a component explicitly documents CVA support.
Instead, you MUST bind their `value` model to the form control's value and update the control on `valueChange`.
Example:
```html
<app-select
  [options]="priorityOptions"
  [value]="taskForm.controls.priority.value"
  (valueChange)="updatePriority($event)">
</app-select>

// In component:
updatePriority(val: string | null) {
  if (val) this.taskForm.controls.priority.setValue(val as 'low' | 'medium' | 'high');
}
```
## State Management
- Use signals for local component state
- Use `computed()` for derived state
- Keep state transformations pure and predictable
- Do NOT use `mutate` on signals, use `update` or `set` instead
## Application Initialization & Routing
- When creating a new application or feature, you MUST overwrite the default `src/app/app.html` to remove the boilerplate template and replace it with your own layout or just `<router-outlet />`.
- You MUST update `src/app/app.routes.ts` to set the default route (`path: ''`) to redirect to your new feature, or load your feature directly.
- Ensure the main page of the feature is the first page to appear.
- NEVER use `import.meta.env` or `enableProdMode()`. Angular CLI handles production mode automatically. Do not modify `main.ts` unless absolutely necessary, and if you do, ensure you pass `appConfig` to `bootstrapApplication`.
- When you overwrite `app.html`, you MUST also update `src/app/app.ts` to remove `NgOptimizedImage` from the `imports` array if you are no longer using it.
- When you overwrite `app.html`, you MUST also update `src/app/app.spec.ts` to remove the test that checks for the `h1` element.
- Do NOT rename the root `App` class in `src/app/app.ts` unless you also update `src/main.ts` and `src/app/app.spec.ts` to match.

## Testing
- When writing tests, do NOT use `RouterTestingModule`. Use `provideRouter([])` in the `providers` array instead.
- Ensure your object literals do not have duplicate keys (e.g., multiple `imports` arrays in `TestBed.configureTestingModule`).
- This template uses Vitest expectations. Do NOT use Jasmine-only matchers like `toBeTrue()` / `toBeFalse()`.
  - Use `toBe(true)` / `toBe(false)` or `toBeTruthy()` / `toBeFalsy()` instead.

## Forms
- NEVER use `[(ngModel)]` or Template-driven forms.
- ALWAYS use Reactive Forms (`FormControl`, `FormGroup`, `ReactiveFormsModule`).
- If using `ReactiveFormsModule`, ensure you import it in the component's `imports` array.
- When using literal unions in FormControls, explicitly type them: `new FormControl<'low' | 'high'>('low', { nonNullable: true })`.
- Always use `{ nonNullable: true }` for FormControls to avoid `| null` or `| undefined` types.
- For form-heavy features, define validation rules explicitly (`Validators.*` and custom validators where needed); do not rely only on HTML `required` attributes.
- Render validation/error messages in the template using `touched`, `dirty`, and/or submitted state so users get actionable feedback.
- Disable submit while the form is invalid or pending and provide a visible submit result state (success/error summary, toast, alert, etc.) when the flow requires submission UX.
- For non-CVA shared UI controls (`app-select`, `app-autocomplete`, `app-checkbox`, `app-switch`, `app-radio-group`, etc.), create explicit bridge methods that read/write the corresponding `FormControl` via `value`/`valueChange`.
- Prefer helper methods for value normalization instead of template casts in form bindings.

## Templates
- Keep templates simple and avoid complex logic
- ALWAYS wrap `<svg>` elements in the `<app-icon>` component. Apply sizing and color classes (e.g., `class="w-5 h-5 text-gray-500"`) directly to the `<app-icon>` element, NOT the `<svg>` element. The `<app-icon>` component automatically handles sizing the SVG to fill its container.
- Use native control flow (`@if`, `@for`, `@switch`) instead of `*ngIf`, `*ngFor`, `*ngSwitch`. NEVER use `*ngFor` or `*ngIf`.
  - Example: `@for (item of items(); track item.id) { ... }` (Do NOT use `let item of items()`)
- Use the async pipe to handle observables
- Do not assume globals like (`new Date()`) are available.
- Do not write arrow functions in templates (they are not supported).
- When using Tailwind CSS, ensure you use standard utility classes. Tailwind v4 is configured natively via `@import "tailwindcss";` in `styles.css`. Do not add custom CSS unless absolutely necessary.
## Services
- Design services around a single responsibility
- Use the `providedIn: 'root'` option for singleton services
- Use the `inject()` function instead of constructor injection

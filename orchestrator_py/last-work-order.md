# Work Order: Two-Page To-Do Application (Landing + Home)

Feature Name & Goal
- Name: Two-Page To-Do Application (Landing + Home)
- Goal: Deliver a polished, production-ready two-page Angular v20/v21 app. The first page is a marketing-like landing page at “/”, the second page is a functional to-do home at “/home”. The landing page must load first and provide a clear CTA to navigate to the Home page. The Home page must allow adding, completing, filtering, and deleting tasks with accessible, responsive UI using the shared UI primitives.

Assumptions: If anything about visuals or exact copy is ambiguous, default to the guidance in the UI/UX Requirements and use the shared UI components to maintain consistency.

CRITICAL INSTRUCTION: Overwrite the default Angular boilerplate to make the landing page the default route:
- Overwrite src/app/app.html to render a layout or just <router-outlet />.
- Overwrite src/app/app.routes.ts to set the default route path: '' to redirect or load the landing route, and ensure the '/home' route exists.
- If you overwrite app.html, also update src/app/app.ts to remove NgOptimizedImage from the imports if not used, and remove related tests in app.spec.ts that expect the default h1 element.

Automated compatibility: The work must be compatible with Angular v20 and v21 templates, with a preference for zoneless patterns as described in the blueprint. Standalone components are the default in both versions.

User Story Data Points (extract exact routes, field lists/options, required selectors, validation rules, and acceptance-critical constraints)
Routes and Navigation
- Landing page route: /
- Home page route: /home
- Default initial load route: Landing page (path: '')
- Landing CTA: Primary CTA button labeled "Start Organizing" navigates to /home
- Landing secondary CTA: "View Demo Tasks" navigates to /home
- Home page navigation: A method to navigate back to / (button or link)

Data Model (Front-End Only)
- Task
  - id: string
  - title: string
  - completed: boolean
  - createdAt: string or number (timestamp)

Form (Quick Add Task)
- Field: title (text input)
- Validation Rules (triggered before submit; visible UX)
  - Required
  - Minimum length: 3 characters
  - Maximum length: 80 characters
  - Before submit: trim whitespace; a whitespace-only value is invalid
- Submit Behavior
  - Button label: Add Task
  - Submit disabled when form invalid
  - Inline validation messages displayed after field is touched or after submit attempt
  - On successful submit: input cleared; focus remains on the input
- Behavior notes: Bridge non-CVA UI controls to the Form via value/valueChange bindings

Task List & Actions
- Each task row displays:
  - Completion checkbox
  - Title text
  - Delete action
- Toggling completion updates immediately
- Completed tasks visually muted and struck-through
- Deleting a task updates immediately

Filters and Counts
- Filters: All, Active, Completed
- Default filter: All
- Header on Home page includes counts:
  - total tasks
  - active tasks
  - completed tasks
- Empty state messaging:
  - When no tasks exist: “No tasks yet — add one to get started.”
  - When filter yields no results: “No tasks match this filter.”

Accessibility & UX
- Semantic landmarks: header, main, section, nav
- Filter controls: clear active state (visual + ARIA)
- ValidationErrors: visible text under the input
- All interactive controls have accessible labels
- Empty state is readable and actionable, guiding task creation

Shared UI Selectors (must be used meaningfully)
- app-button
- app-card
- app-text-input
- app-checkbox
- app-empty-state
- app-badge

UI/UX Requirements
- Landing Page
  - Warm, editorial styling with a gradient/layered shapes background
  - Hero heading with benefit-driven message
  - Short supporting description (1-2 sentences)
  - Primary CTA: "Start Organizing" -> /home
  - Secondary CTA: "View Demo Tasks" -> /home
  - 3 feature highlights (e.g., quick capture, progress tracking, focused lists)
  - Small trust/benefit row (Local-only demo state, No sign-in required, Fast keyboard-friendly)
- Home Page
  - Centered content column
  - Card-based sections: Quick Add form, Task list
  - Badges for counts
  - Visual cue for completed tasks (muted, line-through)
  - Tailwind-based styling with utility classes
  - Focus management and accessible, keyboard-friendly controls
- Patterns (Template Pattern Catalog)
  - Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit
  - Rationale: landing page layout and a form-driven create/edit page pattern
  - If pattern use deviates, include Deviation Notes (document rationale)

State Management
- Use Signals for local state
- Computed for derived state (counts, filtered lists)
- No mutation of signals; use update() or set()
- Feature-specific signals:
  - Home page: tasks signal (Task[]), filter signal ('all'|'active'|'completed'), and derived computed lists
  - Quick Add form: Reactive Form with typed FormControl<string> for title
- Form bridge: For non-CVA controls (shared UI like app-text-input), bind [value] to FormControl.value and (valueChange) to update the FormControl

Form Model & Validation (Typed Reactive Forms)
- Use ReactiveFormsModule
- Form: taskForm
  - title: FormControl<string> with:
    - nonNullable: true
    - Validators: [Validators.required, trimmedLengthRange(3, 80)]
- Custom Validator: trimmedLengthRange(min: number, max: number): ValidatorFn
  - Validates the trimmed length between min and max
  - Provides meaningful errors for minLengthTrim and maxLengthTrim
- Validation UI:
  - Inline error text shown when field touched or on submit attempt
- Submit behavior:
  - On valid submit: add Task to tasks signal with generated id and createdAt timestamp, clear title field, focus back to input
  - Disable submit when invalid or pending
- Non-CVA bridge strategy for app-text-input:
  - Bind [value]="taskForm.controls.title.value"
  - Bind (valueChange)="taskForm.controls.title.setValue($event)"
  - Normalize value in TS (trim before adding to list)

Template Pattern Catalog (Form/Layout)
- Primary layout pattern: layout-page-shell-header-toolbar
- Primary form pattern: form-mixed-controls-create-edit
- Reference: Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit

Component & Module Strategy
- Prefer standalone components (default in v20/v21)
- Use inject() for services (if any)
- Use NgOptimizedImage for static images only (avoid for base64 inline when used)
- Avoid HostBinding/HostListener decorators; use host property in @Component
- Ensure OnPush change detection on generated components

File Structure
- Overarching structure (folders reflect vertical slices and shared UI)
  - src/app/
    - app.html
    - app.ts
    - app.routes.ts
    - landing/
      - landing.component.ts
      - landing.component.html
      - landing.component.css (likely empty/minimal)
    - home/
      - home.component.ts
      - home.component.html
      - home.component.css (likely empty/minimal)
    - shared/
      - ui/
        - (existing shared UI library, including app-button, app-card, app-text-input, app-checkbox, app-empty-state, app-badge)
        - index.ts (barrel exports)
      - state/
        - signals.ts (shared signal utilities and potentially Task type)
    - core/ (optional for global providers/tokens)
    - assets/ (images, icons, etc.)
- Important: All feature logic for the two pages lives in their respective folders; shared UI is reused via imports from src/app/shared/ui

Shared UI Coverage
- Required selectors and their feature locations
  - app-button: Landing CTA buttons and Home page actions (Add Task, Delete, filter toggles)
  - app-card: Card-like containers for landing features and Home sections
  - app-text-input: Quick Add Task input (bridged to form)
  - app-checkbox: Task completion toggle
  - app-empty-state: Empty state for Home page when no tasks or no matches
  - app-badge: Counts for total/active/completed
- Coverage plan: Place the selectors in meaningful UI sections (landing hero CTA area; home header with counts; quick add card; task list item card). Use a Shared UI Coverage panel in the Work Order if the selector list is lengthy to keep the main path clean.

UI/UX – Accessibility
- ARIA:
  - Landing: CTA buttons with aria-labels
  - Home: tab-based filters with aria-pressed or aria-selected; task items with proper aria-labels
- Landmarks: header (site header), main (page content), nav (landing navigation/filters)
- Focus management: After adding a task, focus remains in the input

Routing and Initialization
- Landing page is the first view on load
- /home is accessible directly
- When landing CTA clicked, route to /home
- Navigation back to / from Home via a visible control

Testing Perspective (Not the primary focus here)
- Unit tests should use Vitest-compatible matchers
- Use provideRouter([]) in tests if routing is needed
- Do not rely on Jasmine specific matchers

Requirement Traceability (Mapping Requirements to Implementation)
- Landing and Home routes and navigation
  - Implement routes and default behavior to ensure landing shows first
  - Implement navigation from Landing to /home and from Home back to /
- Data Model
  - Implement Task interface as above
  - Implement in Home component state
- Quick Add form
  - Implement reactive form with typed FormControl and custom trimmed length validator
  - Bind to app-text-input via value/valueChange bridging
- Task List and Filtering
  - Implement task list rendering
  - Implement All/Active/Completed filters with computed list
  - Implement counts (total/active/completed) using computed
  - Implement empty state logic for both no tasks and no matches
- Shared UI selectors
  - Ensure usage of app-button, app-card, app-text-input, app-checkbox, app-empty-state, app-badge in appropriate locations
  - Provide mapping in UI/UX Requirements and Shared UI Coverage section
- Accessibility and UX
  - Implement semantic landmarks and ARIA relationships
  - Validation messages visible
- State Management
  - Use Signals and computed for state
  - Bridges for non-CVA controls
- Template Pattern References
  - UI/UX Requirements to include Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit
- Overwrite app.html and app.routes.ts
  - Implement as a critical step to ensure default route and boilerplate removal

Acceptance Criteria
- Visiting / loads landing page first
- Landing CTA navigates to /home
- /home renders to-do application UI
- User can add a valid task
- Invalid task submit shows validation feedback
- User can mark a task complete/incomplete
- User can delete a task
- Filters All/Active/Completed update the displayed list
- Counts update correctly with add/complete/delete
- Empty state appears when no tasks exist and when a filter has no matches
- All required shared UI selectors are present and used meaningfully

Files to be Created/Modified (Suggested)
- src/app/app.html (overwrite with layout or <router-outlet />)
- src/app/app.ts (adjust imports if necessary to reflect changes)
- src/app/app.routes.ts (overwrite to set '' route to Landing)
- src/app/landing/landing.component.ts
- src/app/landing/landing.component.html
- src/app/home/home.component.ts
- src/app/home/home.component.html
- src/app/shared/state/signals.ts (optional shared hooks for tasks)
- src/app/shared/ui/index.ts (existing; ensure barrel exports)
- Tailwind setup already present per blueprint; use utility classes in templates

Developer Guidance and Runtime Notes
- Prioritize reusing shared UI components from src/app/shared/ui before building any new custom UI
- Read and respect the top usage comments in shared UI component files before usage
- Use path alias imports (src/*) for shared UI components
- Ensure typed Reactive Forms and non-CVA bridging for shared UI controls
- Validate accessibility (AXE checks) and WCAG AA compliance during implementation
- If template/config issues are detected (e.g., shared UI wrapper provider provisioning), mark as Template/Agent-level issues and address upstream when possible

Template Pattern References
- UI/UX Requirements section must include:
  Template Pattern References: layout-page-shell-header-toolbar, form-mixed-controls-create-edit

Deviation Notes
- If any catalog pattern doesn’t fit due to a user-story constraint, document Deviation Notes in UI/UX Requirements with justification.

Assumptions
- None declared beyond standard defaults; see Assumptions section if you adopt any during implementation.

End of Work Order


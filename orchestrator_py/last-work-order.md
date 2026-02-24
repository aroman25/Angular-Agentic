# Work Order: Two-Page To-Do Application (Landing + Home)

---

## Feature Name & Goal
**Feature Name:** Two-Page To-Do App with Landing and Home Pages  
**Goal:** Develop a polished, production-ready two-page Angular application for personal task management, featuring a marketing landing page and an interactive to-do list with filtering, validation, and accessible UI, using Angular v20/v21 best practices and signals-based state management.

---

## User Story Data Points

### Routes & Navigation
- `/` (Landing page): Marketing content with CTA to `/home`
- `/home` (To-Do app): Task management interface
- Initial load: Show `/` (landing page)
- Navigation:
  - Landing page CTA button: "Start Organizing" → `/home`
  - Home page: Button/link to return to `/` (e.g., "Back to Welcome")

### Landing Page Content
- Hero heading: Clear benefit-driven message (e.g., "Organize Your Tasks Effortlessly")
- Supporting description: 1-2 sentences explaining the app
- Primary CTA button: "Start Organizing" (navigates to `/home`)
- Secondary CTA/link: "View Demo Tasks" (navigates to `/home`)
- 3 feature highlights (e.g., quick capture, progress tracking, focused lists)
- Trust/benefit row:
  - "Local-only demo state"
  - "No sign-in required"
  - "Fast keyboard-friendly"

### To-Do Data Model (Front-End Only)
Each task:
- `id`: string
- `title`: string
- `completed`: boolean
- `createdAt`: string (ISO date/time) or number (timestamp)

### Home Page UI & Behavior
- Header:
  - Page title: "My Tasks"
  - Counts:
    - Total tasks
    - Active tasks
    - Completed tasks
- Quick add task form:
  - `title` input (text)
  - Submit button: "Add Task"
  - Validation:
    - Required
    - Min length: 3
    - Max length: 80
    - Trim whitespace before submit
    - Inline validation messages after touch or submit attempt
- Filter controls:
  - Buttons/links: All, Active, Completed
  - Default: All
  - Active state visually and aria-label
- Task list:
  - Each task:
    - Checkbox for completion
    - Task title text
    - Delete button
  - Visual style:
    - Completed tasks: muted + line-through
- Empty state:
  - When no tasks exist or filter yields no results
  - Message varies:
    - "No tasks yet. Add your first task!"
    - "No active tasks."
    - "No completed tasks."

---

## Requirement Traceability

| User Story Requirement | Implementation Task | Acceptance Criteria |
|--------------------------|-----------------------|---------------------|
| Landing page at `/` with CTA to `/home` | Create `LandingPageComponent`, set route `/` | Landing page loads first, CTA navigates to `/home` |
| `/home` route with task management UI | Create `HomePageComponent`, set route `/home` | Navigates correctly, displays task UI |
| Show hero heading, description, features, trust row | Implement in `LandingPageComponent` template | Content appears styled, CTA navigates properly |
| Task data model with `id`, `title`, `completed`, `createdAt` | Define `Task` interface, manage in signals | Tasks stored in signal array, unique IDs assigned |
| Add task form with validation | Use Reactive Form with validators, bind to `app-text-input` | Validation errors shown inline, submit disabled if invalid |
| Clear input after successful add | Reset form control, focus remains in input | Task appears immediately in list |
| Toggle completion checkbox | Bind to task `completed` property via signals | UI updates instantly, style updates accordingly |
| Delete task button | Remove task from signal array | Task disappears immediately |
| Filter controls (All, Active, Completed) | Use signals for filter state, computed for filtered list | List updates on filter change, counts update |
| Counts display | Computed signals for total, active, completed | Counts reflect current task list accurately |
| Empty state messages | Conditional rendering based on filtered list | Appropriate message shown when no tasks |
| Accessibility | Use semantic landmarks, aria-labels, focus management | All controls accessible, validation messages visible |

---

## File Structure

```
src/
├── app/
│   ├── pages/
│   │   ├── landing/
│   │   │   ├── landing-page.component.ts
│   │   │   ├── landing-page.component.html
│   │   │   └── landing-page.component.css
│   │   ├── home/
│   │   │   ├── home-page.component.ts
│   │   │   ├── home-page.component.html
│   │   │   └── home-page.component.css
│   ├── app.routes.ts
│   ├── app.component.ts
│   ├── app.component.html
│   └── app.module.ts (or main.ts for standalone bootstrap)
├── shared/
│   ├── ui/
│   │   ├── index.ts
│   │   ├── app-button.component.ts
│   │   ├── app-card.component.ts
│   │   ├── app-text-input.component.ts
│   │   ├── app-checkbox.component.ts
│   │   ├── app-empty-state.component.ts
│   │   └── app-badge.component.ts
│   └── models/
│       └── task.model.ts
└── main.ts
```

---

## State Management

- Use signals for core feature state:
  - `tasksSignal`: `Signal<Task[]>`
  - `filterSignal`: `Signal<'all' | 'active' | 'completed'>`
  - `filteredTasks`: `computed()` based on `tasksSignal` and `filterSignal`
  - Counts: `totalCount`, `activeCount`, `completedCount` as `computed()`
- Use `update()` and `set()` methods for signals
- No external state management libraries

---

## Form Model & Validation

### Reactive Form Schema
```typescript
const taskForm = new FormGroup({
  title: new FormControl('', {
    validators: [
      Validators.required,
      Validators.minLength(3),
      Validators.maxLength(80),
      Validators.pattern(/\S/) // ensure not whitespace only
    ]
  })
});
```

### Validation Matrix
| Field | Required | Min Length | Max Length | Pattern | Error Message | Behavior |
|---------|------------|--------------|--------------|---------|----------------|----------|
| `title` | Yes        | 3          | 80           | No whitespace only | Show inline message after touch or submit | Disable submit if invalid |

### Binding Strategy
- Use `app-text-input` with `[value]` bound to form control value
- On `valueChange`, update form control
- Show validation messages below input

---

## UI/UX Requirements

- **Landing Page:**
  - Use `section` with semantic headings
  - Large hero heading with Tailwind typography
  - Feature cards in responsive grid
  - CTA button styled with `app-button`, prominent
  - Trust row with small badges or text
  - Background with subtle gradient or layered shapes
- **Home Page:**
  - Header with title and counts (badges)
  - Quick add form in `app-card`, with `app-text-input` and `app-button`
  - Filter controls as toggle buttons with `aria-pressed`
  - Task list:
    - Each task in `app-card`
    - Checkbox (`app-checkbox`) for completion
    - Text with line-through if completed
    - Delete button (`app-button`) with icon
  - Empty state with `app-empty-state`
- **Accessibility:**
  - Use semantic landmarks (`header`, `main`, `section`, `nav`)
  - Labels for inputs
  - ARIA labels for buttons
  - Validation messages visible and accessible
  - Focus management: focus remains in input after add

**Template Pattern References:** layout-page-shell-header-toolbar, form-mixed-controls-create-edit

---

## Acceptance Criteria

- Visiting `/` shows the landing page first
- Clicking "Start Organizing" or "View Demo Tasks" navigates to `/home`
- `/home` displays task management UI with header, form, filters, list
- User can add a task with valid title:
  - Validation errors shown inline for invalid input
  - Input cleared after add
  - Focus remains in input
- User can toggle task completion:
  - UI updates immediately
  - Completed tasks styled with line-through and muted text
- User can delete a task:
  - Task disappears immediately
- Filters update task list:
  - "All" shows all tasks
  - "Active" shows only incomplete
  - "Completed" shows only completed
- Counts update correctly on task add, toggle, delete
- Empty state appears when no tasks or no tasks match filter
- All shared UI components (`app-button`, `app-card`, `app-text-input`, `app-checkbox`, `app-empty-state`, `app-badge`) are used in meaningful locations
- Application is styled with Tailwind utility classes, responsive, accessible, and visually polished

---

## Critical Instructions

- Overwrite `src/app/app.html` and `src/app/app.routes.ts` so the new feature is the default view, removing default Angular boilerplate.
- Use shared UI components from `src/app/shared/ui/` as per their documented usage.
- Import shared UI components via barrel import from `'src/app/shared/ui'`.
- Ensure all code adheres to Angular v20/v21 best practices, especially signals-based state management.
- Address any template/configuration issues upstream if identified (e.g., shared UI behavior, path aliasing).

---

## Notes
- This work order emphasizes a clean, accessible, and responsive design following the modern Angular v21 paradigm with signals.
- Focus on maintainability, performance, and user experience.
- Do not add external dependencies unless explicitly required by the user story.

---

**End of Work Order**
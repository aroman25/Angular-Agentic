# User Story: Two-Page To-Do Application (Landing + Home)

## Goal
Create a polished 2-page Angular application for personal task management.

- The first page is a marketing-style landing page.
- The second page is the actual to-do application ("Home").
- The experience should feel production-ready, not a basic demo.

## Primary Route & Navigation Requirements
- Landing page is accessible at `/`.
- To-do Home page is accessible at `/home`.
- The first page shown on initial load must be the landing page at `/`.
- The landing page must include a primary CTA button that navigates to `/home`.
- The Home page must include a way to navigate back to `/` (button or link).

## Two-Page Application Plan

### 1) Landing Page (`/`)
Purpose: Explain the app and drive the user into the to-do workflow.

Required content:
- Hero heading (clear benefit-driven message)
- Short supporting description (1-2 sentences)
- Primary CTA: "Start Organizing" (navigates to `/home`)
- Secondary CTA or text link: "View Demo Tasks" (also navigates to `/home`)
- 3 feature highlights (for example: quick capture, progress tracking, focused lists)
- Small trust/benefit row (e.g., "Local-only demo state", "No sign-in required", "Fast keyboard-friendly")

### 2) Home Page (`/home`) - Actual To-Do Application
Purpose: Add, complete, filter, and remove tasks with clear feedback.

Required sections:
- Header area with page title and summary counts
- Quick add task form
- Filter controls (All, Active, Completed)
- Task list area
- Empty state when no tasks match the selected filter

## To-Do Data Model (Front-End Only)
Each task item should include:
- `id` (string)
- `title` (string)
- `completed` (boolean)
- `createdAt` (string or number timestamp)

## Form Requirements (Quick Add Task Form)
This feature includes a form and MUST have visible validation UX.

1. Form Fields
- `title`: text input for task title

2. Validation Rules
- `title` is required
- `title` minimum length is 3 characters
- `title` maximum length is 80 characters
- Trim whitespace before submit; a whitespace-only value is invalid

3. Submit Behavior
- Submit button label: `Add Task`
- Prevent submit when invalid
- Show inline validation message under the field after the user touches the field or after submit attempt
- Clear the input after a successful submit
- Keep focus behavior practical (focus remains in the input so multiple tasks can be added quickly)

## Task List Behavior Requirements
- Newly added tasks appear in the list immediately without page reload
- Each task row includes:
  - completion checkbox
  - task title text
  - delete action
- Toggling completion updates the UI immediately
- Completed tasks must have a visual completed style (e.g., muted text + line-through)
- Deleting a task removes it immediately

## Filtering & Counts
- Provide filters: `All`, `Active`, `Completed`
- Default selected filter is `All`
- Show counts in the Home page header:
  - total tasks
  - active tasks
  - completed tasks
- Empty state message must change depending on context:
  - no tasks created yet
  - no tasks in selected filter

## State Management Requirements
- Use Angular Signals for core feature state (`signal`, `computed`)
- Do not use `[(ngModel)]`
- Use a typed Reactive Form for the quick add form
- No backend/API required for this story (in-memory state only)

## Required Shared UI Selectors (must be used meaningfully)
- `app-button`
- `app-card`
- `app-text-input`
- `app-checkbox`
- `app-empty-state`
- `app-badge`

## Accessibility & UX Requirements
- Use semantic landmarks (`header`, `main`, `section`, `nav`) where appropriate
- Home filter controls must expose clear active state (visually and accessible label/state)
- Add-task form must expose validation errors visibly in text (not color-only)
- Buttons and interactive controls must have clear text or accessible labels
- Empty state must be readable and actionable (guide the user to add a task)

## Styling Suggestions (Tailwind-first, intentional visual direction)
Design direction: warm, editorial, clean, high-contrast, light theme.

- Landing page:
  - Background should not be flat white; use a soft gradient or layered shapes
  - Large bold headline with strong typographic hierarchy
  - Feature highlight cards in a responsive grid (stack on mobile)
  - Primary CTA should be visually dominant
- Home page:
  - Use a centered content column with comfortable spacing
  - Use cards/panels to separate quick-add form and task list
  - Use badges for counts/status summaries
  - Completed tasks should visually recede without becoming hard to read
- Motion:
  - Small entry/reveal transitions are okay
  - Respect reduced-motion preferences
- Responsive behavior:
  - Must work well on mobile and desktop
  - Mobile layout should keep the quick add form and filters easy to tap

## Explicit Styling Constraints
- Use Tailwind utility classes (avoid custom CSS unless necessary)
- Keep feature component CSS minimal or empty
- Avoid generic default-looking layouts; make the landing page feel designed

## Acceptance Criteria
- Visiting `/` shows the landing page first
- Landing page CTA navigates to `/home`
- `/home` renders the to-do application UI
- User can add a valid task
- Invalid task submit shows validation feedback
- User can mark a task complete/incomplete
- User can delete a task
- Filters (All/Active/Completed) correctly change the displayed list
- Counts update correctly when tasks are added/completed/deleted
- Empty state appears when no tasks exist and when a filter has no matching tasks
- Shared UI selectors listed above are present in meaningful feature UI locations

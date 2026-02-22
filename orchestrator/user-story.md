# Feature: Advanced & Beautiful Todo Application

As a user, I want a visually stunning and feature-rich Todo application so that I can manage my daily tasks with joy and efficiency.

## Requirements:
1. **Task List**: Display a list of tasks. Each task should have a title, description, priority (low, medium, high), and status (pending, completed).
2. **Add Task**: A beautiful form to add a new task. Title is required. Priority defaults to 'medium'.
3. **Toggle Status**: A smooth, animated checkbox or button on each task to toggle its status between pending and completed. Completed tasks should have a strikethrough effect and faded text.
4. **Delete Task**: A button to delete a task with a hover effect (e.g., a red trash icon).
5. **Filtering**: Buttons or tabs to filter tasks by "All", "Active", and "Completed".
6. **State**: Use Angular Signals (`signal`, `computed`) to manage the list of tasks and the active filter.
7. **Styling**: Use Tailwind CSS to make it look clean, modern, and beautiful. Use gradients, rounded corners, shadows, and smooth transitions.
8. **Routing**: The dashboard should be accessible at the `/todos` route. The default route (`/`) should redirect to `/todos`.

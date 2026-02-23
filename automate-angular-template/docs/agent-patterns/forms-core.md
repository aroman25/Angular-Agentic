# Core Form Patterns

Use these patterns with one primary `layout-*` pattern from `layouts-core.md`.

## Pattern ID: `form-single-column-submit`

### Goal / Use When

Use for a straightforward create/update form with a small number of text inputs and a clear submit action (for example profile details, contact form, task create, basic settings panel).

### Do Not Use When

- The form requires multi-step progression or sectioned tabs.
- The form relies on heavy filter/result interactions.
- The flow must open in a drawer/dialog rather than inline page content.

### Shared UI Composition Map

- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> wraps the form body and optional header.
- `app-text-input` -> `automate-angular-template/src/app/shared/ui/text-input/text-input.component.ts` -> text/email/tel inputs with hint/error display.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> submit/cancel actions and loading state.
- `app-alert` -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts` -> form-level error or success summary.
- `app-toast` (optional) -> `automate-angular-template/src/app/shared/ui/toast/toast.component.ts` -> transient success notification after submit.

### Typed Form Model Example

```ts
import { FormControl, FormGroup, Validators } from '@angular/forms';

type ContactFormModel = FormGroup<{
  fullName: FormControl<string>;
  email: FormControl<string>;
  phone: FormControl<string>;
}>;

contactForm: ContactFormModel = new FormGroup({
  fullName: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.minLength(2)] }),
  email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
  phone: new FormControl('', { nonNullable: true, validators: [Validators.pattern(/^[0-9+()\-\s]*$/)] }),
});
```

### Validation Matrix

| Field | Validators | Error Messages | Show When |
| --- | --- | --- | --- |
| `fullName` | `required`, `minLength(2)` | "Name is required", "Name must be at least 2 characters" | control invalid and (`touched` or submit attempted) |
| `email` | `required`, `email` | "Email is required", "Enter a valid email" | control invalid and (`touched` or submit attempted) |
| `phone` | `pattern` | "Phone can only include digits and +()- spaces" | control invalid and (`dirty` or submit attempted) |

### Non-CVA Bridge Methods

This pattern usually does not require non-CVA shared controls. Keep the section in the Work Order and state that the form uses only `app-text-input`/`app-textarea`, which already expose `[(value)]` for direct string binding.

```ts
updateFullName(value: string): void {
  this.contactForm.controls.fullName.setValue(value);
}
```

### Signal State Example

```ts
import { computed, signal } from '@angular/core';

submitAttempted = signal(false);
isSubmitting = signal(false);
submitError = signal<string>('');
submitSuccess = signal<string>('');
showSuccessToast = signal(false);

canSubmit = computed(() => this.contactForm.valid && !this.isSubmitting());
showErrorSummary = computed(() => this.submitAttempted() && !!this.submitError());
```

### Tailwind Layout Skeleton

```html
<section class="mx-auto w-full max-w-2xl px-4 py-6 sm:px-6 lg:px-8">
  <app-card title="Contact details" description="Used for account communication.">
    <form class="space-y-4" [formGroup]="contactForm" (ngSubmit)="submit()" novalidate>
      @if (showErrorSummary()) {
        <app-alert variant="danger" role="alert" [title]="'Unable to save'" [message]="submitError()" />
      }

      <app-text-input
        label="Full name"
        [required]="true"
        [value]="contactForm.controls.fullName.value"
        [error]="fieldError('fullName')"
        (valueChange)="updateFullName($event)"
      />

      <app-text-input
        label="Email"
        type="email"
        [required]="true"
        [value]="contactForm.controls.email.value"
        [error]="fieldError('email')"
        (valueChange)="updateEmail($event)"
      />

      <app-text-input
        label="Phone"
        type="tel"
        [value]="contactForm.controls.phone.value"
        [error]="fieldError('phone')"
        (valueChange)="updatePhone($event)"
      />

      <div class="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
        <app-button variant="secondary" type="button">Cancel</app-button>
        <app-button [disabled]="!canSubmit()" [loading]="isSubmitting()" type="submit">Save</app-button>
      </div>
    </form>
  </app-card>

  <div class="pointer-events-none fixed bottom-4 right-4 z-40">
    <app-toast [open]="showSuccessToast()" (openChange)="showSuccessToast.set($event)" title="Saved" message="Contact details updated." />
  </div>
</section>
```

### Accessibility Notes

- Pass `role="alert"` on destructive submit failure summaries.
- Keep field errors bound through shared UI `error` inputs so `aria-invalid`/`aria-describedby` are wired.
- Use `novalidate` and rely on visible app validation messages.
- Call `markAllAsTouched()` on invalid submit before showing summary.

### Acceptance Hooks

- Typed `FormGroup`/`FormControl` with explicit validators exists in TS.
- Submit handler prevents invalid submit and sets submitted/error/success state.
- Inline field errors and form-level `app-alert` appear after submit attempt.
- `app-card`, `app-text-input`, `app-button`, `app-alert` are used in the actual form path.

---

## Pattern ID: `form-mixed-controls-create-edit`

### Goal / Use When

Use for create/edit screens with mixed field types (text, textarea, select, radio, checkbox, switch) and explicit validation across multiple sections.

### Do Not Use When

- The flow is primarily a search/filter toolbar rather than entity editing.
- Editing must happen only in an overlay (`app-drawer` / `app-dialog`) instead of page content.
- The form needs dynamic repeating arrays as the main interaction (extend this pattern first).

### Shared UI Composition Map

- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> section containers (details, preferences, publishing).
- `app-text-input` -> `automate-angular-template/src/app/shared/ui/text-input/text-input.component.ts` -> title/slug/owner fields.
- `app-textarea` -> `automate-angular-template/src/app/shared/ui/textarea/textarea.component.ts` -> longer description/notes fields.
- `app-select` -> `automate-angular-template/src/app/shared/ui/select/select.component.ts` -> single-select category/priority/status.
- `app-radio-group` -> `automate-angular-template/src/app/shared/ui/radio-group/radio-group.component.ts` -> visibility or workflow mode choice.
- `app-checkbox` -> `automate-angular-template/src/app/shared/ui/checkbox/checkbox.component.ts` -> opt-in toggles and acknowledgement checkboxes.
- `app-switch` -> `automate-angular-template/src/app/shared/ui/switch/switch.component.ts` -> binary feature/publish toggle.
- `app-divider` -> `automate-angular-template/src/app/shared/ui/divider/divider.component.ts` -> visual split between form sections.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> save/publish/cancel actions.
- `app-alert` -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts` -> summary validation or save result banner.

### Typed Form Model Example

```ts
import { FormControl, FormGroup, Validators } from '@angular/forms';

type Visibility = 'private' | 'team' | 'public';
type Priority = 'low' | 'medium' | 'high';
type Category = 'ops' | 'sales' | 'product';

type EditorFormModel = FormGroup<{
  title: FormControl<string>;
  description: FormControl<string>;
  category: FormControl<Category>;
  priority: FormControl<Priority>;
  visibility: FormControl<Visibility>;
  requiresApproval: FormControl<boolean>;
  publishNow: FormControl<boolean>;
  acceptPolicy: FormControl<boolean>;
}>;

editorForm: EditorFormModel = new FormGroup({
  title: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.minLength(3)] }),
  description: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(500)] }),
  category: new FormControl<Category>('ops', { nonNullable: true, validators: [Validators.required] }),
  priority: new FormControl<Priority>('medium', { nonNullable: true, validators: [Validators.required] }),
  visibility: new FormControl<Visibility>('team', { nonNullable: true, validators: [Validators.required] }),
  requiresApproval: new FormControl(false, { nonNullable: true }),
  publishNow: new FormControl(false, { nonNullable: true }),
  acceptPolicy: new FormControl(false, { nonNullable: true, validators: [Validators.requiredTrue] }),
});
```

### Validation Matrix

| Field | Validators | Error Messages | Show When |
| --- | --- | --- | --- |
| `title` | `required`, `minLength(3)` | "Title is required", "Title must be at least 3 characters" | invalid and (`touched` or submit attempted) |
| `description` | `required`, `maxLength(500)` | "Description is required", "Description must be 500 characters or fewer" | invalid and (`touched` or submit attempted) |
| `category` | `required` | "Category is required" | submit attempted or field changed to invalid |
| `priority` | `required` | "Priority is required" | submit attempted |
| `visibility` | `required` | "Choose a visibility option" | submit attempted |
| `acceptPolicy` | `requiredTrue` | "You must acknowledge the policy" | submit attempted |

### Non-CVA Bridge Methods

Use helper methods in TS (no template casts) for shared controls that do not support `formControlName`.

```ts
import type { SelectOption } from 'src/app/shared/ui';
import type { RadioGroupOption } from 'src/app/shared/ui';

categoryOptions: SelectOption<Category>[] = [
  { label: 'Operations', value: 'ops' },
  { label: 'Sales', value: 'sales' },
  { label: 'Product', value: 'product' },
];

priorityOptions: SelectOption<Priority>[] = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
];

visibilityOptions: RadioGroupOption<Visibility>[] = [
  { label: 'Private', value: 'private', description: 'Only you can view this record.' },
  { label: 'Team', value: 'team', description: 'Visible to your team.' },
  { label: 'Public', value: 'public', description: 'Visible to all users.' },
];

updateCategory(value: Category | null): void {
  if (value === null) return;
  this.editorForm.controls.category.setValue(value);
}

updatePriority(value: Priority | null): void {
  if (value === null) return;
  this.editorForm.controls.priority.setValue(value);
}

updateVisibility(value: Visibility | null): void {
  if (value === null) return;
  this.editorForm.controls.visibility.setValue(value);
}

updateRequiresApproval(checked: boolean): void {
  this.editorForm.controls.requiresApproval.setValue(checked);
}

updatePublishNow(checked: boolean): void {
  this.editorForm.controls.publishNow.setValue(checked);
}

updateAcceptPolicy(checked: boolean): void {
  this.editorForm.controls.acceptPolicy.setValue(checked);
}
```

### Signal State Example

```ts
import { computed, signal } from '@angular/core';

submitAttempted = signal(false);
isSaving = signal(false);
saveMessage = signal<string>('');
saveTone = signal<'success' | 'danger' | 'info'>('info');

hasBlockingErrors = computed(() => this.submitAttempted() && this.editorForm.invalid);
showSaveBanner = computed(() => this.saveMessage().length > 0);
```

### Tailwind Layout Skeleton

```html
<form class="mx-auto grid w-full max-w-5xl gap-6 px-4 py-6 lg:grid-cols-[minmax(0,1fr)_20rem]" [formGroup]="editorForm" (ngSubmit)="submit()" novalidate>
  <div class="space-y-6">
    @if (showSaveBanner()) {
      <app-alert [variant]="saveTone() === 'danger' ? 'danger' : 'success'" [message]="saveMessage()" [role]="saveTone() === 'danger' ? 'alert' : 'status'" />
    }

    <app-card title="Details" description="Core metadata for this record.">
      <div class="grid gap-4">
        <app-text-input label="Title" [value]="editorForm.controls.title.value" [error]="fieldError('title')" (valueChange)="updateTitle($event)" />
        <app-textarea label="Description" [rows]="5" [value]="editorForm.controls.description.value" [error]="fieldError('description')" (valueChange)="updateDescription($event)" />
        <div class="grid gap-4 sm:grid-cols-2">
          <app-select [options]="categoryOptions" [value]="editorForm.controls.category.value" (valueChange)="updateCategory($event)" />
          <app-select [options]="priorityOptions" [value]="editorForm.controls.priority.value" (valueChange)="updatePriority($event)" />
        </div>
      </div>
    </app-card>

    <app-card title="Visibility">
      <app-radio-group [label]="'Who can access this?'" [options]="visibilityOptions" [value]="editorForm.controls.visibility.value" (valueChange)="updateVisibility($event)" />
      <app-divider class="my-4" label="Publishing" />
      <div class="grid gap-3">
        <app-switch label="Publish immediately" [checked]="editorForm.controls.publishNow.value" (checkedChange)="updatePublishNow($event)" />
        <app-checkbox label="Require approval" [checked]="editorForm.controls.requiresApproval.value" (checkedChange)="updateRequiresApproval($event)" />
        <app-checkbox label="I acknowledge the policy" [checked]="editorForm.controls.acceptPolicy.value" (checkedChange)="updateAcceptPolicy($event)" />
      </div>
    </app-card>
  </div>

  <app-card title="Actions" class="h-fit lg:sticky lg:top-6">
    <div class="space-y-3">
      <app-button type="submit" [fullWidth]="true" [loading]="isSaving()">Save Changes</app-button>
      <app-button type="button" variant="secondary" [fullWidth]="true">Cancel</app-button>
      @if (hasBlockingErrors()) {
        <p class="text-xs text-red-600">Fix the highlighted fields before saving.</p>
      }
    </div>
  </app-card>
</form>
```

### Accessibility Notes

- `app-radio-group` renders a `fieldset`/`legend`; use meaningful labels.
- Keep checkbox acknowledgement errors visible in surrounding text or form summary.
- Use `role="alert"` for blocking save errors and `role="status"` for non-blocking success messages.
- Ensure the sticky action card remains reachable in keyboard order on mobile (it should render after main content in DOM if needed).

### Acceptance Hooks

- Work Order lists exact shared UI selectors used in this form pattern.
- Typed literal unions exist for `select` / `radio` values.
- TS bridge methods handle `app-select`, `app-radio-group`, `app-checkbox`, and `app-switch` updates.
- Visible validation messages exist for required fields and policy acknowledgement.

---

## Pattern ID: `form-filter-panel-results`

### Goal / Use When

Use for feature pages where a filter/search form controls a table or grid result set (for example user search, audit logs, inventory list, ticket queue).

### Do Not Use When

- The page is primarily a single record create/edit form.
- Filtering is trivial and can be handled by one input without a dedicated panel/toolbar.
- Server-driven infinite scroll is the primary interaction (adapt pagination/state ownership accordingly).

### Shared UI Composition Map

- `app-text-input` -> `automate-angular-template/src/app/shared/ui/text-input/text-input.component.ts` -> keyword or ID search field.
- `app-autocomplete` -> `automate-angular-template/src/app/shared/ui/autocomplete/autocomplete.component.ts` -> assignee/customer/owner search.
- `app-select` -> `automate-angular-template/src/app/shared/ui/select/select.component.ts` -> status/type/environment filters.
- `app-switch` -> `automate-angular-template/src/app/shared/ui/switch/switch.component.ts` -> toggle-only filters (for example "Active only").
- `app-toolbar` -> `automate-angular-template/src/app/shared/ui/toolbar/toolbar.component.ts` -> quick filter chips/actions with keyboard navigation.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> apply/reset/export actions.
- `app-table` -> `automate-angular-template/src/app/shared/ui/table/table.component.ts` -> read-only result table.
- `app-data-grid` -> `automate-angular-template/src/app/shared/ui/data-grid/data-grid.component.ts` -> keyboard-navigable result grid variant.
- `app-pagination` -> `automate-angular-template/src/app/shared/ui/pagination/pagination.component.ts` -> client-side page UI.
- `app-empty-state` -> `automate-angular-template/src/app/shared/ui/empty-state/empty-state.component.ts` -> no results state.
- `app-skeleton` -> `automate-angular-template/src/app/shared/ui/skeleton/skeleton.component.ts` -> loading placeholders.
- `app-card` (optional panel wrapper) -> `automate-angular-template/src/app/shared/ui/card/card.component.ts`.

### Typed Form Model Example

```ts
import { FormControl, FormGroup } from '@angular/forms';

type StatusFilter = 'all' | 'open' | 'closed' | 'pending';
type ViewMode = 'table' | 'grid';

type FilterFormModel = FormGroup<{
  query: FormControl<string>;
  status: FormControl<StatusFilter>;
  ownerId: FormControl<string>;
  activeOnly: FormControl<boolean>;
  viewMode: FormControl<ViewMode>;
}>;

filterForm: FilterFormModel = new FormGroup({
  query: new FormControl('', { nonNullable: true }),
  status: new FormControl<StatusFilter>('all', { nonNullable: true }),
  ownerId: new FormControl('', { nonNullable: true }),
  activeOnly: new FormControl(true, { nonNullable: true }),
  viewMode: new FormControl<ViewMode>('table', { nonNullable: true }),
});
```

### Validation Matrix

Filter forms often have minimal validation. Define explicit rules anyway when required.

| Field | Validators | Error Messages | Show When |
| --- | --- | --- | --- |
| `query` | optional `maxLength(100)` | "Search must be 100 characters or fewer" | invalid and (`dirty` or submit attempted) |
| `status` | none (typed enum options) | n/a | n/a |
| `ownerId` | none or custom option guard | "Choose a valid owner" | invalid after apply if external data mismatch |
| `activeOnly` | none | n/a | n/a |
| `viewMode` | none | n/a | n/a |

### Non-CVA Bridge Methods

This pattern commonly needs `app-autocomplete`, `app-select`, and `app-switch` bridging plus signal-owned "applied" filter state.

```ts
import type { AutocompleteOption, SelectOption } from 'src/app/shared/ui';

ownerOptions: AutocompleteOption<string>[] = [];
statusOptions: SelectOption<StatusFilter>[] = [
  { label: 'All', value: 'all' },
  { label: 'Open', value: 'open' },
  { label: 'Pending', value: 'pending' },
  { label: 'Closed', value: 'closed' },
];

ownerInputValue = signal('');

updateStatus(value: StatusFilter | null): void {
  if (value === null) return;
  this.filterForm.controls.status.setValue(value);
}

updateOwnerId(value: string | null): void {
  this.filterForm.controls.ownerId.setValue(value ?? '');
}

updateOwnerInput(inputValue: string): void {
  this.ownerInputValue.set(inputValue);
}

updateActiveOnly(checked: boolean): void {
  this.filterForm.controls.activeOnly.setValue(checked);
}
```

### Signal State Example

```ts
import { computed, signal } from '@angular/core';

isLoading = signal(false);
loadError = signal<string>('');
currentPage = signal(1);
pageSize = signal(10);
appliedFilters = signal(this.filterForm.getRawValue());
rows = signal<Array<Record<string, unknown>>>([]);
viewMode = computed(() => this.filterForm.controls.viewMode.value);
hasRows = computed(() => this.rows().length > 0);
showEmpty = computed(() => !this.isLoading() && !this.loadError() && !this.hasRows());
```

### Tailwind Layout Skeleton

```html
<section class="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <app-card title="Filters" description="Refine the result set before loading data.">
    <form class="grid gap-4 lg:grid-cols-12" [formGroup]="filterForm" (ngSubmit)="applyFilters()" novalidate>
      <div class="lg:col-span-4">
        <app-text-input label="Search" [value]="filterForm.controls.query.value" (valueChange)="updateQuery($event)" />
      </div>
      <div class="lg:col-span-3">
        <app-autocomplete
          [options]="ownerOptions"
          [value]="filterForm.controls.ownerId.value || null"
          [inputValue]="ownerInputValue()"
          (valueChange)="updateOwnerId($event)"
          (inputValueChange)="updateOwnerInput($event)"
        />
      </div>
      <div class="lg:col-span-2">
        <app-select [options]="statusOptions" [value]="filterForm.controls.status.value" (valueChange)="updateStatus($event)" />
      </div>
      <div class="lg:col-span-3 flex items-end justify-between gap-3">
        <app-switch label="Active only" [checked]="filterForm.controls.activeOnly.value" (checkedChange)="updateActiveOnly($event)" />
        <div class="flex items-center gap-2">
          <app-button type="button" variant="secondary" (click)="resetFilters()">Reset</app-button>
          <app-button type="submit" [loading]="isLoading()">Apply</app-button>
        </div>
      </div>
    </form>

    <div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4">
      <app-toolbar [items]="quickFilterToolbarItems" ariaLabel="Quick filters" (itemTriggered)="applyQuickFilter($event)" />
      <app-button type="button" variant="ghost">Export</app-button>
    </div>
  </app-card>

  @if (isLoading()) {
    <div class="grid gap-3">
      @for (_ of [1, 2, 3]; track $index) {
        <app-skeleton heightClass="h-12" />
      }
    </div>
  } @else if (showEmpty()) {
    <app-empty-state title="No results" description="Try adjusting your filters."></app-empty-state>
  } @else {
    @if (viewMode() === 'table') {
      <app-table [columns]="tableColumns" [rows]="pagedRows()" trackByKey="id" />
    } @else {
      <app-data-grid [columns]="gridColumns" [rows]="pagedRows()" trackByKey="id" [enableSelection]="true" />
    }
    <app-pagination [totalPages]="totalPages()" [currentPage]="currentPage()" (currentPageChange)="currentPage.set($event)" />
  }
</section>
```

### Accessibility Notes

- `app-toolbar` already applies `role="toolbar"`; provide a specific `ariaLabel`.
- Announce load errors and empty states near the results region.
- Ensure filter actions are keyboard reachable before results table/grid.
- If using `app-data-grid`, validate keyboard navigation and selection mode expectations in acceptance checks.

### Acceptance Hooks

- Typed filter form model exists even if validators are minimal.
- Separate signal state exists for applied filters / loading / pagination.
- `app-empty-state`, `app-skeleton`, and `app-pagination` are used for state transitions.
- At least one result renderer (`app-table` or `app-data-grid`) is wired to the applied filter state.

---

## Pattern ID: `form-overlay-edit-drawer-dialog`

### Goal / Use When

Use for inline edit/create interactions that should preserve page context, with forms hosted in `app-drawer` or `app-dialog` and local submit/result state.

### Do Not Use When

- The form is long, multi-section, or requires persistent navigation context (use full page form pattern).
- The overlay is purely informational with no editable fields.
- The feature requires nested overlays; avoid stacking dialogs/drawers unless absolutely necessary.

### Shared UI Composition Map

- `app-drawer` -> `automate-angular-template/src/app/shared/ui/drawer/drawer.component.ts` -> side-panel edit/create overlay.
- `app-dialog` -> `automate-angular-template/src/app/shared/ui/dialog/dialog.component.ts` -> compact edit/confirm overlay.
- `app-text-input` -> `automate-angular-template/src/app/shared/ui/text-input/text-input.component.ts` -> inline overlay fields.
- `app-textarea` -> `automate-angular-template/src/app/shared/ui/textarea/textarea.component.ts` -> notes/reason/details field.
- `app-select` -> `automate-angular-template/src/app/shared/ui/select/select.component.ts` -> status/type selection.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> save/cancel/confirm actions.
- `app-alert` -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts` -> submit error summary inside overlay.
- `app-toast` -> `automate-angular-template/src/app/shared/ui/toast/toast.component.ts` -> success confirmation after close.
- `app-card` (optional inner sectioning) -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> grouped overlay content.

### Typed Form Model Example

```ts
import { FormControl, FormGroup, Validators } from '@angular/forms';

type RecordStatus = 'draft' | 'active' | 'archived';

type OverlayEditFormModel = FormGroup<{
  name: FormControl<string>;
  status: FormControl<RecordStatus>;
  notes: FormControl<string>;
}>;

overlayForm: OverlayEditFormModel = new FormGroup({
  name: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.minLength(2)] }),
  status: new FormControl<RecordStatus>('draft', { nonNullable: true, validators: [Validators.required] }),
  notes: new FormControl('', { nonNullable: true, validators: [Validators.maxLength(300)] }),
});
```

### Validation Matrix

| Field | Validators | Error Messages | Show When |
| --- | --- | --- | --- |
| `name` | `required`, `minLength(2)` | "Name is required", "Name must be at least 2 characters" | invalid and (`touched` or submit attempted) |
| `status` | `required` | "Status is required" | submit attempted |
| `notes` | `maxLength(300)` | "Notes must be 300 characters or fewer" | invalid and (`dirty` or submit attempted) |

### Non-CVA Bridge Methods

```ts
import type { SelectOption } from 'src/app/shared/ui';

statusOptions: SelectOption<RecordStatus>[] = [
  { label: 'Draft', value: 'draft' },
  { label: 'Active', value: 'active' },
  { label: 'Archived', value: 'archived' },
];

updateOverlayStatus(value: RecordStatus | null): void {
  if (value === null) return;
  this.overlayForm.controls.status.setValue(value);
}
```

### Signal State Example

```ts
import { computed, signal } from '@angular/core';

isDrawerOpen = signal(false);
isDialogOpen = signal(false);
editingId = signal<string | null>(null);
isSubmittingOverlay = signal(false);
overlaySubmitAttempted = signal(false);
overlayError = signal<string>('');
showOverlaySuccessToast = signal(false);

isEditing = computed(() => this.editingId() !== null);
activeOverlayMode = computed<'drawer' | 'dialog' | null>(() => {
  if (this.isDrawerOpen()) return 'drawer';
  if (this.isDialogOpen()) return 'dialog';
  return null;
});
```

### Tailwind Layout Skeleton

```html
<div class="relative">
  <app-button type="button" (click)="openCreateDrawer()">New Record</app-button>

  <app-drawer
    title="Edit Record"
    description="Update the selected record without leaving the list."
    [open]="isDrawerOpen()"
    (openChange)="isDrawerOpen.set($event)"
    (closed)="resetOverlayState()"
  >
    <form class="space-y-4" [formGroup]="overlayForm" (ngSubmit)="submitOverlay()" novalidate>
      @if (overlayError()) {
        <app-alert variant="danger" role="alert" [message]="overlayError()" />
      }
      <app-text-input label="Name" [value]="overlayForm.controls.name.value" [error]="overlayFieldError('name')" (valueChange)="updateOverlayName($event)" />
      <app-select [options]="statusOptions" [value]="overlayForm.controls.status.value" (valueChange)="updateOverlayStatus($event)" />
      <app-textarea label="Notes" [rows]="4" [value]="overlayForm.controls.notes.value" [error]="overlayFieldError('notes')" (valueChange)="updateOverlayNotes($event)" />
    </form>

    <div drawer-actions>
      <app-button type="button" variant="secondary" (click)="closeDrawer()">Cancel</app-button>
      <app-button type="button" [loading]="isSubmittingOverlay()" [disabled]="overlayForm.invalid" (click)="submitOverlay()">Save</app-button>
    </div>
  </app-drawer>

  <app-dialog
    title="Confirm Archive"
    description="This action changes the record status to archived."
    [open]="isDialogOpen()"
    (openChange)="isDialogOpen.set($event)"
    (closed)="clearDialogState()"
  >
    <p class="text-sm text-gray-600">Archive the selected record?</p>
    <div dialog-actions>
      <app-button type="button" variant="secondary" (click)="isDialogOpen.set(false)">Cancel</app-button>
      <app-button type="button" (click)="confirmArchive()">Confirm</app-button>
    </div>
  </app-dialog>

  <div class="pointer-events-none fixed bottom-4 right-4 z-40">
    <app-toast [open]="showOverlaySuccessToast()" (openChange)="showOverlaySuccessToast.set($event)" title="Saved" message="Record updated." />
  </div>
</div>
```

### Accessibility Notes

- `app-drawer` and `app-dialog` already declare `role="dialog"` and `aria-modal`; provide clear `title` and `description`.
- Respect escape/backdrop close behavior; do not trap users in a failed submit state.
- Focus should return to the triggering button after overlay close (feature-level behavior to implement if needed).
- Keep destructive confirmations in `app-dialog` short and explicit.

### Acceptance Hooks

- Overlay open/close ownership is signal-based and not plain mutable booleans.
- Overlay form uses typed Reactive Forms and visible validation UI.
- `app-drawer` and/or `app-dialog` are wired with `(closed)` reset behavior.
- `app-toast` or equivalent result state is shown after successful overlay submit.
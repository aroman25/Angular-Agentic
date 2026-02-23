# Core Layout Patterns

Use one primary layout pattern per feature page. Pair with `forms-core.md` patterns when the page includes a form.

## Pattern ID: `layout-page-shell-header-toolbar`

### Goal / Use When

Use for a standard feature page shell with breadcrumb, page title, actions, and a content area that hosts cards, forms, tables, or tabs.

### Shared UI Composition Map

- `app-breadcrumb` -> `automate-angular-template/src/app/shared/ui/breadcrumb/breadcrumb.component.ts` -> route context and current page label.
- `app-toolbar` -> `automate-angular-template/src/app/shared/ui/toolbar/toolbar.component.ts` -> page-level quick actions/toggles.
- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> content panels.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> primary/secondary header actions.
- `app-dropdown-menu` -> `automate-angular-template/src/app/shared/ui/menu/menu.component.ts` -> overflow actions.
- `app-alert` (optional inline page banner) -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts`.

### Responsive Tailwind Skeleton

```html
<main class="min-h-screen bg-gray-50">
  <section class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="space-y-4">
      <app-breadcrumb [items]="breadcrumbItems" />

      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div class="min-w-0">
          <h1 class="text-2xl font-semibold tracking-tight text-gray-900">{{ pageTitle() }}</h1>
          <p class="mt-1 text-sm text-gray-600">{{ pageDescription() }}</p>
        </div>

        <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap lg:justify-end">
          <app-toolbar [items]="headerToolbarItems" ariaLabel="Page actions" />
          <app-dropdown-menu [label]="'More'" [items]="headerMenuItems" />
          <app-button type="button">Create</app-button>
        </div>
      </div>

      @if (pageBanner()) {
        <app-alert [variant]="pageBanner()!.variant" [message]="pageBanner()!.message" />
      }

      <app-card title="Overview">
        <ng-content></ng-content>
      </app-card>
    </div>
  </section>
</main>
```

### Required States

- Loading: render title skeleton and card skeletons when route/feature data is pending.
- Error: show a page-level `app-alert` above content.
- Populated: render primary content card(s).
- Empty (if applicable): host `app-empty-state` inside a card or directly below header.

### Accessibility and ARIA Notes

- Use `<main>` for primary page content.
- `app-breadcrumb` already renders nav semantics; ensure current item is marked `current`.
- `app-toolbar` should receive a descriptive `ariaLabel`.
- Header actions must remain keyboard reachable on mobile after wrapping.

### State Ownership Notes

- `pageTitle`, `pageDescription`, page banner, and toolbar selection should be signal-owned in the feature container.
- Menu item actions should be defined in typed TS arrays, not inline template lambdas.

### Pattern Variants

- Replace `app-toolbar` with plain button row if there are fewer than 3 actions.
- Use two-column header (`lg:grid`) when actions are dense and title text is long.

### Acceptance Hooks

- `app-breadcrumb` + action area present in the page shell.
- Mobile layout stacks header text and actions without horizontal overflow.
- Toolbar/menu item definitions live in TS and are typed.

---

## Pattern ID: `layout-dashboard-card-grid`

### Goal / Use When

Use for dashboard/overview pages with metric cards, progress indicators, and a secondary list/table/grid section.

### Shared UI Composition Map

- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> metric and content panels.
- `app-badge` -> `automate-angular-template/src/app/shared/ui/badge/badge.component.ts` -> trend/status markers on metric cards.
- `app-progress` -> `automate-angular-template/src/app/shared/ui/progress/progress.component.ts` -> completion/utilization bars.
- `app-table` -> `automate-angular-template/src/app/shared/ui/table/table.component.ts` -> summary lists.
- `app-data-grid` -> `automate-angular-template/src/app/shared/ui/data-grid/data-grid.component.ts` -> keyboard-accessible data panel variant.
- `app-empty-state` -> `automate-angular-template/src/app/shared/ui/empty-state/empty-state.component.ts` -> no data state.
- `app-skeleton` -> `automate-angular-template/src/app/shared/ui/skeleton/skeleton.component.ts` -> loading placeholders.
- `app-button` (optional panel CTA) -> `automate-angular-template/src/app/shared/ui/button/button.component.ts`.

### Responsive Tailwind Skeleton

```html
<main class="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <section class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    @if (isLoadingMetrics()) {
      @for (_ of [1,2,3,4]; track $index) {
        <app-card>
          <div class="space-y-3">
            <app-skeleton widthClass="w-20" heightClass="h-4" />
            <app-skeleton widthClass="w-28" heightClass="h-8" />
            <app-skeleton widthClass="w-full" heightClass="h-2" />
          </div>
        </app-card>
      }
    } @else {
      @for (metric of metrics(); track metric.id) {
        <app-card [interactive]="true" [tone]="metric.tone">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm text-gray-600">{{ metric.label }}</p>
              <p class="mt-1 text-2xl font-semibold text-gray-900">{{ metric.value }}</p>
            </div>
            <app-badge [variant]="metric.badgeVariant">{{ metric.badgeText }}</app-badge>
          </div>
          <div class="mt-4">
            <app-progress [label]="metric.progressLabel" [value]="metric.progressValue" [showValue]="true" />
          </div>
        </app-card>
      }
    }
  </section>

  <section class="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
    <app-card title="Recent Activity">
      @if (isLoadingTable()) {
        <div class="space-y-2">
          @for (_ of [1,2,3,4,5]; track $index) { <app-skeleton heightClass="h-10" /> }
        </div>
      } @else if (!hasActivityRows()) {
        <app-empty-state title="No activity yet" description="Activity will appear here once data is available." />
      } @else {
        <app-table [columns]="activityColumns" [rows]="activityRows()" trackByKey="id" />
      }
    </app-card>

    <app-card title="Queue Snapshot" description="Keyboard navigable grid variant.">
      @if (hasQueueRows()) {
        <app-data-grid [columns]="queueColumns" [rows]="queueRows()" trackByKey="id" [enableSelection]="true" />
      } @else {
        <app-empty-state title="No queued items" description="Nothing needs attention right now." />
      }
    </app-card>
  </section>
</main>
```

### Required States

- Metric loading placeholders (`app-skeleton` cards).
- Panel-level empty state (`app-empty-state`) for no rows.
- Populated metric cards and at least one data panel.
- Error state via `app-alert` in header or panel when fetch fails.

### Accessibility and ARIA Notes

- Maintain heading hierarchy (`h1` page title, `h2`/`h3` panel headings as needed).
- Ensure progress labels or `ariaLabel` describe what each bar represents.
- If using `app-data-grid`, confirm selection/focus behavior matches page expectations.

### State Ownership Notes

- Keep metrics, panel rows, and loading flags as separate signals (`metrics`, `activityRows`, `queueRows`, `isLoadingMetrics`, `isLoadingTable`).
- Derive `has*Rows` flags with `computed()` instead of template length logic everywhere.

### Pattern Variants

- Replace secondary `app-data-grid` with `app-table` if keyboard grid navigation is unnecessary.
- Use `lg:grid-cols-3` metric layout for narrower dashboards.

### Acceptance Hooks

- Metric cards reuse `app-card` and `app-progress` instead of custom card CSS.
- Loading/empty/populated states are all represented in templates.
- Shared table/grid components receive typed columns and rows from TS.

---

## Pattern ID: `layout-list-detail-drawer`

### Goal / Use When

Use for admin/list pages where a table/grid is primary and selecting or acting on a row opens a drawer for details/editing.

### Shared UI Composition Map

- `app-table` -> `automate-angular-template/src/app/shared/ui/table/table.component.ts` -> primary list rendering.
- `app-data-grid` -> `automate-angular-template/src/app/shared/ui/data-grid/data-grid.component.ts` -> keyboard-accessible list variant.
- `app-drawer` -> `automate-angular-template/src/app/shared/ui/drawer/drawer.component.ts` -> detail/edit panel.
- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> list filters/summary and drawer content grouping.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> row actions and drawer actions.
- `app-dropdown-menu` -> `automate-angular-template/src/app/shared/ui/menu/menu.component.ts` -> list row or header overflow actions.
- `app-pagination` -> `automate-angular-template/src/app/shared/ui/pagination/pagination.component.ts` -> page navigation.
- `app-empty-state` (optional) -> `automate-angular-template/src/app/shared/ui/empty-state/empty-state.component.ts` -> empty list state.

### Responsive Tailwind Skeleton

```html
<main class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Records</h1>
        <p class="text-sm text-gray-600">Browse, inspect, and edit records.</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <app-dropdown-menu [label]="'Bulk Actions'" [items]="bulkMenuItems" />
        <app-button type="button" (click)="openCreateDrawer()">New Record</app-button>
      </div>
    </div>

    <app-card title="Results">
      @if (isLoadingRows()) {
        <div class="space-y-2">@for (_ of [1,2,3,4]; track $index) { <app-skeleton heightClass="h-10" /> }</div>
      } @else if (!hasRows()) {
        <app-empty-state title="No records" description="Create a record to get started." />
      } @else {
        @if (useGridMode()) {
          <app-data-grid [columns]="gridColumns" [rows]="pagedRows()" trackByKey="id" [enableSelection]="true" />
        } @else {
          <app-table [columns]="tableColumns" [rows]="pagedRows()" trackByKey="id" />
        }
      }

      <div class="mt-4 border-t border-gray-100 pt-4">
        <app-pagination [totalPages]="totalPages()" [currentPage]="currentPage()" (currentPageChange)="currentPage.set($event)" />
      </div>
    </app-card>
  </div>

  <app-drawer title="Record Details" [open]="isDetailDrawerOpen()" (openChange)="isDetailDrawerOpen.set($event)" (closed)="clearActiveRow()">
    @if (activeRow()) {
      <div class="space-y-4">
        <app-card title="Summary">
          <dl class="grid gap-3 text-sm sm:grid-cols-2">
            <div><dt class="text-gray-500">ID</dt><dd class="font-medium text-gray-900">{{ activeRow()!.id }}</dd></div>
            <div><dt class="text-gray-500">Status</dt><dd class="font-medium text-gray-900">{{ activeRow()!.status }}</dd></div>
          </dl>
        </app-card>
      </div>
    }

    <div drawer-actions>
      <app-button type="button" variant="secondary" (click)="isDetailDrawerOpen.set(false)">Close</app-button>
      <app-button type="button" (click)="editActiveRow()">Edit</app-button>
    </div>
  </app-drawer>
</main>
```

### Required States

- List loading state (`app-skeleton`).
- Empty list state (`app-empty-state`).
- Populated list (`app-table` or `app-data-grid`) with pagination.
- Drawer closed/open states with `activeRow` ownership.

### Accessibility and ARIA Notes

- `app-drawer` provides dialog semantics; ensure title/description are meaningful.
- Row selection/open actions must be keyboard accessible (button/menu triggers, not only row click).
- Paginated list should preserve focus context after page changes where possible.

### State Ownership Notes

- `currentPage`, `activeRow`, `isDetailDrawerOpen`, `useGridMode`, and data rows should be signals.
- Derive `pagedRows` and `totalPages` with `computed()` from `rows`, `currentPage`, and `pageSize`.

### Pattern Variants

- Use a static side panel instead of `app-drawer` on wide-only internal tools.
- Swap to `app-dialog` for lightweight confirmation-only detail actions.

### Acceptance Hooks

- Drawer open/close state is signal-based and reset on `(closed)`.
- Table/grid and pagination are wired to the same source rows/paging state.
- Row actions use shared button/menu components rather than ad hoc HTML buttons everywhere.

---

## Pattern ID: `layout-settings-tabs-sections`

### Goal / Use When

Use for settings/admin pages with multiple configuration sections grouped by tabs and saved independently or together.

### Shared UI Composition Map

- `app-tabs` -> `automate-angular-template/src/app/shared/ui/tabs/tabs.component.ts` -> primary section navigation.
- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> tab panel subsections.
- `app-switch` -> `automate-angular-template/src/app/shared/ui/switch/switch.component.ts` -> boolean toggles.
- `app-checkbox` -> `automate-angular-template/src/app/shared/ui/checkbox/checkbox.component.ts` -> grouped opt-ins.
- `app-radio-group` -> `automate-angular-template/src/app/shared/ui/radio-group/radio-group.component.ts` -> mode/behavior choices.
- `app-alert` -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts` -> tab-level save errors/warnings.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> save/reset actions.
- `app-divider` (optional within cards) -> `automate-angular-template/src/app/shared/ui/divider/divider.component.ts` -> section separation.

### Responsive Tailwind Skeleton

```html
<main class="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <div>
    <h1 class="text-2xl font-semibold text-gray-900">Workspace Settings</h1>
    <p class="mt-1 text-sm text-gray-600">Manage defaults, notifications, and privacy controls.</p>
  </div>

  @if (settingsBanner()) {
    <app-alert [variant]="settingsBanner()!.variant" [message]="settingsBanner()!.message" />
  }

  <app-tabs [tabs]="settingsTabs" [selectedTab]="selectedSettingsTab()" (selectedTabChange)="selectedSettingsTab.set($event)"></app-tabs>

  <div class="sticky bottom-0 z-20 -mx-4 border-t border-gray-200 bg-white/95 px-4 py-3 backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:p-0">
    <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
      <app-button type="button" variant="secondary" (click)="resetCurrentTab()">Reset</app-button>
      <app-button type="button" [loading]="isSavingCurrentTab()" (click)="saveCurrentTab()">Save Changes</app-button>
    </div>
  </div>
</main>
```

### Required States

- Tab selection state (`app-tabs` selected value).
- Tab panel content states (loading if fetched lazily, populated sections, error banners).
- Save in progress / save success / save failure feedback.

### Accessibility and ARIA Notes

- `app-tabs` handles tablist/tab/tabpanel roles; ensure tab labels are short and descriptive.
- Sticky action bar must remain reachable and not obscure focused fields on mobile.
- Use `app-alert` for save feedback and choose `role` based on severity.

### State Ownership Notes

- `selectedSettingsTab`, tab-specific dirty states, and save/loading flags should be signals.
- Each tab section can own its own reactive form while the container owns tab selection and global banners.

### Pattern Variants

- Use `app-accordion` for narrow-only settings pages instead of tabs if tab count is high.
- Split save actions per card instead of a global sticky action bar for isolated settings groups.

### Acceptance Hooks

- `app-tabs` is used as the primary navigation for sections (not custom tabs).
- Selected tab state is signal-owned.
- Mobile action area remains visible and keyboard accessible.

---

## Pattern ID: `layout-wizard-progress-steps`

### Goal / Use When

Use for multi-step workflows (onboarding, import, guided configuration) where progress and step navigation must be visible. This layout can host `form-*` patterns inside step content.

### Shared UI Composition Map

- `app-progress` -> `automate-angular-template/src/app/shared/ui/progress/progress.component.ts` -> step completion indicator.
- `app-tabs` -> `automate-angular-template/src/app/shared/ui/tabs/tabs.component.ts` -> desktop step navigation (when step panels can map cleanly to tabs).
- `app-accordion` -> `automate-angular-template/src/app/shared/ui/accordion/accordion.component.ts` -> mobile step navigation container.
- `app-accordion-item` -> `automate-angular-template/src/app/shared/ui/accordion/accordion-item.component.ts` -> mobile step sections.
- `app-card` -> `automate-angular-template/src/app/shared/ui/card/card.component.ts` -> step content container.
- `app-button` -> `automate-angular-template/src/app/shared/ui/button/button.component.ts` -> next/back/finish controls.
- `app-alert` -> `automate-angular-template/src/app/shared/ui/alert/alert.component.ts` -> step validation summary or workflow warning.
- `app-badge` (optional step status chip) -> `automate-angular-template/src/app/shared/ui/badge/badge.component.ts`.

### Responsive Tailwind Skeleton

```html
<main class="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <div class="space-y-3">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Import Wizard</h1>
        <p class="text-sm text-gray-600">Complete each step to finish setup.</p>
      </div>
      <app-badge variant="info">Step {{ currentStepIndex() + 1 }} of {{ totalSteps() }}</app-badge>
    </div>

    <app-progress [label]="'Progress'" [value]="currentStepIndex() + 1" [max]="totalSteps()" [showValue]="true" />

    @if (wizardBanner()) {
      <app-alert [variant]="wizardBanner()!.variant" [message]="wizardBanner()!.message" />
    }
  </div>

  <div class="hidden md:block">
    <app-tabs [tabs]="wizardTabs" [selectedTab]="selectedStepId()" (selectedTabChange)="onStepTabChange($event)" />
  </div>

  <div class="md:hidden">
    <app-accordion [multiExpandable]="false">
      @for (step of steps(); track step.id) {
        <app-accordion-item [title]="step.label" [id]="step.id">
          <div class="pt-2">
            <app-card [title]="step.label" [description]="step.description">
              <ng-container [ngTemplateOutlet]="step.template"></ng-container>
            </app-card>
          </div>
        </app-accordion-item>
      }
    </app-accordion>
  </div>

  <app-card title="Step Actions" [tone]="'muted'">
    <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
      <app-button type="button" variant="secondary" [disabled]="!canGoBack()" (click)="goBack()">Back</app-button>
      <div class="flex flex-wrap justify-end gap-2">
        <app-button type="button" variant="ghost" (click)="saveDraft()">Save Draft</app-button>
        <app-button type="button" [disabled]="!canContinue()" (click)="goNext()">{{ isLastStep() ? 'Finish' : 'Next' }}</app-button>
      </div>
    </div>
  </app-card>
</main>
```

### Required States

- Current step selection and progress value.
- Step-level validation warnings/errors (`app-alert`).
- Optional draft/saved state and finish state.
- Responsive navigation mode (desktop tabs vs mobile accordion) based on breakpoint in template only (no JS viewport listener required unless behavior diverges).

### Accessibility and ARIA Notes

- `app-tabs` and `app-accordion` provide core ARIA roles; ensure step titles are unique.
- Progress bar label must describe wizard progress.
- Keep action button labels explicit (`Next`, `Back`, `Finish`) and disable unavailable actions.
- For validation failures, announce step-level alert near the step content region.

### State Ownership Notes

- Own `selectedStepId`, `currentStepIndex`, `completedStepIds`, and step validation states with signals.
- Derive `canContinue`, `canGoBack`, and `isLastStep` with `computed()`.
- Step forms can be separate typed reactive forms managed by each step container/component.

### Pattern Variants

- Tabs-only wizard for desktop-only internal tools.
- Accordion-only guided flow for long-form mobile-first experiences.
- Replace `app-tabs` with `app-toolbar` when step content is not tab-panel based but still needs keyboard-selectable navigation.

### Acceptance Hooks

- `app-progress` and one of (`app-tabs`, `app-accordion`) are used for navigation/progress.
- Step selection and navigation enable/disable logic are signal-based.
- Mobile and desktop layouts avoid horizontal overflow and preserve action button reachability.
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  signal,
} from '@angular/core';
import {
  AccordionComponent,
  AccordionItemComponent,
  AlertComponent,
  AutocompleteComponent,
  type AutocompleteOption,
  AvatarComponent,
  BadgeComponent,
  type BreadcrumbItem,
  BreadcrumbComponent,
  ButtonComponent,
  CardComponent,
  CheckboxComponent,
  DataGridComponent,
  type DataGridColumn,
  DialogComponent,
  DividerComponent,
  DrawerComponent,
  DropdownMenuComponent,
  type DropdownMenuItem,
  EmptyStateComponent,
  IconComponent,
  PaginationComponent,
  ProgressComponent,
  RadioGroupComponent,
  type RadioGroupOption,
  SelectComponent,
  type SelectOption,
  SkeletonComponent,
  SpinnerComponent,
  SwitchComponent,
  TableComponent,
  type TableColumn,
  TabsComponent,
  type TabsItem,
  TextInputComponent,
  TextareaComponent,
  ToastComponent,
  ToolbarComponent,
  type ToolbarItem,
  TreeComponent,
  type TreeNode,
} from 'src/app/shared/ui';

type ShowcaseItem = {
  id: string;
  title: string;
  selector: string;
  group: string;
  description: string;
};

type ShowcaseGroup = {
  title: string;
  items: ShowcaseItem[];
};

type DemoRow = {
  id: string;
  name: string;
  status: string;
  owner: string;
  updated: string;
  score: number;
};

@Component({
  selector: 'app-ui-components-gallery-page',
  imports: [
    AccordionComponent,
    AccordionItemComponent,
    AlertComponent,
    AutocompleteComponent,
    AvatarComponent,
    BadgeComponent,
    BreadcrumbComponent,
    ButtonComponent,
    CardComponent,
    CheckboxComponent,
    DataGridComponent,
    DialogComponent,
    DividerComponent,
    DrawerComponent,
    DropdownMenuComponent,
    EmptyStateComponent,
    IconComponent,
    PaginationComponent,
    ProgressComponent,
    RadioGroupComponent,
    SelectComponent,
    SkeletonComponent,
    SpinnerComponent,
    SwitchComponent,
    TableComponent,
    TabsComponent,
    TextInputComponent,
    TextareaComponent,
    ToastComponent,
    ToolbarComponent,
    TreeComponent,
  ],
  templateUrl: './ui-components-gallery.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UiComponentsGalleryPage {

  readonly activeNavId = signal<string>('accordion');
  readonly selectedAlertVariant = signal<'info' | 'success' | 'warning' | 'danger'>('info');
  readonly alertVisible = signal(true);
  readonly toastOpen = signal(true);
  readonly dialogOpen = signal(false);
  readonly drawerOpen = signal(false);
  readonly drawerSide = signal<'left' | 'right'>('right');
  readonly textInputValue = signal('Aster Ridge Workspace');
  readonly textareaValue = signal(
    'A focused UI component gallery with polished examples and production-friendly patterns.',
  );
  readonly selectValue = signal<string | null>('product');
  readonly autocompleteValue = signal<string | null>('alexa-rivera');
  readonly autocompleteInputValue = signal('Alexa Rivera');
  readonly checkboxChecked = signal(true);
  readonly switchChecked = signal(true);
  readonly radioValue = signal<string | null>('team');
  readonly paginationPage = signal(3);
  readonly progressValue = signal(68);
  readonly toolbarValues = signal<string[]>(['grid']);
  readonly treeValues = signal<string[]>(['tokens']);
  readonly tabsSelected = signal<string | undefined>('overview');
  readonly tabsDemoItems = signal<TabsItem[]>([
    { label: 'Overview', value: 'overview' },
    { label: 'Tokens', value: 'tokens' },
    { label: 'Interaction', value: 'interaction' },
  ]);
  readonly buttonClicks = signal(0);
  readonly eventLog = signal<string[]>(['Showcase ready. Explore the components using the left nav.']);

  readonly navGroups: ShowcaseGroup[] = [
    {
      title: 'Disclosure & Structure',
      items: [
        {
          id: 'accordion',
          title: 'Accordion',
          selector: 'app-accordion',
          group: 'Disclosure & Structure',
          description: 'Container for one or more expandable accordion panels.',
        },
        {
          id: 'accordion-item',
          title: 'Accordion Item',
          selector: 'app-accordion-item',
          group: 'Disclosure & Structure',
          description: 'Child panel component projected inside an accordion group.',
        },
        {
          id: 'card',
          title: 'Card',
          selector: 'app-card',
          group: 'Disclosure & Structure',
          description: 'Content container with optional header, tone, and interaction styles.',
        },
        {
          id: 'divider',
          title: 'Divider',
          selector: 'app-divider',
          group: 'Disclosure & Structure',
          description: 'Horizontal or vertical separator with optional label.',
        },
        {
          id: 'tabs',
          title: 'Tabs',
          selector: 'app-tabs',
          group: 'Disclosure & Structure',
          description: 'Accessible tablist and tab panels driven by tab definitions and templates.',
        },
      ],
    },
    {
      title: 'Forms & Inputs',
      items: [
        {
          id: 'autocomplete',
          title: 'Autocomplete',
          selector: 'app-autocomplete',
          group: 'Forms & Inputs',
          description: 'Single-select autocomplete using Angular Aria combobox/listbox patterns.',
        },
        {
          id: 'checkbox',
          title: 'Checkbox',
          selector: 'app-checkbox',
          group: 'Forms & Inputs',
          description: 'Checkbox with label, description, and visual mixed state support.',
        },
        {
          id: 'radio-group',
          title: 'Radio Group',
          selector: 'app-radio-group',
          group: 'Forms & Inputs',
          description: 'Grouped radio choices rendered from typed option data.',
        },
        {
          id: 'select',
          title: 'Select',
          selector: 'app-select',
          group: 'Forms & Inputs',
          description: 'Single-select dropdown built on Angular Aria combobox/listbox.',
        },
        {
          id: 'switch',
          title: 'Switch',
          selector: 'app-switch',
          group: 'Forms & Inputs',
          description: 'Boolean switch toggle with accessible state and labels.',
        },
        {
          id: 'text-input',
          title: 'Text Input',
          selector: 'app-text-input',
          group: 'Forms & Inputs',
          description: 'Reusable input control with label, hint, and error wiring.',
        },
        {
          id: 'textarea',
          title: 'Textarea',
          selector: 'app-textarea',
          group: 'Forms & Inputs',
          description: 'Textarea with built-in label, hint, and error state visuals.',
        },
      ],
    },
    {
      title: 'Feedback & Status',
      items: [
        {
          id: 'alert',
          title: 'Alert',
          selector: 'app-alert',
          group: 'Feedback & Status',
          description: 'Inline status banner with tone variants and dismiss behavior.',
        },
        {
          id: 'badge',
          title: 'Badge',
          selector: 'app-badge',
          group: 'Feedback & Status',
          description: 'Compact status label/tag in multiple variants.',
        },
        {
          id: 'progress',
          title: 'Progress',
          selector: 'app-progress',
          group: 'Feedback & Status',
          description: 'Determinate and indeterminate progress indicator bar.',
        },
        {
          id: 'skeleton',
          title: 'Skeleton',
          selector: 'app-skeleton',
          group: 'Feedback & Status',
          description: 'Animated loading placeholders in line, rect, or circle shapes.',
        },
        {
          id: 'spinner',
          title: 'Spinner',
          selector: 'app-spinner',
          group: 'Feedback & Status',
          description: 'Inline spinner icon for loading actions and status affordance.',
        },
        {
          id: 'toast',
          title: 'Toast',
          selector: 'app-toast',
          group: 'Feedback & Status',
          description: 'Lightweight inline toast panel for transient notifications.',
        },
      ],
    },
    {
      title: 'Navigation & Actions',
      items: [
        {
          id: 'breadcrumb',
          title: 'Breadcrumb',
          selector: 'app-breadcrumb',
          group: 'Navigation & Actions',
          description: 'Breadcrumb navigation from typed item definitions.',
        },
        {
          id: 'button',
          title: 'Button',
          selector: 'app-button',
          group: 'Navigation & Actions',
          description: 'Button variants, sizes, and loading states.',
        },
        {
          id: 'dropdown-menu',
          title: 'Dropdown Menu',
          selector: 'app-dropdown-menu',
          group: 'Navigation & Actions',
          description: 'Trigger + action menu using Angular Aria menu directives.',
        },
        {
          id: 'pagination',
          title: 'Pagination',
          selector: 'app-pagination',
          group: 'Navigation & Actions',
          description: 'Client-side pagination UI with page model and change event.',
        },
        {
          id: 'toolbar',
          title: 'Toolbar',
          selector: 'app-toolbar',
          group: 'Navigation & Actions',
          description: 'Keyboard-navigable toolbar with selectable action items.',
        },
      ],
    },
    {
      title: 'Data & Display',
      items: [
        {
          id: 'avatar',
          title: 'Avatar',
          selector: 'app-avatar',
          group: 'Data & Display',
          description: 'Image or initials avatar with sizes and soft styling.',
        },
        {
          id: 'data-grid',
          title: 'Data Grid',
          selector: 'app-data-grid',
          group: 'Data & Display',
          description: 'Accessible grid wrapper for keyboard-friendly tabular data.',
        },
        {
          id: 'empty-state',
          title: 'Empty State',
          selector: 'app-empty-state',
          group: 'Data & Display',
          description: 'Empty state panel with icon slot and action content.',
        },
        {
          id: 'icon',
          title: 'Icon',
          selector: 'app-icon',
          group: 'Data & Display',
          description: 'SVG wrapper that normalizes sizing and visual consistency.',
        },
        {
          id: 'table',
          title: 'Table',
          selector: 'app-table',
          group: 'Data & Display',
          description: 'Read-only table from typed columns and row objects.',
        },
        {
          id: 'tree',
          title: 'Tree',
          selector: 'app-tree',
          group: 'Data & Display',
          description: 'Recursive tree view with selectable and expandable nodes.',
        },
      ],
    },
    {
      title: 'Overlays',
      items: [
        {
          id: 'dialog',
          title: 'Dialog',
          selector: 'app-dialog',
          group: 'Overlays',
          description: 'Controlled modal dialog overlay with content and action slots.',
        },
        {
          id: 'drawer',
          title: 'Drawer',
          selector: 'app-drawer',
          group: 'Overlays',
          description: 'Controlled side panel overlay for detail or edit flows.',
        },
      ],
    },
  ];

  readonly allShowcaseItems = this.navGroups.flatMap((group) => group.items);
  readonly componentCount = computed(() => this.allShowcaseItems.length);
  readonly lastEvent = computed(() => this.eventLog()[0] ?? 'No events yet.');
  readonly selectedShowcaseItem = computed(
    () => this.allShowcaseItems.find((item) => item.id === this.activeNavId()) ?? this.allShowcaseItems[0],
  );
  readonly selectedComponentTitle = computed(() => this.selectedShowcaseItem()?.title ?? 'UI Component');

  readonly breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Examples', action: () => this.pushEvent('Breadcrumb: Examples clicked') },
    { label: 'Shared UI', action: () => this.pushEvent('Breadcrumb: Shared UI clicked') },
    { label: 'Component Gallery', current: true },
  ];

  readonly dropdownMenuItems: DropdownMenuItem[] = [
    { label: 'Duplicate', action: () => this.pushEvent('Dropdown menu: Duplicate') },
    { label: 'Archive', action: () => this.pushEvent('Dropdown menu: Archive') },
    { label: 'Delete', action: () => this.pushEvent('Dropdown menu: Delete') },
  ];

  readonly toolbarItems: ToolbarItem[] = [
    { label: 'Grid', value: 'grid', action: () => this.pushEvent('Toolbar item: Grid') },
    { label: 'List', value: 'list', action: () => this.pushEvent('Toolbar item: List') },
    { label: 'Compact', value: 'compact', action: () => this.pushEvent('Toolbar item: Compact') },
  ];

  readonly selectOptions: SelectOption<string>[] = [
    { label: 'Product', value: 'product' },
    { label: 'Design', value: 'design' },
    { label: 'Operations', value: 'ops' },
    { label: 'Support', value: 'support' },
  ];

  readonly autocompleteOptions: AutocompleteOption<string>[] = [
    { label: 'Alexa Rivera', value: 'alexa-rivera' },
    { label: 'Marcus Chen', value: 'marcus-chen' },
    { label: 'Priya Shah', value: 'priya-shah' },
    { label: 'Jordan Kim', value: 'jordan-kim' },
  ];

  readonly radioOptions: RadioGroupOption<string>[] = [
    { label: 'Private', value: 'private', description: 'Visible only to you.' },
    { label: 'Team', value: 'team', description: 'Visible to your workspace team.' },
    { label: 'Public', value: 'public', description: 'Visible to all users.' },
  ];

  readonly tableRows: DemoRow[] = [
    { id: 'r-100', name: 'Launch Checklist', status: 'In Review', owner: 'A. Rivera', updated: '2h ago', score: 92 },
    { id: 'r-101', name: 'Billing Migration', status: 'Blocked', owner: 'M. Chen', updated: '5h ago', score: 54 },
    { id: 'r-102', name: 'Design Tokens v3', status: 'Active', owner: 'P. Shah', updated: '1d ago', score: 88 },
    { id: 'r-103', name: 'QA Sweep', status: 'Queued', owner: 'J. Kim', updated: '2d ago', score: 71 },
  ];

  readonly tableColumns: TableColumn<DemoRow>[] = [
    { key: 'name', header: 'Name' },
    { key: 'status', header: 'Status' },
    { key: 'owner', header: 'Owner' },
    { key: 'updated', header: 'Updated', nowrap: true },
  ];

  readonly gridColumns: DataGridColumn<DemoRow>[] = [
    { key: 'name', header: 'Name' },
    { key: 'status', header: 'Status' },
    { key: 'score', header: 'Score', align: 'right' },
    { key: 'updated', header: 'Updated', nowrap: true },
  ];

  readonly treeNodes: TreeNode<string>[] = [
    {
      label: 'Design System',
      value: 'design-system',
      expanded: true,
      children: [
        { label: 'Tokens', value: 'tokens', expanded: true, children: [{ label: 'Colors', value: 'colors' }, { label: 'Spacing', value: 'spacing' }] },
        { label: 'Components', value: 'components', children: [{ label: 'Buttons', value: 'buttons' }, { label: 'Inputs', value: 'inputs' }] },
      ],
    },
    {
      label: 'App Features',
      value: 'app-features',
      children: [
        { label: 'Dashboard', value: 'dashboard' },
        { label: 'Settings', value: 'settings' },
      ],
    },
  ];

  readonly alertVariants: Array<'info' | 'success' | 'warning' | 'danger'> = [
    'info',
    'success',
    'warning',
    'danger',
  ];

  setActiveNav(id: string): void {
    this.activeNavId.set(id);
    if (id === 'dialog') {
      this.dialogOpen.set(true);
      this.pushEvent('Dialog preview auto-opened');
    }
    if (typeof document === 'undefined') return;
    const target = document.getElementById('component-preview-panel');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  isActive(id: string): boolean {
    return this.activeNavId() === id;
  }

  cycleAlertVariant(): void {
    const current = this.selectedAlertVariant();
    const nextIndex = (this.alertVariants.indexOf(current) + 1) % this.alertVariants.length;
    this.selectedAlertVariant.set(this.alertVariants[nextIndex]);
    this.alertVisible.set(true);
    this.pushEvent(`Alert variant: ${this.alertVariants[nextIndex]}`);
  }

  incrementButtonCounter(): void {
    this.buttonClicks.update((count) => count + 1);
    this.pushEvent(`Button clicked ${this.buttonClicks()} time(s)`);
  }

  randomizeProgress(): void {
    const next = 25 + Math.round(Math.random() * 70);
    this.progressValue.set(next);
    this.pushEvent(`Progress value updated to ${next}%`);
  }

  toggleToast(): void {
    const next = !this.toastOpen();
    this.toastOpen.set(next);
    this.pushEvent(`Toast ${next ? 'opened' : 'closed'}`);
  }

  openDialog(): void {
    this.dialogOpen.set(true);
    this.pushEvent('Dialog opened');
  }

  openDrawer(): void {
    this.drawerOpen.set(true);
    this.pushEvent(`Drawer opened (${this.drawerSide()} side)`);
  }

  flipDrawerSide(): void {
    const next = this.drawerSide() === 'right' ? 'left' : 'right';
    this.drawerSide.set(next);
    this.pushEvent(`Drawer side set to ${next}`);
  }

  onPaginationChanged(page: number): void {
    this.paginationPage.set(page);
    this.pushEvent(`Pagination page changed to ${page}`);
  }

  onToolbarTriggered(value: string): void {
    this.pushEvent(`Toolbar triggered: ${value}`);
  }

  onTabsSelectedChange(value: string | undefined): void {
    this.tabsSelected.set(value);
    this.pushEvent(`Tabs selected: ${value ?? 'none'}`);
  }

  onTreeValuesChange(values: string[]): void {
    this.treeValues.set(values);
    this.pushEvent(`Tree selection: ${values.join(', ') || 'none'}`);
  }

  clearEventLog(): void {
    this.eventLog.set(['Event log cleared.']);
  }

  formattedToolbarValues(): string {
    return this.toolbarValues().join(', ') || 'none';
  }

  formattedTreeValues(): string {
    return this.treeValues().join(', ') || 'none';
  }

  pushEvent(message: string): void {
    const timestamp = new Date().toLocaleTimeString();
    this.eventLog.update((entries) => [`${timestamp} - ${message}`, ...entries].slice(0, 8));
  }
}

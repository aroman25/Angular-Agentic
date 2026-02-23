/**
 * Usage: action toolbar with Angular Aria keyboard navigation.
 * Inputs/models/outputs: [items], [orientation], [wrap], [disabled], [ariaLabel], [(values)], (itemTriggered).
 * Note: Angular Aria toolbar selection state is exposed through [(values)] (string[]).
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, input, model, output } from '@angular/core';
import { Toolbar, ToolbarWidget } from '@angular/aria/toolbar';

export interface ToolbarItem {
  label: string;
  value: string;
  disabled?: boolean;
  action?: () => void;
}

@Component({
  selector: 'app-toolbar',
  standalone: true,
  imports: [Toolbar, ToolbarWidget],
  template: `
    <div
      ngToolbar
      [orientation]="orientation()"
      [wrap]="wrap()"
      [disabled]="disabled()"
      [(values)]="values"
      class="inline-flex flex-wrap items-center gap-1 rounded-lg border border-gray-200 bg-white p-1 shadow-sm"
      role="toolbar"
      [attr.aria-label]="ariaLabel()"
    >
      @for (item of items(); track item.value) {
        <button
          ngToolbarWidget
          type="button"
          [value]="item.value"
          [disabled]="item.disabled ?? false"
          class="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          [class.bg-blue-600]="isSelected(item.value)"
          [class.text-white]="isSelected(item.value)"
          [class.text-gray-700]="!isSelected(item.value)"
          [class.hover:bg-gray-100]="!isSelected(item.value)"
          (click)="activate(item)"
        >
          <span
            class="truncate"
            [class.text-white]="isSelected(item.value)"
            [class.text-gray-700]="!isSelected(item.value)"
          >
            {{ item.label }}
          </span>
        </button>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ToolbarComponent {
  items = input.required<ToolbarItem[]>();
  orientation = input<'horizontal' | 'vertical'>('horizontal');
  wrap = input(true, { transform: booleanAttribute });
  disabled = input(false, { transform: booleanAttribute });
  ariaLabel = input<string>('Toolbar');
  values = model<string[]>([]);
  itemTriggered = output<string>();

  activate(item: ToolbarItem): void {
    item.action?.();
    this.itemTriggered.emit(item.value);
  }

  isSelected(value: string): boolean {
    return this.values().includes(value);
  }
}

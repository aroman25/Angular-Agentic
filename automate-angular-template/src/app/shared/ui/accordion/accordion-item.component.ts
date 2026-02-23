/**
 * Usage: child item for <app-accordion>; project panel content inside the component.
 * Inputs: [title], optional [id].
 * Example: <app-accordion-item title="Details">Body content</app-accordion-item>
 */
import { ChangeDetectionStrategy, Component, computed, effect, inject, input, signal } from '@angular/core';
import { APP_ACCORDION_CONTEXT } from './accordion.component';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'app-accordion-item',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="border border-gray-200 rounded-md overflow-hidden">
      <button
        type="button"
        [id]="triggerElementId()"
        [attr.aria-expanded]="expanded()"
        [attr.aria-controls]="panelElementId()"
        (click)="toggle()"
        class="w-full flex justify-between items-center px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left font-medium text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      >
        <span>{{ title() }}</span>
        <app-icon
          class="w-5 h-5 text-gray-500 transition-transform duration-200"
          [class.rotate-180]="expanded()"
        >
          <svg
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </app-icon>
      </button>
      
      <div
        role="region"
        [id]="panelElementId()"
        [attr.aria-labelledby]="triggerElementId()"
        [attr.inert]="!expanded() ? true : null"
        class="overflow-hidden transition-all duration-200"
        [class.hidden]="!expanded()"
      >
        <div class="p-4 bg-white text-gray-700 border-t border-gray-200">
          <ng-content></ng-content>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccordionItemComponent {
  private readonly accordion = inject(APP_ACCORDION_CONTEXT, { optional: true });

  title = input.required<string>();
  id = input<string>(`accordion-item-${Math.random().toString(36).substring(2, 9)}`);
  readonly expanded = signal(false);
  readonly triggerElementId = computed(() => `${this.id()}-trigger`);
  readonly panelElementId = computed(() => `${this.id()}-panel`);

  constructor() {
    effect((onCleanup) => {
      const accordion = this.accordion;
      if (!accordion) {
        return;
      }

      const id = this.id();
      accordion.registerItem({ id, expanded: this.expanded });
      onCleanup(() => accordion.unregisterItem(id, this.expanded));
    });
  }

  toggle(): void {
    if (this.accordion) {
      this.accordion.toggleItem(this.id());
      return;
    }

    this.expanded.update(value => !value);
  }
}

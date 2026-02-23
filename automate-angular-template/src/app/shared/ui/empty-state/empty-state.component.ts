/**
 * Usage: empty-state panel with optional icon slot and action content.
 * Inputs: [title], [description].
 * Slots: [empty-state-icon] for icon, default slot for buttons/actions.
 */
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  template: `
    <section class="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
      <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-500">
        <ng-content select="[empty-state-icon]"></ng-content>
      </div>

      @if (title()) {
        <h3 class="text-base font-semibold text-gray-900">{{ title() }}</h3>
      }
      @if (description()) {
        <p class="mx-auto mt-2 max-w-prose text-sm text-gray-500">{{ description() }}</p>
      }

      <div class="mt-4 flex flex-wrap items-center justify-center gap-2">
        <ng-content></ng-content>
      </div>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EmptyStateComponent {
  title = input<string>('');
  description = input<string>('');
}

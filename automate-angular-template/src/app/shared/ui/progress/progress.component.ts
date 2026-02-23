/**
 * Usage: progress bar for determinate or indeterminate loading.
 * Inputs: [value], [max], [label], [ariaLabel], [showValue], [indeterminate].
 * Example: <app-progress [value]="42" [showValue]="true" label="Upload" />
 */
import { booleanAttribute, numberAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-progress',
  standalone: true,
  template: `
    <div class="w-full">
      @if (label() || (showValue() && !indeterminate())) {
        <div class="mb-1.5 flex items-center justify-between gap-2">
          <span class="text-sm font-medium text-gray-700">{{ label() }}</span>
          @if (showValue() && !indeterminate()) {
            <span class="text-xs text-gray-500">{{ percentage() }}%</span>
          }
        </div>
      }

      <div
        class="relative h-2.5 w-full overflow-hidden rounded-full bg-gray-200"
        role="progressbar"
        [attr.aria-valuemin]="0"
        [attr.aria-valuemax]="max()"
        [attr.aria-valuenow]="indeterminate() ? null : clampedValue()"
        [attr.aria-label]="ariaLabel() || label() || 'Progress'"
      >
        @if (indeterminate()) {
          <span class="absolute inset-y-0 left-0 w-1/3 animate-pulse rounded-full bg-blue-600"></span>
        } @else {
          <span
            class="absolute inset-y-0 left-0 rounded-full bg-blue-600 transition-[width] duration-300"
            [style.width.%]="percentage()"
          ></span>
        }
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProgressComponent {
  value = input(0, { transform: numberAttribute });
  max = input(100, { transform: numberAttribute });
  label = input<string>('');
  ariaLabel = input<string>('');
  showValue = input(false, { transform: booleanAttribute });
  indeterminate = input(false, { transform: booleanAttribute });

  clampedValue = computed(() => {
    const max = Math.max(this.max(), 1);
    return Math.min(Math.max(this.value(), 0), max);
  });

  percentage = computed(() => Math.round((this.clampedValue() / Math.max(this.max(), 1)) * 100));
}

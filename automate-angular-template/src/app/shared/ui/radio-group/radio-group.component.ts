/**
 * Usage: grouped radio options rendered from data.
 * Inputs/models: [label], [name], [options], [orientation], [disabled], [(value)].
 * Option shape: { label, value, description?, disabled? }.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';

let nextRadioGroupId = 0;

export interface RadioGroupOption<T = string> {
  label: string;
  value: T;
  description?: string;
  disabled?: boolean;
}

@Component({
  selector: 'app-radio-group',
  standalone: true,
  template: `
    <fieldset class="w-full" [disabled]="disabled()">
      @if (label()) {
        <legend class="mb-2 text-sm font-medium text-gray-700">{{ label() }}</legend>
      }

      <div [class]="optionsClass()">
        @for (option of options(); track $index) {
          <label
            class="flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 transition-colors"
            [class.border-blue-500]="isSelected(option.value)"
            [class.bg-blue-50]="isSelected(option.value)"
            [class.border-gray-200]="!isSelected(option.value)"
            [class.opacity-60]="disabled() || (option.disabled ?? false)"
          >
            <input
              type="radio"
              class="mt-0.5 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
              [name]="name()"
              [checked]="isSelected(option.value)"
              [disabled]="disabled() || (option.disabled ?? false)"
              (change)="select(option.value)"
            />
            <span class="min-w-0">
              <span class="block text-sm font-medium text-gray-900">{{ option.label }}</span>
              @if (option.description) {
                <span class="mt-0.5 block text-xs text-gray-500">{{ option.description }}</span>
              }
            </span>
          </label>
        }
      </div>
    </fieldset>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RadioGroupComponent<T> {
  label = input<string>('');
  name = input<string>(`app-radio-group-${++nextRadioGroupId}`);
  options = input.required<RadioGroupOption<T>[]>();
  orientation = input<'vertical' | 'horizontal'>('vertical');
  disabled = input(false, { transform: booleanAttribute });
  value = model<T | null>(null);

  optionsClass = computed(() =>
    this.orientation() === 'horizontal' ? 'grid gap-2 sm:grid-cols-2' : 'grid gap-2',
  );

  select(value: T): void {
    if (this.disabled()) return;
    this.value.set(value);
  }

  isSelected(value: T): boolean {
    return this.value() === value;
  }
}

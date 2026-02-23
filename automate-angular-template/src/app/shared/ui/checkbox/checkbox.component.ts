/**
 * Usage: checkbox with optional label/description and visual mixed state.
 * Inputs/models: [label], [description], [disabled], [required], [indeterminate], [(checked)].
 * Project extra helper content inside if needed.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

let nextCheckboxId = 0;

@Component({
  selector: 'app-checkbox',
  standalone: true,
  imports: [IconComponent],
  template: `
    <label class="inline-flex w-full cursor-pointer items-start gap-3" [class.opacity-70]="disabled()">
      <span class="relative mt-0.5 inline-flex">
        <input
          [id]="id()"
          type="checkbox"
          class="peer sr-only"
          [checked]="checked()"
          [indeterminate]="indeterminate()"
          [attr.aria-checked]="indeterminate() ? 'mixed' : checked()"
          [disabled]="disabled()"
          [required]="required()"
          (change)="onChange($event)"
        />

        <span [class]="boxClass()">
          @if (indeterminate()) {
            <span class="block h-0.5 w-2.5 rounded-full bg-white"></span>
          } @else if (checked()) {
            <app-icon class="h-3.5 w-3.5 text-white">
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                  clip-rule="evenodd"
                />
              </svg>
            </app-icon>
          }
        </span>
      </span>

      <span class="min-w-0">
        @if (label()) {
          <span class="block text-sm font-medium text-gray-900">{{ label() }}</span>
        }
        @if (description()) {
          <span class="mt-0.5 block text-xs text-gray-500">{{ description() }}</span>
        }
        <ng-content></ng-content>
      </span>
    </label>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckboxComponent {
  id = input<string>(`app-checkbox-${++nextCheckboxId}`);
  label = input<string>('');
  description = input<string>('');
  disabled = input(false, { transform: booleanAttribute });
  required = input(false, { transform: booleanAttribute });
  indeterminate = input(false, { transform: booleanAttribute });
  checked = model<boolean>(false);

  boxClass = computed(() => {
    const active = this.indeterminate() || this.checked();
    const tone = active ? 'border-blue-600 bg-blue-600' : 'border-gray-300 bg-white';
    return [
      'inline-flex h-5 w-5 items-center justify-center rounded border shadow-sm transition-colors',
      'peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-blue-500 peer-focus-visible:ring-offset-2',
      'peer-disabled:border-gray-300 peer-disabled:bg-gray-100',
      tone,
    ].join(' ');
  });

  onChange(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    this.checked.set(target.checked);
  }
}

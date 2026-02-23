/**
 * Usage: reusable text-like input with label/hint/error wiring.
 * Inputs/models: [label], [type], [placeholder], [hint], [error], [(value)] plus native attrs.
 * Use in forms via [(value)] or bridge it to a FormControl in a wrapper component.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';

let nextTextInputId = 0;

@Component({
  selector: 'app-text-input',
  standalone: true,
  template: `
    <div class="w-full">
      @if (label()) {
        <label [attr.for]="id()" class="mb-1.5 block text-sm font-medium text-gray-700">
          {{ label() }}
          @if (required()) {
            <span class="text-red-500" aria-hidden="true">*</span>
          }
        </label>
      }

      <input
        [id]="id()"
        [attr.type]="type()"
        [value]="value()"
        [placeholder]="placeholder()"
        [disabled]="disabled()"
        [readOnly]="readonly()"
        [required]="required()"
        [attr.autocomplete]="autocomplete() || null"
        [attr.inputmode]="inputmode() || null"
        [attr.aria-invalid]="hasError()"
        [attr.aria-describedby]="describedBy() || null"
        [class]="inputClass()"
        (input)="onInput($event)"
      />

      @if (hint() || error()) {
        <div class="mt-1.5 text-xs">
          @if (error()) {
            <p [id]="errorId()" class="text-red-600">{{ error() }}</p>
          }
          @if (hint() && !error()) {
            <p [id]="hintId()" class="text-gray-500">{{ hint() }}</p>
          }
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextInputComponent {
  id = input<string>(`app-text-input-${++nextTextInputId}`);
  label = input<string>('');
  type = input<'text' | 'email' | 'password' | 'tel' | 'url' | 'search' | 'number'>('text');
  placeholder = input<string>('');
  hint = input<string>('');
  error = input<string>('');
  autocomplete = input<string>('');
  inputmode = input<string>('');
  disabled = input(false, { transform: booleanAttribute });
  readonly = input(false, { transform: booleanAttribute });
  required = input(false, { transform: booleanAttribute });
  value = model<string>('');

  hasError = computed(() => this.error().trim().length > 0);
  hintId = computed(() => `${this.id()}-hint`);
  errorId = computed(() => `${this.id()}-error`);

  describedBy = computed(() => {
    if (this.hasError()) return this.errorId();
    return this.hint().trim() ? this.hintId() : '';
  });

  inputClass = computed(() => {
    const stateClass = this.hasError()
      ? 'border-red-300 text-red-900 placeholder:text-red-300 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-blue-500';

    return [
      'block w-full rounded-md border bg-white px-3 py-2 text-sm shadow-sm',
      'focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
      stateClass,
    ].join(' ');
  });

  onInput(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    this.value.set(target.value);
  }
}

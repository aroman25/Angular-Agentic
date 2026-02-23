/**
 * Usage: reusable textarea with label/hint/error states.
 * Inputs/models: [label], [rows], [placeholder], [hint], [error], [(value)].
 * Designed for composition inside feature forms; styling is fully internal.
 */
import { booleanAttribute, numberAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';

let nextTextareaId = 0;

@Component({
  selector: 'app-textarea',
  standalone: true,
  template: `
    <div class="w-full">
      @if (label()) {
        <label [attr.for]="id()" class="mb-1.5 block text-sm font-medium text-gray-700">
          {{ label() }}
        </label>
      }

      <textarea
        [id]="id()"
        [value]="value()"
        [rows]="rows()"
        [placeholder]="placeholder()"
        [disabled]="disabled()"
        [readOnly]="readonly()"
        [required]="required()"
        [attr.aria-invalid]="hasError()"
        [attr.aria-describedby]="describedBy() || null"
        [class]="textareaClass()"
        (input)="onInput($event)"
      ></textarea>

      @if (error()) {
        <p [id]="errorId()" class="mt-1.5 text-xs text-red-600">{{ error() }}</p>
      } @else if (hint()) {
        <p [id]="hintId()" class="mt-1.5 text-xs text-gray-500">{{ hint() }}</p>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextareaComponent {
  id = input<string>(`app-textarea-${++nextTextareaId}`);
  label = input<string>('');
  placeholder = input<string>('');
  hint = input<string>('');
  error = input<string>('');
  rows = input(4, { transform: numberAttribute });
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

  textareaClass = computed(() => {
    const stateClass = this.hasError()
      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';

    return [
      'block w-full rounded-md border bg-white px-3 py-2 text-sm text-gray-900 shadow-sm',
      'focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
      stateClass,
    ].join(' ');
  });

  onInput(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLTextAreaElement)) return;
    this.value.set(target.value);
  }
}

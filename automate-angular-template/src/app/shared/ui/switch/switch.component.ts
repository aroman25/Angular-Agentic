/**
 * Usage: boolean toggle control rendered as a switch.
 * Inputs/models: [label], [description], [size], [disabled], [(checked)].
 * Emits state changes through the writable model signal.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';

@Component({
  selector: 'app-switch',
  standalone: true,
  template: `
    <button
      type="button"
      role="switch"
      [attr.aria-checked]="checked()"
      [disabled]="disabled()"
      class="inline-flex items-start gap-3 text-left disabled:cursor-not-allowed disabled:opacity-60"
      (click)="toggle()"
    >
      <span [class]="trackClass()" aria-hidden="true">
        <span [class]="thumbClass()"></span>
      </span>

      <span class="min-w-0">
        @if (label()) {
          <span class="block text-sm font-medium text-gray-900">{{ label() }}</span>
        }
        @if (description()) {
          <span class="mt-0.5 block text-xs text-gray-500">{{ description() }}</span>
        }
      </span>
    </button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SwitchComponent {
  checked = model<boolean>(false);
  disabled = input(false, { transform: booleanAttribute });
  label = input<string>('');
  description = input<string>('');
  size = input<'sm' | 'md'>('md');

  trackClass = computed(() => {
    const sizeClass = this.size() === 'sm' ? 'h-5 w-9' : 'h-6 w-11';
    const bgClass = this.checked() ? 'bg-blue-600' : 'bg-gray-300';
    return [
      'relative inline-flex shrink-0 items-center rounded-full transition-colors',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
      sizeClass,
      bgClass,
    ].join(' ');
  });

  thumbClass = computed(() => {
    const base = this.size() === 'sm' ? 'h-4 w-4' : 'h-5 w-5';
    const translate =
      this.size() === 'sm'
        ? this.checked()
          ? 'translate-x-4'
          : 'translate-x-0.5'
        : this.checked()
          ? 'translate-x-5'
          : 'translate-x-0.5';
    return [
      'inline-block rounded-full bg-white shadow ring-0 transition-transform',
      base,
      translate,
    ].join(' ');
  });

  toggle(): void {
    if (this.disabled()) return;
    this.checked.set(!this.checked());
  }
}

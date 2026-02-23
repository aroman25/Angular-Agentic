/**
 * Usage: styled button wrapper with loading state.
 * Inputs: [variant], [size], [type], [disabled], [loading], [fullWidth].
 * Project label/icon content inside; loading shows internal spinner automatically.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { SpinnerComponent } from '../spinner/spinner.component';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [SpinnerComponent],
  template: `
    <button
      [attr.type]="type()"
      [disabled]="disabled() || loading()"
      [attr.aria-busy]="loading()"
      [class]="buttonClass()"
    >
      @if (loading()) {
        <app-spinner [size]="spinnerSize()" ariaLabel="Loading button action"></app-spinner>
      }
      <span [class.opacity-0]="loading() && iconOnly()">
        <ng-content></ng-content>
      </span>
    </button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ButtonComponent {
  variant = input<'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'link'>('primary');
  size = input<'sm' | 'md' | 'lg' | 'icon'>('md');
  type = input<'button' | 'submit' | 'reset'>('button');
  disabled = input(false, { transform: booleanAttribute });
  loading = input(false, { transform: booleanAttribute });
  fullWidth = input(false, { transform: booleanAttribute });

  iconOnly = computed(() => this.size() === 'icon');

  spinnerSize = computed<'sm' | 'md' | 'lg'>(() => {
    const size = this.size();
    if (size === 'sm') return 'sm';
    if (size === 'lg') return 'lg';
    return 'md';
  });

  buttonClass = computed(() => {
    const size = this.size();
    const variant = this.variant();

    const sizeClass =
      size === 'sm'
        ? 'h-8 px-3 text-sm'
        : size === 'lg'
          ? 'h-11 px-5 text-base'
          : size === 'icon'
            ? 'h-10 w-10 p-0'
            : 'h-10 px-4 text-sm';

    const variantClass =
      variant === 'secondary'
        ? 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400'
        : variant === 'outline'
          ? 'border border-gray-300 bg-white text-gray-900 hover:bg-gray-50 focus-visible:ring-gray-400'
          : variant === 'ghost'
            ? 'bg-transparent text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-400'
            : variant === 'danger'
              ? 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500'
              : variant === 'link'
                ? 'h-auto p-0 text-blue-600 underline-offset-4 hover:underline focus-visible:ring-blue-500 shadow-none'
                : 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500';

    const widthClass = this.fullWidth() ? 'w-full' : '';
    const layoutClass =
      size === 'icon'
        ? 'inline-flex items-center justify-center rounded-md'
        : 'inline-flex items-center justify-center gap-2 rounded-md';
    const baseClass =
      'relative font-medium shadow-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2';

    return [baseClass, layoutClass, sizeClass, variantClass, widthClass].filter(Boolean).join(' ');
  });
}

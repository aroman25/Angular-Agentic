/**
 * Usage: inline loading spinner icon.
 * Inputs: [size], [tone], [ariaLabel].
 * Example: <app-spinner size="sm" tone="brand" />
 */
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'app-spinner',
  standalone: true,
  imports: [IconComponent],
  template: `
    <span
      class="inline-flex items-center justify-center"
      role="status"
      [attr.aria-label]="ariaLabel()"
    >
      <app-icon [class]="iconClass()">
        <svg
          class="animate-spin motion-reduce:animate-none"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path
            class="opacity-90"
            d="M22 12a10 10 0 00-10-10"
            stroke="currentColor"
            stroke-width="4"
            stroke-linecap="round"
          />
        </svg>
      </app-icon>
    </span>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SpinnerComponent {
  size = input<'sm' | 'md' | 'lg'>('md');
  tone = input<'default' | 'muted' | 'brand' | 'danger'>('default');
  ariaLabel = input<string>('Loading');

  iconClass = computed(() => {
    const sizeClass =
      this.size() === 'sm' ? 'h-4 w-4' : this.size() === 'lg' ? 'h-6 w-6' : 'h-5 w-5';
    const toneClass =
      this.tone() === 'muted'
        ? 'text-gray-400'
        : this.tone() === 'brand'
          ? 'text-blue-600'
          : this.tone() === 'danger'
            ? 'text-red-600'
            : 'text-current';

    return `${sizeClass} ${toneClass}`;
  });
}

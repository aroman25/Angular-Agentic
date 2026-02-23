/**
 * Usage: small status/tag label.
 * Inputs: [variant], [size], [rounded]; project text/content inside.
 * Example: <app-badge variant="success">Paid</app-badge>
 */
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-badge',
  standalone: true,
  template: `
    <span [class]="badgeClass()">
      <ng-content></ng-content>
    </span>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BadgeComponent {
  variant = input<'default' | 'success' | 'warning' | 'danger' | 'outline' | 'info'>('default');
  size = input<'sm' | 'md'>('md');
  rounded = input<'full' | 'md'>('full');

  badgeClass = computed(() => {
    const sizeClass = this.size() === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';
    const radiusClass = this.rounded() === 'md' ? 'rounded-md' : 'rounded-full';
    const variantClass =
      this.variant() === 'success'
        ? 'bg-emerald-100 text-emerald-800 ring-emerald-600/20'
        : this.variant() === 'warning'
          ? 'bg-amber-100 text-amber-900 ring-amber-600/20'
          : this.variant() === 'danger'
            ? 'bg-red-100 text-red-800 ring-red-600/20'
            : this.variant() === 'outline'
              ? 'bg-white text-gray-700 ring-gray-300'
              : this.variant() === 'info'
                ? 'bg-sky-100 text-sky-800 ring-sky-600/20'
                : 'bg-blue-100 text-blue-800 ring-blue-600/20';

    return [
      'inline-flex items-center font-medium ring-1 ring-inset',
      sizeClass,
      radiusClass,
      variantClass,
    ].join(' ');
  });
}

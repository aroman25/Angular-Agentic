/**
 * Usage: loading placeholder block.
 * Inputs: [shape], [animate], [widthClass], [heightClass].
 * Size is controlled with Tailwind class inputs for flexible reuse.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  template: `<div [class]="skeletonClass()" aria-hidden="true"></div>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SkeletonComponent {
  shape = input<'line' | 'circle' | 'rect'>('line');
  animate = input(true, { transform: booleanAttribute });
  widthClass = input<string>('w-full');
  heightClass = input<string>('');

  skeletonClass = computed(() => {
    const shape = this.shape();
    const radius = shape === 'circle' ? 'rounded-full' : shape === 'rect' ? 'rounded-lg' : 'rounded';
    const defaultHeight = shape === 'line' ? 'h-4' : shape === 'circle' ? 'h-10 w-10' : 'h-24';
    const animateClass = this.animate() ? 'animate-pulse motion-reduce:animate-none' : '';

    return [
      'bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200',
      radius,
      animateClass,
      this.widthClass(),
      this.heightClass() || defaultHeight,
    ]
      .filter(Boolean)
      .join(' ');
  });
}

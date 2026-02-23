/**
 * Usage: avatar for image or initials fallback.
 * Inputs: [src], [alt], [name], [size], [soft], [ariaLabel].
 * If [src] is empty, initials are derived from [name].
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-avatar',
  standalone: true,
  template: `
    <span [class]="hostClass()" [attr.aria-label]="ariaLabel() || null">
      @if (src()) {
        <img [src]="src()" [alt]="alt()" class="h-full w-full object-cover" [class.opacity-90]="soft()" />
      } @else {
        <span class="text-current">{{ initials() }}</span>
      }
    </span>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AvatarComponent {
  src = input<string>('');
  alt = input<string>('');
  name = input<string>('');
  size = input<'xs' | 'sm' | 'md' | 'lg' | 'xl'>('md');
  soft = input(false, { transform: booleanAttribute });
  ariaLabel = input<string>('');

  initials = computed(() => {
    const trimmed = this.name().trim();
    if (!trimmed) return '?';
    const parts = trimmed.split(/\s+/).slice(0, 2);
    return parts.map((part) => part[0]?.toUpperCase() ?? '').join('') || '?';
  });

  hostClass = computed(() => {
    const sizeClass =
      this.size() === 'xs'
        ? 'h-6 w-6 text-[10px]'
        : this.size() === 'sm'
          ? 'h-8 w-8 text-xs'
          : this.size() === 'lg'
            ? 'h-12 w-12 text-base'
            : this.size() === 'xl'
              ? 'h-16 w-16 text-lg'
              : 'h-10 w-10 text-sm';
    const toneClass = this.soft()
      ? 'bg-gray-100 text-gray-600 ring-1 ring-gray-200'
      : 'bg-blue-600 text-white';

    return [
      'inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold',
      sizeClass,
      toneClass,
    ].join(' ');
  });
}

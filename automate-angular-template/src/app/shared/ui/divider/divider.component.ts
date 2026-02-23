/**
 * Usage: visual separator line (horizontal or vertical).
 * Inputs: [orientation], optional [label] (label is rendered only for horizontal divider).
 * Example: <app-divider label="OR" />
 */
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-divider',
  standalone: true,
  template: `
    @if (label() && orientation() === 'horizontal') {
      <div class="flex w-full items-center" role="separator" aria-orientation="horizontal">
        <span class="h-px flex-1 bg-gray-200"></span>
        <span class="px-3 text-xs font-medium uppercase tracking-wide text-gray-500">
          {{ label() }}
        </span>
        <span class="h-px flex-1 bg-gray-200"></span>
      </div>
    } @else {
      <div [class]="lineClass()" role="separator" [attr.aria-orientation]="orientation()"></div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DividerComponent {
  orientation = input<'horizontal' | 'vertical'>('horizontal');
  label = input<string>('');

  lineClass = computed(() =>
    this.orientation() === 'vertical' ? 'h-full w-px bg-gray-200' : 'h-px w-full bg-gray-200',
  );
}

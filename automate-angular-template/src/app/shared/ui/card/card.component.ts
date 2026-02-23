/**
 * Usage: content container with optional header.
 * Inputs: [title], [description], [padded], [tone], [interactive].
 * Project body content inside the component.
 */
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <section [class]="cardClass()">
      @if (title() || description()) {
        <header class="border-b border-gray-100 px-5 py-4">
          @if (title()) {
            <h3 class="text-base font-semibold text-gray-900">{{ title() }}</h3>
          }
          @if (description()) {
            <p class="mt-1 text-sm text-gray-500">{{ description() }}</p>
          }
        </header>
      }

      <div [class]="contentClass()">
        <ng-content></ng-content>
      </div>
    </section>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CardComponent {
  title = input<string>('');
  description = input<string>('');
  padded = input(true);
  tone = input<'default' | 'muted' | 'brand'>('default');
  interactive = input(false);

  cardClass = computed(() => {
    const toneClass =
      this.tone() === 'muted'
        ? 'border-gray-200 bg-gray-50'
        : this.tone() === 'brand'
          ? 'border-blue-100 bg-blue-50/50'
          : 'border-gray-200 bg-white';
    const interactiveClass = this.interactive() ? 'transition-shadow hover:shadow-md' : '';
    return ['rounded-xl border shadow-sm', toneClass, interactiveClass].filter(Boolean).join(' ');
  });

  contentClass = computed(() => (this.padded() ? 'p-5' : ''));
}

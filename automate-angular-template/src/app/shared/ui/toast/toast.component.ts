/**
 * Usage: lightweight toast panel for notifications (no service included).
 * Inputs/models/outputs: [title], [message], [tone], [dismissible], [polite], [(open)], (closed).
 * Render inside a toast container/layout managed by the feature page.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model, output } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [IconComponent],
  template: `
    @if (open()) {
      <div [class]="hostClass()" role="status" [attr.aria-live]="polite() ? 'polite' : 'assertive'">
        <div class="min-w-0 flex-1">
          @if (title()) {
            <p class="text-sm font-semibold">{{ title() }}</p>
          }
          @if (message()) {
            <p class="text-sm text-gray-600" [class.mt-0.5]="title()">{{ message() }}</p>
          }
          <ng-content></ng-content>
        </div>

        @if (dismissible()) {
          <button
            type="button"
            class="inline-flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            (click)="close()"
            [attr.aria-label]="closeLabel()"
          >
            <app-icon class="h-4 w-4">
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M4.22 4.22a.75.75 0 011.06 0L10 8.94l4.72-4.72a.75.75 0 111.06 1.06L11.06 10l4.72 4.72a.75.75 0 01-1.06 1.06L10 11.06l-4.72 4.72a.75.75 0 01-1.06-1.06L8.94 10 4.22 5.28a.75.75 0 010-1.06z"
                  clip-rule="evenodd"
                />
              </svg>
            </app-icon>
          </button>
        }
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ToastComponent {
  title = input<string>('');
  message = input<string>('');
  dismissible = input(true, { transform: booleanAttribute });
  closeLabel = input<string>('Dismiss toast');
  polite = input(true, { transform: booleanAttribute });
  open = model<boolean>(true);
  tone = input<'default' | 'success' | 'warning' | 'danger'>('default');
  closed = output<void>();

  hostClass = computed(() => {
    const toneClass =
      this.tone() === 'success'
        ? 'border-emerald-200'
        : this.tone() === 'warning'
          ? 'border-amber-200'
          : this.tone() === 'danger'
            ? 'border-red-200'
            : 'border-gray-200';

    return [
      'flex w-full max-w-sm items-start gap-3 rounded-xl border bg-white p-4 shadow-lg',
      toneClass,
    ].join(' ');
  });

  close(): void {
    this.open.set(false);
    this.closed.emit();
  }
}

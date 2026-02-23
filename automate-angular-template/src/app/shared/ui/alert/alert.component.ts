/**
 * Usage: inline status/error banner with optional dismiss button.
 * Inputs/models/outputs: [variant], [title], [message], [dismissible], [role], [(visible)], (closed).
 * Project additional content/actions inside when needed.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model, output } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [IconComponent],
  template: `
    @if (visible()) {
      <div [attr.role]="role()" [class]="containerClass()">
        <app-icon [class]="iconClass()">
          @switch (variant()) {
            @case ('success') {
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                  clip-rule="evenodd"
                />
              </svg>
            }
            @case ('warning') {
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.72-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.981-1.742 2.981H4.42c-1.53 0-2.492-1.647-1.742-2.98l5.58-9.92zM11 7a1 1 0 10-2 0v3a1 1 0 102 0V7zm-1 7a1.25 1.25 0 100-2.5A1.25 1.25 0 0010 14z"
                  clip-rule="evenodd"
                />
              </svg>
            }
            @case ('danger') {
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.53-10.47a.75.75 0 00-1.06-1.06L10 8.94 7.53 6.47a.75.75 0 00-1.06 1.06L8.94 10l-2.47 2.47a.75.75 0 101.06 1.06L10 11.06l2.47 2.47a.75.75 0 001.06-1.06L11.06 10l2.47-2.47z"
                  clip-rule="evenodd"
                />
              </svg>
            }
            @default {
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fill-rule="evenodd"
                  d="M18 10A8 8 0 112 10a8 8 0 0116 0zm-7-4a1 1 0 10-2 0 1 1 0 002 0zm-2 3a1 1 0 000 2v3a1 1 0 102 0v-3a1 1 0 00-2-2z"
                  clip-rule="evenodd"
                />
              </svg>
            }
          }
        </app-icon>

        <div class="min-w-0 flex-1">
          @if (title()) {
            <h4 class="font-medium">{{ title() }}</h4>
          }
          @if (message()) {
            <p class="text-sm opacity-90" [class.mt-1]="title()">{{ message() }}</p>
          }
          <ng-content></ng-content>
        </div>

        @if (dismissible()) {
          <button
            type="button"
            class="inline-flex h-7 w-7 items-center justify-center rounded-md hover:bg-black/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
            [attr.aria-label]="closeLabel()"
            (click)="dismiss()"
          >
            <span aria-hidden="true" class="text-base leading-none">&times;</span>
          </button>
        }
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertComponent {
  variant = input<'info' | 'success' | 'warning' | 'danger'>('info');
  title = input<string>('');
  message = input<string>('');
  dismissible = input(false, { transform: booleanAttribute });
  closeLabel = input<string>('Dismiss alert');
  role = input<'status' | 'alert'>('status');
  visible = model<boolean>(true);
  closed = output<void>();

  containerClass = computed(() => {
    const tone =
      this.variant() === 'success'
        ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
        : this.variant() === 'warning'
          ? 'border-amber-200 bg-amber-50 text-amber-900'
          : this.variant() === 'danger'
            ? 'border-red-200 bg-red-50 text-red-900'
            : 'border-sky-200 bg-sky-50 text-sky-900';
    return ['flex items-start gap-3 rounded-lg border p-4', tone].join(' ');
  });

  iconClass = computed(() => {
    const tone =
      this.variant() === 'success'
        ? 'text-emerald-600'
        : this.variant() === 'warning'
          ? 'text-amber-600'
          : this.variant() === 'danger'
            ? 'text-red-600'
            : 'text-sky-600';
    return `h-5 w-5 ${tone}`;
  });

  dismiss(): void {
    this.visible.set(false);
    this.closed.emit();
  }
}

/**
 * Usage: controlled modal dialog overlay component.
 * Inputs/models/outputs: [title], [description], [closeOnBackdrop], [(open)], (closed).
 * Slots: default body content + [dialog-actions] for footer actions.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, input, model, output } from '@angular/core';

@Component({
  selector: 'app-dialog',
  standalone: true,
  template: `
    @if (open()) {
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        (click)="onBackdropClick($event)"
      >
        <div class="absolute inset-0 bg-black/40 backdrop-blur-[1px]" data-dialog-backdrop="true"></div>

        <section
          class="relative z-10 w-full max-w-lg rounded-xl border border-gray-200 bg-white shadow-2xl"
          role="dialog"
          aria-modal="true"
          [attr.aria-labelledby]="title() ? titleId() : null"
          [attr.aria-describedby]="description() ? descriptionId() : null"
          tabindex="-1"
          (keydown.escape)="close()"
        >
          @if (title() || description()) {
            <header class="border-b border-gray-100 px-5 py-4">
              @if (title()) {
                <h2 [id]="titleId()" class="text-lg font-semibold text-gray-900">{{ title() }}</h2>
              }
              @if (description()) {
                <p [id]="descriptionId()" class="mt-1 text-sm text-gray-500">{{ description() }}</p>
              }
            </header>
          }

          <div class="px-5 py-4">
            <ng-content></ng-content>
          </div>

          <div class="flex flex-wrap items-center justify-end gap-2 border-t border-gray-100 px-5 py-4">
            <ng-content select="[dialog-actions]"></ng-content>
          </div>
        </section>
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DialogComponent {
  title = input<string>('');
  description = input<string>('');
  closeOnBackdrop = input(true, { transform: booleanAttribute });
  open = model<boolean>(false);
  closed = output<void>();
  private static nextId = 0;
  private readonly baseId = `app-dialog-${++DialogComponent.nextId}`;

  titleId(): string {
    return `${this.baseId}-title`;
  }

  descriptionId(): string {
    return `${this.baseId}-description`;
  }

  onBackdropClick(event: MouseEvent): void {
    if (!this.closeOnBackdrop()) return;
    const target = event.target;
    if (target instanceof HTMLElement && target.dataset['dialogBackdrop'] === 'true') {
      this.close();
    }
  }

  close(): void {
    this.open.set(false);
    this.closed.emit();
  }
}

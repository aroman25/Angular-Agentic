/**
 * Usage: controlled side drawer/panel overlay.
 * Inputs/models/outputs: [title], [description], [side], [closeOnBackdrop], [(open)], (closed).
 * Slots: default body content + [drawer-actions] for footer actions.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, computed, input, model, output } from '@angular/core';

@Component({
  selector: 'app-drawer',
  standalone: true,
  template: `
    @if (open()) {
      <div class="fixed inset-0 z-50" (click)="onBackdropClick($event)">
        <div class="absolute inset-0 bg-black/30" data-drawer-backdrop="true"></div>

        <aside
          role="dialog"
          aria-modal="true"
          class="absolute inset-y-0 flex w-full max-w-md flex-col bg-white shadow-2xl"
          [class]="panelPositionClass()"
          tabindex="-1"
          (keydown.escape)="close()"
        >
          <header class="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
            <div>
              @if (title()) {
                <h2 class="text-base font-semibold text-gray-900">{{ title() }}</h2>
              }
              @if (description()) {
                <p class="mt-1 text-sm text-gray-500">{{ description() }}</p>
              }
            </div>

            <button
              type="button"
              class="rounded-md px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              (click)="close()"
              [attr.aria-label]="closeLabel()"
            >
              Close
            </button>
          </header>

          <div class="min-h-0 flex-1 overflow-y-auto px-5 py-4">
            <ng-content></ng-content>
          </div>

          <footer class="flex flex-wrap items-center justify-end gap-2 border-t border-gray-100 px-5 py-4">
            <ng-content select="[drawer-actions]"></ng-content>
          </footer>
        </aside>
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DrawerComponent {
  title = input<string>('');
  description = input<string>('');
  side = input<'left' | 'right'>('right');
  closeOnBackdrop = input(true, { transform: booleanAttribute });
  closeLabel = input<string>('Close drawer');
  open = model<boolean>(false);
  closed = output<void>();

  panelPositionClass = computed(() =>
    this.side() === 'left' ? 'left-0 border-r border-gray-200' : 'right-0 border-l border-gray-200',
  );

  onBackdropClick(event: MouseEvent): void {
    if (!this.closeOnBackdrop()) return;
    const target = event.target;
    if (target instanceof HTMLElement && target.dataset['drawerBackdrop'] === 'true') {
      this.close();
    }
  }

  close(): void {
    this.open.set(false);
    this.closed.emit();
  }
}

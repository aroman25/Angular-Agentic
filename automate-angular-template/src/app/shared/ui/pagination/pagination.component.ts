/**
 * Usage: client-side pagination control UI.
 * Inputs/models/outputs: [totalPages], [siblingCount], [(currentPage)], (pageChange).
 * Parent component owns data slicing/fetching; this component only manages page UI state.
 */
import { ChangeDetectionStrategy, Component, computed, input, model, output } from '@angular/core';

@Component({
  selector: 'app-pagination',
  standalone: true,
  template: `
    <nav class="flex flex-wrap items-center justify-between gap-3" aria-label="Pagination">
      <p class="text-sm text-gray-600">
        Page <span class="font-medium text-gray-900">{{ currentPage() }}</span> of
        <span class="font-medium text-gray-900">{{ totalPages() }}</span>
      </p>

      <div class="inline-flex items-center gap-1">
        <button
          type="button"
          class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          [disabled]="currentPage() <= 1"
          (click)="goTo(currentPage() - 1)"
        >
          Previous
        </button>

        @for (page of visiblePages(); track page) {
          @if (page === '…') {
            <span class="px-2 text-sm text-gray-400" aria-hidden="true">…</span>
          } @else {
            <button
              type="button"
              class="min-w-9 rounded-md px-3 py-1.5 text-sm"
              [class.bg-blue-600]="page === currentPage()"
              [class.text-white]="page === currentPage()"
              [class.hover:bg-gray-100]="page !== currentPage()"
              [class.text-gray-700]="page !== currentPage()"
              [attr.aria-current]="page === currentPage() ? 'page' : null"
              (click)="goTo(page)"
            >
              {{ page }}
            </button>
          }
        }

        <button
          type="button"
          class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          [disabled]="currentPage() >= totalPages()"
          (click)="goTo(currentPage() + 1)"
        >
          Next
        </button>
      </div>
    </nav>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaginationComponent {
  totalPages = input<number>(1);
  siblingCount = input<number>(1);
  currentPage = model<number>(1);
  pageChange = output<number>();

  visiblePages = computed<Array<number | '…'>>(() => {
    const total = Math.max(this.totalPages(), 1);
    const current = Math.min(Math.max(this.currentPage(), 1), total);
    const siblings = Math.max(this.siblingCount(), 0);

    if (total <= 7) {
      return Array.from({ length: total }, (_, index) => index + 1);
    }

    const start = Math.max(current - siblings, 2);
    const end = Math.min(current + siblings, total - 1);
    const pages: Array<number | '…'> = [1];

    if (start > 2) pages.push('…');
    for (let page = start; page <= end; page += 1) {
      pages.push(page);
    }
    if (end < total - 1) pages.push('…');
    pages.push(total);

    return pages;
  });

  goTo(page: number): void {
    const total = Math.max(this.totalPages(), 1);
    const next = Math.min(Math.max(page, 1), total);
    this.currentPage.set(next);
    this.pageChange.emit(next);
  }
}

/**
 * Usage: generic read-only table from column definitions + row objects.
 * Inputs: [columns], [rows], [emptyMessage], [trackByKey].
 * Column shape: { key, header, align?, nowrap? } where key maps to a row property.
 */
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export interface TableColumn<T extends Record<string, unknown>> {
  key: keyof T & string;
  header: string;
  align?: 'left' | 'center' | 'right';
  nowrap?: boolean;
}

@Component({
  selector: 'app-table',
  standalone: true,
  template: `
    <div class="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            @for (column of columns(); track column.key) {
              <th
                scope="col"
                class="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-600"
                [class.text-left]="column.align !== 'right' && column.align !== 'center'"
                [class.text-center]="column.align === 'center'"
                [class.text-right]="column.align === 'right'"
              >
                {{ column.header }}
              </th>
            }
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          @if (rows().length === 0) {
            <tr>
              <td [attr.colspan]="columns().length" class="px-4 py-8 text-center text-sm text-gray-500">
                {{ emptyMessage() }}
              </td>
            </tr>
          } @else {
            @for (row of rows(); track rowTrackBy(row, $index); let rowIndex = $index) {
              <tr class="hover:bg-gray-50/80">
                @for (column of columns(); track column.key) {
                  <td
                    class="px-4 py-3 text-sm text-gray-700"
                    [class.whitespace-nowrap]="column.nowrap"
                    [class.text-left]="column.align !== 'right' && column.align !== 'center'"
                    [class.text-center]="column.align === 'center'"
                    [class.text-right]="column.align === 'right'"
                  >
                    {{ formatCell(row[column.key], row, column.key, rowIndex) }}
                  </td>
                }
              </tr>
            }
          }
        </tbody>
      </table>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TableComponent<T extends Record<string, unknown>> {
  columns = input.required<TableColumn<T>[]>();
  rows = input.required<T[]>();
  emptyMessage = input<string>('No rows found.');
  trackByKey = input<keyof T & string | ''>('');

  rowTrackBy(row: T, index: number): string | number {
    const key = this.trackByKey();
    if (key && typeof row[key] !== 'undefined') {
      const value = row[key];
      if (typeof value === 'string' || typeof value === 'number') return value;
    }
    return index;
  }

  formatCell(value: unknown, _row: T, _columnKey: keyof T & string, _rowIndex: number): string {
    if (value == null) return '';
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (value instanceof Date) return value.toISOString();
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
}

/**
 * Usage: keyboard-accessible data grid wrapper built on Angular Aria grid.
 * Inputs: [columns], [rows], [enableSelection], [multi], [selectionMode], [trackByKey].
 * Use when you need grid keyboard navigation; use <app-table> for simpler read-only tables.
 */
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Grid, GridCell, GridRow } from '@angular/aria/grid';

export interface DataGridColumn<T extends Record<string, unknown>> {
  key: keyof T & string;
  header: string;
  align?: 'left' | 'center' | 'right';
  nowrap?: boolean;
}

@Component({
  selector: 'app-data-grid',
  standalone: true,
  imports: [Grid, GridRow, GridCell],
  template: `
    <div class="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table
        ngGrid
        class="min-w-full border-separate border-spacing-0"
        [enableSelection]="enableSelection()"
        [multi]="multi()"
        [selectionMode]="selectionMode()"
      >
        <thead class="bg-gray-50">
          <tr ngGridRow>
            @for (column of columns(); track column.key) {
              <th
                ngGridCell
                [role]="'columnheader'"
                scope="col"
                class="border-b border-gray-200 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-600"
                [class.text-left]="column.align !== 'right' && column.align !== 'center'"
                [class.text-center]="column.align === 'center'"
                [class.text-right]="column.align === 'right'"
              >
                {{ column.header }}
              </th>
            }
          </tr>
        </thead>

        <tbody>
          @if (rows().length === 0) {
            <tr ngGridRow>
              <td ngGridCell [attr.colspan]="columns().length" class="px-4 py-8 text-center text-sm text-gray-500">
                {{ emptyMessage() }}
              </td>
            </tr>
          } @else {
            @for (row of rows(); track rowTrackBy(row, $index); let rowIndex = $index) {
              <tr ngGridRow class="hover:bg-gray-50/80">
                @for (column of columns(); track column.key) {
                  <td
                    ngGridCell
                    class="border-b border-gray-100 px-4 py-3 text-sm text-gray-700"
                    [class.whitespace-nowrap]="column.nowrap"
                    [class.text-left]="column.align !== 'right' && column.align !== 'center'"
                    [class.text-center]="column.align === 'center'"
                    [class.text-right]="column.align === 'right'"
                  >
                    {{ formatCell(row[column.key], rowIndex, column.key) }}
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
export class DataGridComponent<T extends Record<string, unknown>> {
  columns = input.required<DataGridColumn<T>[]>();
  rows = input.required<T[]>();
  emptyMessage = input<string>('No rows found.');
  enableSelection = input(false, { transform: booleanAttribute });
  multi = input(false, { transform: booleanAttribute });
  selectionMode = input<'follow' | 'explicit'>('explicit');
  trackByKey = input<keyof T & string | ''>('');

  rowTrackBy(row: T, index: number): string | number {
    const key = this.trackByKey();
    if (key && typeof row[key] !== 'undefined') {
      const value = row[key];
      if (typeof value === 'string' || typeof value === 'number') return value;
    }
    return index;
  }

  formatCell(value: unknown, _rowIndex: number, _columnKey: keyof T & string): string {
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

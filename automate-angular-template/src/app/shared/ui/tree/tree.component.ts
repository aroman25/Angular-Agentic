/**
 * Usage: recursive tree view backed by Angular Aria tree directives.
 * Inputs/models: [nodes], [emptyMessage], [multi], [wrap], [selectionMode], [focusMode], [(values)].
 * Node shape: { label, value, disabled?, expanded?, selectable?, children? }.
 */
import { NgTemplateOutlet } from '@angular/common';
import { booleanAttribute } from '@angular/core';
import { ChangeDetectionStrategy, Component, input, model } from '@angular/core';
import { Tree, TreeItem as AriaTreeItem, TreeItemGroup } from '@angular/aria/tree';
import { IconComponent } from '../icon/icon.component';

export interface TreeNode<T = string> {
  label: string;
  value: T;
  disabled?: boolean;
  expanded?: boolean;
  selectable?: boolean;
  children?: TreeNode<T>[];
}

@Component({
  selector: 'app-tree',
  standalone: true,
  imports: [NgTemplateOutlet, Tree, TreeItemGroup, AriaTreeItem, IconComponent],
  template: `
    @if (nodes().length === 0) {
      <div class="rounded-lg border border-dashed border-gray-300 bg-white p-4 text-sm text-gray-500">
        {{ emptyMessage() }}
      </div>
    } @else {
      <ul
        ngTree
        #tree="ngTree"
        class="rounded-xl border border-gray-200 bg-white p-2 shadow-sm"
        [multi]="multi()"
        [selectionMode]="selectionMode()"
        [focusMode]="focusMode()"
        [wrap]="wrap()"
        [(values)]="values"
      >
        <ng-container
          [ngTemplateOutlet]="treeNodes"
          [ngTemplateOutletContext]="{ $implicit: nodes(), parent: tree }"
        ></ng-container>
      </ul>
    }

    <ng-template #treeNodes let-branch let-parent="parent">
      @for (node of branch; track nodeTrackBy(node, $index)) {
        <li
          ngTreeItem
          #treeItem="ngTreeItem"
          [parent]="parent"
          [value]="node.value"
          [label]="node.label"
          [disabled]="node.disabled ?? false"
          [selectable]="node.selectable ?? true"
          [expanded]="node.expanded ?? false"
          class="block"
        >
          <div
            class="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            [class.bg-blue-50]="treeItem.selected() === true"
            [class.text-blue-700]="treeItem.selected() === true"
            [class.opacity-60]="node.disabled ?? false"
          >
            @if (node.children?.length) {
              <button
                type="button"
                class="inline-flex h-6 w-6 items-center justify-center rounded hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                [attr.aria-label]="treeItem.expanded() ? 'Collapse node' : 'Expand node'"
                (click)="toggleExpand(treeItem, $event)"
              >
                <app-icon class="h-4 w-4 text-gray-500" [class.rotate-90]="treeItem.expanded()">
                  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path
                      fill-rule="evenodd"
                      d="M7.22 4.22a.75.75 0 011.06 0l5.25 5.25a.75.75 0 010 1.06l-5.25 5.25a.75.75 0 01-1.06-1.06L11.94 10 7.22 5.28a.75.75 0 010-1.06z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </app-icon>
              </button>
            } @else {
              <span class="inline-block h-6 w-6"></span>
            }

            <span class="truncate">{{ node.label }}</span>
          </div>

          @if (node.children?.length) {
            <ul role="group" class="ml-4">
              <ng-template ngTreeItemGroup #group="ngTreeItemGroup" [ownedBy]="treeItem">
                <ng-container
                  [ngTemplateOutlet]="treeNodes"
                  [ngTemplateOutletContext]="{ $implicit: node.children, parent: group }"
                ></ng-container>
              </ng-template>
            </ul>
          }
        </li>
      }
    </ng-template>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TreeComponent<T> {
  nodes = input.required<TreeNode<T>[]>();
  emptyMessage = input<string>('No items found.');
  multi = input(false, { transform: booleanAttribute });
  wrap = input(true, { transform: booleanAttribute });
  selectionMode = input<'follow' | 'explicit'>('explicit');
  focusMode = input<'roving' | 'activedescendant'>('roving');
  values = model<T[]>([]);

  nodeTrackBy(node: TreeNode<T>, index: number): string | number {
    const value = node.value;
    if (typeof value === 'string' || typeof value === 'number') return value;
    return index;
  }

  toggleExpand(item: AriaTreeItem<T>, event: Event): void {
    event.stopPropagation();
    item.expanded.set(!item.expanded());
  }
}

/**
 * Usage: breadcrumb navigation rendered from items.
 * Inputs: [items] where each item supports label + href or action + current.
 * Item shape: { label, href?, current?, action? }.
 */
import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
  action?: () => void;
}

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  imports: [IconComponent],
  template: `
    <nav aria-label="Breadcrumb">
      <ol class="flex flex-wrap items-center gap-1.5 text-sm text-gray-600">
        @for (item of items(); track $index) {
          <li class="inline-flex items-center gap-1.5">
            @if ($index > 0) {
              <app-icon class="h-4 w-4 text-gray-400">
                <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                    fill-rule="evenodd"
                    d="M7.22 4.22a.75.75 0 011.06 0l5.25 5.25a.75.75 0 010 1.06l-5.25 5.25a.75.75 0 01-1.06-1.06L11.94 10 7.22 5.28a.75.75 0 010-1.06z"
                    clip-rule="evenodd"
                  />
                </svg>
              </app-icon>
            }

            @if (item.href && !item.current) {
              <a
                [href]="item.href"
                class="rounded px-1 py-0.5 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                {{ item.label }}
              </a>
            } @else if (item.action && !item.current) {
              <button
                type="button"
                class="rounded px-1 py-0.5 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                (click)="item.action()"
              >
                {{ item.label }}
              </button>
            } @else {
              <span [attr.aria-current]="item.current ? 'page' : null" class="px-1 py-0.5 text-gray-900">
                {{ item.label }}
              </span>
            }
          </li>
        }
      </ol>
    </nav>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BreadcrumbComponent {
  items = input.required<BreadcrumbItem[]>();
}

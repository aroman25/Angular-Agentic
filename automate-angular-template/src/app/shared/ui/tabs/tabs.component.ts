/**
 * Usage: tab container with lazy tab panels via Angular Aria tabs.
 * Inputs/models: [tabs] (label/value/template/disabled), [selectionMode], [(selectedTab)].
 * Each tab panel uses the provided TemplateRef in tabs[].template.
 */
import { ChangeDetectionStrategy, Component, TemplateRef, computed, input, model } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { Tabs, TabList, Tab, TabPanel, TabContent } from '@angular/aria/tabs';

export interface TabsItem {
  label: string;
  value: string;
  template?: TemplateRef<unknown>;
  disabled?: boolean;
}

@Component({
  selector: 'app-tabs',
  standalone: true,
  imports: [Tabs, TabList, Tab, TabPanel, TabContent, NgTemplateOutlet],
  template: `
    <div ngTabs class="w-full">
      <ul
        ngTabList
        class="mb-4 flex border-b border-gray-200"
        [selectionMode]="selectionMode()"
        [(selectedTab)]="selectedTab"
      >
        @for (tab of tabs(); track tab.value) {
          <li
            ngTab
            [value]="tab.value"
            [disabled]="tab.disabled ?? false"
            class="cursor-pointer border-b-2 border-transparent px-4 py-2 font-medium text-gray-600 transition-colors hover:text-gray-900 aria-selected:border-blue-500 aria-selected:text-blue-600"
          >
            {{ tab.label }}
          </li>
        }
      </ul>

      @if (tabsWithTemplate().length > 0) {
        @for (tab of tabsWithTemplate(); track tab.value) {
          <div ngTabPanel [value]="tab.value" class="rounded-lg bg-white p-4 shadow-sm">
            <ng-template ngTabContent>
              <ng-container [ngTemplateOutlet]="tab.template!"></ng-container>
            </ng-template>
          </div>
        }
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TabsComponent {
  tabs = input.required<TabsItem[]>();
  selectionMode = input<'follow' | 'explicit'>('follow');
  selectedTab = model<string | undefined>(undefined);

  tabsWithTemplate = computed(() => this.tabs().filter((tab) => !!tab.template));
}

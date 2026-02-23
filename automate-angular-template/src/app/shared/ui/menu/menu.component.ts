/**
 * Usage: dropdown menu trigger + menu items using Angular Aria menu directives.
 * Inputs: [label], [items] where each item = { label, action, disabled? }.
 * Example: <app-dropdown-menu [label]="'Actions'" [items]="menuItems" />
 */
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostListener,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { Menu, MenuItem, MenuTrigger } from '@angular/aria/menu';
import { IconComponent } from '../icon/icon.component';

export interface DropdownMenuItem {
  label: string;
  action: () => void;
  disabled?: boolean;
}

@Component({
  selector: 'app-dropdown-menu',
  standalone: true,
  imports: [Menu, MenuItem, MenuTrigger, IconComponent],
  template: `
    <div #container class="relative inline-block text-left">
      <button
        ngMenuTrigger
        [menu]="myMenu"
        #trigger="ngMenuTrigger"
        #triggerButton
        (click)="schedulePositionUpdate()"
        class="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      >
        {{ label() }}
        <app-icon class="-mr-1 h-5 w-5 text-gray-400">
          <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
          </svg>
        </app-icon>
      </button>

      <div
        ngMenu
        #myMenu="ngMenu"
        #menuPanel
        [class.hidden]="!trigger.expanded()"
        [style.left.px]="menuLeftOffset()"
        [class.origin-top-left]="menuAlign() === 'left'"
        [class.origin-top-right]="menuAlign() === 'right'"
        class="absolute top-full z-10 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div class="py-1">
          @for (item of items(); track item.label) {
            <button
              ngMenuItem
              [value]="item"
              [disabled]="item.disabled ?? false"
              (click)="item.action()"
              class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 focus:bg-gray-100 focus:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ item.label }}
            </button>
          }
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DropdownMenuComponent {
  private static readonly MENU_WIDTH_PX = 224;
  private static readonly VIEWPORT_PADDING_PX = 8;

  private readonly cdr = inject(ChangeDetectorRef);

  private readonly containerRef = viewChild<ElementRef<HTMLDivElement>>('container');
  private readonly triggerButtonRef = viewChild<ElementRef<HTMLButtonElement>>('triggerButton');
  private readonly menuPanelRef = viewChild<ElementRef<HTMLDivElement>>('menuPanel');
  private readonly menuTrigger = viewChild<MenuTrigger<DropdownMenuItem>>('trigger');

  label = input.required<string>();
  items = input.required<DropdownMenuItem[]>();
  menuAlign = signal<'left' | 'right'>('right');
  menuLeftOffset = signal(0);

  @HostListener('window:resize')
  onWindowResize(): void {
    if (this.menuTrigger()?.expanded()) {
      this.schedulePositionUpdate();
    }
  }

  schedulePositionUpdate(): void {
    setTimeout(() => this.updateMenuPosition(), 0);
  }

  private updateMenuPosition(): void {
    const container = this.containerRef()?.nativeElement;
    const triggerButton = this.triggerButtonRef()?.nativeElement;
    const menuPanel = this.menuPanelRef()?.nativeElement;
    if (!container || !triggerButton || !menuPanel) {
      return;
    }

    const viewportWidth = window.innerWidth;
    const viewportPadding = DropdownMenuComponent.VIEWPORT_PADDING_PX;
    const fallbackMenuWidth = DropdownMenuComponent.MENU_WIDTH_PX;
    const menuWidth = menuPanel.offsetWidth || fallbackMenuWidth;

    const triggerRect = triggerButton.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    const rightAlignedLeft = triggerRect.right - menuWidth;
    const leftAlignedLeft = triggerRect.left;

    const rightFits = rightAlignedLeft >= viewportPadding;
    const leftFits = leftAlignedLeft + menuWidth <= viewportWidth - viewportPadding;

    let align: 'left' | 'right';
    if (rightFits) {
      align = 'right';
    } else if (leftFits) {
      align = 'left';
    } else {
      // Fallback to the side with more available space, then clamp.
      const spaceLeft = triggerRect.right - viewportPadding;
      const spaceRight = viewportWidth - viewportPadding - triggerRect.left;
      align = spaceRight >= spaceLeft ? 'left' : 'right';
    }

    const desiredViewportLeft = align === 'left' ? leftAlignedLeft : rightAlignedLeft;
    const minLeft = viewportPadding;
    const maxLeft = Math.max(viewportPadding, viewportWidth - viewportPadding - menuWidth);
    const clampedViewportLeft = Math.min(Math.max(desiredViewportLeft, minLeft), maxLeft);
    const leftOffset = clampedViewportLeft - containerRect.left;

    this.menuAlign.set(align);
    this.menuLeftOffset.set(leftOffset);
    this.cdr.markForCheck();
  }
}

/**
 * Usage: single-select dropdown built with a CDK overlay + listbox pattern.
 * Inputs/models: [options], [placeholder], [(value)].
 * Option shape: { label, value }.
 */
import { ChangeDetectionStrategy, Component, computed, input, model, signal } from '@angular/core';
import { CdkConnectedOverlay, CdkOverlayOrigin } from '@angular/cdk/overlay';
import { IconComponent } from '../icon/icon.component';

export interface SelectOption<T = unknown> {
  label: string;
  value: T;
}

@Component({
  selector: 'app-select',
  standalone: true,
  imports: [CdkConnectedOverlay, CdkOverlayOrigin, IconComponent],
  template: `
    <div class="relative w-full">
      <div
        cdkOverlayOrigin
        #origin="cdkOverlayOrigin"
        class="relative w-full cursor-pointer"
      >
        <input
          type="text"
          readonly
          [value]="displayValue()"
          [placeholder]="placeholder()"
          role="combobox"
          aria-autocomplete="none"
          aria-haspopup="listbox"
          [attr.aria-expanded]="overlayOpen()"
          [attr.aria-controls]="listboxId"
          [attr.aria-activedescendant]="activeDescendantId()"
          (click)="toggleOverlay()"
          (keydown)="onTriggerKeydown($event)"
          class="w-full px-4 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
        <div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
          <app-icon class="h-5 w-5 text-gray-400">
            <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M10 3a.75.75 0 01.55.24l3.25 3.5a.75.75 0 11-1.1 1.02L10 4.852 7.3 7.76a.75.75 0 01-1.1-1.02l3.25-3.5A.75.75 0 0110 3zm-3.76 9.2a.75.75 0 011.06.04l2.7 2.908 2.7-2.908a.75.75 0 111.1 1.02l-3.25 3.5a.75.75 0 01-1.1 0l-3.25-3.5a.75.75 0 01.04-1.06z" clip-rule="evenodd" />
            </svg>
          </app-icon>
        </div>
      </div>

      <ng-template
        #overlay="cdkConnectedOverlay"
        cdkConnectedOverlay
        [cdkConnectedOverlayOrigin]="origin"
        [cdkConnectedOverlayOpen]="overlayOpen()"
        [cdkConnectedOverlayWidth]="origin.elementRef.nativeElement.offsetWidth"
        [cdkConnectedOverlayHasBackdrop]="true"
        cdkConnectedOverlayBackdropClass="cdk-overlay-transparent-backdrop"
        (backdropClick)="closeOverlay()"
        (detach)="overlayOpen.set(false)"
      >
        <div
          [id]="listboxId"
          role="listbox"
          tabindex="-1"
          class="w-full py-1 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
          (keydown)="onListboxKeydown($event)"
        >
          @for (option of options(); track option.value; let idx = $index) {
            <div
              [id]="optionId(idx)"
              role="option"
              [attr.aria-selected]="isSelected(option.value)"
              (mouseenter)="activeIndex.set(idx)"
              (click)="selectOption(option)"
              class="relative py-2 pl-3 pr-9 cursor-default select-none hover:bg-blue-50"
              [class.bg-blue-100]="activeIndex() === idx"
              [class.text-blue-900]="activeIndex() === idx"
              [class.text-gray-900]="activeIndex() !== idx"
            >
              <span class="block truncate" [class.font-semibold]="isSelected(option.value)">
                {{ option.label }}
              </span>
              @if (isSelected(option.value)) {
                <span class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600">
                  <app-icon class="h-5 w-5">
                    <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                    </svg>
                  </app-icon>
                </span>
              }
            </div>
          }
        </div>
      </ng-template>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectComponent<T> {
  readonly options = input.required<SelectOption<T>[]>();
  readonly placeholder = input<string>('Select an option');
  readonly closeOnSelect = input(true);
  readonly value = model<T | null>(null);

  readonly overlayOpen = signal(false);
  readonly activeIndex = signal(-1);
  readonly listboxId = `app-select-listbox-${Math.random().toString(36).slice(2, 9)}`;

  readonly displayValue = computed(() => {
    const selected = this.value();
    if (selected === null) {
      return '';
    }

    const option = this.options().find(item => Object.is(item.value, selected));
    return option?.label ?? '';
  });

  readonly activeDescendantId = computed(() => {
    const idx = this.activeIndex();
    return idx >= 0 ? this.optionId(idx) : null;
  });

  toggleOverlay(): void {
    if (this.overlayOpen()) {
      this.closeOverlay();
      return;
    }

    this.openOverlay();
  }

  openOverlay(): void {
    const opts = this.options();
    if (opts.length === 0) {
      return;
    }

    this.overlayOpen.set(true);
    this.activeIndex.set(this.selectedIndex());
    if (this.activeIndex() < 0) {
      this.activeIndex.set(0);
    }
  }

  closeOverlay(): void {
    this.overlayOpen.set(false);
  }

  onTriggerKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.overlayOpen()) {
          this.openOverlay();
          return;
        }
        this.moveActive(1);
        return;
      case 'ArrowUp':
        event.preventDefault();
        if (!this.overlayOpen()) {
          this.openOverlay();
          return;
        }
        this.moveActive(-1);
        return;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (!this.overlayOpen()) {
          this.openOverlay();
          return;
        }
        this.selectActiveOption();
        return;
      case 'Escape':
        if (this.overlayOpen()) {
          event.preventDefault();
          this.closeOverlay();
        }
        return;
      default:
        return;
    }
  }

  onListboxKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.closeOverlay();
    }
  }

  selectOption(option: SelectOption<T>): void {
    this.value.set(option.value);
    if (this.closeOnSelect()) {
      this.closeOverlay();
    }
  }

  selectActiveOption(): void {
    const idx = this.activeIndex();
    const opts = this.options();
    if (idx < 0 || idx >= opts.length) {
      return;
    }

    this.selectOption(opts[idx]);
  }

  moveActive(delta: number): void {
    const opts = this.options();
    if (opts.length === 0) {
      this.activeIndex.set(-1);
      return;
    }

    const current = this.activeIndex();
    const start = current >= 0 ? current : 0;
    const next = (start + delta + opts.length) % opts.length;
    this.activeIndex.set(next);
  }

  selectedIndex(): number {
    const selected = this.value();
    if (selected === null) {
      return -1;
    }

    return this.options().findIndex(option => Object.is(option.value, selected));
  }

  optionId(index: number): string {
    return `${this.listboxId}-option-${index}`;
  }

  isSelected(val: T): boolean {
    return Object.is(this.value(), val);
  }
}

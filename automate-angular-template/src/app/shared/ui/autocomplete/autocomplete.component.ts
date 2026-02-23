/**
 * Usage: single-select autocomplete built with a CDK overlay + listbox pattern.
 * Inputs/models: [options], [placeholder], [(value)], [(inputValue)].
 * Option shape: { label, value }.
 */
import { ChangeDetectionStrategy, Component, computed, input, model, signal } from '@angular/core';
import { CdkConnectedOverlay, CdkOverlayOrigin } from '@angular/cdk/overlay';
import { IconComponent } from '../icon/icon.component';

export interface AutocompleteOption<T = unknown> {
  label: string;
  value: T;
}

@Component({
  selector: 'app-autocomplete',
  standalone: true,
  imports: [CdkConnectedOverlay, CdkOverlayOrigin, IconComponent],
  template: `
    <div class="relative w-full">
      <div
        cdkOverlayOrigin
        #origin="cdkOverlayOrigin"
        class="relative w-full"
      >
        <input
          type="text"
          [value]="inputValue()"
          [placeholder]="placeholder()"
          role="combobox"
          aria-autocomplete="list"
          aria-haspopup="listbox"
          [attr.aria-expanded]="overlayVisible()"
          [attr.aria-controls]="listboxId"
          [attr.aria-activedescendant]="activeDescendantId()"
          (click)="openOverlay()"
          (focus)="openOverlay()"
          (input)="onInput($event)"
          (keydown)="onInputKeydown($event)"
          class="w-full px-4 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      <ng-template
        #overlay="cdkConnectedOverlay"
        cdkConnectedOverlay
        [cdkConnectedOverlayOrigin]="origin"
        [cdkConnectedOverlayOpen]="overlayVisible()"
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
        >
          @for (option of filteredOptions(); track option.value; let idx = $index) {
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
export class AutocompleteComponent<T> {
  readonly options = input.required<AutocompleteOption<T>[]>();
  readonly placeholder = input<string>('Search...');
  readonly value = model<T | null>(null);
  readonly inputValue = model<string>('');

  readonly overlayOpen = signal(false);
  readonly activeIndex = signal(-1);
  readonly listboxId = `app-autocomplete-listbox-${Math.random().toString(36).slice(2, 9)}`;

  readonly filteredOptions = computed(() => {
    const filterValue = this.inputValue().toLowerCase();
    return this.options().filter(option => option.label.toLowerCase().includes(filterValue));
  });

  readonly overlayVisible = computed(() => this.overlayOpen() && this.filteredOptions().length > 0);

  readonly activeDescendantId = computed(() => {
    const idx = this.activeIndex();
    return idx >= 0 ? this.optionId(idx) : null;
  });

  openOverlay(): void {
    this.overlayOpen.set(true);
    this.syncActiveIndex();
  }

  closeOverlay(): void {
    this.overlayOpen.set(false);
  }

  onInput(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) {
      return;
    }

    this.inputValue.set(target.value);
    this.overlayOpen.set(true);
    this.syncActiveIndex();
  }

  onInputKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.overlayVisible()) {
          this.openOverlay();
          return;
        }
        this.moveActive(1);
        return;
      case 'ArrowUp':
        event.preventDefault();
        if (!this.overlayVisible()) {
          this.openOverlay();
          return;
        }
        this.moveActive(-1);
        return;
      case 'Enter':
        if (!this.overlayVisible()) {
          return;
        }
        event.preventDefault();
        this.selectActiveOption();
        return;
      case 'Escape':
        if (this.overlayVisible()) {
          event.preventDefault();
          this.closeOverlay();
        }
        return;
      case 'Tab':
        this.closeOverlay();
        return;
      default:
        return;
    }
  }

  selectOption(option: AutocompleteOption<T>): void {
    this.value.set(option.value);
    this.inputValue.set(option.label);
    this.closeOverlay();
  }

  selectActiveOption(): void {
    const idx = this.activeIndex();
    const opts = this.filteredOptions();
    if (idx < 0 || idx >= opts.length) {
      return;
    }

    this.selectOption(opts[idx]);
  }

  moveActive(delta: number): void {
    const opts = this.filteredOptions();
    if (opts.length === 0) {
      this.activeIndex.set(-1);
      return;
    }

    const current = this.activeIndex();
    const start = current >= 0 ? current : 0;
    const next = (start + delta + opts.length) % opts.length;
    this.activeIndex.set(next);
  }

  syncActiveIndex(): void {
    const opts = this.filteredOptions();
    if (opts.length === 0) {
      this.activeIndex.set(-1);
      return;
    }

    const selected = this.value();
    if (selected !== null) {
      const selectedIdx = opts.findIndex(option => Object.is(option.value, selected));
      if (selectedIdx >= 0) {
        this.activeIndex.set(selectedIdx);
        return;
      }
    }

    this.activeIndex.set(0);
  }

  optionId(index: number): string {
    return `${this.listboxId}-option-${index}`;
  }

  isSelected(val: T): boolean {
    return Object.is(this.value(), val);
  }
}

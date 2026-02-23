/**
 * Usage: wrap one or more <app-accordion-item> children.
 * Inputs: [multiExpandable] to allow multiple open panels.
 * Example: <app-accordion [multiExpandable]="true">...</app-accordion>
 */
import { ChangeDetectionStrategy, Component, InjectionToken, WritableSignal, input } from '@angular/core';

export interface AccordionItemController {
  id: string;
  expanded: WritableSignal<boolean>;
}

export interface AccordionContext {
  readonly multiExpandable: () => boolean;
  registerItem(controller: AccordionItemController): void;
  unregisterItem(id: string, expanded: WritableSignal<boolean>): void;
  toggleItem(id: string): void;
}

export const APP_ACCORDION_CONTEXT = new InjectionToken<AccordionContext>('APP_ACCORDION_CONTEXT');

@Component({
  selector: 'app-accordion',
  standalone: true,
  providers: [
    {
      provide: APP_ACCORDION_CONTEXT,
      useExisting: AccordionComponent,
    },
  ],
  host: {
    class: 'w-full flex flex-col gap-2',
  },
  template: `<ng-content></ng-content>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccordionComponent implements AccordionContext {
  readonly multiExpandable = input(true);

  private readonly items = new Map<string, WritableSignal<boolean>>();

  registerItem(controller: AccordionItemController): void {
    this.items.set(controller.id, controller.expanded);
  }

  unregisterItem(id: string, expanded: WritableSignal<boolean>): void {
    const registered = this.items.get(id);
    if (registered === expanded) {
      this.items.delete(id);
    }
  }

  toggleItem(id: string): void {
    const target = this.items.get(id);
    if (!target) {
      return;
    }

    const nextExpanded = !target();
    if (!this.multiExpandable() && nextExpanded) {
      for (const [itemId, itemExpanded] of this.items) {
        if (itemId !== id && itemExpanded()) {
          itemExpanded.set(false);
        }
      }
    }

    target.set(nextExpanded);
  }
}

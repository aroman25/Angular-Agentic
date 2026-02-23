import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { AccordionComponent } from './accordion.component';
import { AccordionItemComponent } from './accordion-item.component';

@Component({
  imports: [AccordionComponent, AccordionItemComponent],
  template: `
    <app-accordion [multiExpandable]="true">
      <app-accordion-item title="FAQ">Accordion body</app-accordion-item>
    </app-accordion>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
class AccordionHostTestComponent {}

describe('AccordionComponent integration', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AccordionHostTestComponent],
    }).compileComponents();
  });

  it('renders projected accordion items without missing accordion group provider', () => {
    const fixture = TestBed.createComponent(AccordionHostTestComponent);

    expect(() => fixture.detectChanges()).not.toThrow();
    expect(fixture.nativeElement.querySelector('button')).toBeTruthy();
  });
});

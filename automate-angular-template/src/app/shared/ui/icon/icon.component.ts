/**
 * Usage: SVG wrapper that sizes projected <svg> to the host element.
 * Apply Tailwind size/color classes on <app-icon>, not the inner <svg>.
 * Example: <app-icon class="h-5 w-5 text-gray-500"><svg ... /></app-icon>
 */
import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `
    <span class="app-icon__content" aria-hidden="true">
      <ng-content></ng-content>
    </span>
  `,
  styles: [
    `
      app-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        line-height: 0;
        flex-shrink: 0;
      }

      app-icon .app-icon__content {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
      }

      app-icon .app-icon__content > svg {
        display: block;
        width: 100%;
        height: 100%;
        flex-shrink: 0;
      }
    `,
  ],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IconComponent {}

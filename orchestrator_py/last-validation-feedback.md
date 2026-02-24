Deterministic validator checks FAILED.

Violations:
- src/app/pages/home/home-page.component.html:22 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:23 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:24 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:25 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:26 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:49 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:51 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:55 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:59 - Use @if instead of *ngIf
- src/app/pages/home/home-page.component.html:60 - Use @for instead of *ngFor
- src/app/features/*:1 - Form/validation story requires ReactiveFormsModule in at least one feature component imports array
- src/app/features/*:1 - Form/validation story requires typed Reactive Forms model usage (FormGroup/FormControl/FormBuilder)
- src/app/features/*:1 - Form/validation story requires validation rules (e.g., Validators.* or custom validator functions)
- src/app/features/*:1 - Form/validation story requires at least one <form> element in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-button' to be used at least once in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-card' to be used at least once in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-text-input' to be used at least once in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-checkbox' to be used at least once in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-empty-state' to be used at least once in feature templates
- src/app/features/*:1 - User story requires shared UI selector 'app-badge' to be used at least once in feature templates
- npm.cmd run build failed.
STDOUT:

> automate-angular-template@0.0.0 build
> ng build

> Building...
âˆš Building...
Application bundle generation failed. [3.158 seconds] - 2026-02-24T05:24:53.335Z


STDERR:
X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AccordionItemComponent'. Did you mean 'AccordionComponent'? [plugin angular-compiler]

    src/app/examples/ui-components-gallery/ui-components-gallery.page.ts:9:2:
      9 â”‚   AccordionItemComponent,
        â•µ   ~~~~~~~~~~~~~~~~~~~~~~

  'AccordionComponent' is declared here.

    src/app/shared/ui/accordion/accordion.component.ts:37:13:
      37 â”‚ export class AccordionComponent implements AccordionContext {
         â•µ              ~~~~~~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/examples/ui-components-gallery/ui-components-gallery.page.ts:77:4:
      77 â”‚     AccordionItemComponent,
         â•µ     ~~~~~~~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/examples/ui-components-gallery/ui-components-gallery.page.ts:77:4:
      77 â”‚     AccordionItemComponent,
         â•µ     ~~~~~~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppButtonComponent'. Did you mean 'ButtonComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:9:
      5 â”‚ import { AppButtonComponent, AppCardComponent, AppTextInputComponen...
        â•µ          ~~~~~~~~~~~~~~~~~~

  'ButtonComponent' is declared here.

    src/app/shared/ui/button/button.component.ts:31:13:
      31 â”‚ export class ButtonComponent {
         â•µ              ~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppCardComponent'. Did you mean 'CardComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:29:
      5 â”‚ ...t { AppButtonComponent, AppCardComponent, AppTextInputComponent,...
        â•µ                            ~~~~~~~~~~~~~~~~

  'CardComponent' is declared here.

    src/app/shared/ui/card/card.component.ts:31:13:
      31 â”‚ export class CardComponent {
         â•µ              ~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppTextInputComponent'. Did you mean 'TextInputComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:47:
      5 â”‚ ...nt, AppCardComponent, AppTextInputComponent, AppCheckboxComponen...
        â•µ                          ~~~~~~~~~~~~~~~~~~~~~

  'TextInputComponent' is declared here.

    src/app/shared/ui/text-input/text-input.component.ts:55:13:
      55 â”‚ export class TextInputComponent {
         â•µ              ~~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppCheckboxComponent'. Did you mean 'CheckboxComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:70:
      5 â”‚ ...ppTextInputComponent, AppCheckboxComponent, AppEmptyStateCompone...
        â•µ                          ~~~~~~~~~~~~~~~~~~~~

  'CheckboxComponent' is declared here.

    src/app/shared/ui/checkbox/checkbox.component.ts:61:13:
      61 â”‚ export class CheckboxComponent {
         â•µ              ~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppEmptyStateComponent'. Did you mean 'EmptyStateComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:92:
      5 â”‚ ...ppCheckboxComponent, AppEmptyStateComponent, AppBadgeComponent, ...
        â•µ                         ~~~~~~~~~~~~~~~~~~~~~~

  'EmptyStateComponent' is declared here.

    src/app/shared/ui/empty-state/empty-state.component.ts:31:13:
      31 â”‚ export class EmptyStateComponent {
         â•µ              ~~~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppBadgeComponent'. Did you mean 'BadgeComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:116:
      5 â”‚ ...AppEmptyStateComponent, AppBadgeComponent, AppIconComponent } fr...
        â•µ                            ~~~~~~~~~~~~~~~~~

  'BadgeComponent' is declared here.

    src/app/shared/ui/badge/badge.component.ts:18:13:
      18 â”‚ export class BadgeComponent {
         â•µ              ~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppIconComponent'. Did you mean 'IconComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:135:
      5 â”‚ ...ent, AppBadgeComponent, AppIconComponent } from 'src/app/shared/...
        â•µ                            ~~~~~~~~~~~~~~~~

  'IconComponent' is declared here.

    src/app/shared/ui/icon/icon.component.ts:45:13:
      45 â”‚ export class IconComponent {}
         â•µ              ~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:33:
      17 â”‚ ... [ReactiveFormsModule, AppButtonComponent, AppCardComponent, Ap...
         â•µ                           ~~~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/pages/home/home-page.component.ts:17:33:
      17 â”‚ ... [ReactiveFormsModule, AppButtonComponent, AppCardComponent, Ap...
         â•µ                           ~~~~~~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:53:
      17 â”‚ ...le, AppButtonComponent, AppCardComponent, AppTextInputComponent...
         â•µ                            ~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/pages/home/home-page.component.ts:17:53:
      17 â”‚ ...le, AppButtonComponent, AppCardComponent, Ap
...[truncated]
- npm.cmd run test -- --watch=false failed.
STDOUT:

> automate-angular-template@0.0.0 test
> ng test --watch=false

> Building...
âˆš Building...
Application bundle generation failed. [3.387 seconds] - 2026-02-24T05:24:58.554Z


STDERR:
X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppButtonComponent'. Did you mean 'ButtonComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:9:
      5 â”‚ import { AppButtonComponent, AppCardComponent, AppTextInputComponen...
        â•µ          ~~~~~~~~~~~~~~~~~~

  'ButtonComponent' is declared here.

    src/app/shared/ui/button/button.component.ts:31:13:
      31 â”‚ export class ButtonComponent {
         â•µ              ~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppCardComponent'. Did you mean 'CardComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:29:
      5 â”‚ ...t { AppButtonComponent, AppCardComponent, AppTextInputComponent,...
        â•µ                            ~~~~~~~~~~~~~~~~

  'CardComponent' is declared here.

    src/app/shared/ui/card/card.component.ts:31:13:
      31 â”‚ export class CardComponent {
         â•µ              ~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppTextInputComponent'. Did you mean 'TextInputComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:47:
      5 â”‚ ...nt, AppCardComponent, AppTextInputComponent, AppCheckboxComponen...
        â•µ                          ~~~~~~~~~~~~~~~~~~~~~

  'TextInputComponent' is declared here.

    src/app/shared/ui/text-input/text-input.component.ts:55:13:
      55 â”‚ export class TextInputComponent {
         â•µ              ~~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppCheckboxComponent'. Did you mean 'CheckboxComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:70:
      5 â”‚ ...ppTextInputComponent, AppCheckboxComponent, AppEmptyStateCompone...
        â•µ                          ~~~~~~~~~~~~~~~~~~~~

  'CheckboxComponent' is declared here.

    src/app/shared/ui/checkbox/checkbox.component.ts:61:13:
      61 â”‚ export class CheckboxComponent {
         â•µ              ~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppEmptyStateComponent'. Did you mean 'EmptyStateComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:92:
      5 â”‚ ...ppCheckboxComponent, AppEmptyStateComponent, AppBadgeComponent, ...
        â•µ                         ~~~~~~~~~~~~~~~~~~~~~~

  'EmptyStateComponent' is declared here.

    src/app/shared/ui/empty-state/empty-state.component.ts:31:13:
      31 â”‚ export class EmptyStateComponent {
         â•µ              ~~~~~~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppBadgeComponent'. Did you mean 'BadgeComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:116:
      5 â”‚ ...AppEmptyStateComponent, AppBadgeComponent, AppIconComponent } fr...
        â•µ                            ~~~~~~~~~~~~~~~~~

  'BadgeComponent' is declared here.

    src/app/shared/ui/badge/badge.component.ts:18:13:
      18 â”‚ export class BadgeComponent {
         â•µ              ~~~~~~~~~~~~~~


X [ERROR] TS2724: '"src/app/shared/ui"' has no exported member named 'AppIconComponent'. Did you mean 'IconComponent'? [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:5:135:
      5 â”‚ ...ent, AppBadgeComponent, AppIconComponent } from 'src/app/shared/...
        â•µ                            ~~~~~~~~~~~~~~~~

  'IconComponent' is declared here.

    src/app/shared/ui/icon/icon.component.ts:45:13:
      45 â”‚ export class IconComponent {}
         â•µ              ~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:33:
      17 â”‚ ... [ReactiveFormsModule, AppButtonComponent, AppCardComponent, Ap...
         â•µ                           ~~~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/pages/home/home-page.component.ts:17:33:
      17 â”‚ ... [ReactiveFormsModule, AppButtonComponent, AppCardComponent, Ap...
         â•µ                           ~~~~~~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:53:
      17 â”‚ ...le, AppButtonComponent, AppCardComponent, AppTextInputComponent...
         â•µ                            ~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/pages/home/home-page.component.ts:17:53:
      17 â”‚ ...le, AppButtonComponent, AppCardComponent, AppTextInputComponent...
         â•µ                            ~~~~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:71:
      17 â”‚ ...t, AppCardComponent, AppTextInputComponent, AppCheckboxComponen...
         â•µ                         ~~~~~~~~~~~~~~~~~~~~~

  Unknown reference.

    src/app/pages/home/home-page.component.ts:17:71:
      17 â”‚ ...t, AppCardComponent, AppTextInputComponent, AppCheckboxComponen...
         â•µ                         ~~~~~~~~~~~~~~~~~~~~~


X [ERROR] NG1010: 'imports' must be an array of components, directives, pipes, or NgModules.
  Value could not be determined statically. [plugin angular-compiler]

    src/app/pages/home/home-page.component.ts:17:94:
      17 â”‚ ...ppTextInputComponent, AppCheckboxComponent, AppEmptyStateCompon...
         â•µ                          ~~~~~~~~~~~~~~~~~~~~

  Unknown ref
...[truncated]
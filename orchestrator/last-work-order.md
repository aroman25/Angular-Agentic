# Work Order: Used Car Inquiry Form Workspace

## Feature Name & Goal
**Feature Name:** Used Car Inquiry Form Workspace  
**Goal:** To create a polished, responsive used-car inquiry experience that allows users to submit their contact details, vehicle preferences, trade-in and financing information, and schedule a follow-up with a dealership. The feature should include a clear summary of the submission and utilize shared UI components for a consistent and accessible user experience.

## User Story Data Points
- **Routes:**
  - Feature route: `/used-car-inquiry`
  - Default route: `/` redirects to `/used-car-inquiry`
- **Form Fields:**
  - Contact Info: First Name, Last Name, Email, Phone, Preferred Contact Method
  - Vehicle Interest: Make/Model Search, Trim, Year Range, Max Mileage, Budget, Preferred Body Type
  - Financing: Financing Needed (Yes/No), Down Payment, Monthly Budget, Credit Range
  - Trade-in: Trade-in Toggle, Current Vehicle Year/Make/Model/Mileage/Condition
  - Appointment & Notes: Preferred Date/Time Window, Dealership Location, Notes/Questions
  - Consent: Contact Consent and Privacy Acknowledgement
- **Validation Rules:**
  - Required fields, email format, min/max values, minLength, pattern, and custom validators
  - Cross-field validation: If preferred contact is email, email is required and valid; if phone, phone is required/pattern-valid
- **Required Selectors:**
  - `app-accordion`, `app-accordion-item`, `app-alert`, `app-autocomplete`, `app-avatar`, `app-badge`, `app-breadcrumb`, `app-button`, `app-card`, `app-checkbox`, `app-data-grid`, `app-dialog`, `app-divider`, `app-drawer`, `app-empty-state`, `app-icon`, `app-dropdown-menu`, `app-pagination`, `app-progress`, `app-radio-group`, `app-select`, `app-skeleton`, `app-spinner`, `app-switch`, `app-table`, `app-tabs`, `app-text-input`, `app-textarea`, `app-toast`, `app-toolbar`, `app-tree`

## Requirement Traceability
- **Fresh App From Template:** Generate a new app from the provided Angular template. Ensure it compiles successfully.
- **Scope:** Use mock/local data only. Simulate submit with a toast/dialog confirmation and local state update.
- **Primary Experience:** Create a responsive `/used-car-inquiry` page with a modern dealership UI. Ensure it feels production-grade with clear hierarchy, spacing, validation messaging, focus states, and polished Tailwind styling.
- **Reactive Form:** Implement using typed Reactive Forms. Use Angular Signals for feature UI state. Bridge non-CVA shared UI controls with `[value]` / `(valueChange)` and `FormControl` updates.
- **Validation:** Implement explicit validators and render validation messages in the UI. Prevent invalid submit and show a visible submit result state.
- **Used-Car Inquiry UX:** Include inventory preview, summary/review area, and keyboard-accessible modal/drawer interactions.
- **Shared UI Reuse:** Utilize all listed shared UI components meaningfully in the feature experience.
- **Routing:** Set `/used-car-inquiry` as the feature route and redirect `/` to it.

## File Structure
```
src/app/
├── core/
│   ├── auth/
│   ├── providers/
│   └── tokens/
├── features/
│   └── used-car-inquiry/
│       ├── components/
│       ├── services/
│       ├── models/
│       ├── used-car-inquiry.component.ts
│       ├── used-car-inquiry.component.html
│       ├── used-car-inquiry.component.css
│       └── used-car-inquiry.routes.ts
└── shared/
    ├── ui/
    └── state/
```

## State Management
- Use Angular Signals for managing UI state such as selected inventory item, loading state, submit status, draft summary, and drawer/dialog state.
- Implement `signal`, `computed`, and `effect` for state management.

## Form Model & Validation
- **Form Group Structure:**
  - `contactInfo`: FormGroup with controls for first name, last name, email, phone, preferred contact method
  - `vehicleInterest`: FormGroup with controls for make/model, trim, year range, max mileage, budget, preferred body type
  - `financing`: FormGroup with controls for financing needed, down payment, monthly budget, credit range
  - `tradeIn`: FormGroup with controls for trade-in toggle, current vehicle details
  - `appointmentNotes`: FormGroup with controls for preferred date/time, dealership location, notes/questions
  - `consent`: FormGroup with controls for contact consent and privacy acknowledgement
- **Validation Matrix:**
  - Required fields, email format, min/max values, minLength, pattern, and custom validators
  - Cross-field validation for contact method and corresponding required fields
- **Validation Message Behavior:**
  - Display inline validation messages based on `touched`, `dirty`, and/or submitted state
  - Form-level validation summary/alert after submit attempt
- **Submit/Disable Rules:**
  - Disable submit button while form is invalid or pending
  - Show visible submit result state (success/error)

## UI/UX Requirements
- **Responsive Design:** Ensure the page is responsive for both mobile and desktop views.
- **Shared UI Components:** Use all listed shared UI components meaningfully in the feature experience.
- **Tailwind CSS:** Use Tailwind CSS utilities for styling. Avoid custom CSS unless necessary.
- **Accessibility:** Maintain clear focus states, labels, aria attributes, keyboard navigation, and readable contrast.

## Acceptance Criteria
- The app compiles successfully from the provided Angular template.
- The `/used-car-inquiry` page is responsive and production-grade.
- The inquiry form uses typed Reactive Forms and Angular Signals for state management.
- All form fields have explicit validators and render validation messages in the UI.
- The form prevents invalid submit and shows a visible submit result state.
- The feature includes inventory preview, summary/review area, and keyboard-accessible modal/drawer interactions.
- All listed shared UI components are used meaningfully in the feature experience.
- The default route (`/`) redirects to `/used-car-inquiry`.

## Assumptions
- The feature will use mock/local data only, with no real API, auth, payment, or persistence backend.
- The submit action will be simulated with a toast/dialog confirmation and local state update.
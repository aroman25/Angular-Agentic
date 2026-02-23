# Feature: Used Car Inquiry Form Workspace (Full Shared UI Coverage)

As a shopper, I want a polished used-car inquiry experience so that I can submit my contact details, vehicle preferences, trade-in and financing information, and schedule a follow-up with a dealership while reviewing a clear summary of my submission.

## Requirements
1. **Fresh App From Template**
   - Start from the provided Angular template and generate a new app from scratch (no reuse of previous generated app output).
   - The generated app must compile successfully.

2. **Scope (Mock App, No Backend)**
   - Build a used-car inquiry workflow using mock/local data only.
   - No real API, auth, payment, or persistence backend is required.
   - Submit can be simulated (e.g., toast/dialog confirmation + local state update).

3. **Primary Experience**
   - Create a responsive `/used-car-inquiry` page (mobile + desktop) with a modern dealership UI.
   - The page should feel production-grade (clear hierarchy, spacing, validation messaging, focus states, polished Tailwind styling).
   - The page should contain a real inquiry form plus supporting panels/components (inventory preview, summary, help, FAQs, etc.).

4. **Reactive Form (Required)**
   - Use **typed Reactive Forms** (`FormGroup`, `FormControl`, `ReactiveFormsModule`) for the inquiry form.
   - No template-driven forms and no `[(ngModel)]`.
   - Use Angular Signals (`signal`, `computed`) for feature UI state (selected inventory item, loading state, submit status, draft summary, drawer/dialog state, etc.).
   - If shared UI controls do not implement CVA, bridge them with `[value]` / `(valueChange)` and `FormControl` updates.

5. **Form Fields (Minimum)**
   - Contact info: first name, last name, email, phone, preferred contact method
   - Vehicle interest: make/model search, trim, year range, max mileage, budget, preferred body type
   - Financing: financing needed (yes/no), down payment, monthly budget, credit range
   - Trade-in: trade-in toggle, current vehicle year/make/model/mileage/condition
   - Appointment & notes: preferred date/time window, dealership location, notes/questions
   - Consent: contact consent and privacy acknowledgement

6. **Validation (Required)**
   - Implement explicit validators (required, email format, min/max, minLength, pattern, and any custom validator(s) as appropriate).
   - Render validation messages in the UI (based on `touched`, `dirty`, and/or submitted state).
   - Include inline validation messages for multiple fields (at least 5 fields), and a form-level validation summary/alert after submit attempt.
   - Prevent invalid submit (disable submit button while invalid/pending).
   - Show a visible submit result state (success and/or simulated error path).
   - Include at least one cross-field validation rule (example: if preferred contact is email, email is required and valid; if phone, phone is required/pattern-valid).

7. **Used-Car Inquiry UX**
   - Include an inventory preview (mock vehicles) users can browse/select while filling out the form.
   - Include a summary/review area showing current form values before submission.
   - Include clear primary/secondary actions (submit, reset, save draft, view summary, etc.).
   - Include keyboard-accessible modal/drawer interaction(s) for reviewing details or confirmation.

8. **Shared UI Reuse (Required: Full Coverage)**
   - Reuse pre-built components from `src/app/shared/ui/` instead of building custom equivalents.
   - Use the `shared/ui` components according to their top usage comments.
   - **All shared UI elements in the template must be used at least once somewhere in the feature experience** (main form or supporting panels/workspace UI):
     - `app-accordion`
     - `app-accordion-item`
     - `app-alert`
     - `app-autocomplete`
     - `app-avatar`
     - `app-badge`
     - `app-breadcrumb`
     - `app-button`
     - `app-card`
     - `app-checkbox`
     - `app-data-grid`
     - `app-dialog`
     - `app-divider`
     - `app-drawer`
     - `app-empty-state`
     - `app-icon` (all SVGs must be wrapped)
     - `app-dropdown-menu`
     - `app-pagination`
     - `app-progress`
     - `app-radio-group`
     - `app-select`
     - `app-skeleton`
     - `app-spinner`
     - `app-switch`
     - `app-table`
     - `app-tabs`
     - `app-text-input`
     - `app-textarea`
     - `app-toast`
     - `app-toolbar`
     - `app-tree`

9. **Suggested Mapping for Shared UI Coverage (Use Similar Intent)**
   - `app-breadcrumb`: navigation context
   - `app-toolbar` + `app-dropdown-menu`: page actions / quick actions
   - `app-tabs`: switch between inquiry sections (Contact, Vehicle, Finance, Trade-In, Review)
   - `app-card`, `app-divider`, `app-badge`, `app-avatar`: layout + advisor/lead status UI
   - `app-radio-group`: MUST be used for preferred contact method selection in the actual inquiry form (not only a demo section)
   - `app-text-input`, `app-textarea`, `app-select`, `app-autocomplete`, `app-checkbox`, `app-switch`: other inquiry form controls
   - `app-alert`: form-level validation summary / dealership notice
   - `app-progress`: completion progress
   - `app-skeleton`, `app-spinner`: loading and submit states
   - `app-table` + `app-data-grid` + `app-pagination`: inventory/quote/offer previews (mock data)
   - `app-tree`: selectable vehicle features/packages/preferences taxonomy
   - `app-accordion` + `app-accordion-item`: FAQs or finance explanations
   - `app-dialog` + `app-drawer`: confirmation, review panel, or inventory details
   - `app-empty-state`: no inventory matches / no saved draft state
   - `app-toast`: submit/draft feedback

10. **Tailwind + Accessibility**
    - Tailwind CSS utilities should be used for styling (avoid custom CSS unless necessary).
    - Maintain clear focus states, labels, aria attributes, keyboard navigation, and readable contrast.
    - Avoid generic boilerplate layouts; make the form visually intentional and polished.

11. **Routing**
    - Feature route should be `/used-car-inquiry`.
    - Default route (`/`) must redirect to `/used-car-inquiry`.

12. **Optional Nice-to-Have**
    - Persist draft form values in `localStorage`.
    - Show unsaved-changes indicator.
    - Add a printable summary section.

# Changelog

## 0.2.0-dev

- Rebranded the guest-facing product from **RhoHMS F&B Menu** to **RhoGuest — Digital Menu & Guest Services** while retaining the technical app slug `fnb_menu`.
- Added an editable hotel-facing public menu route in **FNB Menu Settings**.
- Added protected legacy/existing QR aliases so already-printed hotel QR codes can continue to work.
- Preserved `/fnb-menu` and `/fnb-kitchen` as stable internal compatibility routes.
- Added automatic retention of the previous public menu route when the primary route changes.
- Added RhoGuest-managed markers to Frappe Website Settings route redirects so unrelated hotel redirects are never removed or overwritten.
- Added route validation for protected Frappe paths and conflicting Website Settings redirects.
- Added a route preview and dynamic Preview Public Menu button.
- Added a v0.2.0 routing-foundation static contract validator.
- Live-site routing acceptance passed for the configurable public route, legacy QR aliases and stable `/fnb-menu` compatibility endpoint.
- Added **RhoGuest Service Category** as a generic guest-service family master with workflow, publication, operating-information and capability controls.
- Added **RhoGuest Service Item** as a generic service-choice master with availability, pricing, reservation, capacity and ERPNext Item mapping.
- Added non-destructive default category provisioning for Food & Beverage, Laundry, Swimming Pool, Gym & Fitness, Spa & Wellness, Transport, Housekeeping, Recreation, Guest Requests and Hotel Information.
- Default service categories are created disabled and unpublished so migration never exposes ancillary services automatically.
- Added server-side validation for immutable category keys, publication state, information-only workflows, pricing modes, reservation capability, Charge to Room capability and duplicate service-item keys.
- Added a v0.2.0 generic-services static contract validator.
- Added a read-only **Guest Services Hub** at `/rhoguest`, disabled by default.
- Added Guest Hub settings for title, subtitle and service-item visibility.
- Guest Hub publication requires both category **Enabled** and **Show on Guest Portal** flags.
- Food & Beverage routes from the hub to the existing tested public menu route; unsupported service transactions remain unavailable.
- Added server-authoritative public Service Item price resolution, including current ERPNext Item Price checks.
- Added a v0.2.0 Guest Services Hub static contract validator.

- Added **Laundry Request & Fulfilment** with server-authoritative pricing, public status tokens and controlled fulfilment transitions.
- Added stable public Laundry route `/rhoguest-laundry`.
- Added **RhoGuest Workspace** with a `home` icon for Frappe Desk sidebar/home navigation.
- Added **RhoGuest Dashboard** Desk page with service, F&B, Laundry and pending-folio operational KPIs.
- Added recent Laundry activity and quick navigation from the Dashboard.
- Added updated **RhoGuest Setup Manual** and **RhoGuest User Manual** under `docs/`.
- Added a v0.2.0 Desk/Workspace/manual static contract validator.
- Added **Laundry staff operations UI** with workflow-safe form action buttons, pickup scheduling, staff assignment and operational List View queues.
- Added standard Laundry filters for Status, Billing Status, Room Number, Assigned To and Requested Pickup Time.
- Added a v0.2.0 Laundry operations UI static contract validator.

## 0.1.0

- Standardized the RhoHMS Food & Beverage add-on as **FNB Menu**.
- Standard Frappe/GitHub app slug: `fnb_menu`.
- Public routes: `/fnb-menu` and `/fnb-kitchen`.
- Added responsive Food/Drinks menu books, themes, layouts and floating category navigation.
- Added server-authoritative ERPNext pricing and fallback menu pricing.
- Added guest cart, quantity controls, line deletion and Clear Cart.
- Added prepaid self-ordering and Payment Request workflow.
- Added kitchen workflow with verified-payment release.
- Added non-destructive migration from `restaurant_luxury`.

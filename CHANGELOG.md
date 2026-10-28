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
- Laundry, Swimming Pool, Gym and other ancillary-service workflows are intentionally deferred until the routing layer passes live-site acceptance.

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

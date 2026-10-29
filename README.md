# RhoGuest — Digital Menu & Guest Services

**RhoGuest** is the guest-facing digital menu and services add-on for **RhoHMS — Rho Hospitality Management Suite**, developed by Rhocom Technology Limited.

The technical Frappe app and repository remain **`fnb_menu`** for upgrade and import compatibility. RhoGuest is the product identity from v0.2.0 onward.

The current F&B capability provides Food and Drinks menu books, themed responsive public menus, category navigation, ERPNext item/price integration, guest carts, prepaid self-ordering, Payment Request integration and a kitchen workflow. The v0.2.0 line expands the product toward additional hotel guest services such as Laundry, Swimming Pool, Gym, Spa, Transport, Housekeeping and Recreation.

## Stable technical identity

- Frappe app / GitHub repository: `fnb_menu`
- Product title: `RhoGuest`
- Frappe module: `FNB Menu`
- Existing Settings DocType: `FNB Menu Settings`
- Stable internal menu endpoint: `/fnb-menu`
- Kitchen board: `/fnb-kitchen`
- Publisher: Rhocom Technology Limited
- ERPNext/Frappe: v15.x

Existing Python imports, DocType names and `/fnb-menu` are intentionally retained. Do not rename the technical app to `rhoguest` on an installed site.

## v0.2.0 routing foundation

RhoGuest allows each hotel to choose a hotel-facing menu URL without editing `hooks.py`.

Open **FNB Menu Settings → RhoGuest Public Menu & Legacy QR Routing** and configure:

- **Public Menu Route** — for example `/menu`, `/dine` or `/guest-menu`.
- **Keep Previous Public Route as Alias** — preserves an old public route automatically when the primary route changes.
- **Legacy / Existing QR Routes** — add URLs already printed on QR cards, tent cards, room folders or signage.
- **QR Redirect Type** — defaults to HTTP 302 so the destination can safely change later.

The internal `/fnb-menu` route always remains available. RhoGuest-managed aliases are synchronized to Frappe **Website Settings → Route Redirects** and are marked internally so unrelated hotel redirects are never replaced or deleted.

Protected Frappe paths such as `/app`, `/api`, `/assets`, `/files`, `/private`, `/login` and `/desk` cannot be claimed as RhoGuest QR routes.

Route changes take effect after saving FNB Menu Settings and the website routing cache is cleared automatically; a Bench restart is not required merely to change a QR alias.

## v0.2.0 generic guest-service foundation

RhoGuest provides two generic configuration masters:

- **RhoGuest Service Category** — describes a service family, its guest interaction model, operating information, publication state and supported capabilities.
- **RhoGuest Service Item** — describes a guest-visible service choice, availability, price source, reservation requirements, capacity and optional ERPNext Item mapping.

The application seeds ten standard hospitality categories: Food & Beverage, Laundry, Swimming Pool, Gym & Fitness, Spa & Wellness, Transport, Housekeeping, Recreation, Guest Requests and Hotel Information.

Seeded categories are **disabled and unpublished**. Migration therefore does not expose new guest services automatically. A hotel enables only the services it actually provides.

The generic masters are presentation/configuration records, not transaction documents. Existing F&B ordering and kitchen/KOT behavior remains unchanged. Laundry jobs, transport bookings, spa reservations and other specialized operational workflows will be added as separate transaction models that reference these masters.

## v0.2.0 Guest Services Hub

The stable internal guest-services landing page is `/rhoguest`.

The hub is **disabled by default**. When enabled in **FNB Menu Settings → RhoGuest Guest Services Hub**, it renders only service categories where both **Enabled** and **Show on Guest Portal** are checked.

Phase 2B is intentionally read-only:

- Food & Beverage links to the existing configured public menu route.
- Other published categories can show their approved RhoGuest Service Items, operating hours, location, availability and safe server-resolved pricing.
- Transport, Housekeeping and other unfinished transactional services remain display-only until their dedicated server workflows are implemented.
- ERPNext Item Price service items are displayed only when a current valid selling price can be resolved from the configured Selling Price List.

This separates public presentation from operational fulfilment and prevents the guest UI from creating unsupported transactions.

## v0.2.0 Laundry Request & Fulfilment

Laundry is the first transactional ancillary-service workflow built on the generic service catalog. When the Laundry category is enabled and published, the Guest Services Hub links to `/rhoguest-laundry`.

Guest-submitted prices are never trusted. The browser sends only service-item identifiers, quantities and instructions; RhoGuest resolves current availability and prices again on the server before creating **RhoGuest Laundry Request**.

Charge-to-Room is recorded as **Pending Folio Posting**. RhoGuest supports a safe **Manual** folio workflow and an optional **Custom Integration** adapter without creating a hard dependency on RhoHMS.

### Laundry folio integration

System Manager can configure a trusted dotted Python method in **FNB Menu Settings → RhoGuest Laundry Billing & Notifications**. RhoGuest supplies a stable payload with an idempotency key and marks the request Posted to Room only when the adapter returns `success=True` and a concrete external reference.

Manual posting remains available to authorized billing managers and also requires a real external reference.

Laundry guest/staff email notifications are opt-in; assigned staff in-app notifications are enabled by default.

## v0.2.0 Pool & Gym Reservations

RhoGuest now supports public and staff-managed **Swimming Pool** and **Gym & Fitness** reservations.

Public routes:

- `/rhoguest-pool`
- `/rhoguest-gym`

The shared **RhoGuest Facility Reservation** transaction model provides:

- Requested → Confirmed → Checked In → Completed workflow.
- Cancelled and No Show terminal states.
- Server-authoritative duration, end time and pricing.
- Pricing Basis: Per Reservation or Per Person.
- Capacity-aware overlapping-slot protection.
- Service Item row locking to prevent concurrent overbooking.
- Staff rescheduling with capacity revalidation.
- Public token-based status lookup.
- Staff assignment and operational List View queues.
- Dashboard KPIs and recent Facility Reservations.

Paid facility reservations are recorded as **Pay at Hotel** in this release. Pool/Gym do not yet use the Laundry Charge-to-Room adapter.

## v0.2.0 Spa & Wellness Appointments

RhoGuest now provides a dedicated **Spa & Wellness appointment engine** at `/rhoguest-spa`.

Spa is deliberately resource-aware rather than reusing the Pool/Gym capacity model. The workflow includes:

- **RhoGuest Spa Resource** for therapists, treatment rooms, equipment or other bookable resources.
- Treatment-to-resource mapping.
- Structured weekly availability by day/start/end time.
- Guest choice of a public resource or **Any available**.
- Server-side auto-selection of an eligible free resource.
- Candidate-resource row locking before conflict checks.
- Overlap protection against Requested, Confirmed, Checked In and In Treatment appointments.
- Server-authoritative treatment duration, appointment end and pricing.
- Requested → Confirmed → Checked In → In Treatment → Completed workflow.
- Cancelled / No Show terminal states.
- Staff rescheduling/resource reassignment with availability revalidation.
- Public token-based appointment status lookup.
- Spa Dashboard KPIs, recent appointments and Workspace navigation.

Paid Spa appointments are recorded as **Pay at Hotel** in v0.2.0. Charge-to-Room remains limited to the Laundry adapter until a generic ancillary billing interface is released.

## RhoGuest Desk Workspace & Dashboard

RhoGuest includes a standard Frappe **Workspace** named **RhoGuest**. It is public to permitted Desk users and uses the `share-people` Workspace icon so RhoGuest appears as its own entry in the Frappe Desk sidebar/home navigation.

The Workspace provides direct access to:

- **RhoGuest Dashboard** — operational KPIs and recent Laundry activity.
- **RhoGuest Laundry Request** — operational Laundry queue.
- **RhoGuest Facility Reservation** — Pool/Gym reservation and access queue.
- **RhoGuest Spa Appointment** — Spa treatment appointment queue.
- **RhoGuest Spa Resource** — therapists/treatment resources and weekly availability.
- **RhoGuest Service Category** and **RhoGuest Service Item** — guest-service catalog configuration.
- **FNB Self Order** and **FNB Menu Book** — Food & Beverage operations.
- **FNB Menu Settings** — RhoGuest branding, routing, hub and F&B configuration.
- **Guest Services Hub** and the configured public Food & Beverage menu.

The Dashboard is available at Desk route `/app/rhoguest-dashboard`.

## Manuals

- [RhoGuest Setup Manual](docs/RHOGUEST_SETUP_MANUAL.md)
- [RhoGuest User Manual](docs/RHOGUEST_USER_MANUAL.md)

## Install from GitHub

```bash
cd ~/frappe-bench
bench get-app --branch main https://github.com/bobolabless/fnb_menu.git
bench --site <your-site> install-app fnb_menu
bench --site <your-site> migrate
bench build --app fnb_menu
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
bench restart
```

## Update a live installation

```bash
cd ~/frappe-bench/apps/fnb_menu
git pull --ff-only origin main

cd ~/frappe-bench
bench --site <your-site> migrate
bench build --app fnb_menu
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
bench restart
```

## Migration from Restaurant Luxury

The existing `restaurant_luxury` installation can remain installed while RhoGuest is tested. After installing this app, run:

```bash
bench --site <your-site> execute fnb_menu.migration.migrate_from_restaurant_luxury
```

The migration copies legacy menu configuration and records without deleting the old data. Test the public menu, `/fnb-kitchen`, ordering, payment and kitchen release before retiring the legacy app.

## Security / ordering rule

Browser-supplied prices are never authoritative. Checkout resolves allowed items and prices again on the server. Public self-orders require verified payment before kitchen release.

See `INSTALL.md` and `MIGRATION_FROM_RESTAURANT_LUXURY.md`.

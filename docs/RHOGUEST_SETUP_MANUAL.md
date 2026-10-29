# RhoGuest — Setup Manual

**Product:** RhoGuest — Digital Menu & Guest Services  
**Technical Frappe App:** `fnb_menu`  
**Publisher:** Rhocom Technology Limited  
**Product Family:** RhoHMS — Rho Hospitality Management Suite  
**Manual Version:** v0.2.0 Development Line  
**Copyright:** © 2026 Rhocom Technology Limited. All rights reserved.

---

## 1. Purpose

This manual explains how to install, upgrade, configure, validate and administer RhoGuest on Frappe/ERPNext v15.

RhoGuest provides a guest-facing digital-services layer while preserving the technical package name `fnb_menu` for compatibility. The product currently includes:

- Food & Beverage digital menus.
- Prepaid F&B self ordering and kitchen release.
- Configurable public menu routes and legacy QR aliases.
- Generic guest-service categories and service items.
- Public Guest Services Hub.
- Laundry Request & Fulfilment.
- RhoGuest Desk Workspace and operational Dashboard.
- Foundations for future Pool, Gym, Spa, Transport, Housekeeping and other services.

Do not rename the installed Frappe app from `fnb_menu`.

---

## 2. Prerequisites

Before installation, confirm:

- Frappe v15 and ERPNext v15 are operational.
- The target site has a valid Company.
- A Selling Price List exists.
- A system administrator can run Bench commands.
- HTTPS is used on production guest-facing deployments.
- Backups are available before upgrading an existing installation.

For F&B self ordering, also prepare:

- Default guest Customer.
- Payment Gateway Account.
- ERPNext Items and Item Prices.
- Warehouse where required.
- Sales Taxes and Charges Template where required.

---

## 3. Installation

### 3.1 Fresh installation

```bash
cd ~/frappe-bench
bench get-app --branch main https://github.com/bobolabless/fnb_menu.git
bench --site <site> install-app fnb_menu
bench --site <site> migrate
bench build --app fnb_menu
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

### 3.2 Confirm installation

```bash
bench --site <site> list-apps
```

Confirm `fnb_menu` is listed.

Then log into Frappe Desk. The left/home Workspace navigation should contain **RhoGuest** with a home icon.

---

## 4. Upgrade Procedure

Always back up first:

```bash
cd ~/frappe-bench
bench --site <site> backup --with-files
```

Update:

```bash
cd ~/frappe-bench/apps/fnb_menu
git pull --ff-only origin main

cd ~/frappe-bench
bench --site <site> migrate
bench build --app fnb_menu
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

After every upgrade, verify:

1. RhoGuest Workspace is visible.
2. `/app/rhoguest-dashboard` loads.
3. `/rhoguest` loads.
4. The configured public F&B menu route redirects correctly.
5. `/fnb-menu` remains available.
6. `/fnb-kitchen` remains available to authenticated staff.
7. `/rhoguest-laundry` behaves according to Laundry publication state.

---

## 5. RhoGuest Workspace

The standard Workspace is named **RhoGuest** and belongs to module **FNB Menu**.

It is the principal staff navigation area and contains:

- RhoGuest Dashboard.
- Laundry Requests.
- Service Categories.
- Service Items.
- F&B Self Orders.
- F&B Menu Books.
- FNB Menu Settings.
- Guest Hub and public menu shortcuts.

If the Workspace does not appear after migration:

```bash
bench --site <site> clear-cache
bench --site <site> migrate
bench restart
```

Then hard-refresh the browser.

---

## 6. RhoGuest Dashboard

Open **RhoGuest → RhoGuest Dashboard** or browse to:

`/app/rhoguest-dashboard`

The Dashboard reads live data server-side and displays:

- Published guest services.
- Enabled/guest-available Service Items.
- Active F&B orders.
- F&B orders awaiting payment.
- Open Laundry Requests.
- Laundry Requests awaiting pickup.
- Laundry Requests in processing.
- Laundry Requests ready/out for delivery.
- Laundry Requests delivered today.
- Charge-to-Room requests awaiting folio posting.
- Recent Laundry Requests.

The Dashboard is an operational view only. It does not bypass DocType permissions.

---

## 7. FNB Menu Settings

Open **RhoGuest → FNB Menu Settings**.

### 7.1 Hotel identity

Configure:

- Hotel Company.
- Location/brand subline.
- Company logo display.
- Company name display.

RhoGuest can use the Company RhoGuest logo override where available.

### 7.2 Menu presentation

Configure theme, layout, search, item images, descriptions, prices and category navigation.

### 7.3 Public menu routing

Set **Public Menu Route**, for example:

- `/menu`
- `/guest-menu`
- `/dine`

RhoGuest preserves `/fnb-menu` as the internal compatibility endpoint.

Use **Legacy / Existing QR Routes** to keep already-printed QR codes functioning.

Do not assign protected Frappe paths such as `/app`, `/api`, `/assets`, `/files`, `/private`, `/login` or `/desk`.

### 7.4 Guest Services Hub

Configure:

- Enable Guest Services Hub.
- Hub title.
- Hub subtitle.
- Whether Service Items are displayed.

The Hub is available at `/rhoguest`.

A service appears only when its Service Category has both:

- **Enabled = checked**
- **Show on Guest Portal = checked**

---

## 8. Service Catalog

### 8.1 RhoGuest Service Category

Default categories are created on installation/migration:

1. Food & Beverage
2. Laundry
3. Swimming Pool
4. Gym & Fitness
5. Spa & Wellness
6. Transport
7. Housekeeping
8. Recreation
9. Guest Requests
10. Hotel Information

Defaults are created disabled and unpublished.

Important fields include:

- Category Name.
- Service Key.
- Service Type.
- Workflow Type.
- Description.
- Display Order.
- Enabled.
- Show on Guest Portal.
- Operating Hours.
- Location.
- Guest/room requirements.
- Reservation/order/payment capabilities.
- Charge-to-Room capability.

The Service Key is immutable after creation.

### 8.2 RhoGuest Service Item

Use Service Items for guest-visible choices such as Laundry shirt washing, airport transfer, spa massage or pool day pass.

Pricing modes:

- Free.
- Fixed Price.
- ERPNext Item Price.
- Informational / Quote.

For a Fixed Price, configure Currency.

For ERPNext Item Price, configure a linked ERPNext Item and ensure the current Selling Price List contains a valid selling Item Price.

Do not publish Service Items until their category and operational workflow are ready.

---

## 9. Food & Beverage Setup

### 9.1 Menu Books

Create/publish **FNB Menu Book** records for Food and Drinks.

Configure:

- Company.
- Menu Type.
- Price List.
- Categories.
- Entries.
- Availability.
- Self-order permission.

### 9.2 Self ordering

Before enabling self ordering in FNB Menu Settings, configure:

- Company.
- Default Selling Price List.
- Default Guest Customer.
- Payment Gateway Account.

RhoGuest always re-resolves order prices on the server.

### 9.3 Kitchen

Authenticated staff use:

`/fnb-kitchen`

Only verified paid self-orders are released to the kitchen board.

---

## 10. Laundry Setup

### 10.1 Enable Laundry category

Open **RhoGuest Service Category → Laundry**.

Configure at minimum:

- Enabled.
- Show on Guest Portal.
- Allows Ordering / Item Selection.
- Allows Paid Services where applicable.
- Allows Charge to Room if hotel policy permits.
- Description.
- Operating Hours.
- Location.

### 10.2 Create Laundry Service Items

Create one Service Item per guest-selectable laundry service.

Example:

- Category: Laundry.
- Service Name: Shirt — Wash & Iron.
- Service Key: `shirt-wash-iron`.
- Pricing Mode: Fixed Price.
- Fixed Price: hotel-approved amount.
- Currency: hotel currency.
- Enabled: checked.
- Available to Guests: checked.
- Allow Charge to Room: according to policy.

### 10.3 Public Laundry route

The public page is:

`/rhoguest-laundry`

The Hub shows **Request Laundry Service** only when Laundry is enabled and published.

### 10.4 Billing behavior

**Pay at Hotel** creates an Unbilled request.

**Charge to Room** creates **Pending Folio Posting**.

RhoGuest v0.2.0 does not directly post to a RhoHMS guest folio. This is intentional to avoid unsafe or installation-specific accounting side effects.

### 10.5 Staff Operations UI

The **RhoGuest Laundry Request** form exposes workflow-safe action buttons rather than requiring staff to edit Status.

The List View includes operational queue filters for Open Queue, Awaiting Pickup, Processing, Ready / Delivery and Pending Folio. Status, Billing Status, Room Number, Assigned To and Requested Pickup Time are also standard filters.

Staff assignment is restricted to enabled Frappe **System User** accounts. Delivered or Cancelled requests cannot be reassigned.

Pickup scheduling is allowed only for Submitted or Pickup Scheduled requests and requires a future Date/Time.

### 10.6 Folio Integration Modes

Open **FNB Menu Settings → RhoGuest Laundry Billing & Notifications**.

**Manual** is the safe default. RhoGuest never changes the request to Posted to Room until an authorized System Manager or Sales Manager records the real external folio/PMS reference.

**Custom Integration** calls one trusted dotted Python method configured by System Manager. The method receives:

```python
payload = {
    "source_doctype": "RhoGuest Laundry Request",
    "source_name": "RGL-2026-00001",
    "idempotency_key": "RhoGuest Laundry Request:RGL-2026-00001",
    "company": "...",
    "guest_name": "...",
    "room_number": "...",
    "currency": "NGN",
    "amount": 5000.0,
    "billing_preference": "Charge to Room",
    "items": [
        {
            "service_item": "RGS-00001",
            "service_name": "Shirt — Wash & Iron",
            "service_key": "shirt-wash-iron",
            "qty": 2,
            "rate": 2500.0,
            "amount": 5000.0,
            "currency": "NGN",
        }
    ],
}
```

The configured callable must use signature:

```python
def post_laundry_charge(payload):
    # Validate the room/stay in the PMS.
    # Create or reuse the charge using payload["idempotency_key"].
    # Return the real external folio reference.
    return {
        "success": True,
        "reference": "FOLIO-CHARGE-000123",
        "message": "Posted successfully",
    }
```

RhoGuest marks the request **Posted to Room** only when `success` is true and a non-empty `reference` is returned. Integration failures leave the request at **Pending Folio Posting**.

The RhoGuest API also applies a database row lock before billing mutation. Once a request has a confirmed folio reference, repeated post calls return the existing reference rather than creating a second posting.

Manual posting remains available as an authorized fallback even when Custom Integration is configured.

### 10.7 Laundry Notification Settings

The same Settings section contains:

- **Laundry Staff In-App Notifications** — enabled by default. The assigned System User receives Frappe alerts for operational events.
- **Laundry Guest Email Notifications** — disabled by default.
- **Laundry Staff Email Notifications** — disabled by default.
- **Laundry Operations Email Recipients** — optional comma, semicolon or newline-separated staff addresses.

Guest email notifications are limited to selected guest-relevant events such as Submitted, Pickup Scheduled, Ready, Out for Delivery, Delivered, Cancelled and Posted to Room.

Email/notification delivery errors are logged but do not roll back the Laundry operational transaction.

---

## 11. Pool & Gym Setup

RhoGuest uses one shared **RhoGuest Facility Reservation** engine for Swimming Pool and Gym & Fitness because both follow the same access/reservation semantics while remaining separately published services.

### 11.1 Enable the category

Open **RhoGuest Service Category → Swimming Pool** or **Gym & Fitness**.

Configure:

- Enabled.
- Show on Guest Portal.
- Allows Reservation.
- Description.
- Operating Hours.
- Location.
- Requires Room Number if hotel policy requires it.

The public routes are:

- Swimming Pool: `/rhoguest-pool`
- Gym & Fitness: `/rhoguest-gym`

### 11.2 Create reservable Service Items

Each reservable Pool/Gym option must be a **RhoGuest Service Item** with:

- Correct Service Category.
- Enabled.
- Available to Guests.
- Requires Reservation.
- Duration greater than zero.
- Optional Capacity.
- Pricing Mode.
- Pricing Basis.

**Pricing Basis** supports:

- **Per Reservation** — one resolved rate for the whole booking.
- **Per Person** — resolved rate multiplied by Party Size.

Example Pool item:

- Service Name: Pool Day Access.
- Service Key: `pool-day-access`.
- Duration: 240 minutes.
- Capacity: 30.
- Pricing Mode: Fixed Price.
- Pricing Basis: Per Person.

Example Gym item:

- Service Name: Gym Session.
- Service Key: `gym-session`.
- Duration: 60 minutes.
- Capacity: 12.
- Pricing Mode: Free or Fixed Price.

### 11.3 Capacity protection

When Capacity is greater than zero, RhoGuest locks the Service Item row before checking overlapping active reservations.

Capacity is consumed by reservations in:

- Requested.
- Confirmed.
- Checked In.

The overlap rule is:

`existing.start < requested.end AND existing.end > requested.start`

This prevents simultaneous requests from oversubscribing the same slot.

Capacity `0` means no explicit capacity limit is enforced by the Service Item master.

### 11.4 Reservation workflow

The controlled staff workflow is:

`Requested → Confirmed → Checked In → Completed`

Additional terminal paths:

- Requested → Cancelled.
- Confirmed → Cancelled.
- Confirmed → No Show.

Staff can reschedule only Requested or Confirmed reservations. Rescheduling recalculates the slot end and rechecks capacity while excluding the current reservation itself.

### 11.5 Public security rules

The guest browser submits only:

- Facility category key.
- Service Item identifier.
- Guest/contact details.
- Reservation start.
- Party size.
- Guest note.

The browser does **not** submit authoritative rate, amount, duration, end time or capacity.

RhoGuest resolves all of these again on the server before inserting the reservation.

Reservations are currently limited to 180 days in advance.

Paid Pool/Gym reservations use **Pay at Hotel** in v0.2.0. Charge-to-Room integration remains limited to the Laundry workflow until a generic facility billing adapter is released.

### 11.6 Staff operations

Open **RhoGuest → Facility Reservations**.

Form actions include:

- Confirm Reservation.
- Reschedule.
- Check In.
- Mark No Show.
- Complete Visit.
- Cancel Reservation.
- Assign Staff / Unassign.

The List View provides queues:

- Upcoming.
- Awaiting Confirmation.
- Checked In.
- Pool.
- Gym.
- All Reservations.

The RhoGuest Dashboard includes Upcoming Facilities, Pool Today, Gym Today, Checked In, and Recent Facility Reservations.

---

## 12. Permissions

Current standard Desk roles used by RhoGuest include:

- System Manager.
- Sales Manager.
- Sales User.

System Manager has full configuration access.

Sales Manager can operate service masters and transactions according to DocType permissions.

Sales User has operational/read access according to individual DocType definitions.

Public website users do not receive Desk permissions.

Staff-only APIs reject Guest sessions.

---

## 13. Security Model

RhoGuest follows these rules:

- Browser-supplied prices are not authoritative.
- F&B order price/availability is re-resolved server-side.
- Laundry request price/availability is re-resolved server-side.
- Invalid/unpublished Laundry items are rejected.
- Laundry public status lookup requires the request name plus its secret public token.
- Staff fulfilment transitions are server-controlled.
- Delivered/Cancelled Laundry states are terminal.
- Charge-to-Room does not silently create a folio posting.
- Unrelated Website Settings redirects are not modified by RhoGuest.

---

## 14. Validation Commands

From the Bench directory:

```bash
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_foundation.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_services_foundation.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_guest_hub.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_laundry.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_desk.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_laundry_ops.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_laundry_billing.py
PYTHONDONTWRITEBYTECODE=1 ./env/bin/python apps/fnb_menu/scripts/validate_v020_facilities.py
```

All should report PASS.

---

## 15. Troubleshooting

### Workspace not visible

Run migrate, clear cache and restart. Confirm the user's role is included in the Workspace/Page roles.

### Dashboard loads but contains no data

Confirm the user can read the underlying DocTypes and that operational records exist.

### Public Hub shows no services

Check:

- Guest Hub enabled.
- Category Enabled.
- Category Show on Guest Portal.

### Laundry page says unavailable

Check:

- Guest Hub enabled.
- Laundry category enabled/published.
- Laundry category Allows Ordering.
- At least one Laundry Service Item enabled and available.

### Laundry item does not display

Check pricing configuration. ERPNext Item Price items require a valid active selling price.

### F&B menu route not working

Check FNB Menu Settings routing section, then clear website cache.

### QR alias conflict

RhoGuest refuses protected/conflicting routes. Choose another route instead of overriding Frappe endpoints.

---

## 16. Backup and Recovery

Before upgrades or major configuration changes:

```bash
bench --site <site> backup --with-files
```

Keep both database and public/private file backups.

Restore procedures should follow the normal Frappe Bench recovery process for the site's deployment environment.

---

## 17. Support and Ownership

RhoGuest is developed and maintained by **Rhocom Technology Limited** as a RhoHMS add-on application.

Technical package: `fnb_menu`.

This manual should be updated together with every functional RhoGuest release.

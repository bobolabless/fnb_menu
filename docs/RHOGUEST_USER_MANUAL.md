# RhoGuest — User Manual

**Product:** RhoGuest — Digital Menu & Guest Services  
**Technical Frappe App:** `fnb_menu`  
**Publisher:** Rhocom Technology Limited  
**Product Family:** RhoHMS — Rho Hospitality Management Suite  
**Manual Version:** v0.2.0 Development Line  
**Copyright:** © 2026 Rhocom Technology Limited. All rights reserved.

---

## 1. Introduction

RhoGuest gives hotel staff one place to manage guest-facing digital services while guests use public pages for menus and service requests.

Staff primarily work from the **RhoGuest Workspace** in Frappe Desk.

Current operational areas are:

- Dashboard.
- Food & Beverage.
- Laundry.
- Guest-service catalog.
- Public Guest Services Hub configuration.

---

## 2. Opening RhoGuest

Log into Frappe Desk.

Select **RhoGuest** from the left/home Workspace navigation. It appears with a home icon.

The Workspace provides shortcuts to:

- RhoGuest Dashboard.
- Laundry Requests.
- Service Categories.
- Service Items.
- F&B Orders.
- Menu Books.
- FNB Menu Settings.
- Public Guest Hub.
- Public Food & Beverage menu.

If RhoGuest is not visible, contact a System Manager to verify your role and refresh the site's Workspace/cache.

---

## 3. RhoGuest Dashboard

Open **RhoGuest Dashboard**.

The dashboard summarizes current operations.

### Published Services

Number of service categories currently visible to guests.

### Guest-Available Service Items

Number of enabled Service Items currently available to guests.

### Active F&B Orders

Paid F&B orders currently in kitchen fulfilment.

### Awaiting F&B Payment

Self-orders not yet payment-verified.

### Open Laundry

All Laundry Requests that are not Delivered or Cancelled.

### Awaiting Pickup

Laundry Requests in Submitted or Pickup Scheduled states.

### Processing

Laundry Requests currently Collected or Processing.

### Ready / Delivery

Laundry Requests in Ready or Out for Delivery states.

### Delivered Today

Laundry Requests completed today.

### Pending Folio Posting

Charge-to-Room Laundry Requests awaiting later folio/accounting posting.

### Recent Laundry Requests

The recent table shows request number, guest, room, status, billing state and estimated total. Select a request to open the full record.

Use **Refresh** to reload live dashboard data.

---

## 4. Guest Services Hub

The public Guest Services Hub is:

`/rhoguest`

Only explicitly published services appear.

A service must have:

- Enabled = checked.
- Show on Guest Portal = checked.

Food & Beverage opens the hotel's configured public menu.

Laundry opens the Laundry Request page when Laundry is published.

Do not publish future service categories merely because they exist. Publish only when their guest-facing and staff workflows are operational.

---

## 5. Food & Beverage Operations

### 5.1 Public menu

Guests use the configured public menu route, such as `/guest-menu`.

The stable internal menu remains `/fnb-menu`.

### 5.2 Self orders

When self ordering is enabled:

1. Guest selects Food/Drinks.
2. Guest submits details.
3. ERPNext creates the server-authoritative order.
4. Guest completes payment.
5. Only verified paid orders are released to the kitchen.

### 5.3 Kitchen board

Kitchen staff use `/fnb-kitchen`.

Typical sequence:

- Sent to Kitchen.
- Preparing.
- Ready.
- Served.

Never release an unpaid self-order to kitchen manually as a workaround.

---

## 6. Laundry — Guest Experience

Guests open:

`/rhoguest-laundry`

They:

1. Select one or more Laundry items.
2. Enter quantities.
3. Add optional item instructions.
4. Enter Guest Name.
5. Enter Room Number.
6. Enter phone or email.
7. Optionally select preferred pickup time.
8. Add pickup/laundry instructions.
9. Choose billing preference.
10. Submit.

RhoGuest recalculates current prices on the server. The price shown in the browser is not trusted as the transaction authority.

The guest receives a Laundry Request reference.

---

## 7. Laundry — Staff Operations

Open **RhoGuest → Laundry Requests**.

Open a request to review:

- Guest.
- Room.
- Contact.
- Pickup preference.
- Item lines.
- Item instructions.
- Estimated total.
- Billing preference.
- Billing status.
- Operational timestamps.

### 7.1 Status flow

Permitted sequence:

**Submitted**

May move to:

- Pickup Scheduled.
- Collected.
- Cancelled.

**Pickup Scheduled**

May move to:

- Collected.
- Cancelled.

**Collected**

May move to:

- Processing.
- Cancelled.

**Processing**

May move to:

- Ready.
- Cancelled.

**Ready**

May move to:

- Out for Delivery.
- Delivered.
- Cancelled.

**Out for Delivery**

May move to:

- Delivered.
- Cancelled.

**Delivered** and **Cancelled** are terminal.

The server rejects invalid jumps.

### 7.2 Operational timestamps

RhoGuest automatically records timestamps when applicable:

- Collected At.
- Ready At.
- Delivered At.

---

## 8. Laundry Billing

### Pay at Hotel

Billing Status begins as **Unbilled**.

Hotel staff settle the charge using the hotel's approved operational/accounting process.

### Charge to Room

Billing Status becomes:

**Pending Folio Posting**

This is a queue/approval state.

It does not mean the guest folio has already been charged.

Do not change the status to Posted to Room until the actual hotel folio/accounting process has completed and the appropriate reference is available.

---

## 9. Managing Service Categories

Open **RhoGuest Service Category**.

Use categories to control what appears on the Guest Hub.

Important controls:

- Enabled.
- Show on Guest Portal.
- Workflow Type.
- Operating Hours.
- Location.
- Requires Guest Identification.
- Requires Room Number.
- Allows Reservation.
- Allows Ordering.
- Allows Paid Services.
- Allows Charge to Room.

Do not change the Service Key of an existing category.

---

## 10. Managing Service Items

Open **RhoGuest Service Item**.

Use one record for each guest-visible service option.

Examples:

- Shirt — Wash & Iron.
- Trouser — Dry Clean.
- Airport Pickup.
- 60-minute Massage.
- Pool Day Pass.

A Service Item should be enabled and marked Available to Guests only when staff can actually fulfil it.

Pricing modes:

- Free.
- Fixed Price.
- ERPNext Item Price.
- Informational / Quote.

Quote-only items can be displayed but should not be treated as a fixed-price transactional selection.

---

## 11. FNB Menu Settings

System Managers use FNB Menu Settings for:

- Hotel identity.
- Theme/layout.
- Public menu route.
- Legacy QR aliases.
- Guest Hub enable/title/subtitle.
- Default Menu Books.
- Selling Price List.
- Self ordering.
- Payment Gateway.
- Default Customer.
- F&B service types.
- Stock/accounting defaults.

Operational users should not alter routing/payment configuration unless authorized.

---

## 12. Daily Operating Checklist

At start of shift:

1. Open RhoGuest Dashboard.
2. Review active F&B orders.
3. Review Open Laundry.
4. Review Awaiting Pickup.
5. Review Ready / Delivery.
6. Review Pending Folio Posting.
7. Confirm published services are actually available.
8. Confirm no unavailable Laundry item remains guest-visible.

During shift:

- Keep Laundry status current.
- Do not skip fulfilment states.
- Verify room number before collection/delivery.
- Follow hotel policy before Charge-to-Room posting.
- Keep guest instructions with the request.

End of shift:

- Review unresolved Open Laundry.
- Hand over pending pickup/delivery items.
- Reconcile pending folio postings.
- Confirm active F&B orders have been completed or handed over.

---

## 13. Security and Privacy

Staff should:

- Access RhoGuest only with their own Frappe account.
- Never share public request tokens.
- Avoid placing unnecessary sensitive information in internal notes.
- Verify guest/room details before service delivery.
- Follow hotel policy for personal data and payment information.

RhoGuest intentionally does not trust browser-submitted prices.

---

## 14. Common Issues

### Guest cannot see a service

Check category Enabled + Show on Guest Portal.

### Laundry page unavailable

Check Guest Hub enabled, Laundry published and Allows Ordering.

### Laundry item missing

Check Service Item Enabled, Available to Guests and valid pricing.

### Guest says total is different

The server-authoritative price at submission is the accepted request estimate. Review the stored Laundry Request line.

### Invalid status transition error

Follow the documented Laundry workflow sequence.

### F&B order not on Kitchen board

Confirm payment is verified Paid and order status is eligible for kitchen release.

### RhoGuest menu not visible in Desk

Contact System Manager to verify roles, run migrate/clear-cache if recently upgraded, then hard-refresh.

---

## 15. Future Modules

The generic RhoGuest service framework is designed to support additional operational workflows including:

- Swimming Pool.
- Gym & Fitness.
- Spa & Wellness.
- Transport.
- Housekeeping.
- Recreation.
- Guest Requests.
- Hotel Information.

A category may exist before its transaction workflow is released. Staff must not publish unfinished service workflows.

---

## 16. Support

RhoGuest is a RhoHMS add-on application developed by **Rhocom Technology Limited**.

For technical support, provide:

- Site name.
- RhoGuest/fnb_menu version.
- Relevant request/order reference.
- Screenshot or error traceback where applicable.
- Exact steps that produced the issue.

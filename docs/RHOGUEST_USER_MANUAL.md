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
- Pool & Gym reservations.
- Spa & Wellness appointments.
- Guest-service catalog.
- Public Guest Services Hub configuration.

---

RhoGuest Menu Settings is the central configuration record for guest-facing menus and services. Legacy FNB Desk naming is no longer used in normal hotel operations.

## 2. Opening RhoGuest

Log into Frappe Desk.

Select **RhoGuest** from the left/home Workspace navigation. It appears with a share-people icon.

The Workspace provides shortcuts to:

- RhoGuest Dashboard.
- Laundry Requests.
- Facility Reservations.
- Spa Appointments.
- Spa Resources.
- Service Categories.
- Service Items.
- Food & Beverage Orders.
- Menu Books.
- RhoGuest Menu Settings.
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

### Active Food & Beverage Orders

Paid Food & Beverage orders currently in kitchen fulfilment.

### Awaiting Food & Beverage Payment

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

Swimming Pool and Gym open their reservation pages when published.

Spa & Wellness opens the Spa Appointment page when published.

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

### 7.3 Form Action Buttons

Open a Laundry Request and use the **Laundry Actions** group instead of editing Status manually.

Available actions depend on the current state:

- Submitted: Schedule Pickup, Mark Collected, Cancel Request.
- Pickup Scheduled: Reschedule Pickup, Mark Collected, Cancel Request.
- Collected: Start Processing, Cancel Request.
- Processing: Mark Ready, Cancel Request.
- Ready: Out for Delivery, Mark Delivered, Cancel Request.
- Out for Delivery: Mark Delivered, Cancel Request.
- Delivered / Cancelled: no further fulfilment transition is available.

Use **Operations → Assign Staff** to assign an open request to an enabled System User. Use **Unassign** to remove the current assignment.

The server validates every action. A button being visible does not bypass the server-side workflow rules.

### 7.4 Laundry Queue Filters

The Laundry Request List includes quick **Queues**:

- Open Queue.
- Awaiting Pickup.
- Processing.
- Ready / Delivery.
- Pending Folio.
- All Requests.

Standard filters are also available for Status, Billing Status, Room Number, Assigned To and Requested Pickup Time.

Use these queues during shift handover and daily operational review.

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

### Manual Folio Posting

For a request showing **Pending Folio Posting**, an authorized System Manager or Sales Manager uses:

**Billing → Record Folio Posting**

Enter the real external folio/PMS transaction reference only after the charge has actually been posted.

RhoGuest records:

- Folio Reference.
- Folio Posting Mode.
- Folio Posted At.
- Folio Posted By.

### Custom Folio Integration

When System Manager has configured **Custom Integration**, the form also shows:

**Billing → Post to Folio**

RhoGuest sends the request through the configured server-side adapter. The request changes to **Posted to Room** only after the integration confirms success and returns an external reference.

If the integration fails, do not manually invent a reference. Resolve the external PMS issue or use the authorized manual fallback only after a real posting has been completed.

### Mark Settled

Once Billing Status is **Posted to Room**, an authorized billing manager may use **Billing → Mark Settled** after the hotel billing process confirms settlement.

RhoGuest stores the settlement timestamp and user for audit purposes.

### Laundry Notifications

The hotel may enable guest and staff email notifications in RhoGuest Menu Settings.

Assigned staff can also receive in-app Frappe alerts for Laundry lifecycle events.

Email notifications are supplementary. Staff should continue to use the RhoGuest Dashboard and Laundry operational queues as the source of truth.

---

## 9. Swimming Pool & Gym Reservations

Guests use:

- Swimming Pool: `/rhoguest-pool`
- Gym & Fitness: `/rhoguest-gym`

A guest:

1. Selects a published reservable access option.
2. Enters Guest Name.
3. Enters Room Number if applicable.
4. Provides phone or email.
5. Selects Reservation Start.
6. Enters Party Size.
7. Adds an optional note.
8. Submits the request.

RhoGuest calculates duration, end time, capacity and price again on the server.

### 9.1 Staff workflow

Open **RhoGuest → Facility Reservations**.

The status flow is:

**Requested**
- Confirm Reservation.
- Reschedule.
- Cancel Reservation.

**Confirmed**
- Check In.
- Reschedule.
- Mark No Show.
- Cancel Reservation.

**Checked In**
- Complete Visit.

**Completed**, **Cancelled**, and **No Show** are terminal.

### 9.2 Capacity

If the Service Item has a Capacity greater than zero, RhoGuest blocks a reservation when overlapping Requested, Confirmed or Checked In reservations would exceed that capacity.

Party Size consumes capacity.

Do not override a capacity rejection by manually changing reservation snapshot fields.

### 9.3 Pricing

Pool/Gym pricing can be:

- Complimentary.
- Paid at Hotel.

The Service Item may price **Per Reservation** or **Per Person**.

RhoGuest stores the authoritative server-resolved rate and estimated total in the Facility Reservation.

### 9.4 Queue filters

The Facility Reservation List provides:

- Upcoming.
- Awaiting Confirmation.
- Checked In.
- Pool.
- Gym.
- All Reservations.

Staff can also filter by Facility, Status, Reservation Start, Room Number and Assigned To.

---

## 10. Spa & Wellness Appointments

Guests use:

`/rhoguest-spa`

A guest:

1. Selects a published Spa treatment.
2. Enters Guest Name.
3. Enters Room Number if applicable.
4. Provides phone or email.
5. Selects Appointment Start.
6. Optionally chooses a public therapist/resource, or leaves **Any available**.
7. Adds an optional Guest Note.
8. Submits.

RhoGuest resolves the treatment price, duration, end time and actual available resource on the server.

### 10.1 Staff workflow

Open **RhoGuest → Spa Appointments**.

**Requested**
- Confirm Appointment.
- Reschedule / Change Resource.
- Cancel Appointment.

**Confirmed**
- Check In.
- Reschedule / Change Resource.
- Mark No Show.
- Cancel Appointment.

**Checked In**
- Start Treatment.

**In Treatment**
- Complete Treatment.

**Completed**, **Cancelled**, and **No Show** are terminal.

### 10.2 Spa resources

System Manager/Sales Manager configure **RhoGuest Spa Resource** records.

A resource may represent:

- Therapist.
- Treatment Room.
- Equipment.
- Other.

A Spa Resource must be mapped to the treatments it can perform and given weekly availability.

If a resource is not marked **Allow Guest to Select This Resource**, guests will not see its name; the server may still assign it automatically when **Any available** is selected.

### 10.3 Availability and conflicts

RhoGuest rejects a Spa booking when:

- No enabled resource supports the treatment.
- The selected resource is outside its configured weekly availability.
- Another active appointment overlaps that resource.
- A duplicate active appointment exists for the same guest contact/treatment/time.
- The appointment is more than 180 days in advance.

Requested appointments already reserve the resource to prevent double booking while staff confirmation is pending.

### 10.4 Pricing and settlement

Spa pricing is always resolved by the server.

The guest browser cannot set:

- Rate.
- Amount.
- Duration.
- Appointment End.

Settlement is currently:

- Complimentary; or
- Pay at Hotel.

### 10.5 Spa queues

The Spa Appointment List provides:

- Upcoming.
- Awaiting Confirmation.
- Checked In.
- In Treatment.
- All Appointments.

The RhoGuest Dashboard also shows Upcoming Spa, Spa Today, In Treatment and Recent Spa Appointments.

---

## 11. Managing Service Categories

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

## 12. Managing Service Items

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

## 13. RhoGuest Menu Settings

System Managers use RhoGuest Menu Settings for:

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
- Food & Beverage service types.
- Stock/accounting defaults.

Operational users should not alter routing/payment configuration unless authorized.

---

## 14. Daily Operating Checklist

At start of shift:

1. Open RhoGuest Dashboard.
2. Review active Food & Beverage orders.
3. Review Open Laundry.
4. Review Awaiting Pickup.
5. Review Ready / Delivery.
6. Review Pending Folio Posting.
7. Review Upcoming Pool/Gym reservations.
8. Review guests currently Checked In to facilities.
9. Review Upcoming Spa appointments and treatments In Treatment.
10. Confirm published services are actually available.
11. Confirm no unavailable Laundry, Facility or Spa treatment remains guest-visible.

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
- Confirm active Food & Beverage orders have been completed or handed over.

---

## 15. Security and Privacy

Staff should:

- Access RhoGuest only with their own Frappe account.
- Never share public request tokens.
- Avoid placing unnecessary sensitive information in internal notes.
- Verify guest/room details before service delivery.
- Follow hotel policy for personal data and payment information.

RhoGuest intentionally does not trust browser-submitted prices.

---

## 16. Common Issues

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

### Food & Beverage order not on Kitchen board

Confirm payment is verified Paid and order status is eligible for kitchen release.

### Spa appointment cannot be booked

Check the treatment is published/reservable and that at least one mapped enabled Spa Resource has weekly availability covering the requested time without an overlapping active appointment.

### RhoGuest menu not visible in Desk

Contact System Manager to verify roles, run migrate/clear-cache if recently upgraded, then hard-refresh.

---

## 17. Future Modules

The generic RhoGuest service framework is designed to support additional operational workflows including:

- Transport.
- Housekeeping.
- Recreation.
- Guest Requests.
- Hotel Information.

A category may exist before its transaction workflow is released. Staff must not publish unfinished service workflows.

---

## 18. Support

RhoGuest is a RhoHMS add-on application developed by **Rhocom Technology Limited**.

For technical support, provide:

- Site name.
- RhoGuest/fnb_menu version.
- Relevant request/order reference.
- Screenshot or error traceback where applicable.
- Exact steps that produced the issue.

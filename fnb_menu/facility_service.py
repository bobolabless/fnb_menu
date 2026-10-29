"""Public Pool/Gym catalog, slot resolution and capacity protection."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, cint, flt, get_datetime, now_datetime

from fnb_menu.guest_service import resolve_public_service_item
from fnb_menu.menu_service import get_company_brand, get_settings

FACILITY_KEYS = {"swimming-pool", "gym-fitness"}
ACTIVE_CAPACITY_STATUSES = ("Requested", "Confirmed", "Checked In")


def get_public_facility_catalog(category_key):
    """Return one published Pool/Gym catalog with transaction-ready items."""

    if category_key not in FACILITY_KEYS:
        frappe.throw(_("Unsupported RhoGuest facility."))

    settings = get_settings()
    if not cint(settings.get("guest_hub_enabled")):
        return frappe._dict({"available": 0, "category": None, "items": []})

    category = frappe.db.get_value(
        "RhoGuest Service Category",
        {
            "name": category_key,
            "enabled": 1,
            "show_on_portal": 1,
        },
        [
            "name",
            "category_name",
            "short_description",
            "operating_hours",
            "location",
            "requires_room_number",
            "allows_reservation",
        ],
        as_dict=True,
    )

    if not category or not cint(category.allows_reservation):
        return frappe._dict({"available": 0, "category": category, "items": []})

    company_currency = "NGN"
    if settings.company:
        company_currency = get_company_brand(settings.company).currency or "NGN"

    rows = frappe.get_all(
        "RhoGuest Service Item",
        filters={
            "service_category": category_key,
            "enabled": 1,
            "available_to_guests": 1,
        },
        fields=[
            "name",
            "service_category",
            "service_name",
            "service_key",
            "description",
            "image",
            "sort_order",
            "availability_note",
            "pricing_mode",
            "pricing_basis",
            "fixed_price",
            "currency",
            "erpnext_item",
            "allow_charge_to_room",
            "requires_reservation",
            "duration_minutes",
            "fulfilment_time_minutes",
            "capacity",
            "location",
        ],
        order_by="sort_order asc, service_name asc",
        limit_page_length=500,
    )

    items = []
    for row in rows:
        public_item = resolve_public_service_item(
            row,
            settings=settings,
            company_currency=company_currency,
        )
        if not public_item:
            continue

        public_item.selectable = bool(
            cint(public_item.requires_reservation)
            and cint(public_item.duration_minutes) > 0
            and public_item.pricing_mode != "Informational / Quote"
            and public_item.rate is not None
        )
        public_item.location = public_item.location or category.location or ""
        items.append(public_item)

    return frappe._dict(
        {
            "available": 1,
            "category": category,
            "items": items,
            "currency": company_currency,
        }
    )


def validate_reservation_start(value):
    """Validate a guest reservation start within the supported booking horizon."""

    start = get_datetime(value)
    now = now_datetime()

    if not start or start <= now:
        frappe.throw(_("Reservation time must be in the future."))

    if start > add_days(now, 180):
        frappe.throw(_("Reservations cannot be made more than 180 days in advance."))

    return start


def _lock_service_item(service_item):
    """Serialize capacity decisions for a reservable Service Item."""

    frappe.db.sql(
        """
        select name
        from `tabRhoGuest Service Item`
        where name = %s
        for update
        """,
        service_item,
    )


def _reserved_capacity(service_item, start, end, exclude_reservation=None):
    """Return participants already occupying an overlapping active slot."""

    conditions = [
        "service_item = %(service_item)s",
        "status in ('Requested', 'Confirmed', 'Checked In')",
        "reservation_start < %(end)s",
        "reservation_end > %(start)s",
    ]
    values = {
        "service_item": service_item,
        "start": start,
        "end": end,
    }

    if exclude_reservation:
        conditions.append("name != %(exclude)s")
        values["exclude"] = exclude_reservation

    row = frappe.db.sql(
        f"""
        select coalesce(sum(party_size), 0)
        from `tabRhoGuest Facility Reservation`
        where {" and ".join(conditions)}
        """,
        values=values,
    )

    return cint(row[0][0] if row else 0)


def resolve_facility_reservation(
    category_key,
    service_item,
    reservation_start,
    party_size,
    exclude_reservation=None,
):
    """Resolve an authoritative slot, price and capacity snapshot."""

    if category_key not in FACILITY_KEYS:
        frappe.throw(_("Unsupported RhoGuest facility."))

    party_size = cint(party_size)
    if party_size < 1 or party_size > 50:
        frappe.throw(_("Party Size must be between 1 and 50."))

    start = validate_reservation_start(reservation_start)
    _lock_service_item(service_item)

    # Re-read the publication/pricing state after acquiring the service-item
    # lock so concurrent configuration/booking work cannot use a stale snapshot.
    catalog = get_public_facility_catalog(category_key)
    if not catalog.available:
        frappe.throw(_("This facility is currently unavailable for reservations."))

    item = next(
        (
            row
            for row in catalog["items"]
            if row.name == service_item and row.selectable
        ),
        None,
    )
    if not item:
        frappe.throw(_("The selected facility service is not available for reservation."))

    duration = cint(item.duration_minutes)
    end = add_to_date(start, minutes=duration, as_datetime=True)

    capacity = cint(item.capacity)
    if capacity > 0:
        occupied = _reserved_capacity(
            service_item,
            start,
            end,
            exclude_reservation=exclude_reservation,
        )
        if occupied + party_size > capacity:
            remaining = max(capacity - occupied, 0)
            frappe.throw(
                _("This slot does not have enough capacity. Remaining capacity: {0}.").format(
                    remaining
                )
            )

    rate = flt(item.rate)
    basis = item.pricing_basis or "Per Reservation"
    total = rate * party_size if basis == "Per Person" else rate

    return frappe._dict(
        {
            "catalog": catalog,
            "item": item,
            "start": start,
            "end": end,
            "party_size": party_size,
            "pricing_basis": basis,
            "estimated_total": total,
            "settlement_mode": "Complimentary" if total <= 0 else "Pay at Hotel",
        }
    )


def reject_duplicate_guest_booking(email, phone, service_item, start, end):
    """Reject an obvious duplicate active reservation for the same guest contact."""

    contact_filters = []
    if email:
        contact_filters.append(["email", "=", email])
    if phone:
        contact_filters.append(["phone", "=", phone])

    if not contact_filters:
        return

    rows = frappe.get_all(
        "RhoGuest Facility Reservation",
        filters=[
            ["RhoGuest Facility Reservation", "service_item", "=", service_item],
            ["RhoGuest Facility Reservation", "status", "in", list(ACTIVE_CAPACITY_STATUSES)],
            ["RhoGuest Facility Reservation", "reservation_start", "<", end],
            ["RhoGuest Facility Reservation", "reservation_end", ">", start],
        ],
        or_filters=contact_filters,
        pluck="name",
        limit_page_length=1,
    )
    if rows:
        frappe.throw(
            _("A matching active reservation already exists for this guest and time slot.")
        )

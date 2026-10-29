"""Transport catalog, booking resolution and dispatch conflict protection."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, cint, flt, getdate, get_datetime, now_datetime

from fnb_menu.guest_service import resolve_public_service_item
from fnb_menu.menu_service import get_company_brand, get_settings

TRANSPORT_CATEGORY_KEY = "transport"
ACTIVE_RESOURCE_STATUSES = (
    "Requested",
    "Confirmed",
    "Dispatched",
    "Arrived at Pickup",
    "In Transit",
)


def get_public_transport_catalog():
    """Return the published Transport category and transactional service items."""

    settings = get_settings()
    if not cint(settings.get("guest_hub_enabled")):
        return frappe._dict({"available": 0, "category": None, "items": []})

    category = frappe.db.get_value(
        "RhoGuest Service Category",
        {
            "name": TRANSPORT_CATEGORY_KEY,
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
            "service_category": TRANSPORT_CATEGORY_KEY,
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
        items.append(public_item)

    return frappe._dict(
        {
            "available": 1,
            "category": category,
            "items": items,
            "currency": company_currency,
        }
    )


def validate_pickup_time(value):
    start = get_datetime(value)
    now = now_datetime()

    if not start or start <= now:
        frappe.throw(_("Scheduled Pickup must be in the future."))

    if start > add_days(now, 180):
        frappe.throw(_("Transport bookings cannot be made more than 180 days in advance."))

    return start


def resolve_transport_booking(service_item, scheduled_pickup_at, passenger_count):
    """Resolve the selected public transport service on the server."""

    passengers = cint(passenger_count)
    if passengers < 1 or passengers > 50:
        frappe.throw(_("Passengers must be between 1 and 50."))

    start = validate_pickup_time(scheduled_pickup_at)
    catalog = get_public_transport_catalog()

    if not catalog.available:
        frappe.throw(_("Transport is currently unavailable for booking."))

    item = next(
        (
            row
            for row in catalog["items"]
            if row.name == service_item and row.selectable
        ),
        None,
    )
    if not item:
        frappe.throw(_("The selected Transport service is not available for booking."))

    if cint(item.capacity) > 0 and passengers > cint(item.capacity):
        frappe.throw(
            _("This Transport service accepts a maximum of {0} passengers per booking.").format(
                cint(item.capacity)
            )
        )

    duration = cint(item.duration_minutes)
    end = add_to_date(start, minutes=duration, as_datetime=True)

    rate = flt(item.rate)
    basis = item.pricing_basis or "Per Reservation"
    total = rate * passengers if basis == "Per Person" else rate

    return frappe._dict(
        {
            "catalog": catalog,
            "item": item,
            "start": start,
            "end": end,
            "passenger_count": passengers,
            "pricing_basis": basis,
            "estimated_total": total,
            "settlement_mode": "Complimentary" if total <= 0 else "Pay at Hotel",
        }
    )


def reject_duplicate_guest_booking(email, phone, service_item, start, end, exclude=None):
    """Reject an obvious duplicate active booking for the same guest contact."""

    contact_filters = []
    if email:
        contact_filters.append(["email", "=", email])
    if phone:
        contact_filters.append(["phone", "=", phone])

    if not contact_filters:
        return

    filters = [
        ["RhoGuest Transport Booking", "service_item", "=", service_item],
        ["RhoGuest Transport Booking", "status", "in", list(ACTIVE_RESOURCE_STATUSES)],
        ["RhoGuest Transport Booking", "scheduled_pickup_at", "<", end],
        ["RhoGuest Transport Booking", "estimated_dropoff_at", ">", start],
    ]
    if exclude:
        filters.append(["RhoGuest Transport Booking", "name", "!=", exclude])

    rows = frappe.get_all(
        "RhoGuest Transport Booking",
        filters=filters,
        or_filters=contact_filters,
        pluck="name",
        limit_page_length=1,
    )
    if rows:
        frappe.throw(_("A matching active Transport booking already exists for this guest and time."))


def lock_booking(booking_name):
    frappe.db.sql(
        """
        select name
        from `tabRhoGuest Transport Booking`
        where name = %s
        for update
        """,
        booking_name,
    )


def _lock_vehicle(vehicle):
    frappe.db.sql(
        """
        select name
        from `tabRhoGuest Transport Vehicle`
        where name = %s
        for update
        """,
        vehicle,
    )


def _lock_driver(driver):
    frappe.db.sql(
        """
        select name
        from `tabRhoGuest Transport Driver`
        where name = %s
        for update
        """,
        driver,
    )


def _has_resource_overlap(fieldname, value, start, end, exclude_booking=None):
    conditions = [
        f"{fieldname} = %(resource)s",
        "status in ('Requested', 'Confirmed', 'Dispatched', 'Arrived at Pickup', 'In Transit')",
        "scheduled_pickup_at < %(end)s",
        "estimated_dropoff_at > %(start)s",
    ]
    values = {"resource": value, "start": start, "end": end}

    if exclude_booking:
        conditions.append("name != %(exclude)s")
        values["exclude"] = exclude_booking

    rows = frappe.db.sql(
        f"""
        select name
        from `tabRhoGuest Transport Booking`
        where {" and ".join(conditions)}
        limit 1
        """,
        values=values,
    )
    return bool(rows)


def validate_and_lock_resources(
    vehicle,
    driver,
    start,
    end,
    passenger_count,
    luggage_count=0,
    exclude_booking=None,
):
    """Lock and validate one vehicle/driver pair against the trip window."""

    _lock_vehicle(vehicle)
    _lock_driver(driver)

    vehicle_doc = frappe.db.get_value(
        "RhoGuest Transport Vehicle",
        vehicle,
        [
            "name",
            "vehicle_name",
            "registration_number",
            "passenger_capacity",
            "luggage_capacity",
            "enabled",
        ],
        as_dict=True,
    )
    if not vehicle_doc or not cint(vehicle_doc.enabled):
        frappe.throw(_("The selected Transport Vehicle is not enabled."))

    if cint(vehicle_doc.passenger_capacity) < cint(passenger_count):
        frappe.throw(
            _("The selected vehicle cannot carry {0} passengers.").format(
                cint(passenger_count)
            )
        )

    if cint(vehicle_doc.luggage_capacity) > 0 and cint(luggage_count) > cint(vehicle_doc.luggage_capacity):
        frappe.throw(
            _("The selected vehicle cannot carry {0} luggage pieces.").format(
                cint(luggage_count)
            )
        )

    driver_doc = frappe.db.get_value(
        "RhoGuest Transport Driver",
        driver,
        ["name", "driver_name", "license_expiry", "enabled"],
        as_dict=True,
    )
    if not driver_doc or not cint(driver_doc.enabled):
        frappe.throw(_("The selected Transport Driver is not enabled."))

    if getdate(driver_doc.license_expiry) < getdate(start):
        frappe.throw(_("The selected driver's licence expires before the scheduled trip."))

    if _has_resource_overlap("vehicle", vehicle, start, end, exclude_booking):
        frappe.throw(_("The selected Transport Vehicle is already assigned to an overlapping active trip."))

    if _has_resource_overlap("driver", driver, start, end, exclude_booking):
        frappe.throw(_("The selected Transport Driver is already assigned to an overlapping active trip."))

    return frappe._dict({"vehicle": vehicle_doc, "driver": driver_doc})

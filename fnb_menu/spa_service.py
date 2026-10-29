"""Public Spa catalog and conflict-safe resource scheduling."""

from __future__ import annotations

from datetime import time, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, cint, flt, get_datetime, now_datetime

from fnb_menu.guest_service import resolve_public_service_item
from fnb_menu.menu_service import get_company_brand, get_settings

SPA_CATEGORY_KEY = "spa-wellness"
ACTIVE_STATUSES = ("Requested", "Confirmed", "Checked In", "In Treatment")


def _time_seconds(value):
    if value is None:
        return None
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, time):
        return value.hour * 3600 + value.minute * 60 + value.second

    text = str(value).strip()
    if not text:
        return None

    parts = text.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2] or 0))


def get_public_spa_catalog():
    """Return published Spa treatments and guest-selectable resources."""

    settings = get_settings()
    if not cint(settings.get("guest_hub_enabled")):
        return frappe._dict({"available": 0, "category": None, "items": []})

    category = frappe.db.get_value(
        "RhoGuest Service Category",
        {
            "name": SPA_CATEGORY_KEY,
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
            "service_category": SPA_CATEGORY_KEY,
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
        public_item.resources = get_public_resources_for_service(row.name)
        items.append(public_item)

    return frappe._dict(
        {
            "available": 1,
            "category": category,
            "items": items,
            "currency": company_currency,
        }
    )


def get_public_resources_for_service(service_item):
    """Return enabled mapped resources whose names may be shown to guests."""

    return frappe.db.sql(
        """
        select distinct
            r.name,
            r.resource_name,
            r.resource_type,
            r.location
        from `tabRhoGuest Spa Resource` r
        inner join `tabRhoGuest Spa Resource Service` s
            on s.parent = r.name
            and s.parenttype = 'RhoGuest Spa Resource'
            and s.parentfield = 'services'
        where
            r.enabled = 1
            and r.allow_public_selection = 1
            and s.service_item = %s
        order by r.sort_order asc, r.resource_name asc
        """,
        service_item,
        as_dict=True,
    )


def validate_appointment_start(value):
    start = get_datetime(value)
    now = now_datetime()

    if not start or start <= now:
        frappe.throw(_("Appointment time must be in the future."))

    if start > add_days(now, 180):
        frappe.throw(_("Spa appointments cannot be made more than 180 days in advance."))

    return start


def _candidate_resource_names(service_item):
    rows = frappe.get_all(
        "RhoGuest Spa Resource Service",
        filters={
            "parenttype": "RhoGuest Spa Resource",
            "parentfield": "services",
            "service_item": service_item,
        },
        pluck="parent",
        limit_page_length=1000,
    )
    return sorted(set(rows))


def _lock_candidate_resources(service_item):
    """Lock eligible resource rows so concurrent booking selection is serialized."""

    names = _candidate_resource_names(service_item)
    if not names:
        return []

    placeholders = ", ".join(["%s"] * len(names))
    return frappe.db.sql(
        f"""
        select name
        from `tabRhoGuest Spa Resource`
        where enabled = 1 and name in ({placeholders})
        order by sort_order asc, resource_name asc
        for update
        """,
        tuple(names),
        pluck=True,
    )


def _resource_supports_service(resource_name, service_item):
    return bool(
        frappe.db.exists(
            "RhoGuest Spa Resource Service",
            {
                "parent": resource_name,
                "parenttype": "RhoGuest Spa Resource",
                "parentfield": "services",
                "service_item": service_item,
            },
        )
    )


def _resource_covers_period(resource_name, start, end):
    """Require one availability row to cover the complete appointment."""

    if start.date() != end.date():
        return False

    day = start.strftime("%A")
    start_seconds = start.hour * 3600 + start.minute * 60 + start.second
    end_seconds = end.hour * 3600 + end.minute * 60 + end.second

    rows = frappe.get_all(
        "RhoGuest Spa Resource Availability",
        filters={
            "parent": resource_name,
            "parenttype": "RhoGuest Spa Resource",
            "parentfield": "availability",
            "day_of_week": day,
        },
        fields=["start_time", "end_time"],
        limit_page_length=100,
    )

    for row in rows:
        available_start = _time_seconds(row.start_time)
        available_end = _time_seconds(row.end_time)
        if (
            available_start is not None
            and available_end is not None
            and start_seconds >= available_start
            and end_seconds <= available_end
        ):
            return True

    return False


def _resource_has_overlap(resource_name, start, end, exclude_appointment=None):
    conditions = [
        "spa_resource = %(resource)s",
        "status in ('Requested', 'Confirmed', 'Checked In', 'In Treatment')",
        "appointment_start < %(end)s",
        "appointment_end > %(start)s",
    ]
    values = {
        "resource": resource_name,
        "start": start,
        "end": end,
    }

    if exclude_appointment:
        conditions.append("name != %(exclude)s")
        values["exclude"] = exclude_appointment

    rows = frappe.db.sql(
        f"""
        select name
        from `tabRhoGuest Spa Appointment`
        where {" and ".join(conditions)}
        limit 1
        """,
        values=values,
    )
    return bool(rows)


def _choose_resource(
    service_item,
    start,
    end,
    preferred_resource=None,
    require_public_preference=False,
    exclude_appointment=None,
):
    """Choose and lock one capable resource that covers the requested period."""

    locked_names = _lock_candidate_resources(service_item)
    if not locked_names:
        frappe.throw(_("No enabled Spa Resource is configured for this treatment."))

    if preferred_resource:
        if preferred_resource not in locked_names:
            frappe.throw(_("The selected Spa Resource cannot perform this treatment."))

        if require_public_preference:
            public = frappe.db.get_value(
                "RhoGuest Spa Resource",
                preferred_resource,
                "allow_public_selection",
            )
            if not cint(public):
                frappe.throw(_("The selected Spa Resource is not available for guest selection."))

        candidates = [preferred_resource]
    else:
        candidates = locked_names

    for resource_name in candidates:
        if not _resource_supports_service(resource_name, service_item):
            continue
        if not _resource_covers_period(resource_name, start, end):
            continue
        if _resource_has_overlap(
            resource_name,
            start,
            end,
            exclude_appointment=exclude_appointment,
        ):
            continue

        resource = frappe.db.get_value(
            "RhoGuest Spa Resource",
            resource_name,
            ["name", "resource_name", "resource_type", "location"],
            as_dict=True,
        )
        if resource:
            return resource

    if preferred_resource:
        frappe.throw(_("The selected Spa Resource is not available for this appointment time."))

    frappe.throw(_("No Spa Resource is available for this treatment and time."))


def resolve_spa_appointment(
    service_item,
    appointment_start,
    preferred_resource=None,
    require_public_preference=False,
    exclude_appointment=None,
):
    """Resolve treatment, price, end time and one conflict-free resource."""

    start = validate_appointment_start(appointment_start)

    catalog = get_public_spa_catalog()
    if not catalog.available:
        frappe.throw(_("Spa & Wellness is currently unavailable for appointments."))

    item = next(
        (
            row
            for row in catalog["items"]
            if row.name == service_item and row.selectable
        ),
        None,
    )
    if not item:
        frappe.throw(_("The selected Spa treatment is not available for appointment."))

    duration = cint(item.duration_minutes)
    end = add_to_date(start, minutes=duration, as_datetime=True)

    resource = _choose_resource(
        service_item,
        start,
        end,
        preferred_resource=preferred_resource,
        require_public_preference=require_public_preference,
        exclude_appointment=exclude_appointment,
    )

    rate = flt(item.rate)

    return frappe._dict(
        {
            "catalog": catalog,
            "item": item,
            "resource": resource,
            "start": start,
            "end": end,
            "estimated_total": rate,
            "settlement_mode": "Complimentary" if rate <= 0 else "Pay at Hotel",
        }
    )


def reject_duplicate_guest_appointment(email, phone, service_item, start, end, exclude=None):
    contact_filters = []
    if email:
        contact_filters.append(["email", "=", email])
    if phone:
        contact_filters.append(["phone", "=", phone])

    if not contact_filters:
        return

    filters = [
        ["RhoGuest Spa Appointment", "service_item", "=", service_item],
        ["RhoGuest Spa Appointment", "status", "in", list(ACTIVE_STATUSES)],
        ["RhoGuest Spa Appointment", "appointment_start", "<", end],
        ["RhoGuest Spa Appointment", "appointment_end", ">", start],
    ]
    if exclude:
        filters.append(["RhoGuest Spa Appointment", "name", "!=", exclude])

    rows = frappe.get_all(
        "RhoGuest Spa Appointment",
        filters=filters,
        or_filters=contact_filters,
        pluck="name",
        limit_page_length=1,
    )
    if rows:
        frappe.throw(_("A matching active Spa appointment already exists for this guest and time."))

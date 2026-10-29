"""Server-authoritative Laundry catalog and request-line resolution."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from fnb_menu.guest_service import resolve_public_service_item
from fnb_menu.menu_service import get_company_brand, get_settings

LAUNDRY_CATEGORY_KEY = "laundry"


def get_public_laundry_catalog():
    """Return the published Laundry category and public service items."""

    settings = get_settings()

    if not cint(settings.get("guest_hub_enabled")):
        return frappe._dict({"available": 0, "category": None, "items": []})

    category = frappe.db.get_value(
        "RhoGuest Service Category",
        {"name": LAUNDRY_CATEGORY_KEY, "enabled": 1, "show_on_portal": 1},
        [
            "name",
            "category_name",
            "short_description",
            "operating_hours",
            "location",
            "allows_ordering",
            "allows_payment",
            "allows_charge_to_room",
        ],
        as_dict=True,
    )

    if not category or not cint(category.allows_ordering):
        return frappe._dict({"available": 0, "category": category, "items": []})

    company_currency = "NGN"
    if settings.company:
        company_currency = get_company_brand(settings.company).currency or "NGN"

    rows = frappe.get_all(
        "RhoGuest Service Item",
        filters={
            "service_category": LAUNDRY_CATEGORY_KEY,
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

        # Quote-only items may be displayed but cannot be submitted because
        # there is no authoritative numeric amount to snapshot.
        public_item.selectable = (
            public_item.pricing_mode != "Informational / Quote"
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


def parse_laundry_request_items(items):
    """Parse browser identifiers/quantities and ignore browser price metadata."""

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            frappe.throw(_("Invalid Laundry Request items."))

    if not isinstance(items, list) or not items:
        frappe.throw(_("Select at least one laundry item."))
    if len(items) > 50:
        frappe.throw(_("Too many Laundry Request lines."))

    parsed = []
    for row in items:
        if not isinstance(row, dict):
            frappe.throw(_("Invalid Laundry Request line."))

        service_item = (row.get("service_item") or "").strip()
        qty = cint(row.get("qty") or 0)
        instruction = (row.get("special_instruction") or "").strip()[:500]

        if not service_item or qty < 1 or qty > 50:
            frappe.throw(_("Invalid laundry item or quantity."))

        # Security boundary: only these three guest-controlled values survive.
        parsed.append(
            {
                "service_item": service_item,
                "qty": qty,
                "special_instruction": instruction,
            }
        )

    return parsed


def resolve_laundry_request_lines(items):
    """Re-resolve current published Laundry items and prices on the server."""

    catalog = get_public_laundry_catalog()
    if not catalog.available:
        frappe.throw(_("Laundry service is currently unavailable."))

    public_by_name = {
        row.name: row
        for row in catalog["items"]
        if row.selectable
    }

    resolved = []
    currency = None

    for submitted in parse_laundry_request_items(items):
        public_item = public_by_name.get(submitted["service_item"])
        if not public_item:
            frappe.throw(
                _("A selected laundry item is not currently available for requests.")
            )

        if currency and public_item.currency != currency:
            frappe.throw(_("Selected laundry items use different currencies."))
        currency = public_item.currency

        resolved.append(
            {
                "service_item": public_item.name,
                "service_name": public_item.service_name,
                "service_key": public_item.service_key,
                "qty": submitted["qty"],
                "pricing_mode": public_item.pricing_mode,
                "rate": public_item.rate,
                "currency": public_item.currency,
                "amount": public_item.rate * submitted["qty"],
                "special_instruction": submitted["special_instruction"],
                "allow_charge_to_room": cint(public_item.allow_charge_to_room),
            }
        )

    return frappe._dict(
        {
            "catalog": catalog,
            "lines": resolved,
            "currency": currency or catalog.currency,
        }
    )


def validate_requested_pickup(value):
    """Normalize an optional requested pickup time and reject past values."""

    if not value:
        return None

    requested = get_datetime(value)
    if requested < now_datetime():
        frappe.throw(_("Requested Pickup Time cannot be in the past."))
    return requested

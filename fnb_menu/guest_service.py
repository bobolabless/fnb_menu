"""Public read-only service catalog for the RhoGuest Guest Services Hub.

The hub deliberately exposes configuration data only. Operational transactions
such as laundry jobs, reservations, transport requests and housekeeping tasks
must be implemented through dedicated, authenticated/server-validated workflow
services before a public action is added to the UI.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint, flt

from fnb_menu.menu_service import get_company_brand, get_settings, item_price
from fnb_menu.routing import get_public_menu_route


def get_public_guest_hub():
    """Return brand, settings and the public-safe guest-service catalog."""

    settings = get_settings()
    brand = (
        get_company_brand(settings.company)
        if settings.company
        else frappe._dict(
            {
                "hotel_name": "Hotel",
                "logo": None,
                "currency": "NGN",
            }
        )
    )

    return frappe._dict(
        {
            "enabled": cint(settings.get("guest_hub_enabled")),
            "title": settings.get("guest_hub_title") or "Guest Services",
            "subtitle": (
                settings.get("guest_hub_subtitle")
                or "Everything you need during your stay"
            ),
            "show_items": cint(settings.get("show_service_items_on_hub")),
            "brand": brand,
            "services": (
                get_public_service_catalog(settings=settings, brand=brand)
                if cint(settings.get("guest_hub_enabled"))
                else []
            ),
        }
    )


def get_public_service_catalog(settings=None, brand=None):
    """Return only categories explicitly enabled and published for guests."""

    settings = settings or get_settings()
    brand = brand or (
        get_company_brand(settings.company)
        if settings.company
        else frappe._dict({"currency": "NGN"})
    )

    categories = frappe.get_all(
        "RhoGuest Service Category",
        filters={
            "enabled": 1,
            "show_on_portal": 1,
        },
        fields=[
            "name",
            "category_name",
            "service_key",
            "service_type",
            "workflow_type",
            "icon",
            "image",
            "short_description",
            "sort_order",
            "operating_hours",
            "location",
            "requires_guest_identification",
            "requires_room_number",
            "allows_reservation",
            "allows_ordering",
            "allows_payment",
            "allows_charge_to_room",
        ],
        order_by="sort_order asc, category_name asc",
        limit_page_length=200,
    )

    if not categories:
        return []

    category_names = [row.name for row in categories]
    by_category = {name: [] for name in category_names}

    if cint(settings.get("show_service_items_on_hub")):
        items = frappe.get_all(
            "RhoGuest Service Item",
            filters={
                "service_category": ["in", category_names],
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
            limit_page_length=2000,
        )

        for row in items:
            public_item = resolve_public_service_item(
                row,
                settings=settings,
                company_currency=brand.get("currency") or "NGN",
            )
            if public_item:
                by_category.setdefault(row.service_category, []).append(public_item)

    output = []
    menu_route = get_public_menu_route()

    for category in categories:
        action_url = None
        action_label = None

        # Existing F&B continues to own ordering/payment/KOT. The hub merely
        # links to the already-tested menu route instead of reimplementing it.
        if category.service_key == "food-beverage":
            action_url = menu_route
            action_label = "View Food & Drinks"
        elif category.service_key == "laundry":
            # Laundry has its own server-validated transaction workflow. The
            # action remains publication-gated by the category above.
            action_url = "/rhoguest-laundry"
            action_label = "Request Laundry Service"

        output.append(
            frappe._dict(
                {
                    **category,
                    "items": by_category.get(category.name, []),
                    "action_url": action_url,
                    "action_label": action_label,
                }
            )
        )

    return output


def resolve_public_service_item(row, settings, company_currency):
    """Resolve one service item into a public-safe, display-only payload."""

    mode = row.pricing_mode or "Free"
    rate = None
    currency = row.currency or company_currency
    price_label = None

    if mode == "Free":
        rate = 0
        price_label = "Complimentary"

    elif mode == "Fixed Price":
        rate = flt(row.fixed_price)
        if rate <= 0:
            return None

    elif mode == "ERPNext Item Price":
        if not row.erpnext_item:
            return None

        item = frappe.db.get_value(
            "Item",
            row.erpnext_item,
            ["item_code", "disabled", "is_sales_item"],
            as_dict=True,
        )
        if not item or cint(item.disabled) or not cint(item.is_sales_item):
            return None

        resolved = item_price(
            item.item_code,
            settings.default_selling_price_list,
        )
        if not resolved or flt(resolved.rate) <= 0:
            # Never publish a stale/fabricated ERPNext-backed price.
            return None

        rate = flt(resolved.rate)
        currency = resolved.currency or company_currency

    elif mode == "Informational / Quote":
        price_label = "Price on request"

    else:
        return None

    return frappe._dict(
        {
            "name": row.name,
            "service_name": row.service_name,
            "service_key": row.service_key,
            "description": row.description or "",
            "image": row.image,
            "availability_note": row.availability_note or "",
            "pricing_mode": mode,
            "rate": rate,
            "currency": currency,
            "price_label": price_label,
            "allow_charge_to_room": cint(row.allow_charge_to_room),
            "requires_reservation": cint(row.requires_reservation),
            "duration_minutes": cint(row.duration_minutes),
            "fulfilment_time_minutes": cint(row.fulfilment_time_minutes),
            "capacity": cint(row.capacity),
            "location": row.location or "",
        }
    )

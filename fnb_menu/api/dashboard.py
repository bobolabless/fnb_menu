"""Operational data service for the RhoGuest Desk dashboard."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

from fnb_menu.routing import get_public_menu_route


def _count(doctype, filters=None):
    """Return a DocType count while keeping dashboard code readable."""

    return frappe.db.count(doctype, filters=filters or {})


@frappe.whitelist()
def get_dashboard_data():
    """Return permission-aware operational KPIs for authenticated Desk users."""

    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    # Reading the dashboard is intentionally aligned with the operational
    # Laundry queue. Users without read permission must not receive its details.
    if not frappe.has_permission("RhoGuest Laundry Request", "read"):
        frappe.throw(
            _("You do not have permission to view the RhoGuest Dashboard."),
            frappe.PermissionError,
        )

    today = nowdate()
    tomorrow = add_days(today, 1)

    delivered_today = len(
        frappe.get_all(
            "RhoGuest Laundry Request",
            filters=[
                ["RhoGuest Laundry Request", "status", "=", "Delivered"],
                ["RhoGuest Laundry Request", "delivered_at", ">=", today],
                ["RhoGuest Laundry Request", "delivered_at", "<", tomorrow],
            ],
            pluck="name",
            limit_page_length=5000,
        )
    )

    recent_laundry = frappe.get_all(
        "RhoGuest Laundry Request",
        fields=[
            "name",
            "guest_name",
            "room_number",
            "status",
            "billing_status",
            "estimated_total",
            "currency",
            "requested_pickup_at",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=10,
    )

    published_services = frappe.get_all(
        "RhoGuest Service Category",
        filters={"enabled": 1, "show_on_portal": 1},
        fields=["name", "category_name", "service_type"],
        order_by="sort_order asc, category_name asc",
        limit_page_length=100,
    )

    settings = frappe.get_single("FNB Menu Settings")

    return {
        "generated_at": frappe.utils.now(),
        "hub_enabled": int(settings.get("guest_hub_enabled") or 0),
        "public_menu_route": get_public_menu_route(),
        "cards": {
            "published_services": len(published_services),
            "service_items": _count(
                "RhoGuest Service Item",
                {"enabled": 1, "available_to_guests": 1},
            ),
            "fnb_active": _count(
                "FNB Self Order",
                {"status": ["in", ["Sent to Kitchen", "Preparing", "Ready"]]},
            ),
            "fnb_pending_payment": _count(
                "FNB Self Order",
                {"payment_status": "Pending"},
            ),
            "laundry_open": _count(
                "RhoGuest Laundry Request",
                {"status": ["not in", ["Delivered", "Cancelled"]]},
            ),
            "laundry_awaiting_pickup": _count(
                "RhoGuest Laundry Request",
                {"status": ["in", ["Submitted", "Pickup Scheduled"]]},
            ),
            "laundry_processing": _count(
                "RhoGuest Laundry Request",
                {"status": ["in", ["Collected", "Processing"]]},
            ),
            "laundry_ready": _count(
                "RhoGuest Laundry Request",
                {"status": ["in", ["Ready", "Out for Delivery"]]},
            ),
            "laundry_delivered_today": delivered_today,
            "pending_folio_posting": _count(
                "RhoGuest Laundry Request",
                {"billing_status": "Pending Folio Posting"},
            ),
        },
        "published_services": published_services,
        "recent_laundry": recent_laundry,
    }

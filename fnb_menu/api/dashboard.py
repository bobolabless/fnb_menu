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

    facility_today = frappe.get_all(
        "RhoGuest Facility Reservation",
        filters=[
            ["RhoGuest Facility Reservation", "reservation_start", ">=", today],
            ["RhoGuest Facility Reservation", "reservation_start", "<", tomorrow],
        ],
        fields=["name", "service_category", "status", "party_size"],
        limit_page_length=5000,
    )
    pool_today = sum(
        1 for row in facility_today
        if row.service_category == "swimming-pool"
        and row.status not in {"Cancelled", "No Show"}
    )
    gym_today = sum(
        1 for row in facility_today
        if row.service_category == "gym-fitness"
        and row.status not in {"Cancelled", "No Show"}
    )
    checked_in_facilities = sum(
        1 for row in facility_today if row.status == "Checked In"
    )

    recent_facilities = frappe.get_all(
        "RhoGuest Facility Reservation",
        fields=[
            "name",
            "service_category",
            "service_name",
            "guest_name",
            "room_number",
            "reservation_start",
            "party_size",
            "status",
        ],
        order_by="modified desc",
        limit_page_length=10,
    )

    spa_today = frappe.get_all(
        "RhoGuest Spa Appointment",
        filters=[
            ["RhoGuest Spa Appointment", "appointment_start", ">=", today],
            ["RhoGuest Spa Appointment", "appointment_start", "<", tomorrow],
        ],
        fields=["name", "status"],
        limit_page_length=5000,
    )
    spa_today_count = sum(
        1 for row in spa_today if row.status not in {"Cancelled", "No Show"}
    )
    spa_in_treatment = sum(
        1 for row in spa_today if row.status == "In Treatment"
    )

    recent_spa = frappe.get_all(
        "RhoGuest Spa Appointment",
        fields=[
            "name",
            "service_name",
            "resource_name",
            "guest_name",
            "room_number",
            "appointment_start",
            "status",
        ],
        order_by="modified desc",
        limit_page_length=10,
    )

    transport_today = frappe.get_all(
        "RhoGuest Transport Booking",
        filters=[
            ["RhoGuest Transport Booking", "scheduled_pickup_at", ">=", today],
            ["RhoGuest Transport Booking", "scheduled_pickup_at", "<", tomorrow],
        ],
        fields=["name", "status"],
        limit_page_length=5000,
    )
    transport_today_count = sum(
        1 for row in transport_today if row.status not in {"Cancelled", "No Show"}
    )
    transport_in_transit = sum(
        1 for row in transport_today if row.status == "In Transit"
    )

    recent_transport = frappe.get_all(
        "RhoGuest Transport Booking",
        fields=[
            "name",
            "service_name",
            "guest_name",
            "room_number",
            "scheduled_pickup_at",
            "pickup_location",
            "dropoff_location",
            "vehicle_name",
            "driver_name",
            "status",
        ],
        order_by="modified desc",
        limit_page_length=10,
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

    settings = frappe.get_single("RhoGuest Menu Settings")

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
                "RhoGuest Self Order",
                {"status": ["in", ["Sent to Kitchen", "Preparing", "Ready"]]},
            ),
            "fnb_pending_payment": _count(
                "RhoGuest Self Order",
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
            "facility_upcoming": _count(
                "RhoGuest Facility Reservation",
                {"status": ["in", ["Requested", "Confirmed"]]},
            ),
            "pool_today": pool_today,
            "gym_today": gym_today,
            "facility_checked_in": checked_in_facilities,
            "spa_upcoming": _count(
                "RhoGuest Spa Appointment",
                {"status": ["in", ["Requested", "Confirmed"]]},
            ),
            "spa_today": spa_today_count,
            "spa_in_treatment": spa_in_treatment,
            "transport_upcoming": _count(
                "RhoGuest Transport Booking",
                {"status": ["in", ["Requested", "Confirmed"]]},
            ),
            "transport_unassigned": _count(
                "RhoGuest Transport Booking",
                {
                    "status": ["in", ["Requested", "Confirmed"]],
                    "vehicle": ["is", "not set"],
                },
            ),
            "transport_today": transport_today_count,
            "transport_in_transit": transport_in_transit,
        },
        "published_services": published_services,
        "recent_laundry": recent_laundry,
        "recent_facilities": recent_facilities,
        "recent_spa": recent_spa,
        "recent_transport": recent_transport,
    }

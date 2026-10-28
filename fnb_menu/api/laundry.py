"""Public and staff APIs for RhoGuest Laundry Request & Fulfilment."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from fnb_menu.laundry_service import (
    resolve_laundry_request_lines,
    validate_requested_pickup,
)
from fnb_menu.menu_service import get_settings

STATUS_TRANSITIONS = {
    "Submitted": {"Pickup Scheduled", "Collected", "Cancelled"},
    "Pickup Scheduled": {"Collected", "Cancelled"},
    "Collected": {"Processing", "Cancelled"},
    "Processing": {"Ready", "Cancelled"},
    "Ready": {"Out for Delivery", "Delivered", "Cancelled"},
    "Out for Delivery": {"Delivered", "Cancelled"},
    "Delivered": set(),
    "Cancelled": set(),
}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_request(
    guest_name,
    room_number,
    items,
    email=None,
    phone=None,
    requested_pickup_at=None,
    pickup_note=None,
    billing_preference="Pay at Hotel",
):
    """Create a public Laundry Request from server-validated catalog data."""

    settings = get_settings()
    guest_name = (guest_name or "").strip()[:140]
    room_number = (room_number or "").strip()[:30]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    pickup_note = (pickup_note or "").strip()[:1000]
    billing_preference = (billing_preference or "Pay at Hotel").strip()

    if not guest_name:
        frappe.throw(_("Guest Name is required."))
    if not room_number:
        frappe.throw(_("Room Number is required."))
    if not email and not phone:
        frappe.throw(_("Provide at least an email address or phone number."))
    if email and "@" not in email:
        frappe.throw(_("Enter a valid email address."))
    if billing_preference not in {"Pay at Hotel", "Charge to Room"}:
        frappe.throw(_("Invalid billing preference."))

    requested_pickup = validate_requested_pickup(requested_pickup_at)
    resolved = resolve_laundry_request_lines(items)

    if billing_preference == "Charge to Room":
        if not cint(resolved.catalog.category.allows_charge_to_room):
            frappe.throw(_("Laundry service is not configured for Charge to Room."))
        if any(not row["allow_charge_to_room"] for row in resolved.lines):
            frappe.throw(
                _("One or more selected laundry items cannot be charged to the room.")
            )

    request = frappe.get_doc(
        {
            "doctype": "RhoGuest Laundry Request",
            "guest_name": guest_name,
            "room_number": room_number,
            "email": email,
            "phone": phone,
            "requested_pickup_at": requested_pickup,
            "pickup_note": pickup_note,
            "status": "Submitted",
            "billing_preference": billing_preference,
            "billing_status": (
                "Pending Folio Posting"
                if billing_preference == "Charge to Room"
                else "Unbilled"
            ),
            "company": settings.company,
            "currency": resolved.currency,
            "items": [
                {
                    key: value
                    for key, value in row.items()
                    if key != "allow_charge_to_room"
                }
                for row in resolved.lines
            ],
        }
    )
    request.insert(ignore_permissions=True)

    return {
        "request": request.name,
        "token": request.public_token,
        "status": request.status,
        "billing_status": request.billing_status,
        "estimated_total": request.estimated_total,
        "currency": request.currency,
    }


@frappe.whitelist(allow_guest=True)
def get_request_status(request_name, token):
    """Return a minimal public status payload when the token matches."""

    request = frappe.db.get_value(
        "RhoGuest Laundry Request",
        {"name": request_name, "public_token": token},
        [
            "name",
            "status",
            "billing_preference",
            "billing_status",
            "estimated_total",
            "currency",
            "requested_pickup_at",
            "collected_at",
            "ready_at",
            "delivered_at",
            "creation",
        ],
        as_dict=True,
    )
    if not request:
        frappe.throw(_("Laundry Request not found."))
    return request


@frappe.whitelist(methods=["POST"])
def update_status(request_name, status):
    """Advance a request through the controlled Laundry fulfilment graph."""

    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    request = frappe.get_doc("RhoGuest Laundry Request", request_name)
    if not request.has_permission("write"):
        frappe.throw(
            _("You do not have permission to update this Laundry Request."),
            frappe.PermissionError,
        )

    status = (status or "").strip()
    if status not in STATUS_TRANSITIONS.get(request.status, set()):
        frappe.throw(
            _("Invalid Laundry status transition from {0} to {1}.").format(
                frappe.bold(request.status),
                frappe.bold(status),
            )
        )

    values = {"status": status}
    if status == "Collected" and not request.collected_at:
        values["collected_at"] = now_datetime()
    elif status == "Ready" and not request.ready_at:
        values["ready_at"] = now_datetime()
    elif status == "Delivered" and not request.delivered_at:
        values["delivered_at"] = now_datetime()
    elif status == "Cancelled" and request.billing_status not in {
        "Posted to Room",
        "Settled",
    }:
        values["billing_status"] = "Cancelled"

    request.db_set(values)
    return {
        "request": request.name,
        "status": status,
        "billing_status": values.get("billing_status", request.billing_status),
    }

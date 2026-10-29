"""Public and staff APIs for RhoGuest Pool/Gym reservations."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from fnb_menu.facility_service import (
    FACILITY_KEYS,
    reject_duplicate_guest_booking,
    resolve_facility_reservation,
)
from fnb_menu.menu_service import get_settings

STATUS_TRANSITIONS = {
    "Requested": {"Confirmed", "Cancelled"},
    "Confirmed": {"Checked In", "Cancelled", "No Show"},
    "Checked In": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
    "No Show": set(),
}


def _get_staff_reservation(reservation_name):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    reservation = frappe.get_doc("RhoGuest Facility Reservation", reservation_name)
    if not reservation.has_permission("write"):
        frappe.throw(
            _("You do not have permission to update this Facility Reservation."),
            frappe.PermissionError,
        )
    return reservation


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_reservation(
    category_key,
    service_item,
    guest_name,
    reservation_start,
    party_size=1,
    room_number=None,
    email=None,
    phone=None,
    guest_note=None,
):
    """Create one server-authoritative Pool/Gym reservation."""

    category_key = (category_key or "").strip()
    guest_name = (guest_name or "").strip()[:140]
    room_number = (room_number or "").strip()[:30]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    guest_note = (guest_note or "").strip()[:1000]

    if category_key not in FACILITY_KEYS:
        frappe.throw(_("Unsupported RhoGuest facility."))
    if not guest_name:
        frappe.throw(_("Guest Name is required."))
    if not email and not phone:
        frappe.throw(_("Provide at least an email address or phone number."))
    if email and "@" not in email:
        frappe.throw(_("Enter a valid email address."))

    resolved = resolve_facility_reservation(
        category_key=category_key,
        service_item=service_item,
        reservation_start=reservation_start,
        party_size=party_size,
    )

    if resolved.catalog.category.requires_room_number and not room_number:
        frappe.throw(_("Room Number is required for this facility."))

    reject_duplicate_guest_booking(
        email,
        phone,
        service_item,
        resolved.start,
        resolved.end,
    )

    settings = get_settings()
    item = resolved.item

    reservation = frappe.get_doc(
        {
            "doctype": "RhoGuest Facility Reservation",
            "guest_name": guest_name,
            "room_number": room_number,
            "email": email,
            "phone": phone,
            "service_category": category_key,
            "service_item": item.name,
            "service_name": item.service_name,
            "service_key": item.service_key,
            "reservation_start": resolved.start,
            "reservation_end": resolved.end,
            "party_size": resolved.party_size,
            "status": "Requested",
            "guest_note": guest_note,
            "pricing_mode": item.pricing_mode,
            "pricing_basis": resolved.pricing_basis,
            "rate": item.rate,
            "currency": item.currency,
            "estimated_total": resolved.estimated_total,
            "settlement_mode": resolved.settlement_mode,
            "company": settings.company,
            "location": item.location or resolved.catalog.category.location,
            "duration_minutes": item.duration_minutes,
            "capacity": item.capacity,
        }
    )
    reservation.insert(ignore_permissions=True)

    return {
        "reservation": reservation.name,
        "token": reservation.public_token,
        "status": reservation.status,
        "reservation_start": reservation.reservation_start,
        "reservation_end": reservation.reservation_end,
        "estimated_total": reservation.estimated_total,
        "currency": reservation.currency,
        "settlement_mode": reservation.settlement_mode,
    }


@frappe.whitelist(allow_guest=True)
def get_reservation_status(reservation_name, token):
    """Return a minimal public reservation status when the secret token matches."""

    row = frappe.db.get_value(
        "RhoGuest Facility Reservation",
        {
            "name": reservation_name,
            "public_token": token,
        },
        [
            "name",
            "service_category",
            "service_name",
            "reservation_start",
            "reservation_end",
            "party_size",
            "status",
            "location",
            "estimated_total",
            "currency",
            "settlement_mode",
            "creation",
        ],
        as_dict=True,
    )
    if not row:
        frappe.throw(_("Facility Reservation not found."))
    return row


@frappe.whitelist(methods=["POST"])
def update_status(reservation_name, status):
    """Advance a reservation through the controlled access state graph."""

    reservation = _get_staff_reservation(reservation_name)
    status = (status or "").strip()

    if status not in STATUS_TRANSITIONS.get(reservation.status, set()):
        frappe.throw(
            _("Invalid Facility Reservation transition from {0} to {1}.").format(
                frappe.bold(reservation.status),
                frappe.bold(status),
            )
        )

    values = {"status": status}
    now = now_datetime()
    user = frappe.session.user

    if status == "Confirmed":
        values.update({"confirmed_at": now, "confirmed_by": user})
    elif status == "Checked In":
        values.update({"checked_in_at": now, "checked_in_by": user})
    elif status == "Completed":
        values.update({"completed_at": now, "completed_by": user})

    reservation.db_set(values)
    return {"reservation": reservation.name, "status": status}


@frappe.whitelist(methods=["POST"])
def reschedule_reservation(reservation_name, reservation_start):
    """Move a Requested/Confirmed reservation after rechecking slot capacity."""

    reservation = _get_staff_reservation(reservation_name)
    if reservation.status not in {"Requested", "Confirmed"}:
        frappe.throw(_("Only Requested or Confirmed reservations can be rescheduled."))

    resolved = resolve_facility_reservation(
        category_key=reservation.service_category,
        service_item=reservation.service_item,
        reservation_start=reservation_start,
        party_size=reservation.party_size,
        exclude_reservation=reservation.name,
    )

    reservation.db_set(
        {
            "reservation_start": resolved.start,
            "reservation_end": resolved.end,
        }
    )
    return {
        "reservation": reservation.name,
        "reservation_start": resolved.start,
        "reservation_end": resolved.end,
    }


@frappe.whitelist(methods=["POST"])
def assign_reservation(reservation_name, user=None):
    """Assign or unassign an active facility reservation."""

    reservation = _get_staff_reservation(reservation_name)
    if reservation.status in {"Completed", "Cancelled", "No Show"}:
        frappe.throw(_("Terminal Facility Reservations cannot be reassigned."))

    user = (user or "").strip()
    if user:
        account = frappe.db.get_value(
            "User",
            user,
            ["enabled", "user_type"],
            as_dict=True,
        )
        if not account or not account.enabled or account.user_type != "System User":
            frappe.throw(_("Assign Facility Reservations only to an enabled System User."))

    reservation.db_set("assigned_to", user or None)
    return {"reservation": reservation.name, "assigned_to": user or None}

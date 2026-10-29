"""Public and staff APIs for RhoGuest Spa & Wellness appointments."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from fnb_menu.menu_service import get_settings
from fnb_menu.spa_service import (
    reject_duplicate_guest_appointment,
    resolve_spa_appointment,
)

STATUS_TRANSITIONS = {
    "Requested": {"Confirmed", "Cancelled"},
    "Confirmed": {"Checked In", "Cancelled", "No Show"},
    "Checked In": {"In Treatment"},
    "In Treatment": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
    "No Show": set(),
}


def _get_staff_appointment(appointment_name):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    appointment = frappe.get_doc("RhoGuest Spa Appointment", appointment_name)
    if not appointment.has_permission("write"):
        frappe.throw(
            _("You do not have permission to update this Spa Appointment."),
            frappe.PermissionError,
        )
    return appointment


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_appointment(
    service_item,
    guest_name,
    appointment_start,
    spa_resource=None,
    room_number=None,
    email=None,
    phone=None,
    guest_note=None,
):
    """Create one guest Spa appointment using server-resolved treatment data."""

    guest_name = (guest_name or "").strip()[:140]
    room_number = (room_number or "").strip()[:30]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    guest_note = (guest_note or "").strip()[:1000]
    spa_resource = (spa_resource or "").strip() or None

    if not guest_name:
        frappe.throw(_("Guest Name is required."))
    if not email and not phone:
        frappe.throw(_("Provide at least an email address or phone number."))
    if email and "@" not in email:
        frappe.throw(_("Enter a valid email address."))

    resolved = resolve_spa_appointment(
        service_item=service_item,
        appointment_start=appointment_start,
        preferred_resource=spa_resource,
        require_public_preference=bool(spa_resource),
    )

    if resolved.catalog.category.requires_room_number and not room_number:
        frappe.throw(_("Room Number is required for Spa appointments."))

    reject_duplicate_guest_appointment(
        email,
        phone,
        service_item,
        resolved.start,
        resolved.end,
    )

    settings = get_settings()
    item = resolved.item
    resource = resolved.resource

    appointment = frappe.get_doc(
        {
            "doctype": "RhoGuest Spa Appointment",
            "guest_name": guest_name,
            "room_number": room_number,
            "email": email,
            "phone": phone,
            "service_item": item.name,
            "service_name": item.service_name,
            "service_key": item.service_key,
            "spa_resource": resource.name,
            "resource_name": resource.resource_name,
            "appointment_start": resolved.start,
            "appointment_end": resolved.end,
            "status": "Requested",
            "guest_note": guest_note,
            "pricing_mode": item.pricing_mode,
            "rate": item.rate,
            "currency": item.currency,
            "estimated_total": resolved.estimated_total,
            "settlement_mode": resolved.settlement_mode,
            "company": settings.company,
            "location": resource.location or item.location or resolved.catalog.category.location,
            "duration_minutes": item.duration_minutes,
        }
    )
    appointment.insert(ignore_permissions=True)

    return {
        "appointment": appointment.name,
        "token": appointment.public_token,
        "status": appointment.status,
        "resource": appointment.spa_resource,
        "resource_name": appointment.resource_name,
        "appointment_start": appointment.appointment_start,
        "appointment_end": appointment.appointment_end,
        "estimated_total": appointment.estimated_total,
        "currency": appointment.currency,
        "settlement_mode": appointment.settlement_mode,
    }


@frappe.whitelist(allow_guest=True)
def get_appointment_status(appointment_name, token):
    row = frappe.db.get_value(
        "RhoGuest Spa Appointment",
        {"name": appointment_name, "public_token": token},
        [
            "name",
            "service_name",
            "resource_name",
            "appointment_start",
            "appointment_end",
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
        frappe.throw(_("Spa Appointment not found."))
    return row


@frappe.whitelist(methods=["POST"])
def update_status(appointment_name, status):
    appointment = _get_staff_appointment(appointment_name)
    status = (status or "").strip()

    if status not in STATUS_TRANSITIONS.get(appointment.status, set()):
        frappe.throw(
            _("Invalid Spa Appointment transition from {0} to {1}.").format(
                frappe.bold(appointment.status),
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
    elif status == "In Treatment":
        values.update({"treatment_started_at": now, "treatment_started_by": user})
    elif status == "Completed":
        values.update({"completed_at": now, "completed_by": user})

    appointment.db_set(values)
    return {"appointment": appointment.name, "status": status}


@frappe.whitelist(methods=["POST"])
def reschedule_appointment(appointment_name, appointment_start, spa_resource=None):
    """Reschedule/reassign a Requested or Confirmed appointment safely."""

    appointment = _get_staff_appointment(appointment_name)
    if appointment.status not in {"Requested", "Confirmed"}:
        frappe.throw(_("Only Requested or Confirmed Spa Appointments can be rescheduled."))

    preferred = (spa_resource or "").strip() or appointment.spa_resource

    resolved = resolve_spa_appointment(
        service_item=appointment.service_item,
        appointment_start=appointment_start,
        preferred_resource=preferred,
        require_public_preference=False,
        exclude_appointment=appointment.name,
    )

    appointment.db_set(
        {
            "spa_resource": resolved.resource.name,
            "resource_name": resolved.resource.resource_name,
            "appointment_start": resolved.start,
            "appointment_end": resolved.end,
            "location": resolved.resource.location
            or appointment.location,
        }
    )

    return {
        "appointment": appointment.name,
        "spa_resource": resolved.resource.name,
        "resource_name": resolved.resource.resource_name,
        "appointment_start": resolved.start,
        "appointment_end": resolved.end,
    }

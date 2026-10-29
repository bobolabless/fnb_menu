"""Public and staff APIs for RhoGuest Transport bookings."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from fnb_menu.menu_service import get_settings
from fnb_menu.transport_service import (
    reject_duplicate_guest_booking,
    resolve_transport_booking,
    validate_and_lock_resources,
    validate_pickup_time,
    lock_booking,
)

STATUS_TRANSITIONS = {
    "Requested": {"Confirmed", "Cancelled"},
    "Confirmed": {"Dispatched", "Cancelled", "No Show"},
    "Dispatched": {"Arrived at Pickup"},
    "Arrived at Pickup": {"In Transit", "No Show"},
    "In Transit": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
    "No Show": set(),
}


def _get_staff_booking(booking_name):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    booking = frappe.get_doc("RhoGuest Transport Booking", booking_name)
    if not booking.has_permission("write"):
        frappe.throw(
            _("You do not have permission to update this Transport Booking."),
            frappe.PermissionError,
        )
    return booking


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_booking(
    service_item,
    guest_name,
    scheduled_pickup_at,
    pickup_location,
    dropoff_location,
    passenger_count=1,
    luggage_count=0,
    room_number=None,
    email=None,
    phone=None,
    flight_number=None,
    trip_note=None,
):
    """Create one public Transport request with server-authoritative pricing."""

    guest_name = (guest_name or "").strip()[:140]
    room_number = (room_number or "").strip()[:30]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    pickup_location = (pickup_location or "").strip()[:240]
    dropoff_location = (dropoff_location or "").strip()[:240]
    flight_number = (flight_number or "").strip()[:40]
    trip_note = (trip_note or "").strip()[:1000]

    if not guest_name:
        frappe.throw(_("Guest Name is required."))
    if not email and not phone:
        frappe.throw(_("Provide at least an email address or phone number."))
    if email and "@" not in email:
        frappe.throw(_("Enter a valid email address."))
    if not pickup_location:
        frappe.throw(_("Pickup Location is required."))
    if not dropoff_location:
        frappe.throw(_("Drop-off Location is required."))

    resolved = resolve_transport_booking(
        service_item=service_item,
        scheduled_pickup_at=scheduled_pickup_at,
        passenger_count=passenger_count,
    )

    if resolved.catalog.category.requires_room_number and not room_number:
        frappe.throw(_("Room Number is required for Transport bookings."))

    reject_duplicate_guest_booking(
        email,
        phone,
        service_item,
        resolved.start,
        resolved.end,
    )

    settings = get_settings()
    item = resolved.item

    booking = frappe.get_doc(
        {
            "doctype": "RhoGuest Transport Booking",
            "guest_name": guest_name,
            "room_number": room_number,
            "email": email,
            "phone": phone,
            "passenger_count": resolved.passenger_count,
            "luggage_count": luggage_count,
            "flight_number": flight_number,
            "service_item": item.name,
            "service_name": item.service_name,
            "service_key": item.service_key,
            "pickup_location": pickup_location,
            "dropoff_location": dropoff_location,
            "scheduled_pickup_at": resolved.start,
            "estimated_dropoff_at": resolved.end,
            "status": "Requested",
            "trip_note": trip_note,
            "pricing_mode": item.pricing_mode,
            "pricing_basis": resolved.pricing_basis,
            "rate": item.rate,
            "currency": item.currency,
            "estimated_total": resolved.estimated_total,
            "settlement_mode": resolved.settlement_mode,
            "company": settings.company,
            "duration_minutes": item.duration_minutes,
        }
    )
    booking.insert(ignore_permissions=True)

    return {
        "booking": booking.name,
        "token": booking.public_token,
        "status": booking.status,
        "scheduled_pickup_at": booking.scheduled_pickup_at,
        "estimated_dropoff_at": booking.estimated_dropoff_at,
        "estimated_total": booking.estimated_total,
        "currency": booking.currency,
        "settlement_mode": booking.settlement_mode,
    }


@frappe.whitelist(allow_guest=True)
def get_booking_status(booking_name, token):
    """Return token-protected guest tracking information."""

    row = frappe.db.get_value(
        "RhoGuest Transport Booking",
        {"name": booking_name, "public_token": token},
        [
            "name",
            "service_name",
            "pickup_location",
            "dropoff_location",
            "scheduled_pickup_at",
            "estimated_dropoff_at",
            "status",
            "vehicle_name",
            "vehicle_registration",
            "driver_name",
            "estimated_total",
            "currency",
            "settlement_mode",
            "creation",
        ],
        as_dict=True,
    )
    if not row:
        frappe.throw(_("Transport Booking not found."))
    return row


@frappe.whitelist(methods=["POST"])
def assign_resources(booking_name, vehicle, driver):
    """Assign or replace the vehicle/driver on a Requested/Confirmed booking."""

    lock_booking(booking_name)
    booking = _get_staff_booking(booking_name)

    if booking.status not in {"Requested", "Confirmed"}:
        frappe.throw(_("Vehicle/Driver assignment is allowed only for Requested or Confirmed bookings."))

    resources = validate_and_lock_resources(
        vehicle=vehicle,
        driver=driver,
        start=get_datetime(booking.scheduled_pickup_at),
        end=get_datetime(booking.estimated_dropoff_at),
        passenger_count=booking.passenger_count,
        luggage_count=booking.luggage_count,
        exclude_booking=booking.name,
    )

    booking.db_set(
        {
            "vehicle": resources.vehicle.name,
            "vehicle_name": resources.vehicle.vehicle_name,
            "vehicle_registration": resources.vehicle.registration_number,
            "driver": resources.driver.name,
            "driver_name": resources.driver.driver_name,
            "assigned_at": now_datetime(),
            "assigned_by": frappe.session.user,
        }
    )

    return {
        "booking": booking.name,
        "vehicle": resources.vehicle.name,
        "vehicle_name": resources.vehicle.vehicle_name,
        "driver": resources.driver.name,
        "driver_name": resources.driver.driver_name,
    }


@frappe.whitelist(methods=["POST"])
def reschedule_booking(booking_name, scheduled_pickup_at):
    """Move a Requested/Confirmed booking while preserving its duration."""

    lock_booking(booking_name)
    booking = _get_staff_booking(booking_name)

    if booking.status not in {"Requested", "Confirmed"}:
        frappe.throw(_("Only Requested or Confirmed Transport bookings can be rescheduled."))

    start = validate_pickup_time(scheduled_pickup_at)
    end = add_to_date(start, minutes=booking.duration_minutes, as_datetime=True)

    reject_duplicate_guest_booking(
        booking.email,
        booking.phone,
        booking.service_item,
        start,
        end,
        exclude=booking.name,
    )

    if booking.vehicle and booking.driver:
        validate_and_lock_resources(
            vehicle=booking.vehicle,
            driver=booking.driver,
            start=start,
            end=end,
            passenger_count=booking.passenger_count,
            luggage_count=booking.luggage_count,
            exclude_booking=booking.name,
        )

    booking.db_set(
        {
            "scheduled_pickup_at": start,
            "estimated_dropoff_at": end,
        }
    )

    return {
        "booking": booking.name,
        "scheduled_pickup_at": start,
        "estimated_dropoff_at": end,
    }


@frappe.whitelist(methods=["POST"])
def update_status(booking_name, status):
    """Advance one booking through the controlled dispatch state graph."""

    lock_booking(booking_name)
    booking = _get_staff_booking(booking_name)
    status = (status or "").strip()

    if status not in STATUS_TRANSITIONS.get(booking.status, set()):
        frappe.throw(
            _("Invalid Transport Booking transition from {0} to {1}.").format(
                frappe.bold(booking.status),
                frappe.bold(status),
            )
        )

    if status == "Confirmed":
        if not booking.vehicle or not booking.driver:
            frappe.throw(_("Assign both a Transport Vehicle and Driver before confirming the booking."))

        validate_and_lock_resources(
            vehicle=booking.vehicle,
            driver=booking.driver,
            start=get_datetime(booking.scheduled_pickup_at),
            end=get_datetime(booking.estimated_dropoff_at),
            passenger_count=booking.passenger_count,
            luggage_count=booking.luggage_count,
            exclude_booking=booking.name,
        )

    values = {"status": status}
    now = now_datetime()
    user = frappe.session.user

    if status == "Confirmed":
        values.update({"confirmed_at": now, "confirmed_by": user})
    elif status == "Dispatched":
        values.update({"dispatched_at": now, "dispatched_by": user})
    elif status == "Arrived at Pickup":
        values.update({"arrived_at_pickup_at": now, "arrived_at_pickup_by": user})
    elif status == "In Transit":
        values.update({"trip_started_at": now, "trip_started_by": user})
    elif status == "Completed":
        values.update({"completed_at": now, "completed_by": user})

    booking.db_set(values)
    return {"booking": booking.name, "status": status}

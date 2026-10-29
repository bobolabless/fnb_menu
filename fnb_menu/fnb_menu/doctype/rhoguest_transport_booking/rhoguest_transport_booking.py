"""Operational Transport booking record for RhoGuest."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime

SNAPSHOT_FIELDS = (
    "service_item",
    "service_name",
    "service_key",
    "pricing_mode",
    "pricing_basis",
    "rate",
    "currency",
    "estimated_total",
    "settlement_mode",
    "company",
    "duration_minutes",
)


class RhoGuestTransportBooking(Document):
    """One guest transport request with a server-authoritative price snapshot."""

    def before_insert(self):
        if not self.public_token:
            self.public_token = secrets.token_urlsafe(24)

    def validate(self):
        self.guest_name = (self.guest_name or "").strip()
        self.room_number = (self.room_number or "").strip()
        self.email = (self.email or "").strip()
        self.phone = (self.phone or "").strip()
        self.pickup_location = (self.pickup_location or "").strip()
        self.dropoff_location = (self.dropoff_location or "").strip()
        self.flight_number = (self.flight_number or "").strip().upper()
        self.trip_note = (self.trip_note or "").strip()[:1000]

        if not self.guest_name:
            frappe.throw(_("Guest Name is required."))
        if not self.email and not self.phone:
            frappe.throw(_("Provide at least an email address or phone number."))
        if self.email and "@" not in self.email:
            frappe.throw(_("Enter a valid email address."))
        if not self.pickup_location:
            frappe.throw(_("Pickup Location is required."))
        if not self.dropoff_location:
            frappe.throw(_("Drop-off Location is required."))

        if cint(self.passenger_count) < 1 or cint(self.passenger_count) > 50:
            frappe.throw(_("Passengers must be between 1 and 50."))
        if cint(self.luggage_count) < 0 or cint(self.luggage_count) > 100:
            frappe.throw(_("Luggage Pieces must be between 0 and 100."))

        start = get_datetime(self.scheduled_pickup_at)
        end = get_datetime(self.estimated_dropoff_at)
        if not start or not end or end <= start:
            frappe.throw(_("Estimated Drop-off must be after Scheduled Pickup."))

        basis = self.pricing_basis or "Per Reservation"
        if basis not in {"Per Reservation", "Per Person"}:
            frappe.throw(_("Invalid Pricing Basis."))

        expected = flt(self.rate)
        if basis == "Per Person":
            expected *= cint(self.passenger_count)

        self.estimated_total = expected
        self.settlement_mode = "Complimentary" if expected <= 0 else "Pay at Hotel"

        self._validate_snapshot_immutability()

    def _validate_snapshot_immutability(self):
        if self.is_new():
            return

        before = self.get_doc_before_save()
        if not before:
            return

        for fieldname in SNAPSHOT_FIELDS:
            if str(before.get(fieldname) or "") != str(self.get(fieldname) or ""):
                frappe.throw(
                    _("Field {0} is server-managed and cannot be edited directly.").format(
                        frappe.bold(fieldname)
                    )
                )

"""Pool/Gym reservation record for RhoGuest."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime

FACILITY_KEYS = {"swimming-pool", "gym-fitness"}

SNAPSHOT_FIELDS = (
    "service_category",
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
    "location",
    "duration_minutes",
    "capacity",
)


class RhoGuestFacilityReservation(Document):
    """Guest reservation/access record for Pool and Gym services."""

    def before_insert(self):
        if not self.public_token:
            self.public_token = secrets.token_urlsafe(24)

    def validate(self):
        self.guest_name = (self.guest_name or "").strip()
        self.room_number = (self.room_number or "").strip()
        self.email = (self.email or "").strip()
        self.phone = (self.phone or "").strip()
        self.guest_note = (self.guest_note or "").strip()[:1000]

        if not self.guest_name:
            frappe.throw(_("Guest Name is required."))
        if not self.email and not self.phone:
            frappe.throw(_("Provide at least an email address or phone number."))
        if self.email and "@" not in self.email:
            frappe.throw(_("Enter a valid email address."))

        if self.service_category not in FACILITY_KEYS:
            frappe.throw(_("Facility reservations are currently limited to Pool and Gym."))

        if not self.service_item or not self.service_name or not self.service_key:
            frappe.throw(_("A valid Facility Service is required."))

        if cint(self.party_size) < 1 or cint(self.party_size) > 50:
            frappe.throw(_("Party Size must be between 1 and 50."))

        start = get_datetime(self.reservation_start)
        end = get_datetime(self.reservation_end)
        if not start or not end or end <= start:
            frappe.throw(_("Reservation End must be after Reservation Start."))

        basis = self.pricing_basis or "Per Reservation"
        if basis not in {"Per Reservation", "Per Person"}:
            frappe.throw(_("Invalid Pricing Basis."))

        expected = flt(self.rate)
        if basis == "Per Person":
            expected *= cint(self.party_size)
        self.estimated_total = expected
        self.settlement_mode = "Complimentary" if expected <= 0 else "Pay at Hotel"

        self._validate_snapshot_immutability()

    def _validate_snapshot_immutability(self):
        """Block normal edits to server-resolved commercial snapshot fields."""

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

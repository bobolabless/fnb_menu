"""Operational Spa & Wellness appointment record."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime

SNAPSHOT_FIELDS = (
    "service_item",
    "service_name",
    "service_key",
    "pricing_mode",
    "rate",
    "currency",
    "estimated_total",
    "settlement_mode",
    "company",
    "location",
    "duration_minutes",
)


class RhoGuestSpaAppointment(Document):
    """One guest Spa appointment with server-authoritative commercial snapshot."""

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

        if not self.service_item or not self.service_name or not self.service_key:
            frappe.throw(_("A valid Spa Service is required."))
        if not self.spa_resource or not self.resource_name:
            frappe.throw(_("A valid Spa Resource is required."))

        start = get_datetime(self.appointment_start)
        end = get_datetime(self.appointment_end)
        if not start or not end or end <= start:
            frappe.throw(_("Appointment End must be after Appointment Start."))

        expected = flt(self.rate)
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

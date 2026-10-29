"""Transport vehicle master for RhoGuest dispatch operations."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalise_key(value):
    key = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", key)


class RhoGuestTransportVehicle(Document):
    """A hotel-controlled vehicle that can be assigned to guest transport."""

    def validate(self):
        self.vehicle_name = (self.vehicle_name or "").strip()
        self.vehicle_key = _normalise_key(self.vehicle_key)
        self.registration_number = (self.registration_number or "").strip().upper()
        self.make_model = (self.make_model or "").strip()
        self.color = (self.color or "").strip()
        self.location = (self.location or "").strip()

        if not self.vehicle_name:
            frappe.throw(_("Vehicle Name is required."))

        if not self.vehicle_key or not _KEY_RE.fullmatch(self.vehicle_key):
            frappe.throw(_("Vehicle Key must contain lower-case letters, numbers and single hyphens only."))

        if not self.registration_number:
            frappe.throw(_("Registration Number is required."))

        if cint(self.passenger_capacity) < 1:
            frappe.throw(_("Passenger Capacity must be at least 1."))

        if cint(self.luggage_capacity) < 0:
            frappe.throw(_("Luggage Capacity cannot be negative."))

"""Transport driver master for RhoGuest dispatch operations."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalise_key(value):
    key = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", key)


class RhoGuestTransportDriver(Document):
    """A driver that may be assigned to one RhoGuest Transport Booking."""

    def validate(self):
        self.driver_name = (self.driver_name or "").strip()
        self.driver_key = _normalise_key(self.driver_key)
        self.phone = (self.phone or "").strip()
        self.license_number = (self.license_number or "").strip().upper()

        if not self.driver_name:
            frappe.throw(_("Driver Name is required."))

        if not self.driver_key or not _KEY_RE.fullmatch(self.driver_key):
            frappe.throw(_("Driver Key must contain lower-case letters, numbers and single hyphens only."))

        if not self.license_number:
            frappe.throw(_("Licence Number is required."))

        if not self.license_expiry:
            frappe.throw(_("Licence Expiry is required."))

        if self.user:
            account = frappe.db.get_value(
                "User",
                self.user,
                ["enabled", "user_type"],
                as_dict=True,
            )
            if not account or not cint(account.enabled) or account.user_type != "System User":
                frappe.throw(_("Transport Driver System User must be an enabled System User."))

        if self.employee and not frappe.db.exists("Employee", self.employee):
            frappe.throw(_("Linked Employee does not exist."))

        # Expired licences cannot remain enabled for dispatch.
        if cint(self.enabled) and getdate(self.license_expiry) < getdate():
            frappe.throw(_("An enabled Transport Driver cannot have an expired driving licence."))

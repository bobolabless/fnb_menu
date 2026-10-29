"""Generic RhoGuest service-item master.

Service Items describe guest-visible choices beneath a Service Category. They
are deliberately not operational transactions: Laundry jobs, F&B orders,
reservations and other fulfilment records will link back to these masters.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

_SERVICE_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_service_item_key(value: str | None) -> str:
    """Return a predictable lower-case, hyphenated item key."""

    key = (value or "").strip().lower()
    key = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    return re.sub(r"-{2,}", "-", key)


class RhoGuestServiceItem(Document):
    """Configuration master for a guest-selectable or informational service."""

    def validate(self):
        self.service_name = (self.service_name or "").strip()
        self.service_key = normalize_service_item_key(self.service_key)

        if not self.service_name:
            frappe.throw(_("Service Name is required."))

        if not self.service_key or not _SERVICE_KEY_RE.fullmatch(self.service_key):
            frappe.throw(
                _(
                    "Service Item Key must contain lower-case letters, numbers "
                    "and single hyphens only."
                )
            )

        self._validate_numeric_fields()
        self._validate_category_capabilities()
        self._validate_pricing()
        self._validate_unique_category_key()

        # A disabled item may remain configured for later use, but it must not
        # continue to advertise itself as guest-available.
        if not self.enabled:
            self.available_to_guests = 0

    def _validate_numeric_fields(self):
        """Reject negative operational quantities and lead times."""

        if cint(self.sort_order) < 0:
            frappe.throw(_("Display Order cannot be negative."))
        if cint(self.duration_minutes) < 0:
            frappe.throw(_("Duration cannot be negative."))
        if cint(self.fulfilment_time_minutes) < 0:
            frappe.throw(_("Preparation / Fulfilment Time cannot be negative."))
        if cint(self.capacity) < 0:
            frappe.throw(_("Capacity cannot be negative."))
        if flt(self.fixed_price) < 0:
            frappe.throw(_("Fixed Price cannot be negative."))

    def _validate_category_capabilities(self):
        """Keep item-level actions within the capabilities of its category."""

        if not self.service_category:
            return

        category = frappe.db.get_value(
            "RhoGuest Service Category",
            self.service_category,
            ["allows_reservation", "allows_charge_to_room"],
            as_dict=True,
        )
        if not category:
            return

        if self.requires_reservation and not category.allows_reservation:
            frappe.throw(
                _(
                    "This Service Category does not allow reservations. Enable "
                    "Allows Reservation on the category first."
                )
            )

        if self.allow_charge_to_room and not category.allows_charge_to_room:
            frappe.throw(
                _(
                    "This Service Category does not allow Charge to Room. Enable "
                    "that capability on the category first."
                )
            )

    def _validate_pricing(self):
        """Validate pricing configuration without trusting browser-side values."""

        mode = self.pricing_mode or "Free"
        self.pricing_basis = self.pricing_basis or "Per Reservation"

        if self.pricing_basis not in {"Per Reservation", "Per Person"}:
            frappe.throw(_("Invalid Pricing Basis."))

        if mode == "Free":
            self.fixed_price = 0
            return

        if mode == "Fixed Price":
            if flt(self.fixed_price) <= 0:
                frappe.throw(_("Fixed Price must be greater than zero."))
            if not self.currency:
                frappe.throw(_("Currency is required for a Fixed Price service."))
            return

        if mode == "ERPNext Item Price" and not self.erpnext_item:
            frappe.throw(
                _("Linked ERPNext Item is required for ERPNext Item Price mode.")
            )

        if mode == "Informational / Quote":
            self.fixed_price = 0

    def _validate_unique_category_key(self):
        """Enforce a stable item key within each service category."""

        if not self.service_category or not self.service_key:
            return

        duplicate = frappe.db.get_value(
            "RhoGuest Service Item",
            {
                "service_category": self.service_category,
                "service_key": self.service_key,
            },
            "name",
        )

        if duplicate and duplicate != self.name:
            frappe.throw(
                _(
                    "Service Item Key {0} already exists in category {1}."
                ).format(
                    frappe.bold(self.service_key),
                    frappe.bold(self.service_category),
                )
            )

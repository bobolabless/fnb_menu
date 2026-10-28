"""Generic RhoGuest service-category master.

This DocType describes what a hotel offers to a guest and which high-level
interaction model that service supports. Operational documents such as KOTs,
laundry jobs or transport bookings remain separate, specialized workflows.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

_SERVICE_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_service_key(value: str | None) -> str:
    """Return a predictable lower-case, hyphenated machine key."""

    key = (value or "").strip().lower()
    key = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    return re.sub(r"-{2,}", "-", key)


class RhoGuestServiceCategory(Document):
    """Configuration master for one guest-service family."""

    def validate(self):
        self.category_name = (self.category_name or "").strip()
        self.service_key = normalize_service_key(self.service_key)

        if not self.category_name:
            frappe.throw(_("Category Name is required."))

        if not self.service_key or not _SERVICE_KEY_RE.fullmatch(self.service_key):
            frappe.throw(
                _(
                    "Service Key must contain lower-case letters, numbers and "
                    "single hyphens only."
                )
            )

        # The DocType name is the service key. Renaming an operational key after
        # integrations or portal links exist would create ambiguous references.
        if not self.is_new() and self.name and self.service_key != self.name:
            frappe.throw(
                _(
                    "Service Key cannot be changed after the category is created. "
                    "Change the Category Name for guest-facing wording instead."
                )
            )

        if cint(self.sort_order) < 0:
            frappe.throw(_("Display Order cannot be negative."))

        if self.show_on_portal and not self.enabled:
            frappe.throw(
                _("Enable the service category before publishing it on the Guest Portal.")
            )

        # Information-only categories are intentionally non-transactional.
        if self.workflow_type == "Information Only":
            transactional = (
                self.allows_reservation
                or self.allows_ordering
                or self.allows_payment
                or self.allows_charge_to_room
            )
            if transactional:
                frappe.throw(
                    _(
                        "Information Only services cannot allow reservations, "
                        "ordering, paid services or Charge to Room."
                    )
                )

        if self.allows_charge_to_room and not self.allows_payment:
            frappe.throw(
                _(
                    "Allows Charge to Room requires Allows Paid Services to be enabled."
                )
            )

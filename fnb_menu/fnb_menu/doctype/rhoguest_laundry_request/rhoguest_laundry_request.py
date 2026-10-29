"""Operational Laundry Request document for RhoGuest.

Request-line rates are immutable snapshots populated by the server-side
Laundry API. Later catalog changes must not rewrite a guest's submitted total.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class RhoGuestLaundryRequest(Document):
    """Room-linked guest Laundry Request and fulfilment record."""

    def before_insert(self):
        if not self.public_token:
            self.public_token = secrets.token_urlsafe(24)

    def validate(self):
        self.guest_name = (self.guest_name or "").strip()
        self.room_number = (self.room_number or "").strip()
        self.email = (self.email or "").strip()
        self.phone = (self.phone or "").strip()
        self.pickup_note = (self.pickup_note or "").strip()[:1000]

        if not self.guest_name:
            frappe.throw(_("Guest Name is required."))
        if not self.room_number:
            frappe.throw(_("Room Number is required."))
        if not self.email and not self.phone:
            frappe.throw(_("Provide at least an email address or phone number."))
        if self.email and "@" not in self.email:
            frappe.throw(_("Enter a valid email address."))

        rows = self.items or []
        if not rows:
            frappe.throw(_("Add at least one laundry item."))
        if len(rows) > 50:
            frappe.throw(_("A Laundry Request cannot contain more than 50 lines."))

        currency = None
        total = 0.0

        for row in rows:
            qty = cint(row.qty)
            if qty < 1 or qty > 50:
                frappe.throw(_("Laundry item quantity must be between 1 and 50."))
            if not row.service_item or not row.service_name:
                frappe.throw(_("Every Laundry Request line requires a Service Item."))

            if currency and row.currency and row.currency != currency:
                frappe.throw(_("A Laundry Request cannot mix multiple currencies."))
            if row.currency:
                currency = row.currency

            row.amount = flt(row.rate) * qty
            total += flt(row.amount)

        self.currency = currency or self.currency
        self.estimated_total = total

        if self.billing_preference == "Charge to Room":
            # Queue-only state. Phase 2C never writes a room folio directly.
            self.billing_status = "Pending Folio Posting"
        elif self.is_new() and not self.billing_status:
            self.billing_status = "Unbilled"

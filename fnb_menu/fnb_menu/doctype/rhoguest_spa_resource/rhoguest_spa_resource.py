"""Operational resource master for RhoGuest Spa & Wellness."""

from __future__ import annotations

import re
from datetime import time, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

_RESOURCE_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_spa_resource_key(value):
    key = (value or "").strip().lower()
    key = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    return re.sub(r"-{2,}", "-", key)


def _time_seconds(value):
    """Normalize Frappe Time values to seconds since midnight."""

    if value is None:
        return None

    if isinstance(value, timedelta):
        return int(value.total_seconds())

    if isinstance(value, time):
        return value.hour * 3600 + value.minute * 60 + value.second

    text = str(value).strip()
    if not text:
        return None

    parts = text.split(":")
    if len(parts) < 2:
        return None

    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2] or 0))


class RhoGuestSpaResource(Document):
    """Therapist/treatment resource used by Spa appointment scheduling."""

    def validate(self):
        self.resource_name = (self.resource_name or "").strip()
        self.resource_key = normalize_spa_resource_key(self.resource_key)
        self.location = (self.location or "").strip()

        if not self.resource_name:
            frappe.throw(_("Resource Name is required."))

        if not self.resource_key or not _RESOURCE_KEY_RE.fullmatch(self.resource_key):
            frappe.throw(
                _("Resource Key must contain lower-case letters, numbers and single hyphens only.")
            )

        if cint(self.sort_order) < 0:
            frappe.throw(_("Display Order cannot be negative."))

        if not self.enabled:
            self.allow_public_selection = 0

        self._validate_user()
        self._validate_services()
        self._validate_availability()

    def _validate_user(self):
        if not self.user:
            return

        account = frappe.db.get_value(
            "User",
            self.user,
            ["enabled", "user_type"],
            as_dict=True,
        )
        if not account or not cint(account.enabled) or account.user_type != "System User":
            frappe.throw(_("Spa Resource System User must be an enabled System User."))

    def _validate_services(self):
        seen = set()

        for row in self.services or []:
            if not row.service_item:
                continue

            if row.service_item in seen:
                frappe.throw(_("Duplicate Spa Service {0}.").format(frappe.bold(row.service_item)))
            seen.add(row.service_item)

            item = frappe.db.get_value(
                "RhoGuest Service Item",
                row.service_item,
                ["service_category", "requires_reservation", "duration_minutes"],
                as_dict=True,
            )
            if not item or item.service_category != "spa-wellness":
                frappe.throw(_("Spa Resources may only map to Spa & Wellness Service Items."))
            if not cint(item.requires_reservation) or cint(item.duration_minutes) <= 0:
                frappe.throw(
                    _("Spa Service {0} must require reservation and have Duration greater than zero.").format(
                        frappe.bold(row.service_item)
                    )
                )

    def _validate_availability(self):
        by_day = {}

        for row in self.availability or []:
            start = _time_seconds(row.start_time)
            end = _time_seconds(row.end_time)

            if start is None or end is None or end <= start:
                frappe.throw(
                    _("Spa availability End Time must be later than Start Time on {0}.").format(
                        frappe.bold(row.day_of_week)
                    )
                )

            by_day.setdefault(row.day_of_week, []).append((start, end))

        for day, periods in by_day.items():
            periods.sort()
            previous_end = None

            for start, end in periods:
                if previous_end is not None and start < previous_end:
                    frappe.throw(
                        _("Spa Resource availability overlaps on {0}.").format(
                            frappe.bold(day)
                        )
                    )
                previous_end = end

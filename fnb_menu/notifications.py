"""Laundry lifecycle notifications for RhoGuest.

Notification failures are isolated from the operational transaction. A Laundry
status/billing update must never be rolled back merely because an email server
or notification queue is unavailable.
"""

from __future__ import annotations

import re

import frappe
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
)
from frappe.utils import cint, escape_html

GUEST_EMAIL_EVENTS = {
    "Submitted",
    "Pickup Scheduled",
    "Ready",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
    "Posted to Room",
}


def _operations_emails(raw):
    return sorted(
        {
            token.strip()
            for token in re.split(r"[,;\n]+", raw or "")
            if token.strip() and "@" in token
        }
    )


def _event_text(request, event):
    event_label = event or request.status or "Updated"
    title = f"Laundry {request.name}: {event_label}"
    description = (
        f"Room {request.room_number} · Guest {request.guest_name} · "
        f"Status {request.status} · Billing {request.billing_status}"
    )
    return title, description


def _email_message(request, event):
    title, description = _event_text(request, event)

    return f"""
        <p><strong>{escape_html(title)}</strong></p>
        <p>{escape_html(description)}</p>
        <p>Estimated total: {escape_html(request.currency or "")}
        {escape_html(request.estimated_total or 0)}</p>
        <p>Reference: {escape_html(request.name)}</p>
    """


def notify_laundry_event(request, event, actor=None):
    """Dispatch enabled in-app/email notifications without blocking operations."""

    settings = frappe.get_single("FNB Menu Settings")
    actor = actor or frappe.session.user
    title, description = _event_text(request, event)

    if cint(settings.get("laundry_staff_in_app_notifications")) and request.assigned_to:
        try:
            enqueue_create_notification(
                users=[request.assigned_to],
                doc={
                    "type": "Alert",
                    "title": title,
                    "description": description,
                    "document_type": "RhoGuest Laundry Request",
                    "document_name": request.name,
                    "from_user": actor,
                },
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"RhoGuest Laundry in-app notification failed: {request.name}",
            )

    if (
        cint(settings.get("laundry_guest_email_notifications"))
        and request.email
        and event in GUEST_EMAIL_EVENTS
    ):
        try:
            frappe.sendmail(
                recipients=[request.email],
                subject=title,
                message=_email_message(request, event),
                delayed=True,
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"RhoGuest Laundry guest email failed: {request.name}",
            )

    if cint(settings.get("laundry_staff_email_notifications")):
        recipients = set(_operations_emails(settings.get("laundry_operations_emails")))

        if request.assigned_to:
            assigned_email = frappe.db.get_value("User", request.assigned_to, "email")
            if assigned_email:
                recipients.add(assigned_email)

        if recipients:
            try:
                frappe.sendmail(
                    recipients=sorted(recipients),
                    subject=title,
                    message=_email_message(request, event),
                    delayed=True,
                )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"RhoGuest Laundry staff email failed: {request.name}",
                )

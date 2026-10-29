"""Public and staff APIs for RhoGuest Laundry Request & Fulfilment."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from fnb_menu.laundry_service import (
    resolve_laundry_request_lines,
    validate_requested_pickup,
)
from fnb_menu.integrations.folio import post_laundry_request_to_folio
from fnb_menu.menu_service import get_settings
from fnb_menu.notifications import notify_laundry_event

STATUS_TRANSITIONS = {
    "Submitted": {"Pickup Scheduled", "Collected", "Cancelled"},
    "Pickup Scheduled": {"Collected", "Cancelled"},
    "Collected": {"Processing", "Cancelled"},
    "Processing": {"Ready", "Cancelled"},
    "Ready": {"Out for Delivery", "Delivered", "Cancelled"},
    "Out for Delivery": {"Delivered", "Cancelled"},
    "Delivered": set(),
    "Cancelled": set(),
}


def _get_staff_request(request_name):
    """Load one Laundry Request after enforcing authenticated write access."""

    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    request = frappe.get_doc("RhoGuest Laundry Request", request_name)

    if not request.has_permission("write"):
        frappe.throw(
            _("You do not have permission to update this Laundry Request."),
            frappe.PermissionError,
        )

    return request


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_request(
    guest_name,
    room_number,
    items,
    email=None,
    phone=None,
    requested_pickup_at=None,
    pickup_note=None,
    billing_preference="Pay at Hotel",
):
    """Create a public Laundry Request from server-validated catalog data."""

    settings = get_settings()
    guest_name = (guest_name or "").strip()[:140]
    room_number = (room_number or "").strip()[:30]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    pickup_note = (pickup_note or "").strip()[:1000]
    billing_preference = (billing_preference or "Pay at Hotel").strip()

    if not guest_name:
        frappe.throw(_("Guest Name is required."))
    if not room_number:
        frappe.throw(_("Room Number is required."))
    if not email and not phone:
        frappe.throw(_("Provide at least an email address or phone number."))
    if email and "@" not in email:
        frappe.throw(_("Enter a valid email address."))
    if billing_preference not in {"Pay at Hotel", "Charge to Room"}:
        frappe.throw(_("Invalid billing preference."))

    requested_pickup = validate_requested_pickup(requested_pickup_at)
    resolved = resolve_laundry_request_lines(items)

    if billing_preference == "Charge to Room":
        if not cint(resolved.catalog.category.allows_charge_to_room):
            frappe.throw(_("Laundry service is not configured for Charge to Room."))
        if any(not row["allow_charge_to_room"] for row in resolved.lines):
            frappe.throw(
                _("One or more selected laundry items cannot be charged to the room.")
            )

    request = frappe.get_doc(
        {
            "doctype": "RhoGuest Laundry Request",
            "guest_name": guest_name,
            "room_number": room_number,
            "email": email,
            "phone": phone,
            "requested_pickup_at": requested_pickup,
            "pickup_note": pickup_note,
            "status": "Submitted",
            "billing_preference": billing_preference,
            "billing_status": (
                "Pending Folio Posting"
                if billing_preference == "Charge to Room"
                else "Unbilled"
            ),
            "company": settings.company,
            "currency": resolved.currency,
            "items": [
                {
                    key: value
                    for key, value in row.items()
                    if key != "allow_charge_to_room"
                }
                for row in resolved.lines
            ],
        }
    )
    request.insert(ignore_permissions=True)
    notify_laundry_event(request, "Submitted")

    return {
        "request": request.name,
        "token": request.public_token,
        "status": request.status,
        "billing_status": request.billing_status,
        "estimated_total": request.estimated_total,
        "currency": request.currency,
    }


@frappe.whitelist(allow_guest=True)
def get_request_status(request_name, token):
    """Return a minimal public status payload when the token matches."""

    request = frappe.db.get_value(
        "RhoGuest Laundry Request",
        {"name": request_name, "public_token": token},
        [
            "name",
            "status",
            "billing_preference",
            "billing_status",
            "estimated_total",
            "currency",
            "requested_pickup_at",
            "collected_at",
            "ready_at",
            "delivered_at",
            "creation",
        ],
        as_dict=True,
    )
    if not request:
        frappe.throw(_("Laundry Request not found."))
    return request


@frappe.whitelist(methods=["POST"])
def update_status(request_name, status):
    """Advance a request through the controlled Laundry fulfilment graph."""

    request = _get_staff_request(request_name)

    status = (status or "").strip()
    if status not in STATUS_TRANSITIONS.get(request.status, set()):
        frappe.throw(
            _("Invalid Laundry status transition from {0} to {1}.").format(
                frappe.bold(request.status),
                frappe.bold(status),
            )
        )

    values = {"status": status}
    if status == "Collected" and not request.collected_at:
        values["collected_at"] = now_datetime()
    elif status == "Ready" and not request.ready_at:
        values["ready_at"] = now_datetime()
    elif status == "Delivered" and not request.delivered_at:
        values["delivered_at"] = now_datetime()
    elif status == "Cancelled" and request.billing_status not in {
        "Posted to Room",
        "Settled",
    }:
        values["billing_status"] = "Cancelled"

    request.db_set(values)
    request.reload()
    notify_laundry_event(request, status)

    return {
        "request": request.name,
        "status": status,
        "billing_status": values.get("billing_status", request.billing_status),
    }



@frappe.whitelist(methods=["POST"])
def schedule_pickup(request_name, requested_pickup_at):
    """Schedule or reschedule a future Laundry pickup for an open request."""

    request = _get_staff_request(request_name)

    if request.status not in {"Submitted", "Pickup Scheduled"}:
        frappe.throw(
            _("Pickup can only be scheduled while the request is Submitted or Pickup Scheduled.")
        )

    requested = validate_requested_pickup(requested_pickup_at)
    if not requested:
        frappe.throw(_("Requested Pickup Time is required."))

    values = {"requested_pickup_at": requested}

    # Scheduling the initial pickup is itself a controlled status transition.
    if request.status == "Submitted":
        values["status"] = "Pickup Scheduled"

    request.db_set(values)
    request.reload()
    notify_laundry_event(request, "Pickup Scheduled")

    return {
        "request": request.name,
        "status": values.get("status", request.status),
        "requested_pickup_at": requested,
    }


@frappe.whitelist(methods=["POST"])
def assign_request(request_name, user=None):
    """Assign or unassign an open Laundry Request to an enabled System User."""

    request = _get_staff_request(request_name)

    if request.status in {"Delivered", "Cancelled"}:
        frappe.throw(_("Completed or Cancelled Laundry Requests cannot be reassigned."))

    user = (user or "").strip()

    if user:
        account = frappe.db.get_value(
            "User",
            user,
            ["enabled", "user_type"],
            as_dict=True,
        )

        if not account or not cint(account.enabled) or account.user_type != "System User":
            frappe.throw(_("Assign Laundry Requests only to an enabled System User."))

    request.db_set("assigned_to", user or None)
    request.reload()
    if user:
        notify_laundry_event(request, "Assigned")

    return {
        "request": request.name,
        "assigned_to": user or None,
    }



def _require_billing_manager():
    """Restrict folio/billing actions to System Manager or Sales Manager."""

    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.PermissionError)

    roles = set(frappe.get_roles(frappe.session.user))
    if not roles.intersection({"System Manager", "Sales Manager"}):
        frappe.throw(
            _("System Manager or Sales Manager role is required for Laundry billing actions."),
            frappe.PermissionError,
        )


def _lock_billing_request(request_name):
    """Lock and reload one Laundry Request before an external billing mutation."""

    _require_billing_manager()

    frappe.db.sql(
        """
        select name
        from `tabRhoGuest Laundry Request`
        where name = %s
        for update
        """,
        request_name,
    )

    request = _get_staff_request(request_name)

    if request.billing_preference != "Charge to Room":
        frappe.throw(_("This Laundry Request is not configured for Charge to Room."))

    if request.status == "Cancelled":
        frappe.throw(_("Cancelled Laundry Requests cannot be posted to a folio."))

    return request


def _mark_folio_posted(request, reference, mode):
    """Persist a confirmed external folio posting with audit metadata."""

    reference = (reference or "").strip()
    if not reference:
        frappe.throw(_("Folio Reference is required."))

    if request.billing_status in {"Posted to Room", "Settled"} and request.folio_reference:
        return {
            "request": request.name,
            "billing_status": request.billing_status,
            "folio_reference": request.folio_reference,
            "idempotent": 1,
        }

    if request.billing_status != "Pending Folio Posting":
        frappe.throw(
            _("Only Laundry Requests awaiting folio posting can be posted to room.")
        )

    values = {
        "billing_status": "Posted to Room",
        "folio_reference": reference[:140],
        "folio_posting_mode": mode,
        "folio_posted_at": now_datetime(),
        "folio_posted_by": frappe.session.user,
    }
    request.db_set(values)
    request.reload()
    notify_laundry_event(request, "Posted to Room")

    return {
        "request": request.name,
        "billing_status": request.billing_status,
        "folio_reference": request.folio_reference,
        "idempotent": 0,
    }


@frappe.whitelist()
def get_folio_posting_mode():
    """Return non-sensitive Laundry folio integration state for the Desk form."""

    _require_billing_manager()
    settings = get_settings()
    mode = settings.get("laundry_folio_posting_mode") or "Manual"

    return {
        "mode": mode,
        "custom_integration_configured": bool(
            (settings.get("laundry_folio_posting_method") or "").strip()
        ),
    }


@frappe.whitelist(methods=["POST"])
def post_to_folio(request_name):
    """Post a Charge-to-Room Laundry Request through the configured adapter."""

    request = _lock_billing_request(request_name)

    if request.billing_status in {"Posted to Room", "Settled"} and request.folio_reference:
        return {
            "request": request.name,
            "billing_status": request.billing_status,
            "folio_reference": request.folio_reference,
            "idempotent": 1,
        }

    result = post_laundry_request_to_folio(request)
    return _mark_folio_posted(
        request,
        result.reference,
        result.mode,
    )


@frappe.whitelist(methods=["POST"])
def record_folio_posting(request_name, folio_reference):
    """Record a manually completed posting using its real external reference."""

    request = _lock_billing_request(request_name)
    return _mark_folio_posted(
        request,
        folio_reference,
        "Manual",
    )


@frappe.whitelist(methods=["POST"])
def mark_billing_settled(request_name):
    """Mark a previously posted room charge as settled with audit metadata."""

    request = _lock_billing_request(request_name)

    if request.billing_status == "Settled":
        return {
            "request": request.name,
            "billing_status": request.billing_status,
            "idempotent": 1,
        }

    if request.billing_status != "Posted to Room" or not request.folio_reference:
        frappe.throw(
            _("Billing can be marked Settled only after a confirmed folio posting.")
        )

    request.db_set(
        {
            "billing_status": "Settled",
            "billing_settled_at": now_datetime(),
            "billing_settled_by": frappe.session.user,
        }
    )
    request.reload()
    notify_laundry_event(request, "Settled")

    return {
        "request": request.name,
        "billing_status": request.billing_status,
        "idempotent": 0,
    }

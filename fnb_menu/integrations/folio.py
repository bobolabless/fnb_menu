"""Optional room-folio integration adapter for RhoGuest Laundry.

This module deliberately has no hard dependency on RhoHMS. Hotels can keep
Manual mode or configure one trusted dotted Python method that posts a charge
to their local PMS/folio implementation and returns an external reference.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from fnb_menu.menu_service import get_settings


def build_laundry_folio_payload(request):
    """Build the stable integration payload for one Laundry Request."""

    return {
        "source_doctype": "RhoGuest Laundry Request",
        "source_name": request.name,
        "idempotency_key": f"RhoGuest Laundry Request:{request.name}",
        "company": request.company,
        "guest_name": request.guest_name,
        "room_number": request.room_number,
        "currency": request.currency,
        "amount": flt(request.estimated_total),
        "billing_preference": request.billing_preference,
        "items": [
            {
                "service_item": row.service_item,
                "service_name": row.service_name,
                "service_key": row.service_key,
                "qty": cint(row.qty),
                "rate": flt(row.rate),
                "amount": flt(row.amount),
                "currency": row.currency,
            }
            for row in request.items
        ],
    }


def post_laundry_request_to_folio(request):
    """Call the configured custom adapter and return a validated result."""

    settings = get_settings()
    mode = settings.get("laundry_folio_posting_mode") or "Manual"

    if mode != "Custom Integration":
        frappe.throw(
            _(
                "Laundry Folio Posting Mode is Manual. Use Record Folio Posting "
                "after the charge is posted in the hotel folio system."
            )
        )

    method = (settings.get("laundry_folio_posting_method") or "").strip()
    if not method:
        frappe.throw(_("Custom Folio Posting Method is not configured."))

    handler = frappe.get_attr(method)
    result = handler(payload=build_laundry_folio_payload(request))

    if not isinstance(result, dict):
        frappe.throw(
            _("Custom folio integration must return a dictionary response.")
        )

    success = cint(result.get("success"))
    reference = str(result.get("reference") or "").strip()

    if not success or not reference:
        message = str(result.get("message") or "").strip()
        frappe.throw(
            message
            or _(
                "The folio integration did not confirm a successful posting "
                "with an external reference."
            )
        )

    return frappe._dict(
        {
            "success": 1,
            "reference": reference[:140],
            "mode": "Custom Integration",
            "message": str(result.get("message") or "").strip(),
        }
    )

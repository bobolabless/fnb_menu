#!/usr/bin/env python3
"""Static contract checks for Laundry folio integration and notifications."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    settings = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/rhoguest_menu_settings.json"
    )
    settings_fields = {row["fieldname"]: row for row in settings["fields"]}

    required_settings = {
        "laundry_folio_posting_mode",
        "laundry_folio_posting_method",
        "laundry_staff_in_app_notifications",
        "laundry_guest_email_notifications",
        "laundry_staff_email_notifications",
        "laundry_operations_emails",
    }
    assert required_settings <= set(settings_fields)
    assert settings_fields["laundry_folio_posting_mode"]["default"] == "Manual"
    assert settings_fields["laundry_staff_in_app_notifications"]["default"] == "1"
    assert settings_fields["laundry_guest_email_notifications"]["default"] == "0"
    assert settings_fields["laundry_staff_email_notifications"]["default"] == "0"
    assert settings_fields["laundry_folio_posting_method"]["permlevel"] == 1

    request = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.json"
    )
    request_fields = {row["fieldname"]: row for row in request["fields"]}
    assert {
        "folio_reference",
        "folio_posting_mode",
        "folio_posted_at",
        "folio_posted_by",
        "billing_settled_at",
        "billing_settled_by",
    } <= set(request_fields)
    for fieldname in (
        "folio_posting_mode",
        "folio_posted_at",
        "folio_posted_by",
        "billing_settled_at",
        "billing_settled_by",
    ):
        assert request_fields[fieldname]["read_only"] == 1

    install = (ROOT / "fnb_menu/install.py").read_text()

    settings_py = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/"
        "rhoguest_menu_settings.py"
    ).read_text()
    folio = (ROOT / "fnb_menu/integrations/folio.py").read_text()
    api = (ROOT / "fnb_menu/api/laundry.py").read_text()
    notifications = (ROOT / "fnb_menu/notifications.py").read_text()
    form_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.js"
    ).read_text()
    setup = (ROOT / "docs/RHOGUEST_SETUP_MANUAL.md").read_text()
    user = (ROOT / "docs/RHOGUEST_USER_MANUAL.md").read_text()

    assert "def ensure_settings_defaults" in install
    assert '"laundry_folio_posting_mode": "Manual"' in install
    assert '"laundry_staff_in_app_notifications": "1"' in install
    assert '"laundry_guest_email_notifications": "0"' in install
    assert '"laundry_staff_email_notifications": "0"' in install
    assert "select value" in install
    assert "from tabSingles" in install
    assert "frappe.db.set_single_value" in install

    assert "_validate_laundry_integration" in settings_py
    assert 'mode not in {"Manual", "Custom Integration"}' in settings_py
    assert "frappe.get_attr(method)" in settings_py

    assert '"idempotency_key": f"RhoGuest Laundry Request:{request.name}"' in folio
    assert "handler(payload=build_laundry_folio_payload(request))" in folio
    assert 'result.get("success")' in folio
    assert 'result.get("reference")' in folio

    assert "def _require_billing_manager" in api
    assert '{"System Manager", "Sales Manager"}' in api
    assert "for update" in api.lower()
    assert "def post_to_folio" in api
    assert "def record_folio_posting" in api
    assert "def mark_billing_settled" in api
    assert '"idempotent": 1' in api
    assert '"billing_status": "Posted to Room"' in api
    assert '"billing_status": "Settled"' in api

    assert 'GUEST_EMAIL_EVENTS' in notifications
    assert '"Posted to Room"' in notifications
    assert '"type": "Alert"' in notifications
    assert "laundry_staff_in_app_notifications" in notifications
    assert "laundry_guest_email_notifications" in notifications
    assert "laundry_staff_email_notifications" in notifications
    assert "frappe.log_error" in notifications

    assert "Post to Folio" in form_js
    assert "Record Folio Posting" in form_js
    assert "Mark Settled" in form_js
    assert "fnb_menu.api.laundry.post_to_folio" in form_js
    assert "fnb_menu.api.laundry.record_folio_posting" in form_js

    assert "Folio Integration Modes" in setup
    assert "idempotency_key" in setup
    assert "Laundry Notification Settings" in setup
    assert "Manual Folio Posting" in user
    assert "Custom Folio Integration" in user
    assert "Laundry Notifications" in user

    print("RhoGuest v0.2.0 laundry billing/folio/notifications: PASS")


if __name__ == "__main__":
    main()

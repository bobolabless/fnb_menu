#!/usr/bin/env python3
"""Static contract checks for RhoGuest Spa & Wellness appointments."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    resource = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_spa_resource/"
        "rhoguest_spa_resource.json"
    )
    appointment = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_spa_appointment/"
        "rhoguest_spa_appointment.json"
    )

    assert resource["autoname"] == "field:resource_key"
    resource_fields = {row["fieldname"]: row for row in resource["fields"]}
    assert {
        "resource_name",
        "resource_key",
        "resource_type",
        "enabled",
        "allow_public_selection",
        "services",
        "availability",
    } <= set(resource_fields)

    assert appointment["autoname"] == "format:RGSA-{YYYY}-{#####}"
    appointment_fields = {row["fieldname"]: row for row in appointment["fields"]}
    assert {
        "service_item",
        "spa_resource",
        "resource_name",
        "appointment_start",
        "appointment_end",
        "status",
        "public_token",
        "rate",
        "estimated_total",
        "settlement_mode",
        "confirmed_at",
        "checked_in_at",
        "treatment_started_at",
        "completed_at",
    } <= set(appointment_fields)
    assert appointment_fields["public_token"]["unique"] == 1

    resource_py = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_spa_resource/"
        "rhoguest_spa_resource.py"
    ).read_text()
    service = (ROOT / "fnb_menu/spa_service.py").read_text()
    api = (ROOT / "fnb_menu/api/spa.py").read_text()
    public_js = (ROOT / "fnb_menu/public/js/rhoguest_spa.js").read_text()
    form_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_spa_appointment/"
        "rhoguest_spa_appointment.js"
    ).read_text()
    list_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_spa_appointment/"
        "rhoguest_spa_appointment_list.js"
    ).read_text()
    hub = (ROOT / "fnb_menu/guest_service.py").read_text()
    hooks = (ROOT / "fnb_menu/hooks.py").read_text()
    dashboard = (ROOT / "fnb_menu/api/dashboard.py").read_text()
    workspace = load_json("fnb_menu/fnb_menu/workspace/rhoguest/rhoguest.json")
    setup = (ROOT / "docs/RHOGUEST_SETUP_MANUAL.md").read_text()
    user = (ROOT / "docs/RHOGUEST_USER_MANUAL.md").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "Spa Resource availability overlaps" in resource_py
    assert 'service_category != "spa-wellness"' in resource_py
    assert 'account.user_type != "System User"' in resource_py

    assert 'SPA_CATEGORY_KEY = "spa-wellness"' in service
    assert "for update" in service.lower()
    assert "_resource_covers_period" in service
    assert "_resource_has_overlap" in service
    assert "No Spa Resource is available" in service
    assert "180 days" in service
    assert "reject_duplicate_guest_appointment" in service

    assert '@frappe.whitelist(allow_guest=True, methods=["POST"])' in api
    assert "resolve_spa_appointment" in api
    assert "get_appointment_status" in api
    assert "STATUS_TRANSITIONS" in api
    assert "reschedule_appointment" in api

    payload_block = public_js.split(
        "const params = new URLSearchParams({", 1
    )[1].split("});", 1)[0]
    for forbidden in ("rate:", "amount:", "duration:", "appointment_end:"):
        assert forbidden not in payload_block
    assert "service_item:" in payload_block
    assert "spa_resource:" in payload_block
    assert "appointment_start:" in payload_block

    for label in (
        "Confirm Appointment",
        "Check In",
        "Start Treatment",
        "Complete Treatment",
        "Mark No Show",
        "Cancel Appointment",
        "Reschedule / Change Resource",
    ):
        assert label in form_js

    for label in (
        "Upcoming",
        "Awaiting Confirmation",
        "Checked In",
        "In Treatment",
        "All Appointments",
    ):
        assert label in list_js

    assert 'category.service_key == "spa-wellness"' in hub
    assert 'action_url = "/rhoguest-spa"' in hub
    assert '"/rhoguest-spa", "to_route": "rhoguest_spa"' in hooks

    assert '"spa_upcoming"' in dashboard
    assert '"spa_today"' in dashboard
    assert '"spa_in_treatment"' in dashboard

    assert any(row["label"] == "Spa Appointments" for row in workspace["shortcuts"])
    assert any(row["label"] == "Spa Resources" for row in workspace["shortcuts"])

    content = json.loads(workspace["content"])
    assert any(
        row.get("data", {}).get("shortcut_name") == "Spa Appointments"
        for row in content
    )

    assert "Spa & Wellness Setup" in setup
    assert "Candidate resources are row-locked" in setup
    assert "Spa & Wellness Appointments" in user
    assert "Any available" in user
    assert "v0.2.0 Spa & Wellness Appointments" in readme

    print("RhoGuest v0.2.0 Spa & Wellness appointments: PASS")


if __name__ == "__main__":
    main()

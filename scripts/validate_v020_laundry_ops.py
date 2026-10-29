#!/usr/bin/env python3
"""Static contract checks for RhoGuest Laundry staff operations UI."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    doctype = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.json"
    )
    fields = {row["fieldname"]: row for row in doctype["fields"]}

    for fieldname in (
        "room_number",
        "status",
        "billing_status",
        "assigned_to",
        "requested_pickup_at",
    ):
        assert fields[fieldname]["in_standard_filter"] == 1

    assert fields["assigned_to"]["in_list_view"] == 1
    assert fields["requested_pickup_at"]["in_list_view"] == 1

    api = (ROOT / "fnb_menu/api/laundry.py").read_text()
    form_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.js"
    ).read_text()
    list_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request_list.js"
    ).read_text()
    user_manual = (ROOT / "docs/RHOGUEST_USER_MANUAL.md").read_text()
    setup_manual = (ROOT / "docs/RHOGUEST_SETUP_MANUAL.md").read_text()

    assert "def _get_staff_request" in api
    assert "def schedule_pickup" in api
    assert "def assign_request" in api
    assert 'request.status not in {"Submitted", "Pickup Scheduled"}' in api
    assert 'account.user_type != "System User"' in api
    assert 'request.status in {"Delivered", "Cancelled"}' in api

    for label in (
        "Schedule Pickup",
        "Reschedule Pickup",
        "Mark Collected",
        "Start Processing",
        "Mark Ready",
        "Out for Delivery",
        "Mark Delivered",
        "Cancel Request",
        "Assign Staff",
        "Unassign",
    ):
        assert label in form_js

    assert "fnb_menu.api.laundry.update_status" in form_js
    assert "fnb_menu.api.laundry.schedule_pickup" in form_js
    assert "fnb_menu.api.laundry.assign_request" in form_js
    assert "Pending Folio Posting" in form_js

    for label in (
        "Open Queue",
        "Awaiting Pickup",
        "Processing",
        "Ready / Delivery",
        "Pending Folio",
        "All Requests",
    ):
        assert label in list_js

    assert "filter_area.clear(false)" in list_js
    assert "filter_area.set(filters)" in list_js
    assert 'frappe.set_route("rhoguest-dashboard")' in list_js

    assert "Form Action Buttons" in user_manual
    assert "Laundry Queue Filters" in user_manual
    assert "Staff Operations UI" in setup_manual

    print("RhoGuest v0.2.0 laundry operations UI: PASS")


if __name__ == "__main__":
    main()

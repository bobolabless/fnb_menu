#!/usr/bin/env python3
"""Static contract checks for Pool/Gym facility reservations."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    item = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_service_item/"
        "rhoguest_service_item.json"
    )
    item_fields = {row["fieldname"]: row for row in item["fields"]}
    assert "pricing_basis" in item_fields
    assert item_fields["pricing_basis"]["default"] == "Per Reservation"
    assert "Per Person" in item_fields["pricing_basis"]["options"]

    reservation = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_facility_reservation/"
        "rhoguest_facility_reservation.json"
    )
    fields = {row["fieldname"]: row for row in reservation["fields"]}
    assert reservation["autoname"] == "format:RGF-{YYYY}-{#####}"
    assert {
        "service_category",
        "service_item",
        "reservation_start",
        "reservation_end",
        "party_size",
        "status",
        "public_token",
        "pricing_basis",
        "estimated_total",
        "settlement_mode",
        "assigned_to",
        "confirmed_at",
        "checked_in_at",
        "completed_at",
    } <= set(fields)
    assert fields["public_token"]["unique"] == 1

    service = (ROOT / "fnb_menu/facility_service.py").read_text()
    api = (ROOT / "fnb_menu/api/facility.py").read_text()
    form_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_facility_reservation/"
        "rhoguest_facility_reservation.js"
    ).read_text()
    list_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_facility_reservation/"
        "rhoguest_facility_reservation_list.js"
    ).read_text()
    hub = (ROOT / "fnb_menu/guest_service.py").read_text()
    hooks = (ROOT / "fnb_menu/hooks.py").read_text()
    public_js = (ROOT / "fnb_menu/public/js/rhoguest_facility.js").read_text()
    dashboard = (ROOT / "fnb_menu/api/dashboard.py").read_text()
    workspace = load_json("fnb_menu/fnb_menu/workspace/rhoguest/rhoguest.json")

    assert 'FACILITY_KEYS = {"swimming-pool", "gym-fitness"}' in service
    assert "for update" in service.lower()
    assert "_reserved_capacity" in service
    assert "reservation_start < %(end)s" in service
    assert "reservation_end > %(start)s" in service
    assert "Remaining capacity" in service
    assert "180 days" in service
    assert "reject_duplicate_guest_booking" in service

    assert '@frappe.whitelist(allow_guest=True, methods=["POST"])' in api
    assert "resolve_facility_reservation" in api
    assert "get_reservation_status" in api
    assert "STATUS_TRANSITIONS" in api
    assert "reschedule_reservation" in api
    assert "assign_reservation" in api

    for label in (
        "Confirm Reservation",
        "Check In",
        "Complete Visit",
        "Mark No Show",
        "Cancel Reservation",
        "Reschedule",
        "Assign Staff",
    ):
        assert label in form_js

    for label in (
        "Upcoming",
        "Awaiting Confirmation",
        "Checked In",
        "Pool",
        "Gym",
        "All Reservations",
    ):
        assert label in list_js

    assert 'category.service_key == "swimming-pool"' in hub
    assert 'action_url = "/rhoguest-pool"' in hub
    assert 'category.service_key == "gym-fitness"' in hub
    assert 'action_url = "/rhoguest-gym"' in hub
    assert '"/rhoguest-pool", "to_route": "rhoguest_pool"' in hooks
    assert '"/rhoguest-gym", "to_route": "rhoguest_gym"' in hooks

    payload_block = public_js.split(
        "const params = new URLSearchParams({", 1
    )[1].split("});", 1)[0]
    assert "rate:" not in payload_block
    assert "amount:" not in payload_block
    assert "currency:" not in payload_block
    assert "category_key:" in payload_block
    assert "service_item:" in payload_block

    assert '"facility_upcoming"' in dashboard
    assert '"pool_today"' in dashboard
    assert '"gym_today"' in dashboard
    assert any(row["label"] == "Facility Reservations" for row in workspace["shortcuts"])

    print("RhoGuest v0.2.0 Pool/Gym facility reservations: PASS")


if __name__ == "__main__":
    main()

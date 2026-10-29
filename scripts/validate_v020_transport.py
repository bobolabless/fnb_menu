#!/usr/bin/env python3
"""Static contract checks for RhoGuest Transport booking and dispatch."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def main():
    vehicle = load(
        "fnb_menu/fnb_menu/doctype/rhoguest_transport_vehicle/"
        "rhoguest_transport_vehicle.json"
    )
    driver = load(
        "fnb_menu/fnb_menu/doctype/rhoguest_transport_driver/"
        "rhoguest_transport_driver.json"
    )
    booking = load(
        "fnb_menu/fnb_menu/doctype/rhoguest_transport_booking/"
        "rhoguest_transport_booking.json"
    )

    assert vehicle["autoname"] == "field:vehicle_key"
    assert driver["autoname"] == "field:driver_key"
    assert booking["autoname"] == "format:RGT-{YYYY}-{#####}"

    booking_fields = {row["fieldname"]: row for row in booking["fields"]}
    assert {
        "service_item",
        "scheduled_pickup_at",
        "estimated_dropoff_at",
        "pickup_location",
        "dropoff_location",
        "passenger_count",
        "luggage_count",
        "flight_number",
        "status",
        "public_token",
        "vehicle",
        "driver",
        "vehicle_registration",
        "pricing_basis",
        "estimated_total",
        "settlement_mode",
        "assigned_at",
        "confirmed_at",
        "dispatched_at",
        "arrived_at_pickup_at",
        "trip_started_at",
        "completed_at",
    } <= set(booking_fields)
    assert booking_fields["public_token"]["unique"] == 1

    service = (ROOT / "fnb_menu/transport_service.py").read_text()
    api = (ROOT / "fnb_menu/api/transport.py").read_text()
    public_js = (ROOT / "fnb_menu/public/js/rhoguest_transport.js").read_text()
    form_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_transport_booking/"
        "rhoguest_transport_booking.js"
    ).read_text()
    list_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_transport_booking/"
        "rhoguest_transport_booking_list.js"
    ).read_text()
    hub = (ROOT / "fnb_menu/guest_service.py").read_text()
    hooks = (ROOT / "fnb_menu/hooks.py").read_text()
    dashboard = (ROOT / "fnb_menu/api/dashboard.py").read_text()
    workspace = load("fnb_menu/fnb_menu/workspace/rhoguest/rhoguest.json")

    assert 'TRANSPORT_CATEGORY_KEY = "transport"' in service
    assert "for update" in service.lower()
    assert "_has_resource_overlap" in service
    assert "passenger_capacity" in service
    assert "luggage_capacity" in service
    assert "licence expires before" in service
    assert "180 days" in service
    assert "reject_duplicate_guest_booking" in service

    assert '@frappe.whitelist(allow_guest=True, methods=["POST"])' in api
    assert "create_booking" in api
    assert "get_booking_status" in api
    assert "assign_resources" in api
    assert "reschedule_booking" in api
    assert "STATUS_TRANSITIONS" in api
    assert "Assign both a Transport Vehicle and Driver" in api

    payload = public_js.split(
        "const params = new URLSearchParams({", 1
    )[1].split("});", 1)[0]
    for forbidden in ("rate:", "amount:", "duration:", "estimated_dropoff_at:", "vehicle:", "driver:"):
        assert forbidden not in payload
    assert "service_item:" in payload
    assert "scheduled_pickup_at:" in payload
    assert "passenger_count:" in payload

    for label in (
        "Assign / Change Vehicle & Driver",
        "Confirm Booking",
        "Dispatch Vehicle",
        "Arrived at Pickup",
        "Start Trip",
        "Complete Trip",
        "Mark No Show",
        "Cancel Booking",
        "Reschedule",
    ):
        assert label in form_js

    for label in (
        "Upcoming",
        "Awaiting Assignment",
        "Dispatched",
        "Active Trips",
        "Completed",
        "All Bookings",
    ):
        assert label in list_js

    assert 'category.service_key == "transport"' in hub
    assert 'action_url = "/rhoguest-transport"' in hub
    assert '"/rhoguest-transport", "to_route": "rhoguest_transport"' in hooks

    assert '"transport_upcoming"' in dashboard
    assert '"transport_unassigned"' in dashboard
    assert '"transport_today"' in dashboard
    assert '"transport_in_transit"' in dashboard

    assert any(row["label"] == "Transport Bookings" for row in workspace["shortcuts"])
    assert any(row["label"] == "Transport Vehicles" for row in workspace["shortcuts"])
    assert any(row["label"] == "Transport Drivers" for row in workspace["shortcuts"])

    content = json.loads(workspace["content"])
    assert any(
        row.get("data", {}).get("shortcut_name") == "Transport Bookings"
        for row in content
    )

    print("RhoGuest v0.2.0 Transport booking/dispatch: PASS")


if __name__ == "__main__":
    main()

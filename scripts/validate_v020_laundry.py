#!/usr/bin/env python3
"""Static contract checks for RhoGuest v0.2.0 Laundry workflow."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text())


def field_map(doc):
    return {row["fieldname"]: row for row in doc.get("fields", [])}


def main():
    request = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.json"
    )
    line = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request_item/"
        "rhoguest_laundry_request_item.json"
    )

    assert request["name"] == "RhoGuest Laundry Request"
    assert request["autoname"] == "format:RGL-{YYYY}-{#####}"
    fields = field_map(request)
    assert {
        "guest_name",
        "room_number",
        "requested_pickup_at",
        "status",
        "public_token",
        "items",
        "billing_preference",
        "billing_status",
        "currency",
        "estimated_total",
        "folio_reference",
        "collected_at",
        "ready_at",
        "delivered_at",
    } <= set(fields)
    assert fields["items"]["options"] == "RhoGuest Laundry Request Item"
    assert fields["status"]["read_only"] == 1
    assert fields["public_token"]["unique"] == 1
    assert "Pending Folio Posting" in fields["billing_status"]["options"]

    line_fields = field_map(line)
    assert line["istable"] == 1
    assert {
        "service_item",
        "service_name",
        "service_key",
        "qty",
        "rate",
        "currency",
        "amount",
        "special_instruction",
    } <= set(line_fields)

    service = (ROOT / "fnb_menu/laundry_service.py").read_text()
    api = (ROOT / "fnb_menu/api/laundry.py").read_text()
    controller = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/"
        "rhoguest_laundry_request.py"
    ).read_text()
    page = (ROOT / "fnb_menu/www/rhoguest_laundry.html").read_text()
    js = (ROOT / "fnb_menu/public/js/rhoguest_laundry.js").read_text()
    hub = (ROOT / "fnb_menu/guest_service.py").read_text()
    hooks = (ROOT / "fnb_menu/hooks.py").read_text()

    assert 'LAUNDRY_CATEGORY_KEY = "laundry"' in service
    assert "resolve_laundry_request_lines" in service
    assert "Security boundary: only these three guest-controlled values survive." in service
    assert 'catalog["items"]' in service
    assert "validate_requested_pickup" in service

    assert '@frappe.whitelist(allow_guest=True, methods=["POST"])' in api
    assert "resolve_laundry_request_lines(items)" in api
    assert "STATUS_TRANSITIONS" in api
    assert '"Delivered": set()' in api
    assert '"Cancelled": set()' in api
    assert 'request.has_permission("write")' in api
    assert "Pending Folio Posting" in api

    assert "secrets.token_urlsafe(24)" in controller
    assert "self.estimated_total = total" in controller
    assert "A Laundry Request cannot mix multiple currencies." in controller

    assert "/api/method/fnb_menu.api.laundry.create_request" in page
    assert 'catalog["items"]' in page
    assert "data-service-item" in page
    assert "Charge to Room" in page
    assert "Security contract: send identifiers/quantity/instruction only." in js
    assert "service_item:" in js
    assert "JSON.stringify(items)" in js

    assert 'category.service_key == "laundry"' in hub
    assert 'action_url = "/rhoguest-laundry"' in hub
    assert '{"from_route": "/rhoguest-laundry", "to_route": "rhoguest_laundry"}' in hooks
    assert "def resolve_public_service_item" in hub

    print("RhoGuest v0.2.0 laundry workflow: PASS")


if __name__ == "__main__":
    main()

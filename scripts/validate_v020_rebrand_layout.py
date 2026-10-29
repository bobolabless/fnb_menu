#!/usr/bin/env python3
"""Static contract for the RhoGuest Desk rebrand and two-column form layouts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RENAMED = {
    "FNB Menu Settings": "RhoGuest Menu Settings",
    "FNB Menu Book": "RhoGuest Menu Book",
    "FNB Menu Category": "RhoGuest Menu Category",
    "FNB Menu Entry": "RhoGuest Menu Entry",
    "FNB Self Order": "RhoGuest Self Order",
    "FNB Self Order Item": "RhoGuest Self Order Item",
}

JSON_PATHS = [
    "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/rhoguest_menu_settings.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_menu_book/rhoguest_menu_book.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_menu_category/rhoguest_menu_category.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_menu_entry/rhoguest_menu_entry.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_self_order/rhoguest_self_order.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_service_category/rhoguest_service_category.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_service_item/rhoguest_service_item.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_laundry_request/rhoguest_laundry_request.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_facility_reservation/rhoguest_facility_reservation.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_spa_resource/rhoguest_spa_resource.json",
    "fnb_menu/fnb_menu/doctype/rhoguest_spa_appointment/rhoguest_spa_appointment.json",
]


def load(path):
    return json.loads((ROOT / path).read_text())


def main():
    # The actual standard DocTypes must now use RhoGuest names.
    for path in JSON_PATHS[:5]:
        doc = load(path)
        assert not doc["name"].startswith("FNB ")

    expected_names = [
        "RhoGuest Menu Settings",
        "RhoGuest Menu Book",
        "RhoGuest Menu Category",
        "RhoGuest Menu Entry",
        "RhoGuest Self Order",
    ]
    assert [load(path)["name"] for path in JSON_PATHS[:5]] == expected_names

    child = load(
        "fnb_menu/fnb_menu/doctype/rhoguest_self_order_item/"
        "rhoguest_self_order_item.json"
    )
    assert child["name"] == "RhoGuest Self Order Item"

    # Old standard source paths must not remain, otherwise Frappe could sync
    # duplicate legacy DocTypes back into Desk.
    for old_dir in (
        "fnb_menu_settings",
        "fnb_menu_book",
        "fnb_menu_category",
        "fnb_menu_entry",
        "fnb_self_order",
        "fnb_self_order_item",
    ):
        assert not (ROOT / "fnb_menu/fnb_menu/doctype" / old_dir).exists()

    patch = (
        ROOT
        / "fnb_menu/patches/v0_2/rename_fnb_doctypes_to_rhoguest.py"
    ).read_text()
    for old, new in RENAMED.items():
        assert old in patch
        assert new in patch
    assert "update tabSingles" in patch
    assert "frappe.rename_doc" in patch

    # High-use forms must have at least one actual Column Break. Settings and
    # major transactions should contain several balanced sections.
    counts = {}
    for path in JSON_PATHS:
        doc = load(path)
        counts[doc["name"]] = sum(
            1 for field in doc["fields"] if field["fieldtype"] == "Column Break"
        )

    assert counts["RhoGuest Menu Settings"] >= 8
    assert counts["RhoGuest Self Order"] >= 5
    assert counts["RhoGuest Service Category"] >= 4
    assert counts["RhoGuest Service Item"] >= 4
    assert counts["RhoGuest Laundry Request"] >= 4
    assert counts["RhoGuest Facility Reservation"] >= 4
    assert counts["RhoGuest Spa Resource"] >= 1
    assert counts["RhoGuest Spa Appointment"] >= 4

    workspace = load("fnb_menu/fnb_menu/workspace/rhoguest/rhoguest.json")
    settings_text = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/"
        "rhoguest_menu_settings.json"
    ).read_text()
    settings_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/"
        "rhoguest_menu_settings.js"
    ).read_text()
    dashboard_js = (
        ROOT
        / "fnb_menu/fnb_menu/page/rhoguest_dashboard/"
        "rhoguest_dashboard.js"
    ).read_text()
    workspace_text = json.dumps(workspace)
    assert "RhoGuest Menu Settings" in workspace_text
    assert "RhoGuest Menu Book" in workspace_text
    assert "RhoGuest Self Order" in workspace_text
    assert "FNB Menu Settings" not in workspace_text
    assert "FNB Self Order" not in workspace_text
    assert "F&B" not in settings_text
    assert "F&B" not in settings_js
    assert "Active Food & Beverage" in dashboard_js
    assert "Awaiting Food & Beverage Payment" in dashboard_js

    runtime_files = [
        ROOT / "fnb_menu/api/checkout.py",
        ROOT / "fnb_menu/api/dashboard.py",
        ROOT / "fnb_menu/api/kitchen.py",
        ROOT / "fnb_menu/api/menu_admin.py",
        ROOT / "fnb_menu/api/menu_designer.py",
        ROOT / "fnb_menu/menu_service.py",
        ROOT / "fnb_menu/migration.py",
        ROOT / "fnb_menu/notifications.py",
        ROOT / "fnb_menu/payment_events.py",
        ROOT / "fnb_menu/routing.py",
        ROOT / "fnb_menu/install.py",
    ]
    runtime = "\n".join(path.read_text() for path in runtime_files)
    for old in RENAMED:
        assert old not in runtime

    # Public website controllers are runtime code too. The original rebrand
    # contract intentionally expands beyond API/services so renamed DocTypes
    # cannot survive in a page controller and cause a post-migrate 500.
    public_page_files = sorted((ROOT / "fnb_menu/www").glob("*.py"))
    public_runtime = "\n".join(path.read_text() for path in public_page_files)
    for old in RENAMED:
        assert old not in public_runtime

    kitchen_html = (ROOT / "fnb_menu/www/fnb_kitchen.html").read_text()
    assert "RhoHMS F&B Menu" not in kitchen_html
    assert "RhoGuest Food & Beverage" in kitchen_html

    print("RhoGuest v0.2.0 rebrand and two-column layouts: PASS")


if __name__ == "__main__":
    main()

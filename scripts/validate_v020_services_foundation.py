#!/usr/bin/env python3
"""Static contract checks for the RhoGuest v0.2.0 service foundation."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text())


def field_map(doc):
    return {row["fieldname"]: row for row in doc.get("fields", [])}


def literal_assignment(path: Path, variable: str):
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{variable} not found in {path}")


def main():
    category_path = (
        "fnb_menu/fnb_menu/doctype/rhoguest_service_category/"
        "rhoguest_service_category.json"
    )
    item_path = (
        "fnb_menu/fnb_menu/doctype/rhoguest_service_item/"
        "rhoguest_service_item.json"
    )

    category = load_json(category_path)
    item = load_json(item_path)

    assert category["name"] == "RhoGuest Service Category"
    assert category["module"] == "FNB Menu"
    assert category["autoname"] == "field:service_key"
    assert category["title_field"] == "category_name"

    category_fields = field_map(category)
    required_category_fields = {
        "category_name",
        "service_key",
        "service_type",
        "workflow_type",
        "sort_order",
        "enabled",
        "show_on_portal",
        "operating_hours",
        "location",
        "requires_guest_identification",
        "requires_room_number",
        "allows_reservation",
        "allows_ordering",
        "allows_payment",
        "allows_charge_to_room",
    }
    assert required_category_fields <= set(category_fields)
    assert category_fields["enabled"]["default"] == "0"
    assert category_fields["show_on_portal"]["default"] == "0"
    assert category_fields["service_key"]["unique"] == 1

    assert item["name"] == "RhoGuest Service Item"
    assert item["module"] == "FNB Menu"
    assert item["title_field"] == "service_name"

    item_fields = field_map(item)
    required_item_fields = {
        "service_category",
        "service_name",
        "service_key",
        "sort_order",
        "enabled",
        "available_to_guests",
        "pricing_mode",
        "fixed_price",
        "currency",
        "erpnext_item",
        "allow_charge_to_room",
        "requires_reservation",
        "duration_minutes",
        "fulfilment_time_minutes",
        "capacity",
        "location",
    }
    assert required_item_fields <= set(item_fields)
    assert item_fields["service_category"]["options"] == "RhoGuest Service Category"
    assert item_fields["erpnext_item"]["options"] == "Item"
    assert "ERPNext Item Price" in item_fields["pricing_mode"]["options"]

    category_controller = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_service_category/"
        "rhoguest_service_category.py"
    ).read_text()
    item_controller = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/rhoguest_service_item/"
        "rhoguest_service_item.py"
    ).read_text()

    assert "normalize_service_key" in category_controller
    assert "Information Only" in category_controller
    assert "Allows Charge to Room requires Allows Paid Services" in category_controller

    assert "_validate_category_capabilities" in item_controller
    assert "_validate_pricing" in item_controller
    assert "_validate_unique_category_key" in item_controller

    defaults = literal_assignment(
        ROOT / "fnb_menu/service_catalog.py", "DEFAULT_SERVICE_CATEGORIES"
    )
    keys = [row["service_key"] for row in defaults]
    assert len(defaults) == 10
    assert len(keys) == len(set(keys))
    assert {
        "food-beverage",
        "laundry",
        "swimming-pool",
        "gym-fitness",
        "spa-wellness",
        "transport",
        "housekeeping",
        "recreation",
        "guest-requests",
        "hotel-information",
    } == set(keys)

    install = (ROOT / "fnb_menu/install.py").read_text()
    assert "ensure_default_service_categories" in install
    assert install.count("ensure_default_service_categories()") >= 2

    print("RhoGuest v0.2.0 services foundation: PASS")


if __name__ == "__main__":
    main()

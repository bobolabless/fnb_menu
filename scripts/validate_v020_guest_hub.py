#!/usr/bin/env python3
"""Static contract checks for the RhoGuest v0.2.0 Guest Services Hub."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text())


def field_map(doc):
    return {row["fieldname"]: row for row in doc.get("fields", [])}


def main():
    settings = load_json(
        "fnb_menu/fnb_menu/doctype/fnb_menu_settings/fnb_menu_settings.json"
    )
    fields = field_map(settings)

    required = {
        "guest_hub_enabled",
        "guest_hub_title",
        "guest_hub_subtitle",
        "show_service_items_on_hub",
    }
    assert required <= set(fields)
    assert fields["guest_hub_enabled"]["default"] == "0"
    assert fields["show_service_items_on_hub"]["default"] == "1"

    service = (ROOT / "fnb_menu/guest_service.py").read_text()
    page_py = (ROOT / "fnb_menu/www/rhoguest.py").read_text()
    page_html = (ROOT / "fnb_menu/www/rhoguest.html").read_text()
    css = (ROOT / "fnb_menu/public/css/rhoguest.css").read_text()
    settings_js = (
        ROOT
        / "fnb_menu/fnb_menu/doctype/fnb_menu_settings/fnb_menu_settings.js"
    ).read_text()

    assert 'filters={' in service
    assert '"enabled": 1' in service
    assert '"show_on_portal": 1' in service
    assert '"available_to_guests": 1' in service
    assert "get_public_menu_route" in service
    assert 'category.service_key == "food-beverage"' in service
    assert "ERPNext Item Price" in service
    assert "item_price(" in service
    assert "return None" in service

    assert "get_public_guest_hub" in page_py
    assert "theme_slug" in page_py
    assert "Guest services are not published yet" in page_html
    assert "Please contact the hotel team for this service." in page_html
    assert 'service["items"]' in page_html
    assert "service.items" not in page_html
    assert "/assets/fnb_menu/css/rhoguest.css" in page_html
    assert ".rhoguest-shell" in css
    assert "Preview Guest Services Hub" in settings_js

    # No public transaction/API endpoint is introduced by Phase 2B.
    assert "/api/method/" not in page_html
    assert "fetch(" not in page_html
    assert "<form" not in page_html.lower()

    print("RhoGuest v0.2.0 guest hub: PASS")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Static contract checks for the RhoGuest v0.2.0 routing foundation."""

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
        "fnb_menu/fnb_menu/doctype/rhoguest_menu_settings/rhoguest_menu_settings.json"
    )
    aliases = load_json(
        "fnb_menu/fnb_menu/doctype/rhoguest_route_alias/rhoguest_route_alias.json"
    )
    hooks = (ROOT / "fnb_menu/hooks.py").read_text()
    routing = (ROOT / "fnb_menu/routing.py").read_text()
    version = (ROOT / "fnb_menu/__init__.py").read_text()

    fields = field_map(settings)
    required = {
        "public_menu_route",
        "route_redirect_http_status",
        "keep_previous_routes",
        "route_preview",
        "legacy_qr_routes",
    }
    missing = sorted(required - set(fields))
    assert not missing, f"Missing RhoGuest route settings fields: {missing}"

    assert fields["legacy_qr_routes"]["options"] == "RhoGuest Route Alias"
    assert fields["public_menu_route"]["default"] == "/menu"
    for fieldname in required:
        assert int(fields[fieldname].get("permlevel", 0)) == 1, (
            f"{fieldname} must be restricted to routing administrators"
        )
    assert any(
        row.get("role") == "System Manager"
        and int(row.get("permlevel", 0)) == 1
        and row.get("read")
        and row.get("write")
        for row in settings.get("permissions", [])
    ), "System Manager must have permlevel 1 routing access"
    assert aliases["istable"] == 1

    alias_fields = field_map(aliases)
    assert {"route", "enabled", "note"} <= set(alias_fields)

    assert 'app_title = "RhoGuest"' in hooks
    assert '{"from_route": "/fnb-menu", "to_route": "fnb_menu"}' in hooks
    assert '{"from_route": "/fnb-kitchen", "to_route": "fnb_kitchen"}' in hooks

    assert 'INTERNAL_MENU_ROUTE = "/fnb-menu"' in routing
    assert "rhoguest_managed" in routing
    assert "Website Settings" in routing
    assert "def validate_route_change_authority" in routing
    assert "System Manager" in routing
    assert '__version__ = "0.2.0.dev0"' in version

    print("RhoGuest v0.2.0 routing foundation: PASS")


if __name__ == "__main__":
    main()

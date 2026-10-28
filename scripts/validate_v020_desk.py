#!/usr/bin/env python3
"""Static contract checks for the RhoGuest Desk Workspace, Dashboard and manuals."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    workspace = load_json(
        "fnb_menu/fnb_menu/workspace/rhoguest/rhoguest.json"
    )
    page = load_json(
        "fnb_menu/fnb_menu/page/rhoguest_dashboard/rhoguest_dashboard.json"
    )

    assert workspace["doctype"] == "Workspace"
    assert workspace["label"] == "RhoGuest"
    assert workspace["title"] == "RhoGuest"
    assert workspace["module"] == "FNB Menu"
    assert workspace["public"] == 1
    assert workspace["is_hidden"] == 0
    assert workspace["icon"] == "home"

    shortcut_labels = {row["label"] for row in workspace["shortcuts"]}
    assert {
        "RhoGuest Dashboard",
        "Laundry Requests",
        "Guest Services Hub",
        "Public F&B Menu",
        "Service Categories",
        "Service Items",
        "RhoGuest Settings",
    } <= shortcut_labels

    assert page["doctype"] == "Page"
    assert page["name"] == "rhoguest-dashboard"
    assert page["module"] == "FNB Menu"
    roles = {row["role"] for row in page["roles"]}
    assert {"System Manager", "Sales Manager", "Sales User"} <= roles

    api = (ROOT / "fnb_menu/api/dashboard.py").read_text()
    js = (
        ROOT
        / "fnb_menu/fnb_menu/page/rhoguest_dashboard/"
        "rhoguest_dashboard.js"
    ).read_text()
    css = (ROOT / "fnb_menu/public/css/rhoguest_dashboard.css").read_text()

    assert '@frappe.whitelist()' in api
    assert 'frappe.session.user == "Guest"' in api
    assert 'frappe.has_permission("RhoGuest Laundry Request", "read")' in api
    assert '"pending_folio_posting"' in api
    assert '"fnb_active"' in api
    assert '"recent_laundry"' in api

    assert "fnb_menu.api.dashboard.get_dashboard_data" in js
    assert "RhoGuest Dashboard" in js
    assert "Pending Folio Posting" in js
    assert "Recent Laundry Requests" in js
    assert "rhoguest_dashboard.css" in js
    assert ".rgd-shell" in css

    setup = (ROOT / "docs/RHOGUEST_SETUP_MANUAL.md").read_text()
    user = (ROOT / "docs/RHOGUEST_USER_MANUAL.md").read_text()
    install = (ROOT / "INSTALL.md").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "Rhocom Technology Limited" in setup
    assert "RhoGuest Workspace" in setup
    assert "Laundry Setup" in setup
    assert "Validation Commands" in setup
    assert "RhoGuest Dashboard" in user
    assert "Laundry — Staff Operations" in user
    assert "Daily Operating Checklist" in user
    assert "docs/RHOGUEST_SETUP_MANUAL.md" in readme
    assert "docs/RHOGUEST_USER_MANUAL.md" in readme
    assert "docs/RHOGUEST_SETUP_MANUAL.md" in install

    print("RhoGuest v0.2.0 desk workspace/dashboard/manuals: PASS")


if __name__ == "__main__":
    main()

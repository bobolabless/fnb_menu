"""Rename legacy FNB user-facing DocTypes to RhoGuest names.

The Python package and internal Frappe module remain fnb_menu / FNB Menu for
upgrade compatibility. This patch changes the actual Desk DocType identities
so hotel users no longer see the legacy FNB names.

It runs before model sync. Existing records/tables are renamed in place, and
Single settings rows are explicitly moved because Single values live in
tabSingles rather than a dedicated DocType table.
"""

import frappe


RENAMES = (
    ("FNB Menu Settings", "RhoGuest Menu Settings"),
    ("FNB Menu Book", "RhoGuest Menu Book"),
    ("FNB Menu Category", "RhoGuest Menu Category"),
    ("FNB Menu Entry", "RhoGuest Menu Entry"),
    ("FNB Self Order", "RhoGuest Self Order"),
    ("FNB Self Order Item", "RhoGuest Self Order Item"),
)


def execute():
    for old, new in RENAMES:
        old_exists = frappe.db.exists("DocType", old)
        new_exists = frappe.db.exists("DocType", new)

        # Existing installations have the old DocType. Rename before schema
        # sync so links, child table options and historical records are kept.
        if old_exists and not new_exists:
            frappe.rename_doc(
                "DocType",
                old,
                new,
                force=True,
                show_alert=False,
                rebuild_search=False,
            )

        # Single DocType values are stored by doctype name in tabSingles.
        if old == "FNB Menu Settings":
            frappe.db.sql(
                """
                update tabSingles
                set doctype = %s
                where doctype = %s
                """,
                (new, old),
            )

    frappe.clear_cache()

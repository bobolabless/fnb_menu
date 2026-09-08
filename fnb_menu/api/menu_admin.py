import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def bulk_set_self_ordering(menu_book, enabled=1):
    if not menu_book:
        frappe.throw(_("Menu Book is required."))

    frappe.get_doc("FNB Menu Book", menu_book)

    enabled = cint(enabled)

    rows = frappe.get_all(
        "FNB Menu Entry",
        filters={"menu_book": menu_book},
        fields=[
            "name",
            "erpnext_item",
            "is_available",
            "show_on_menu",
        ],
        limit_page_length=5000,
    )

    changed = 0
    skipped_unlinked = 0

    for row in rows:
        if enabled:
            if not row.erpnext_item:
                skipped_unlinked += 1
                continue

            value = 1 if row.is_available and row.show_on_menu else 0
        else:
            value = 0

        frappe.db.set_value(
            "FNB Menu Entry",
            row.name,
            "allow_self_order",
            value,
            update_modified=False,
        )
        changed += 1

    frappe.db.commit()

    return {
        "menu_book": menu_book,
        "enabled": bool(enabled),
        "changed": changed,
        "skipped_unlinked": skipped_unlinked,
        "note": (
            "Unlinked fallback-price-only menu lines remain display-only "
            "until an ERPNext Item or combo mapping is configured."
        ),
    }

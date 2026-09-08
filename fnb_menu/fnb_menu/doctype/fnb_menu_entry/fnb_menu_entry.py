import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FNBMenuEntry(Document):
    def validate(self):
        if self.category:
            category_book = frappe.db.get_value(
                "FNB Menu Category",
                self.category,
                "menu_book"
            )
            if category_book and category_book != self.menu_book:
                frappe.throw(
                    "Selected category belongs to another Menu Book."
                )

        # This field describes the mapping state only.
        # Final price source is resolved at render time because Item Price
        # validity and the Menu Book Price List can change independently.
        self.link_status = "Linked" if self.erpnext_item else "Unlinked"

        if flt(self.fallback_price) < 0:
            frappe.throw("Backend / Fallback Price cannot be negative.")

        # Unlinked entries can appear on the public digital menu using
        # fallback_price, but cannot be posted to ERPNext Sales Order/POS.
        if not self.erpnext_item and self.allow_self_order:
            self.allow_self_order = 0

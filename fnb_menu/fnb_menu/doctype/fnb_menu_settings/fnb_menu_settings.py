import frappe
from frappe import _
from frappe.model.document import Document

from fnb_menu.routing import (
    preserve_previous_public_route,
    sync_rhoguest_routes,
    validate_rhoguest_settings,
    validate_route_change_authority,
)


class FNBMenuSettings(Document):
    def validate(self):
        # Public self-orders must remain prepaid.
        self.require_payment = 1

        # Public QR routing is security-sensitive. Enforce the role server-side
        # before any compatibility alias is added or any redirect is synchronized.
        validate_route_change_authority(self)

        # Validate public QR routes independently of F&B/payment configuration.
        preserve_previous_public_route(self)
        validate_rhoguest_settings(self)

        if self.default_food_menu:
            self._validate_menu(self.default_food_menu, "Food")

        if self.default_drinks_menu:
            self._validate_menu(self.default_drinks_menu, "Drinks")

        if self.self_ordering_enabled:
            missing = []

            for fieldname, label in [
                ("company", _("Hotel Company")),
                ("default_selling_price_list", _("Default Selling Price List")),
                ("default_customer", _("Default Guest Customer")),
                ("payment_gateway_account", _("Payment Gateway Account")),
            ]:
                if not self.get(fieldname):
                    missing.append(label)

            if missing:
                frappe.throw(
                    _("Self ordering cannot be enabled until these are configured: {0}").format(
                        ", ".join(missing)
                    )
                )

    def on_update(self):
        # RhoGuest updates only redirects it owns. Other Website Settings
        # redirects remain untouched.
        sync_rhoguest_routes(self)

    def _validate_menu(self, menu_name, expected_type):
        row = frappe.db.get_value(
            "FNB Menu Book",
            menu_name,
            ["company", "menu_type"],
            as_dict=True,
        )

        if not row:
            frappe.throw(_("Menu {0} does not exist.").format(menu_name))

        if self.company and row.company != self.company:
            frappe.throw(_("Menu {0} belongs to a different Company.").format(menu_name))

        if row.menu_type != expected_type:
            frappe.throw(_("{0} must be a {1} menu.").format(menu_name, expected_type))

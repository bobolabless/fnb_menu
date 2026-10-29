"""Public RhoGuest Guest Services Hub page."""

import frappe

from fnb_menu.guest_service import get_public_guest_hub
from fnb_menu.menu_service import theme_slug

no_cache = 1


def get_context(context):
    context.no_cache = 1

    hub = get_public_guest_hub()
    context.hub = hub
    context.brand = hub.brand
    context.services = hub.services
    context.theme_slug = theme_slug(
        frappe.db.get_single_value("RhoGuest Menu Settings", "menu_theme")
        or "Classic Gold"
    )
    context.title = f"{hub.brand.hotel_name} - {hub.title}"

"""Public RhoGuest Laundry Request page."""

import frappe
from frappe.sessions import get_csrf_token

from fnb_menu.laundry_service import get_public_laundry_catalog
from fnb_menu.menu_service import get_company_brand, get_settings, theme_slug

no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.csrf_token = get_csrf_token()

    settings = get_settings()
    context.settings = settings
    context.brand = (
        get_company_brand(settings.company)
        if settings.company
        else frappe._dict({"hotel_name": "Hotel", "logo": None, "currency": "NGN"})
    )
    context.catalog = get_public_laundry_catalog()
    context.theme_slug = theme_slug(settings.menu_theme)
    context.title = f"{context.brand.hotel_name} - Laundry Service"

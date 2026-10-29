"""Shared website context builder for Pool/Gym reservation pages."""

import frappe
from frappe.sessions import get_csrf_token

from fnb_menu.facility_service import get_public_facility_catalog
from fnb_menu.menu_service import get_company_brand, get_settings, theme_slug


def build_context(context, category_key):
    settings = get_settings()
    context.no_cache = 1
    context.csrf_token = get_csrf_token()
    context.settings = settings
    context.brand = (
        get_company_brand(settings.company)
        if settings.company
        else frappe._dict({"hotel_name": "Hotel", "logo": None, "currency": "NGN"})
    )
    context.catalog = get_public_facility_catalog(category_key)
    context.category_key = category_key
    context.theme_slug = theme_slug(settings.menu_theme)

    category_name = (
        context.catalog.category.category_name
        if context.catalog.category
        else ("Swimming Pool" if category_key == "swimming-pool" else "Gym & Fitness")
    )
    context.facility_name = category_name
    context.title = f"{context.brand.hotel_name} - {category_name}"

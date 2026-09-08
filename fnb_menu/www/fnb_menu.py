import frappe
from frappe.sessions import get_csrf_token
from frappe.utils import cint

from fnb_menu.menu_service import get_company_brand, get_public_menus, get_settings, theme_slug

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
    context.menus = get_public_menus()
    context.self_ordering_enabled = cint(settings.self_ordering_enabled)
    context.theme_slug = theme_slug(settings.menu_theme)
    context.layout_slug = theme_slug(settings.menu_layout)
    context.requested_menu = (frappe.form_dict.get("menu") or "").strip().lower()
    context.title = f"{context.brand.hotel_name} - Menu"

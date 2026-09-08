import frappe
from frappe import _
from frappe.utils import cint, flt

OLD_SETTINGS = "Luxury Menu Settings"
OLD_BOOK = "Luxury Menu Book"
OLD_CATEGORY = "Luxury Menu Category"
OLD_ENTRY = "Luxury Menu Entry"

NEW_SETTINGS = "FNB Menu Settings"
NEW_BOOK = "FNB Menu Book"
NEW_CATEGORY = "FNB Menu Category"
NEW_ENTRY = "FNB Menu Entry"


def _doctype_exists(name):
    return bool(frappe.db.exists("DocType", name))


def _copy_if_field(src, dst, fieldname):
    if src.meta.has_field(fieldname) and dst.meta.has_field(fieldname):
        dst.set(fieldname, src.get(fieldname))


@frappe.whitelist()
def migrate_from_restaurant_luxury():
    """Copy menu configuration from the legacy restaurant_luxury app.

    The old and new apps can be installed together because FNB Menu uses
    distinct DocType names and the public route /fnb-menu. The routine is
    intentionally non-destructive: it never deletes old records.
    """
    required = [OLD_SETTINGS, OLD_BOOK, OLD_CATEGORY, OLD_ENTRY]
    missing = [name for name in required if not _doctype_exists(name)]
    if missing:
        frappe.throw(_("Legacy menu DocTypes are missing: {0}").format(", ".join(missing)))

    old_settings = frappe.get_single(OLD_SETTINGS)
    new_settings = frappe.get_single(NEW_SETTINGS)

    setting_fields = [
        "company", "brand_location_label", "show_company_logo", "show_company_name",
        "menu_theme", "menu_layout", "category_navigation", "show_search",
        "show_item_images", "show_item_description", "show_prices",
        "full_bleed_background", "default_selling_price_list",
        "hide_unavailable_items", "self_ordering_enabled", "require_payment",
        "default_customer", "payment_gateway_account", "minimum_order_amount",
        "allow_room_service", "allow_dine_in", "allow_takeaway", "warehouse",
        "sales_taxes_and_charges_template",
    ]
    for fieldname in setting_fields:
        _copy_if_field(old_settings, new_settings, fieldname)

    book_map = {}
    category_map = {}
    entry_count = 0

    for row in frappe.get_all(OLD_BOOK, fields=["*"], order_by="creation asc", limit_page_length=1000):
        existing = frappe.db.exists(NEW_BOOK, {
            "company": row.company, "menu_type": row.menu_type, "title": row.title
        })
        if existing:
            book_map[row.name] = existing
            continue
        doc = frappe.get_doc({
            "doctype": NEW_BOOK,
            "title": row.title,
            "company": row.company,
            "menu_type": row.menu_type,
            "published": cint(row.published),
            "price_list": row.price_list,
            "subtitle": row.subtitle,
            "sort_order": row.sort_order,
            "default_item_image": row.default_item_image,
            "notes": row.notes,
        })
        doc.insert(ignore_permissions=True)
        book_map[row.name] = doc.name

    for row in frappe.get_all(OLD_CATEGORY, fields=["*"], order_by="creation asc", limit_page_length=5000):
        new_book = book_map.get(row.menu_book)
        if not new_book:
            continue
        existing = frappe.db.exists(NEW_CATEGORY, {
            "menu_book": new_book, "category_name": row.category_name
        })
        if existing:
            category_map[row.name] = existing
            continue
        doc = frappe.get_doc({
            "doctype": NEW_CATEGORY,
            "menu_book": new_book,
            "category_name": row.category_name,
            "display_title": row.display_title,
            "sort_order": row.sort_order,
            "enabled": cint(row.enabled),
            "description": row.description,
        })
        doc.insert(ignore_permissions=True)
        category_map[row.name] = doc.name

    for row in frappe.get_all(OLD_ENTRY, fields=["*"], order_by="creation asc", limit_page_length=10000):
        new_book = book_map.get(row.menu_book)
        new_category = category_map.get(row.category)
        if not new_book or not new_category:
            continue
        existing = frappe.db.exists(NEW_ENTRY, {
            "menu_book": new_book,
            "category": new_category,
            "display_name": row.display_name,
            "sort_order": row.sort_order,
        })
        if existing:
            continue
        doc = frappe.get_doc({
            "doctype": NEW_ENTRY,
            "menu_book": new_book,
            "category": new_category,
            "display_name": row.display_name,
            "display_description": row.display_description,
            "menu_image": row.menu_image,
            "erpnext_item": row.erpnext_item,
            "fallback_price": flt(row.fallback_price),
            "sort_order": row.sort_order,
            "show_on_menu": cint(row.show_on_menu),
            "is_available": cint(row.is_available),
            "allow_self_order": cint(row.allow_self_order),
        })
        doc.insert(ignore_permissions=True)
        entry_count += 1

    old_food = old_settings.get("default_food_menu")
    old_drinks = old_settings.get("default_drinks_menu")
    new_settings.default_food_menu = book_map.get(old_food) if old_food else None
    new_settings.default_drinks_menu = book_map.get(old_drinks) if old_drinks else None
    new_settings.save(ignore_permissions=True)

    frappe.db.commit()
    return {
        "books": len(book_map),
        "categories": len(category_map),
        "entries_created": entry_count,
        "food_menu": new_settings.default_food_menu,
        "drinks_menu": new_settings.default_drinks_menu,
        "note": "Legacy records were copied, not deleted. Test FNB Menu before removing the old app.",
    }

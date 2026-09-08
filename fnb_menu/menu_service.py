import re

import frappe
from frappe.utils import cint, flt, getdate, nowdate


def get_settings():
    return frappe.get_single("FNB Menu Settings")


def get_company_brand(company_name):
    company = frappe.get_cached_doc("Company", company_name)
    logo = None

    if frappe.get_meta("Company").has_field("fnb_menu_logo"):
        logo = company.get("fnb_menu_logo")

    if not logo and company.meta.has_field("company_logo"):
        logo = company.get("company_logo")

    return frappe._dict({
        "company": company.name,
        "hotel_name": company.company_name or company.name,
        "logo": logo,
        "currency": company.default_currency,
    })


def theme_slug(value):
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        (value or "classic-gold").lower()
    ).strip("-")


def item_price(item_code, price_list):
    if not item_code or not price_list:
        return None

    today = getdate(nowdate())

    rows = frappe.get_all(
        "Item Price",
        filters={
            "item_code": item_code,
            "price_list": price_list,
            "selling": 1,
        },
        fields=[
            "name",
            "price_list_rate",
            "currency",
            "valid_from",
            "valid_upto",
            "uom",
        ],
        order_by="valid_from desc, modified desc",
        limit_page_length=50,
    )

    for row in rows:
        if row.valid_from and getdate(row.valid_from) > today:
            continue

        if row.valid_upto and getdate(row.valid_upto) < today:
            continue

        return frappe._dict({
            "rate": flt(row.price_list_rate),
            "currency": row.currency,
            "uom": row.uom,
            "item_price": row.name,
        })

    return None


def resolve_entry_price(entry, item, price_list, company_currency):
    # 1) Linked ERPNext Item Price.
    if item:
        erp_price = item_price(item.item_code, price_list)

        if erp_price and flt(erp_price.rate) > 0:
            return frappe._dict({
                "rate": flt(erp_price.rate),
                "currency": erp_price.currency or company_currency,
                "uom": erp_price.uom or item.stock_uom,
                "source": "ERPNext Item Price",
            })

    # 2) Backend / Fallback Price.
    if flt(entry.fallback_price) > 0:
        return frappe._dict({
            "rate": flt(entry.fallback_price),
            "currency": company_currency,
            "uom": item.stock_uom if item else None,
            "source": "Menu Fallback Price",
        })

    return None


def get_menu_book_payload(book_name):
    settings = get_settings()

    if not book_name:
        return None

    book = frappe.get_cached_doc("FNB Menu Book", book_name)

    if not cint(book.published):
        return None

    if settings.company and book.company != settings.company:
        return None

    price_list = book.price_list or settings.default_selling_price_list
    company_currency = (
        frappe.db.get_value("Company", book.company, "default_currency")
        or "NGN"
    )

    categories = frappe.get_all(
        "FNB Menu Category",
        filters={"menu_book": book.name, "enabled": 1},
        fields=[
            "name",
            "category_name",
            "display_title",
            "description",
            "sort_order",
        ],
        order_by="sort_order asc, creation asc",
        limit_page_length=500,
    )

    entries = frappe.get_all(
        "FNB Menu Entry",
        filters={"menu_book": book.name, "show_on_menu": 1},
        fields=[
            "name",
            "category",
            "display_name",
            "display_description",
            "erpnext_item",
            "fallback_price",
            "sort_order",
            "is_available",
            "allow_self_order",
            "menu_image",
            "link_status",
            "price_source",
        ],
        order_by="sort_order asc, creation asc",
        limit_page_length=3000,
    )

    by_category = {}

    for entry in entries:
        if cint(settings.hide_unavailable_items) and not cint(entry.is_available):
            continue

        item = None

        if entry.erpnext_item:
            item = frappe.db.get_value(
                "Item",
                entry.erpnext_item,
                [
                    "item_code",
                    "item_name",
                    "description",
                    "image",
                    "disabled",
                    "is_sales_item",
                    "stock_uom",
                ],
                as_dict=True,
            )

            if item and (cint(item.disabled) or not cint(item.is_sales_item)):
                item = None

        resolved = resolve_entry_price(
            entry,
            item,
            price_list,
            company_currency,
        )

        if not resolved:
            if entry.price_source != "No Price":
                frappe.db.set_value(
                    "FNB Menu Entry",
                    entry.name,
                    "price_source",
                    "No Price",
                    update_modified=False,
                )
            continue

        link_status = "Linked" if entry.erpnext_item else "Unlinked"

        if (
            entry.link_status != link_status
            or entry.price_source != resolved.source
        ):
            frappe.db.set_value(
                "FNB Menu Entry",
                entry.name,
                {
                    "link_status": link_status,
                    "price_source": resolved.source,
                },
                update_modified=False,
            )

        # Current v3.2 checkout posts a real ERPNext Item.
        # Therefore unlinked fallback-price-only lines remain display-only.
        orderable = bool(
            item
            and entry.erpnext_item
            and cint(entry.is_available)
            and cint(entry.allow_self_order)
        )

        by_category.setdefault(entry.category, []).append(
            frappe._dict({
                "entry_name": entry.name,
                "item_code": item.item_code if item else None,
                "item_name": (
                    entry.display_name
                    or (item.item_name if item else "")
                ),
                "description": (
                    entry.display_description
                    or (item.description if item else "")
                    or ""
                ),
                "image": (
                    entry.menu_image
                    or (item.image if item else None)
                    or book.default_item_image
                ),
                "price": resolved.rate,
                "currency": resolved.currency,
                "uom": resolved.uom,
                "price_source": resolved.source,
                "available": cint(entry.is_available),
                "allow_self_order": 1 if orderable else 0,
                "orderable": 1 if orderable else 0,
                "sort_order": entry.sort_order or 0,
            })
        )

    output = []

    for category in categories:
        items = by_category.get(category.name, [])

        if not items:
            continue

        items.sort(
            key=lambda row: (
                row.sort_order or 0,
                row.item_name or "",
            )
        )

        output.append(
            frappe._dict({
                "name": category.name,
                "label": category.display_title or category.category_name,
                "description": category.description or "",
                "items": items,
            })
        )

    return frappe._dict({
        "name": book.name,
        "title": book.title,
        "subtitle": book.subtitle or "",
        "menu_type": book.menu_type,
        "price_list": price_list,
        "categories": output,
    })


def get_public_menus():
    settings = get_settings()

    return frappe._dict({
        "food": (
            get_menu_book_payload(settings.default_food_menu)
            if settings.default_food_menu
            else None
        ),
        "drinks": (
            get_menu_book_payload(settings.default_drinks_menu)
            if settings.default_drinks_menu
            else None
        ),
    })


def get_public_menu():
    menus = get_public_menus()
    output = []

    for menu in (menus.food, menus.drinks):
        if menu:
            output.extend(menu.categories)

    return output


def allowed_item_codes():
    return {
        item.item_code
        for category in get_public_menu()
        for item in category["items"]
        if (
            item.item_code
            and item.available
            and item.allow_self_order
        )
    }


def get_item_for_order(item_code):
    if item_code not in allowed_item_codes():
        frappe.throw(
            "This item is not currently available for self ordering."
        )

    menus = get_public_menus()

    for menu in (menus.food, menus.drinks):
        if not menu:
            continue

        for category in menu.categories:
            for item in category["items"]:
                if (
                    item.item_code == item_code
                    and item.available
                    and item.allow_self_order
                ):
                    return (
                        frappe.get_cached_doc("Item", item_code),
                        frappe._dict({
                            "rate": item.price,
                            "currency": item.currency,
                            "uom": item.uom,
                            "price_source": item.price_source,
                        }),
                    )

    frappe.throw(
        "This item is not currently available for self ordering."
    )

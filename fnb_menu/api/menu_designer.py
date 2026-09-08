import csv
import io

import frappe
from frappe import _
from frappe.utils import cint, flt


def _clean_header(value):
    return str(value or "").replace("\ufeff", "").strip().lower()


def _file_content(file_url):
    if not file_url:
        frappe.throw(_("CSV file is required."))

    file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not file_name:
        frappe.throw(_("Uploaded CSV file could not be found."))

    raw = frappe.get_doc("File", file_name).get_content()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig", errors="replace")
    else:
        text = str(raw or "")

    return text.lstrip("\ufeff")


def _exact_item_match(value):
    value = (value or "").strip()
    if not value:
        return None
    if frappe.db.exists("Item", value):
        return value

    matches = frappe.get_all(
        "Item",
        filters={"item_name": value, "disabled": 0},
        pluck="name",
        limit_page_length=2,
    )
    return matches[0] if len(matches) == 1 else None


def _as_check(value, default=1):
    value = str(value if value is not None else "").strip().lower()
    if value == "":
        return default
    return 0 if value in ("0", "false", "no", "off") else 1


def _fallback_price(row):
    raw = (
        row.get("fallback_price")
        or row.get("menu_price")
        or row.get("price")
        or row.get("backend_price")
        or 0
    )
    cleaned = str(raw).replace(",", "").replace("₦", "").replace("N", "").strip()
    return flt(cleaned or 0)


@frappe.whitelist()
def import_menu_csv(menu_book, file_url, replace_existing=0):
    book = frappe.get_doc("FNB Menu Book", menu_book)
    content = _file_content(file_url)
    if not content.strip():
        frappe.throw(_("Uploaded CSV file is empty."))

    reader = csv.DictReader(io.StringIO(content))
    actual_headers = {_clean_header(header) for header in (reader.fieldnames or [])}
    required_headers = {"category", "item_name"}
    missing = required_headers - actual_headers
    if missing:
        frappe.throw(
            _("CSV must include at least: category,item_name. Detected headers: {0}").format(
                ", ".join(sorted(actual_headers)) or "None"
            )
        )

    if cint(replace_existing):
        for name in frappe.get_all(
            "FNB Menu Entry", filters={"menu_book": book.name}, pluck="name"
        ):
            frappe.delete_doc("FNB Menu Entry", name, ignore_permissions=True)
        for name in frappe.get_all(
            "FNB Menu Category", filters={"menu_book": book.name}, pluck="name"
        ):
            frappe.delete_doc("FNB Menu Category", name, ignore_permissions=True)

    categories = {
        row.category_name: row.name
        for row in frappe.get_all(
            "FNB Menu Category",
            filters={"menu_book": book.name},
            fields=["name", "category_name"],
            limit_page_length=1000,
        )
    }

    inserted = linked = fallback_priced = skipped = 0
    unresolved = []
    errors = []
    category_counter = len(categories)

    for row_no, raw_row in enumerate(reader, start=2):
        try:
            row = {
                _clean_header(key): (str(value).strip() if value is not None else "")
                for key, value in raw_row.items()
            }
            category_name = (row.get("category") or "").strip()
            display_name = (row.get("item_name") or "").strip()
            description = (row.get("description") or "").strip()

            if not category_name and not display_name:
                skipped += 1
                continue
            if not category_name:
                errors.append({"row": row_no, "item_name": display_name, "error": "Category is missing."})
                continue
            if not display_name:
                errors.append({"row": row_no, "item_name": "", "error": "Item name is missing."})
                continue

            requested_item = (row.get("erpnext_item") or row.get("item_code") or "").strip()
            item = _exact_item_match(requested_item or display_name)
            menu_price = _fallback_price(row)

            if category_name not in categories:
                category_counter += 1
                category = frappe.get_doc(
                    {
                        "doctype": "FNB Menu Category",
                        "menu_book": book.name,
                        "category_name": category_name,
                        "display_title": row.get("category_display_title") or category_name,
                        "sort_order": cint(row.get("category_sort_order") or category_counter * 10),
                        "enabled": 1,
                    }
                )
                category.insert(ignore_permissions=True)
                categories[category_name] = category.name

            requested_self_order = _as_check(row.get("allow_self_order"), default=0)
            actual_self_order = requested_self_order if item else 0

            if item:
                linked += 1
            else:
                unresolved.append(
                    {
                        "row": row_no,
                        "item_name": display_name,
                        "requested_link": requested_item,
                        "fallback_price": menu_price,
                        "display_only": True,
                    }
                )

            if menu_price > 0:
                fallback_priced += 1

            doc = frappe.get_doc(
                {
                    "doctype": "FNB Menu Entry",
                    "menu_book": book.name,
                    "category": categories[category_name],
                    "display_name": display_name,
                    "display_description": description,
                    "erpnext_item": item,
                    "fallback_price": menu_price,
                    "sort_order": cint(row.get("sort_order") or inserted * 10 + 10),
                    "show_on_menu": _as_check(row.get("show_on_menu"), default=1),
                    "is_available": _as_check(row.get("is_available"), default=1),
                    "allow_self_order": actual_self_order,
                    "menu_image": row.get("menu_image") or None,
                }
            )
            doc.insert(ignore_permissions=True)
            inserted += 1
        except Exception as exc:
            errors.append(
                {
                    "row": row_no,
                    "item_name": raw_row.get("item_name", "") if isinstance(raw_row, dict) else "",
                    "error": str(exc),
                }
            )

    frappe.db.commit()
    return {
        "menu_book": book.name,
        "inserted": inserted,
        "auto_linked": linked,
        "fallback_priced": fallback_priced,
        "skipped": skipped,
        "unresolved_count": len(unresolved),
        "error_count": len(errors),
        "unresolved": unresolved[:100],
        "errors": errors[:100],
        "note": "Unlinked entries with a fallback price are displayed, but remain display-only until an ERPNext Item is linked.",
    }


@frappe.whitelist()
def auto_link_items(menu_book):
    rows = frappe.get_all(
        "FNB Menu Entry",
        filters={"menu_book": menu_book, "erpnext_item": ["is", "not set"]},
        fields=["name", "display_name", "fallback_price"],
        limit_page_length=2000,
    )

    linked = 0
    unresolved = []
    for row in rows:
        item = _exact_item_match(row.display_name)
        if item:
            frappe.db.set_value(
                "FNB Menu Entry",
                row.name,
                {"erpnext_item": item, "link_status": "Linked"},
                update_modified=False,
            )
            linked += 1
        else:
            unresolved.append(
                {
                    "name": row.name,
                    "item_name": row.display_name,
                    "fallback_price": row.fallback_price,
                }
            )

    frappe.db.commit()
    return {"linked": linked, "unresolved_count": len(unresolved), "unresolved": unresolved[:100]}

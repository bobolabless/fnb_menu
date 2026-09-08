import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure_company_fields():
    create_custom_fields(
        {
            "Company": [
                {
                    "fieldname": "fnb_menu_branding_section",
                    "label": "FNB Menu Branding",
                    "fieldtype": "Section Break",
                    "insert_after": "company_name",
                    "collapsible": 1,
                },
                {
                    "fieldname": "fnb_menu_logo",
                    "label": "FNB Menu Logo",
                    "fieldtype": "Attach Image",
                    "insert_after": "fnb_menu_branding_section",
                    "description": "Optional logo override for the public Food & Beverage menu.",
                },
            ]
        },
        update=True,
    )

    # Non-destructive compatibility: copy the prior menu logo when the old
    # custom field still exists and the new field is blank.
    company_meta = frappe.get_meta("Company")
    if company_meta.has_field("luxury_menu_logo"):
        for row in frappe.get_all(
            "Company",
            fields=["name", "luxury_menu_logo", "fnb_menu_logo"],
            limit_page_length=500,
        ):
            if row.luxury_menu_logo and not row.fnb_menu_logo:
                frappe.db.set_value(
                    "Company",
                    row.name,
                    "fnb_menu_logo",
                    row.luxury_menu_logo,
                    update_modified=False,
                )

    frappe.clear_cache(doctype="Company")


def after_install():
    ensure_company_fields()


def after_migrate():
    ensure_company_fields()

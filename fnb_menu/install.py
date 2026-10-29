import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from fnb_menu.service_catalog import ensure_default_service_categories


_SETTINGS_DEFAULTS = {
    # Existing Single DocTypes store values in tabSingles. Adding a required
    # field with a JSON default does not automatically create the tabSingles
    # row on an already-installed site, so upgrades must backfill explicitly.
    "laundry_folio_posting_mode": "Manual",
    "laundry_staff_in_app_notifications": "1",
    "laundry_guest_email_notifications": "0",
    "laundry_staff_email_notifications": "0",
}


def ensure_settings_defaults():
    """Backfill newly-added FNB Menu Settings values on existing sites.

    Only missing tabSingles rows are inserted. Existing hotel configuration,
    including explicit zero values for notification toggles, is never changed.
    """

    doctype = "FNB Menu Settings"

    for fieldname, default in _SETTINGS_DEFAULTS.items():
        existing = frappe.db.sql(
            """
            select value
            from tabSingles
            where doctype = %s and field = %s
            limit 1
            """,
            (doctype, fieldname),
        )

        if existing:
            continue

        frappe.db.set_single_value(
            doctype,
            fieldname,
            default,
        )

    frappe.clear_cache(doctype=doctype)


def ensure_company_fields():
    """Create non-destructive Company branding fields used by RhoGuest."""

    create_custom_fields(
        {
            "Company": [
                {
                    "fieldname": "fnb_menu_branding_section",
                    "label": "RhoGuest Branding",
                    "fieldtype": "Section Break",
                    "insert_after": "company_name",
                    "collapsible": 1,
                },
                {
                    "fieldname": "fnb_menu_logo",
                    "label": "RhoGuest Logo",
                    "fieldtype": "Attach Image",
                    "insert_after": "fnb_menu_branding_section",
                    "description": "Optional logo override for RhoGuest public guest-service pages.",
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


def ensure_route_redirect_fields():
    """Mark redirect rows managed by RhoGuest without touching hotel-owned rows."""

    create_custom_fields(
        {
            "Website Route Redirect": [
                {
                    "fieldname": "rhoguest_managed",
                    "label": "RhoGuest Managed",
                    "fieldtype": "Check",
                    "default": "0",
                    "hidden": 1,
                    "read_only": 1,
                    "no_copy": 1,
                },
                {
                    "fieldname": "rhoguest_route_key",
                    "label": "RhoGuest Route Key",
                    "fieldtype": "Data",
                    "hidden": 1,
                    "read_only": 1,
                    "no_copy": 1,
                },
            ]
        },
        update=True,
    )

    frappe.clear_cache(doctype="Website Route Redirect")


def after_install():
    ensure_company_fields()
    ensure_route_redirect_fields()
    ensure_settings_defaults()
    # Default service categories are configuration scaffolding only: they are
    # created disabled and unpublished so installation never exposes a service.
    ensure_default_service_categories()


def after_migrate():
    ensure_company_fields()
    ensure_route_redirect_fields()
    ensure_settings_defaults()
    # Non-destructive on upgrades: only missing default keys are created.
    # Existing hotel-edited categories are never overwritten.
    ensure_default_service_categories()

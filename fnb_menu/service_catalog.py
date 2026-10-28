"""Non-destructive default RhoGuest service-category provisioning.

The defaults establish a common hospitality vocabulary across installations,
but they are intentionally disabled and unpublished. Hotels must explicitly
enable and publish the services they actually offer.
"""

from __future__ import annotations

import frappe

DEFAULT_SERVICE_CATEGORIES = [
    {
        "service_key": "food-beverage",
        "category_name": "Food & Beverage",
        "service_type": "Food & Beverage",
        "workflow_type": "Order + Fulfilment",
        "sort_order": 10,
        "allows_ordering": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "laundry",
        "category_name": "Laundry",
        "service_type": "Laundry",
        "workflow_type": "Request + Fulfilment",
        "sort_order": 20,
        "requires_guest_identification": 1,
        "requires_room_number": 1,
        "allows_ordering": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "swimming-pool",
        "category_name": "Swimming Pool",
        "service_type": "Swimming Pool",
        "workflow_type": "Access / Admission",
        "sort_order": 30,
        "requires_guest_identification": 1,
        "allows_reservation": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "gym-fitness",
        "category_name": "Gym & Fitness",
        "service_type": "Gym & Fitness",
        "workflow_type": "Access / Admission",
        "sort_order": 40,
        "requires_guest_identification": 1,
        "allows_reservation": 1,
    },
    {
        "service_key": "spa-wellness",
        "category_name": "Spa & Wellness",
        "service_type": "Spa & Wellness",
        "workflow_type": "Reservation",
        "sort_order": 50,
        "requires_guest_identification": 1,
        "allows_reservation": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "transport",
        "category_name": "Transport",
        "service_type": "Transport",
        "workflow_type": "Reservation",
        "sort_order": 60,
        "requires_guest_identification": 1,
        "allows_reservation": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "housekeeping",
        "category_name": "Housekeeping",
        "service_type": "Housekeeping",
        "workflow_type": "Request",
        "sort_order": 70,
        "requires_guest_identification": 1,
        "requires_room_number": 1,
    },
    {
        "service_key": "recreation",
        "category_name": "Recreation",
        "service_type": "Recreation",
        "workflow_type": "Reservation",
        "sort_order": 80,
        "requires_guest_identification": 1,
        "allows_reservation": 1,
        "allows_payment": 1,
        "allows_charge_to_room": 1,
    },
    {
        "service_key": "guest-requests",
        "category_name": "Guest Requests",
        "service_type": "Guest Requests",
        "workflow_type": "Request",
        "sort_order": 90,
        "requires_guest_identification": 1,
        "requires_room_number": 1,
    },
    {
        "service_key": "hotel-information",
        "category_name": "Hotel Information",
        "service_type": "Hotel Information",
        "workflow_type": "Information Only",
        "sort_order": 100,
    },
]


def ensure_default_service_categories():
    """Create missing default categories without modifying existing hotel data."""

    if not frappe.db.exists("DocType", "RhoGuest Service Category"):
        return

    for values in DEFAULT_SERVICE_CATEGORIES:
        service_key = values["service_key"]

        # The DocType name is the stable service key. Existing rows are owned by
        # the hotel after creation and are never overwritten by future migrations.
        if frappe.db.exists("RhoGuest Service Category", service_key):
            continue

        doc = frappe.get_doc(
            {
                "doctype": "RhoGuest Service Category",
                **values,
                "enabled": 0,
                "show_on_portal": 0,
            }
        )
        doc.insert(ignore_permissions=True)

import frappe
from frappe.sessions import get_csrf_token

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw("Login required", frappe.PermissionError)

    context.no_cache = 1
    context.csrf_token = get_csrf_token()
    context.title = "FNB Kitchen"
    context.orders = frappe.get_all(
        "FNB Self Order",
        filters={
            "payment_status": "Paid",
            "status": ["in", ["Sent to Kitchen", "Preparing", "Ready"]],
        },
        fields=[
            "name",
            "guest_name",
            "service_type",
            "room_number",
            "table_number",
            "status",
            "creation",
        ],
        order_by="creation asc",
        limit_page_length=100,
    )

    for order in context.orders:
        order["order_items"] = frappe.get_all(
            "FNB Self Order Item",
            filters={"parent": order.name, "parenttype": "FNB Self Order"},
            fields=["item_name", "qty", "special_instruction"],
            order_by="idx asc",
        )

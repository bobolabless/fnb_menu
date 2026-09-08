import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, nowdate

from fnb_menu.menu_service import get_item_for_order, get_settings


def _parse_cart(cart):
    if isinstance(cart, str):
        try:
            cart = json.loads(cart)
        except Exception:
            frappe.throw(_("Invalid cart data."))

    if not isinstance(cart, list) or not cart:
        frappe.throw(_("Your cart is empty."))
    if len(cart) > 50:
        frappe.throw(_("Too many cart lines."))

    out = []
    for row in cart:
        if not isinstance(row, dict):
            frappe.throw(_("Invalid cart line."))
        item_code = (row.get("item_code") or "").strip()
        qty = cint(row.get("qty") or 0)
        note = (row.get("special_instruction") or "").strip()[:500]
        if not item_code or qty < 1 or qty > 20:
            frappe.throw(_("Invalid item or quantity."))
        out.append({"item_code": item_code, "qty": qty, "special_instruction": note})
    return out


def _service_allowed(settings, service_type):
    mapping = {
        "Room Service": settings.allow_room_service,
        "Dine In": settings.allow_dine_in,
        "Takeaway": settings.allow_takeaway,
    }
    return bool(cint(mapping.get(service_type, 0)))


def _gateway_details(account):
    meta = frappe.get_meta("Payment Gateway Account")
    fields = ["payment_gateway", "payment_account"]
    for fieldname in ("payment_channel", "company", "currency"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    return frappe.db.get_value("Payment Gateway Account", account, fields, as_dict=True)


def _make_payment_request(sales_order, settings, email, phone):
    gateway = _gateway_details(settings.payment_gateway_account)
    if not gateway:
        frappe.throw(_("Invalid Payment Gateway Account."))
    if gateway.get("company") and gateway.company != sales_order.company:
        frappe.throw(_("The Payment Gateway Account belongs to a different Company."))

    meta = frappe.get_meta("Payment Request")
    values = {
        "doctype": "Payment Request",
        "payment_gateway_account": settings.payment_gateway_account,
        "payment_request_type": "Inward",
        "currency": sales_order.currency,
        "grand_total": sales_order.grand_total,
        "email_to": email,
        "subject": _("Payment for RhoHMS F&B Menu order {0}").format(sales_order.name),
        "reference_doctype": "Sales Order",
        "reference_name": sales_order.name,
        "company": sales_order.company,
        "party_type": "Customer",
        "party": sales_order.customer,
    }

    optional = {
        "payment_gateway": gateway.get("payment_gateway"),
        "payment_account": gateway.get("payment_account"),
        "payment_channel": gateway.get("payment_channel") or "Email",
        "party_name": frappe.db.get_value("Customer", sales_order.customer, "customer_name") or sales_order.customer,
        "phone_number": phone,
        "party_account_currency": sales_order.currency,
    }
    for fieldname, value in optional.items():
        if value not in (None, "") and meta.has_field(fieldname):
            values[fieldname] = value

    payment_request = frappe.get_doc(values)
    payment_request.flags.ignore_permissions = True
    payment_request.flags.mute_email = True
    payment_request.insert(ignore_permissions=True)
    payment_request.submit()
    payment_request.reload()

    # Older v15 gateway implementations may expose get_payment_url without
    # persisting payment_url during submit. Resolve it once if necessary.
    if not payment_request.payment_url and hasattr(payment_request, "get_payment_url"):
        payment_url = payment_request.get_payment_url()
        if payment_url:
            payment_request.db_set("payment_url", payment_url, update_modified=False)
            payment_request.payment_url = payment_url

    if not payment_request.payment_url:
        frappe.throw(_("Payment gateway did not return a payment URL."))

    return payment_request


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_checkout(
    guest_name,
    email,
    service_type,
    cart,
    phone=None,
    room_number=None,
    table_number=None,
):
    settings = get_settings()

    if not cint(settings.self_ordering_enabled):
        frappe.throw(_("Guest self ordering is currently disabled."))

    required = {
        "Hotel Company": settings.company,
        "Default Selling Price List": settings.default_selling_price_list,
        "Default Guest Customer": settings.default_customer,
        "Payment Gateway Account": settings.payment_gateway_account,
    }
    missing = [label for label, value in required.items() if not value]
    if missing:
        frappe.throw(_("Online ordering is not fully configured: {0}").format(", ".join(missing)))

    guest_name = (guest_name or "").strip()[:140]
    email = (email or "").strip()[:140]
    phone = (phone or "").strip()[:40]
    room_number = (room_number or "").strip()[:30]
    table_number = (table_number or "").strip()[:30]
    service_type = (service_type or "").strip()

    if not guest_name:
        frappe.throw(_("Guest name is required."))
    if not email or "@" not in email:
        frappe.throw(_("A valid email address is required."))
    if not _service_allowed(settings, service_type):
        frappe.throw(_("Selected service type is not available."))
    if service_type == "Room Service" and not room_number:
        frappe.throw(_("Room number is required."))
    if service_type == "Dine In" and not table_number:
        frappe.throw(_("Table number is required."))

    rows = _parse_cart(cart)
    validated = []
    subtotal = 0.0

    for row in rows:
        item, price = get_item_for_order(row["item_code"])
        rate = flt(price.rate)
        amount = rate * row["qty"]
        subtotal += amount
        validated.append(
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "item_group": item.item_group,
                "qty": row["qty"],
                "rate": rate,
                "amount": amount,
                "note": row["special_instruction"],
                "uom": price.uom or item.stock_uom,
            }
        )

    if settings.minimum_order_amount and subtotal < flt(settings.minimum_order_amount):
        frappe.throw(_("Minimum order amount not reached."))

    currency = frappe.db.get_value("Company", settings.company, "default_currency") or "NGN"

    order = frappe.get_doc(
        {
            "doctype": "FNB Self Order",
            "guest_name": guest_name,
            "email": email,
            "phone": phone,
            "service_type": service_type,
            "room_number": room_number,
            "table_number": table_number,
            "status": "Awaiting Payment",
            "payment_status": "Pending",
            "company": settings.company,
            "customer": settings.default_customer,
            "price_list": settings.default_selling_price_list,
            "currency": currency,
            "items": [
                {
                    "item_code": row["item_code"],
                    "item_name": row["item_name"],
                    "item_group": row["item_group"],
                    "qty": row["qty"],
                    "rate": row["rate"],
                    "amount": row["amount"],
                    "special_instruction": row["note"],
                }
                for row in validated
            ],
        }
    )
    order.insert(ignore_permissions=True)

    sales_order = frappe.get_doc(
        {
            "doctype": "Sales Order",
            "company": settings.company,
            "customer": settings.default_customer,
            "transaction_date": nowdate(),
            "delivery_date": add_days(nowdate(), 1),
            "selling_price_list": settings.default_selling_price_list,
            "currency": currency,
            "order_type": "Sales",
            "items": [
                {
                    "item_code": row["item_code"],
                    "qty": row["qty"],
                    "uom": row["uom"],
                    "rate": row["rate"],
                    "description": (
                        ((row["note"] + "\n\n") if row["note"] else "")
                        + (frappe.db.get_value("Item", row["item_code"], "description") or row["item_name"])
                    ),
                }
                for row in validated
            ],
        }
    )

    if settings.warehouse:
        for line in sales_order.items:
            line.warehouse = settings.warehouse
    if settings.sales_taxes_and_charges_template:
        sales_order.taxes_and_charges = settings.sales_taxes_and_charges_template

    sales_order.flags.ignore_permissions = True
    if hasattr(sales_order, "set_missing_values"):
        sales_order.run_method("set_missing_values")
    sales_order.run_method("calculate_taxes_and_totals")
    sales_order.insert(ignore_permissions=True)
    sales_order.submit()

    order.db_set(
        {
            "sales_order": sales_order.name,
            "subtotal": sales_order.net_total,
            "tax_amount": flt(sales_order.total_taxes_and_charges),
            "grand_total": sales_order.grand_total,
            "currency": sales_order.currency,
        }
    )

    try:
        payment_request = _make_payment_request(sales_order, settings, email, phone)
    except Exception:
        order.db_set({"status": "Payment Failed", "payment_status": "Failed"})
        frappe.log_error(
            title=f"RhoHMS F&B Menu Payment Request Failed - {order.name}",
            message=frappe.get_traceback(),
        )
        raise

    order.db_set("payment_request", payment_request.name)

    return {
        "order": order.name,
        "token": order.public_token,
        "payment_request": payment_request.name,
        "payment_url": payment_request.payment_url,
        "amount": sales_order.grand_total,
        "currency": sales_order.currency,
        "status": order.status,
    }


@frappe.whitelist(allow_guest=True)
def get_order_status(order_name, token):
    order = frappe.db.get_value(
        "FNB Self Order",
        {"name": order_name, "public_token": token},
        ["name", "status", "payment_status", "grand_total", "currency", "creation", "service_type"],
        as_dict=True,
    )
    if not order:
        frappe.throw(_("Order not found."))
    return order

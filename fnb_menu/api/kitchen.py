import frappe
from frappe import _
NEXT={"Sent to Kitchen":"Preparing","Preparing":"Ready","Ready":"Served"}
@frappe.whitelist()
def update_status(order_name,status):
    if frappe.session.user=="Guest":frappe.throw(_("Login required."),frappe.PermissionError)
    o=frappe.get_doc("FNB Self Order",order_name)
    if o.payment_status!="Paid":frappe.throw(_("Payment has not been verified."))
    if NEXT.get(o.status)!=status:frappe.throw(_("Invalid status transition."))
    o.db_set("status",status); return {"name":o.name,"status":status}

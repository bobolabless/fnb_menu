import frappe

def payment_request_updated(doc,method=None):
    if doc.reference_doctype!="Sales Order" or not doc.reference_name:return
    name=frappe.db.get_value("FNB Self Order",{"sales_order":doc.reference_name,"payment_request":doc.name},"name")
    if not name:return
    o=frappe.get_doc("FNB Self Order",name)
    if doc.status=="Paid" and o.payment_status!="Paid":
        pe=frappe.db.get_value("Payment Entry Reference",{"reference_doctype":"Sales Order","reference_name":doc.reference_name,"docstatus":1},"parent")
        o.db_set({"payment_status":"Paid","status":"Sent to Kitchen","payment_entry":pe})
        frappe.publish_realtime("fnb_menu_paid_order",{"order":o.name},after_commit=True)
    elif doc.status in ("Failed","Cancelled") and o.payment_status!="Paid":
        o.db_set({"payment_status":"Failed" if doc.status=="Failed" else "Cancelled","status":"Payment Failed" if doc.status=="Failed" else "Cancelled"})

def sync_paid_orders():
    for r in frappe.get_all("FNB Self Order",filters={"payment_status":"Pending","payment_request":["is","set"]},fields=["name","payment_request"],limit_page_length=200):
        if frappe.db.get_value("Payment Request",r.payment_request,"status")=="Paid": payment_request_updated(frappe.get_doc("Payment Request",r.payment_request))

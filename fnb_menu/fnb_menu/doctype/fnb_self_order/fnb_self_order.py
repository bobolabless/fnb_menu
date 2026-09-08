import secrets
import frappe
from frappe.model.document import Document
from frappe.utils import flt
class RhoHMSSelfOrder(Document):
    def before_insert(self):
        if not self.public_token: self.public_token=secrets.token_urlsafe(24)
    def validate(self):
        total=0
        for r in self.items or []:
            r.amount=flt(r.qty)*flt(r.rate); total+=r.amount
        self.subtotal=total

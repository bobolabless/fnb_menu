frappe.ui.form.on("FNB Self Order",{refresh(frm){
 if(frm.doc.payment_request)frm.add_custom_button(__("Open Payment Request"),()=>frappe.set_route("Form","Payment Request",frm.doc.payment_request),__("View"));
 if(frm.doc.sales_order)frm.add_custom_button(__("Open Sales Order"),()=>frappe.set_route("Form","Sales Order",frm.doc.sales_order),__("View"));
 const next={"Sent to Kitchen":"Preparing","Preparing":"Ready","Ready":"Served"}[frm.doc.status];
 if(next)frm.add_custom_button(__(next==="Preparing"?"Start Preparing":next==="Ready"?"Mark Ready":"Mark Served"),()=>frappe.call({method:"fnb_menu.api.kitchen.update_status",args:{order_name:frm.doc.name,status:next},freeze:true,callback:()=>frm.reload_doc()}));
}});

frappe.ui.form.on("FNB Menu Book", {
  refresh(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(__("Import Menu CSV"), () => {
      const d = new frappe.ui.Dialog({
        title: __("Import Existing Hotel Menu"),
        fields: [
          {
            fieldname: "file",
            fieldtype: "Attach",
            label: __("CSV File"),
            reqd: 1
          },
          {
            fieldname: "replace_existing",
            fieldtype: "Check",
            label: __("Replace Existing Categories & Lines"),
            default: 0
          }
        ],
        primary_action_label: __("Import"),
        primary_action(values) {
          d.hide();

          frappe.call({
            method: "fnb_menu.api.menu_designer.import_menu_csv",
            args: {
              menu_book: frm.doc.name,
              file_url: values.file,
              replace_existing: values.replace_existing ? 1 : 0
            },
            freeze: true,
            freeze_message: __("Importing menu..."),
            callback(r) {
              if (r.message) {
                frappe.msgprint(
                  `<pre>${frappe.utils.escape_html(
                    JSON.stringify(r.message, null, 2)
                  )}</pre>`
                );
              }
            }
          });
        }
      });

      d.show();
    }, __("Menu Tools"));

    frm.add_custom_button(__("Auto-Link ERPNext Items"), () => {
      frappe.call({
        method: "fnb_menu.api.menu_designer.auto_link_items",
        args: { menu_book: frm.doc.name },
        freeze: true,
        callback(r) {
          frappe.msgprint(
            `<pre>${frappe.utils.escape_html(
              JSON.stringify(r.message || {}, null, 2)
            )}</pre>`
          );
        }
      });
    }, __("Menu Tools"));

    frm.add_custom_button(__("Enable Self Order for Linked Items"), () => {
      frappe.confirm(
        __("Enable self ordering for linked, available menu entries?"),
        () => {
          frappe.call({
            method: "fnb_menu.api.menu_admin.bulk_set_self_ordering",
            args: {
              menu_book: frm.doc.name,
              enabled: 1
            },
            freeze: true,
            callback(r) {
              frappe.msgprint(
                `<pre>${frappe.utils.escape_html(
                  JSON.stringify(r.message || {}, null, 2)
                )}</pre>`
              );
            }
          });
        }
      );
    }, __("Self Ordering"));

    frm.add_custom_button(__("Disable Self Order for All"), () => {
      frappe.call({
        method: "fnb_menu.api.menu_admin.bulk_set_self_ordering",
        args: {
          menu_book: frm.doc.name,
          enabled: 0
        },
        freeze: true,
        callback(r) {
          frappe.msgprint(
            `<pre>${frappe.utils.escape_html(
              JSON.stringify(r.message || {}, null, 2)
            )}</pre>`
          );
        }
      });
    }, __("Self Ordering"));

    frm.add_custom_button(__("Download CSV Template"), () => {
      window.open(
        "/assets/fnb_menu/templates/hotel_menu_import_template.csv",
        "_blank"
      );
    }, __("Menu Tools"));

    frm.add_custom_button(__("Preview"), () => {
      window.open(
        `/fnb-menu?menu=${encodeURIComponent(
          (frm.doc.menu_type || "Food").toLowerCase()
        )}`,
        "_blank"
      );
    });
  }
});

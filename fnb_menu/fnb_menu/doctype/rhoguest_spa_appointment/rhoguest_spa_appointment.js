frappe.ui.form.on("RhoGuest Spa Appointment", {
  refresh(frm) {
    if (frm.is_new()) return;

    const colors = {
      "Requested": "orange",
      "Confirmed": "blue",
      "Checked In": "green",
      "In Treatment": "purple",
      "Completed": "green",
      "Cancelled": "gray",
      "No Show": "gray",
    };
    frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "gray");

    frm.add_custom_button(__("RhoGuest Dashboard"), () => {
      frappe.set_route("rhoguest-dashboard");
    }, __("View"));

    frm.add_custom_button(__("Public Spa Page"), () => {
      window.open("/rhoguest-spa", "_blank");
    }, __("View"));

    if (!frappe.model.can_write(frm.doctype)) return;

    if (["Requested", "Confirmed"].includes(frm.doc.status)) {
      frm.add_custom_button(
        __("Reschedule / Change Resource"),
        () => show_reschedule_dialog(frm),
        __("Spa Actions")
      );
    }

    if (frm.doc.status === "Requested") {
      add_status_button(frm, __("Confirm Appointment"), "Confirmed");
      add_cancel_button(frm);
    } else if (frm.doc.status === "Confirmed") {
      add_status_button(frm, __("Check In"), "Checked In");
      add_status_button(frm, __("Mark No Show"), "No Show");
      add_cancel_button(frm);
    } else if (frm.doc.status === "Checked In") {
      add_status_button(frm, __("Start Treatment"), "In Treatment");
    } else if (frm.doc.status === "In Treatment") {
      add_status_button(frm, __("Complete Treatment"), "Completed");
    }
  },
});

function add_status_button(frm, label, status) {
  frm.add_custom_button(
    label,
    () => frappe.call({
      method: "fnb_menu.api.spa.update_status",
      args: { appointment_name: frm.doc.name, status },
      freeze: true,
      freeze_message: __("Updating Spa Appointment…"),
      callback(r) {
        if (!r.exc) frm.reload_doc();
      },
    }),
    __("Spa Actions")
  );
}

function add_cancel_button(frm) {
  frm.add_custom_button(
    __("Cancel Appointment"),
    () => frappe.confirm(
      __("Cancel Spa Appointment {0}?", [frm.doc.name]),
      () => frappe.call({
        method: "fnb_menu.api.spa.update_status",
        args: { appointment_name: frm.doc.name, status: "Cancelled" },
        freeze: true,
        callback(r) {
          if (!r.exc) frm.reload_doc();
        },
      })
    ),
    __("Spa Actions")
  );
}

function show_reschedule_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Reschedule / Change Spa Resource"),
    fields: [
      {
        fieldname: "appointment_start",
        fieldtype: "Datetime",
        label: __("Appointment Start"),
        reqd: 1,
        default: frm.doc.appointment_start,
      },
      {
        fieldname: "spa_resource",
        fieldtype: "Link",
        options: "RhoGuest Spa Resource",
        label: __("Spa Resource"),
        reqd: 1,
        default: frm.doc.spa_resource,
        get_query() {
          return { filters: { enabled: 1 } };
        },
      },
    ],
    primary_action_label: __("Apply"),
    primary_action(values) {
      dialog.disable_primary_action();

      frappe.call({
        method: "fnb_menu.api.spa.reschedule_appointment",
        args: {
          appointment_name: frm.doc.name,
          appointment_start: values.appointment_start,
          spa_resource: values.spa_resource,
        },
        freeze: true,
        freeze_message: __("Checking Spa availability…"),
        callback(r) {
          if (!r.exc) {
            dialog.hide();
            frm.reload_doc();
          } else {
            dialog.enable_primary_action();
          }
        },
      });
    },
  });

  dialog.show();
}

frappe.ui.form.on("RhoGuest Facility Reservation", {
  refresh(frm) {
    if (frm.is_new()) return;

    const colors = {
      "Requested": "orange",
      "Confirmed": "blue",
      "Checked In": "green",
      "Completed": "green",
      "Cancelled": "gray",
      "No Show": "gray",
    };
    frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "gray");

    frm.add_custom_button(__("RhoGuest Dashboard"), () => {
      frappe.set_route("rhoguest-dashboard");
    }, __("View"));

    const publicUrl =
      frm.doc.service_category === "swimming-pool"
        ? "/rhoguest-pool"
        : "/rhoguest-gym";
    frm.add_custom_button(__("Public Facility Page"), () => {
      window.open(publicUrl, "_blank");
    }, __("View"));

    if (!frappe.model.can_write(frm.doctype)) return;

    if (!["Completed", "Cancelled", "No Show"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Assign Staff"), () => show_assignment(frm), __("Operations"));
      if (frm.doc.assigned_to) {
        frm.add_custom_button(__("Unassign"), () => assign_reservation(frm, ""), __("Operations"));
      }
    }

    if (["Requested", "Confirmed"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Reschedule"), () => show_reschedule(frm), __("Reservation Actions"));
    }

    if (frm.doc.status === "Requested") {
      add_status(frm, __("Confirm Reservation"), "Confirmed");
      add_cancel(frm);
    } else if (frm.doc.status === "Confirmed") {
      add_status(frm, __("Check In"), "Checked In");
      add_status(frm, __("Mark No Show"), "No Show");
      add_cancel(frm);
    } else if (frm.doc.status === "Checked In") {
      add_status(frm, __("Complete Visit"), "Completed");
    }
  },
});

function add_status(frm, label, status) {
  frm.add_custom_button(
    label,
    () => frappe.call({
      method: "fnb_menu.api.facility.update_status",
      args: { reservation_name: frm.doc.name, status },
      freeze: true,
      freeze_message: __("Updating reservation…"),
      callback(r) {
        if (!r.exc) frm.reload_doc();
      },
    }),
    __("Reservation Actions")
  );
}

function add_cancel(frm) {
  frm.add_custom_button(
    __("Cancel Reservation"),
    () => frappe.confirm(
      __("Cancel Facility Reservation {0}?", [frm.doc.name]),
      () => frappe.call({
        method: "fnb_menu.api.facility.update_status",
        args: { reservation_name: frm.doc.name, status: "Cancelled" },
        freeze: true,
        callback(r) {
          if (!r.exc) frm.reload_doc();
        },
      })
    ),
    __("Reservation Actions")
  );
}

function show_reschedule(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Reschedule Facility Reservation"),
    fields: [{
      fieldname: "reservation_start",
      fieldtype: "Datetime",
      label: __("New Reservation Start"),
      reqd: 1,
      default: frm.doc.reservation_start,
    }],
    primary_action_label: __("Reschedule"),
    primary_action(values) {
      dialog.disable_primary_action();
      frappe.call({
        method: "fnb_menu.api.facility.reschedule_reservation",
        args: {
          reservation_name: frm.doc.name,
          reservation_start: values.reservation_start,
        },
        freeze: true,
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

function show_assignment(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Assign Facility Reservation"),
    fields: [{
      fieldname: "user",
      fieldtype: "Link",
      options: "User",
      label: __("Staff User"),
      reqd: 1,
      default: frm.doc.assigned_to || null,
      get_query() {
        return { filters: { enabled: 1, user_type: "System User" } };
      },
    }],
    primary_action_label: __("Assign"),
    primary_action(values) {
      dialog.disable_primary_action();
      assign_reservation(frm, values.user, dialog);
    },
  });
  dialog.show();
}

function assign_reservation(frm, user, dialog = null) {
  frappe.call({
    method: "fnb_menu.api.facility.assign_reservation",
    args: { reservation_name: frm.doc.name, user },
    freeze: true,
    callback(r) {
      if (!r.exc) {
        if (dialog) dialog.hide();
        frm.reload_doc();
      } else if (dialog) {
        dialog.enable_primary_action();
      }
    },
  });
}

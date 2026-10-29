frappe.ui.form.on("RhoGuest Transport Booking", {
  refresh(frm) {
    if (frm.is_new()) return;

    const colors = {
      "Requested": "orange",
      "Confirmed": "blue",
      "Dispatched": "purple",
      "Arrived at Pickup": "cyan",
      "In Transit": "green",
      "Completed": "green",
      "Cancelled": "gray",
      "No Show": "gray",
    };
    frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || "gray");

    frm.add_custom_button(__("RhoGuest Dashboard"), () => {
      frappe.set_route("rhoguest-dashboard");
    }, __("View"));

    frm.add_custom_button(__("Public Transport Page"), () => {
      window.open("/rhoguest-transport", "_blank");
    }, __("View"));

    if (!frappe.model.can_write(frm.doctype)) return;

    if (["Requested", "Confirmed"].includes(frm.doc.status)) {
      frm.add_custom_button(
        __("Assign / Change Vehicle & Driver"),
        () => show_assignment_dialog(frm),
        __("Transport Actions")
      );
      frm.add_custom_button(
        __("Reschedule"),
        () => show_reschedule_dialog(frm),
        __("Transport Actions")
      );
    }

    if (frm.doc.status === "Requested") {
      add_status_button(frm, __("Confirm Booking"), "Confirmed");
      add_cancel_button(frm);
    } else if (frm.doc.status === "Confirmed") {
      add_status_button(frm, __("Dispatch Vehicle"), "Dispatched");
      add_status_button(frm, __("Mark No Show"), "No Show");
      add_cancel_button(frm);
    } else if (frm.doc.status === "Dispatched") {
      add_status_button(frm, __("Arrived at Pickup"), "Arrived at Pickup");
    } else if (frm.doc.status === "Arrived at Pickup") {
      add_status_button(frm, __("Start Trip"), "In Transit");
      add_status_button(frm, __("Mark No Show"), "No Show");
    } else if (frm.doc.status === "In Transit") {
      add_status_button(frm, __("Complete Trip"), "Completed");
    }
  },
});

function add_status_button(frm, label, status) {
  frm.add_custom_button(
    label,
    () => frappe.call({
      method: "fnb_menu.api.transport.update_status",
      args: { booking_name: frm.doc.name, status },
      freeze: true,
      freeze_message: __("Updating Transport Booking…"),
      callback(r) {
        if (!r.exc) frm.reload_doc();
      },
    }),
    __("Transport Actions")
  );
}

function add_cancel_button(frm) {
  frm.add_custom_button(
    __("Cancel Booking"),
    () => frappe.confirm(
      __("Cancel Transport Booking {0}?", [frm.doc.name]),
      () => frappe.call({
        method: "fnb_menu.api.transport.update_status",
        args: { booking_name: frm.doc.name, status: "Cancelled" },
        freeze: true,
        callback(r) {
          if (!r.exc) frm.reload_doc();
        },
      })
    ),
    __("Transport Actions")
  );
}

function show_assignment_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Assign Transport Resources"),
    fields: [
      {
        fieldname: "vehicle",
        fieldtype: "Link",
        options: "RhoGuest Transport Vehicle",
        label: __("Vehicle"),
        reqd: 1,
        default: frm.doc.vehicle,
        get_query() {
          return { filters: { enabled: 1 } };
        },
      },
      {
        fieldname: "driver",
        fieldtype: "Link",
        options: "RhoGuest Transport Driver",
        label: __("Driver"),
        reqd: 1,
        default: frm.doc.driver,
        get_query() {
          return { filters: { enabled: 1 } };
        },
      },
    ],
    primary_action_label: __("Assign"),
    primary_action(values) {
      dialog.disable_primary_action();
      frappe.call({
        method: "fnb_menu.api.transport.assign_resources",
        args: {
          booking_name: frm.doc.name,
          vehicle: values.vehicle,
          driver: values.driver,
        },
        freeze: true,
        freeze_message: __("Checking vehicle and driver availability…"),
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

function show_reschedule_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Reschedule Transport Booking"),
    fields: [{
      fieldname: "scheduled_pickup_at",
      fieldtype: "Datetime",
      label: __("Scheduled Pickup"),
      reqd: 1,
      default: frm.doc.scheduled_pickup_at,
    }],
    primary_action_label: __("Reschedule"),
    primary_action(values) {
      dialog.disable_primary_action();
      frappe.call({
        method: "fnb_menu.api.transport.reschedule_booking",
        args: {
          booking_name: frm.doc.name,
          scheduled_pickup_at: values.scheduled_pickup_at,
        },
        freeze: true,
        freeze_message: __("Checking Transport availability…"),
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

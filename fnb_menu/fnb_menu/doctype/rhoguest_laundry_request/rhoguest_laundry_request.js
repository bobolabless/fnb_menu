frappe.ui.form.on("RhoGuest Laundry Request", {
  refresh(frm) {
    if (frm.is_new()) return;

    set_status_indicator(frm);
    show_billing_notice(frm);
    add_navigation_buttons(frm);

    if (!frm.doc.__islocal && frappe.model.can_write(frm.doctype)) {
      add_assignment_buttons(frm);
      add_fulfilment_buttons(frm);
      add_billing_buttons(frm);
    }
  },
});

const STATUS_COLORS = {
  "Submitted": "gray",
  "Pickup Scheduled": "blue",
  "Collected": "orange",
  "Processing": "orange",
  "Ready": "green",
  "Out for Delivery": "blue",
  "Delivered": "green",
  "Cancelled": "gray",
};

function set_status_indicator(frm) {
  if (frm.page && frm.page.set_indicator) {
    frm.page.set_indicator(
      __(frm.doc.status || "Submitted"),
      STATUS_COLORS[frm.doc.status] || "gray"
    );
  }
}

function show_billing_notice(frm) {
  if (frm.doc.billing_status === "Pending Folio Posting") {
    frm.set_intro(
      __(
        "Charge to Room is pending folio posting. This request has not been posted to a guest folio yet."
      ),
      "orange"
    );
  }
}

function add_navigation_buttons(frm) {
  frm.add_custom_button(
    __("RhoGuest Dashboard"),
    () => frappe.set_route("rhoguest-dashboard"),
    __("View")
  );

  frm.add_custom_button(
    __("Public Laundry Page"),
    () => window.open("/rhoguest-laundry", "_blank"),
    __("View")
  );
}

function add_assignment_buttons(frm) {
  if (["Delivered", "Cancelled"].includes(frm.doc.status)) return;

  frm.add_custom_button(
    __("Assign Staff"),
    () => show_assignment_dialog(frm),
    __("Operations")
  );

  if (frm.doc.assigned_to) {
    frm.add_custom_button(
      __("Unassign"),
      () => assign_request(frm, ""),
      __("Operations")
    );
  }
}

function add_fulfilment_buttons(frm) {
  const status = frm.doc.status;

  if (status === "Submitted") {
    frm.add_custom_button(
      __("Schedule Pickup"),
      () => show_pickup_dialog(frm),
      __("Laundry Actions")
    );
    add_transition_button(frm, __("Mark Collected"), "Collected");
    add_cancel_button(frm);
  } else if (status === "Pickup Scheduled") {
    frm.add_custom_button(
      __("Reschedule Pickup"),
      () => show_pickup_dialog(frm),
      __("Laundry Actions")
    );
    add_transition_button(frm, __("Mark Collected"), "Collected");
    add_cancel_button(frm);
  } else if (status === "Collected") {
    add_transition_button(frm, __("Start Processing"), "Processing");
    add_cancel_button(frm);
  } else if (status === "Processing") {
    add_transition_button(frm, __("Mark Ready"), "Ready");
    add_cancel_button(frm);
  } else if (status === "Ready") {
    add_transition_button(frm, __("Out for Delivery"), "Out for Delivery");
    add_transition_button(frm, __("Mark Delivered"), "Delivered");
    add_cancel_button(frm);
  } else if (status === "Out for Delivery") {
    add_transition_button(frm, __("Mark Delivered"), "Delivered");
    add_cancel_button(frm);
  }
}

function add_transition_button(frm, label, status) {
  frm.add_custom_button(
    label,
    () => transition_request(frm, status),
    __("Laundry Actions")
  );
}

function add_cancel_button(frm) {
  frm.add_custom_button(
    __("Cancel Request"),
    () => {
      frappe.confirm(
        __(
          "Cancel Laundry Request {0}? This operation cannot be reversed through the normal fulfilment workflow.",
          [frm.doc.name]
        ),
        () => transition_request(frm, "Cancelled")
      );
    },
    __("Laundry Actions")
  );

  if (frm.change_custom_button_type) {
    frm.change_custom_button_type(
      __("Cancel Request"),
      __("Laundry Actions"),
      "danger"
    );
  }
}

function transition_request(frm, status) {
  return frappe.call({
    method: "fnb_menu.api.laundry.update_status",
    args: {
      request_name: frm.doc.name,
      status,
    },
    freeze: true,
    freeze_message: __("Updating Laundry Request…"),
    callback(r) {
      if (!r.exc) {
        frappe.show_alert({
          message: __("Laundry Request moved to {0}.", [status]),
          indicator: "green",
        });
        frm.reload_doc();
      }
    },
  });
}

function show_pickup_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title:
      frm.doc.status === "Pickup Scheduled"
        ? __("Reschedule Laundry Pickup")
        : __("Schedule Laundry Pickup"),
    fields: [
      {
        fieldname: "requested_pickup_at",
        fieldtype: "Datetime",
        label: __("Pickup Date & Time"),
        reqd: 1,
        default: frm.doc.requested_pickup_at || null,
      },
    ],
    primary_action_label: __("Save Pickup"),
    primary_action(values) {
      dialog.disable_primary_action();

      frappe.call({
        method: "fnb_menu.api.laundry.schedule_pickup",
        args: {
          request_name: frm.doc.name,
          requested_pickup_at: values.requested_pickup_at,
        },
        freeze: true,
        freeze_message: __("Scheduling pickup…"),
        callback(r) {
          if (!r.exc) {
            dialog.hide();
            frappe.show_alert({
              message: __("Laundry pickup scheduled."),
              indicator: "green",
            });
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

function show_assignment_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Assign Laundry Request"),
    fields: [
      {
        fieldname: "user",
        fieldtype: "Link",
        options: "User",
        label: __("Staff User"),
        reqd: 1,
        default: frm.doc.assigned_to || null,
        get_query() {
          return {
            filters: {
              enabled: 1,
              user_type: "System User",
            },
          };
        },
      },
    ],
    primary_action_label: __("Assign"),
    primary_action(values) {
      dialog.disable_primary_action();
      assign_request(frm, values.user, dialog);
    },
  });

  dialog.show();
}

function assign_request(frm, user, dialog = null) {
  return frappe.call({
    method: "fnb_menu.api.laundry.assign_request",
    args: {
      request_name: frm.doc.name,
      user,
    },
    freeze: true,
    freeze_message: user ? __("Assigning Laundry Request…") : __("Removing assignment…"),
    callback(r) {
      if (!r.exc) {
        if (dialog) dialog.hide();
        frappe.show_alert({
          message: user
            ? __("Laundry Request assigned to {0}.", [user])
            : __("Laundry Request unassigned."),
          indicator: "green",
        });
        frm.reload_doc();
      } else if (dialog) {
        dialog.enable_primary_action();
      }
    },
  });
}


function can_manage_laundry_billing() {
  return (
    frappe.user.has_role("System Manager") ||
    frappe.user.has_role("Sales Manager")
  );
}

function add_billing_buttons(frm) {
  if (!can_manage_laundry_billing()) return;
  if (frm.doc.billing_preference !== "Charge to Room") return;

  if (frm.doc.billing_status === "Pending Folio Posting") {
    frappe.call({
      method: "fnb_menu.api.laundry.get_folio_posting_mode",
      callback(r) {
        if (frm.doc.billing_status !== "Pending Folio Posting") return;

        const mode = r.message?.mode || "Manual";

        if (mode === "Custom Integration") {
          frm.add_custom_button(
            __("Post to Folio"),
            () => post_to_folio(frm),
            __("Billing")
          );
        }

        frm.add_custom_button(
          __("Record Folio Posting"),
          () => show_manual_folio_dialog(frm),
          __("Billing")
        );
      },
    });
  }

  if (frm.doc.billing_status === "Posted to Room" && frm.doc.folio_reference) {
    frm.add_custom_button(
      __("Mark Settled"),
      () => mark_billing_settled(frm),
      __("Billing")
    );
  }
}

function post_to_folio(frm) {
  frappe.confirm(
    __(
      "Post Laundry Request {0} to the configured room-folio integration?",
      [frm.doc.name]
    ),
    () => {
      frappe.call({
        method: "fnb_menu.api.laundry.post_to_folio",
        args: { request_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Posting Laundry charge to folio…"),
        callback(r) {
          if (!r.exc) {
            frappe.show_alert({
              message: __("Posted to folio: {0}", [r.message?.folio_reference || ""]),
              indicator: "green",
            });
            frm.reload_doc();
          }
        },
      });
    }
  );
}

function show_manual_folio_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Record Laundry Folio Posting"),
    fields: [
      {
        fieldname: "folio_reference",
        fieldtype: "Data",
        label: __("External Folio Reference"),
        reqd: 1,
        description: __(
          "Enter the real PMS/folio transaction reference after the room charge has been posted."
        ),
      },
    ],
    primary_action_label: __("Confirm Posted to Room"),
    primary_action(values) {
      dialog.disable_primary_action();

      frappe.call({
        method: "fnb_menu.api.laundry.record_folio_posting",
        args: {
          request_name: frm.doc.name,
          folio_reference: values.folio_reference,
        },
        freeze: true,
        freeze_message: __("Recording folio posting…"),
        callback(r) {
          if (!r.exc) {
            dialog.hide();
            frappe.show_alert({
              message: __("Room folio posting recorded."),
              indicator: "green",
            });
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

function mark_billing_settled(frm) {
  frappe.confirm(
    __(
      "Confirm that the posted Laundry room charge has been settled in the hotel billing process?"
    ),
    () => {
      frappe.call({
        method: "fnb_menu.api.laundry.mark_billing_settled",
        args: { request_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Updating Laundry billing…"),
        callback(r) {
          if (!r.exc) {
            frappe.show_alert({
              message: __("Laundry billing marked Settled."),
              indicator: "green",
            });
            frm.reload_doc();
          }
        },
      });
    }
  );
}

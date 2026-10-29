frappe.listview_settings["RhoGuest Spa Appointment"] = {
  add_fields: [
    "service_name",
    "spa_resource",
    "resource_name",
    "guest_name",
    "room_number",
    "appointment_start",
    "appointment_end",
    "status",
  ],

  get_indicator(doc) {
    const map = {
      "Requested": ["Requested", "orange"],
      "Confirmed": ["Confirmed", "blue"],
      "Checked In": ["Checked In", "green"],
      "In Treatment": ["In Treatment", "purple"],
      "Completed": ["Completed", "green"],
      "Cancelled": ["Cancelled", "gray"],
      "No Show": ["No Show", "gray"],
    };
    const [label, color] = map[doc.status] || [doc.status || "Requested", "gray"];
    return [__(label), color, "status,=," + (doc.status || "Requested")];
  },

  onload(listview) {
    listview.page.add_inner_button(
      __("RhoGuest Dashboard"),
      () => frappe.set_route("rhoguest-dashboard")
    );

    const queues = [
      [__("Upcoming"), [["RhoGuest Spa Appointment", "status", "in", ["Requested", "Confirmed"]]]],
      [__("Awaiting Confirmation"), [["RhoGuest Spa Appointment", "status", "=", "Requested"]]],
      [__("Checked In"), [["RhoGuest Spa Appointment", "status", "=", "Checked In"]]],
      [__("In Treatment"), [["RhoGuest Spa Appointment", "status", "=", "In Treatment"]]],
    ];

    queues.forEach(([label, filters]) => {
      listview.page.add_inner_button(
        label,
        () => apply_spa_filter(listview, filters),
        __("Queues")
      );
    });

    listview.page.add_inner_button(
      __("All Appointments"),
      () => clear_spa_filter(listview),
      __("Queues")
    );
  },
};

async function apply_spa_filter(listview, filters) {
  await listview.filter_area.clear(false);
  await listview.filter_area.set(filters);
  listview.start = 0;
  listview.refresh();
}

async function clear_spa_filter(listview) {
  await listview.filter_area.clear(false);
  listview.start = 0;
  listview.refresh();
}

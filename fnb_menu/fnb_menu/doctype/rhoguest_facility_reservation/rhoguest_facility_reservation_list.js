frappe.listview_settings["RhoGuest Facility Reservation"] = {
  add_fields: [
    "service_category",
    "service_name",
    "guest_name",
    "room_number",
    "reservation_start",
    "reservation_end",
    "party_size",
    "status",
    "assigned_to",
  ],

  get_indicator(doc) {
    const map = {
      "Requested": ["Requested", "orange"],
      "Confirmed": ["Confirmed", "blue"],
      "Checked In": ["Checked In", "green"],
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
      [__("Upcoming"), [["RhoGuest Facility Reservation", "status", "in", ["Requested", "Confirmed"]]]],
      [__("Awaiting Confirmation"), [["RhoGuest Facility Reservation", "status", "=", "Requested"]]],
      [__("Checked In"), [["RhoGuest Facility Reservation", "status", "=", "Checked In"]]],
      [__("Pool"), [["RhoGuest Facility Reservation", "service_category", "=", "swimming-pool"]]],
      [__("Gym"), [["RhoGuest Facility Reservation", "service_category", "=", "gym-fitness"]]],
    ];

    queues.forEach(([label, filters]) => {
      listview.page.add_inner_button(
        label,
        () => apply_facility_filter(listview, filters),
        __("Queues")
      );
    });

    listview.page.add_inner_button(
      __("All Reservations"),
      () => clear_facility_filter(listview),
      __("Queues")
    );
  },
};

async function apply_facility_filter(listview, filters) {
  await listview.filter_area.clear(false);
  await listview.filter_area.set(filters);
  listview.start = 0;
  listview.refresh();
}

async function clear_facility_filter(listview) {
  await listview.filter_area.clear(false);
  listview.start = 0;
  listview.refresh();
}

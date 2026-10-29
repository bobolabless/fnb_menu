frappe.listview_settings["RhoGuest Transport Booking"] = {
  add_fields: [
    "service_name",
    "guest_name",
    "room_number",
    "scheduled_pickup_at",
    "pickup_location",
    "dropoff_location",
    "vehicle",
    "driver",
    "status",
  ],

  get_indicator(doc) {
    const map = {
      "Requested": ["Requested", "orange"],
      "Confirmed": ["Confirmed", "blue"],
      "Dispatched": ["Dispatched", "purple"],
      "Arrived at Pickup": ["Arrived at Pickup", "cyan"],
      "In Transit": ["In Transit", "green"],
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
      [__("Upcoming"), [["RhoGuest Transport Booking", "status", "in", ["Requested", "Confirmed"]]]],
      [__("Awaiting Assignment"), [
        ["RhoGuest Transport Booking", "status", "in", ["Requested", "Confirmed"]],
        ["RhoGuest Transport Booking", "vehicle", "is", "not set"],
      ]],
      [__("Dispatched"), [["RhoGuest Transport Booking", "status", "=", "Dispatched"]]],
      [__("Active Trips"), [["RhoGuest Transport Booking", "status", "in", ["Arrived at Pickup", "In Transit"]]]],
      [__("Completed"), [["RhoGuest Transport Booking", "status", "=", "Completed"]]],
    ];

    queues.forEach(([label, filters]) => {
      listview.page.add_inner_button(
        label,
        () => apply_transport_filter(listview, filters),
        __("Queues")
      );
    });

    listview.page.add_inner_button(
      __("All Bookings"),
      () => clear_transport_filter(listview),
      __("Queues")
    );
  },
};

async function apply_transport_filter(listview, filters) {
  await listview.filter_area.clear(false);
  await listview.filter_area.set(filters);
  listview.start = 0;
  listview.refresh();
}

async function clear_transport_filter(listview) {
  await listview.filter_area.clear(false);
  listview.start = 0;
  listview.refresh();
}

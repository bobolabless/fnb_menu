frappe.listview_settings["RhoGuest Laundry Request"] = {
  add_fields: [
    "guest_name",
    "room_number",
    "status",
    "billing_status",
    "assigned_to",
    "requested_pickup_at",
    "estimated_total",
    "currency",
  ],

  get_indicator(doc) {
    const indicators = {
      "Submitted": ["Submitted", "gray"],
      "Pickup Scheduled": ["Pickup Scheduled", "blue"],
      "Collected": ["Collected", "orange"],
      "Processing": ["Processing", "orange"],
      "Ready": ["Ready", "green"],
      "Out for Delivery": ["Out for Delivery", "blue"],
      "Delivered": ["Delivered", "green"],
      "Cancelled": ["Cancelled", "gray"],
    };

    const [label, color] = indicators[doc.status] || [doc.status || "Submitted", "gray"];
    return [__(label), color, "status,=," + (doc.status || "Submitted")];
  },

  onload(listview) {
    listview.page.add_inner_button(
      __("RhoGuest Dashboard"),
      () => frappe.set_route("rhoguest-dashboard")
    );

    listview.page.add_inner_button(
      __("Open Queue"),
      () =>
        apply_queue_filter(listview, [
          [
            "RhoGuest Laundry Request",
            "status",
            "not in",
            ["Delivered", "Cancelled"],
          ],
        ]),
      __("Queues")
    );

    listview.page.add_inner_button(
      __("Awaiting Pickup"),
      () =>
        apply_queue_filter(listview, [
          [
            "RhoGuest Laundry Request",
            "status",
            "in",
            ["Submitted", "Pickup Scheduled"],
          ],
        ]),
      __("Queues")
    );

    listview.page.add_inner_button(
      __("Processing"),
      () =>
        apply_queue_filter(listview, [
          [
            "RhoGuest Laundry Request",
            "status",
            "in",
            ["Collected", "Processing"],
          ],
        ]),
      __("Queues")
    );

    listview.page.add_inner_button(
      __("Ready / Delivery"),
      () =>
        apply_queue_filter(listview, [
          [
            "RhoGuest Laundry Request",
            "status",
            "in",
            ["Ready", "Out for Delivery"],
          ],
        ]),
      __("Queues")
    );

    listview.page.add_inner_button(
      __("Pending Folio"),
      () =>
        apply_queue_filter(listview, [
          [
            "RhoGuest Laundry Request",
            "billing_status",
            "=",
            "Pending Folio Posting",
          ],
        ]),
      __("Queues")
    );

    listview.page.add_inner_button(
      __("All Requests"),
      () => clear_queue_filter(listview),
      __("Queues")
    );
  },
};

async function apply_queue_filter(listview, filters) {
  await listview.filter_area.clear(false);
  await listview.filter_area.set(filters);
  listview.start = 0;
  listview.refresh();
}

async function clear_queue_filter(listview) {
  await listview.filter_area.clear(false);
  listview.start = 0;
  listview.refresh();
}

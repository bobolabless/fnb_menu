frappe.pages["rhoguest-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("RhoGuest Dashboard"),
    single_column: true,
  });

  page.set_primary_action(__("Refresh"), () => load_dashboard(page));
  page.add_inner_button(__("Guest Hub"), () => window.open("/rhoguest", "_blank"));
  page.add_inner_button(__("Laundry Requests"), () => {
    frappe.set_route("List", "RhoGuest Laundry Request");
  });
  page.add_inner_button(__("Settings"), () => {
    frappe.set_route("Form", "FNB Menu Settings");
  });

  frappe.require("/assets/fnb_menu/css/rhoguest_dashboard.css", () => {
    load_dashboard(page);
  });
};

frappe.pages["rhoguest-dashboard"].on_page_show = function (wrapper) {
  const page = wrapper.page;
  if (page) load_dashboard(page);
};

function load_dashboard(page) {
  const body = page.main;
  body.html('<div class="rgd-loading">' + __("Loading RhoGuest operations…") + "</div>");

  frappe.call({
    method: "fnb_menu.api.dashboard.get_dashboard_data",
    freeze: false,
    callback(r) {
      if (!r.message) return;
      render_dashboard(body, r.message);
    },
  });
}

function escape_html(value) {
  return $("<div>").text(value == null ? "" : String(value)).html();
}

function money(value, currency) {
  const amount = Number(value || 0);
  const code = currency || "NGN";
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: code,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch (e) {
    return code + " " + amount.toLocaleString();
  }
}

function card(label, value, hint, route) {
  const routeAttr = route ? ' data-route="' + escape_html(route) + '"' : "";
  return [
    '<button class="rgd-card"' + routeAttr + ' type="button">',
    '<span class="rgd-card-label">' + escape_html(label) + "</span>",
    '<strong>' + escape_html(value) + "</strong>",
    '<small>' + escape_html(hint || "") + "</small>",
    "</button>",
  ].join("");
}

function render_dashboard(body, data) {
  const c = data.cards || {};

  const cards = [
    card(__("Published Services"), c.published_services, __("Visible on Guest Hub"), "List/RhoGuest Service Category"),
    card(__("Guest Service Items"), c.service_items, __("Enabled and guest-available"), "List/RhoGuest Service Item"),
    card(__("Active F&B"), c.fnb_active, __("Kitchen fulfilment"), "List/FNB Self Order"),
    card(__("Awaiting F&B Payment"), c.fnb_pending_payment, __("Not yet payment-verified"), "List/FNB Self Order"),
    card(__("Open Laundry"), c.laundry_open, __("Not delivered/cancelled"), "List/RhoGuest Laundry Request"),
    card(__("Awaiting Pickup"), c.laundry_awaiting_pickup, __("Submitted or scheduled"), "List/RhoGuest Laundry Request"),
    card(__("Processing"), c.laundry_processing, __("Collected / processing"), "List/RhoGuest Laundry Request"),
    card(__("Ready / Delivery"), c.laundry_ready, __("Ready or out for delivery"), "List/RhoGuest Laundry Request"),
    card(__("Delivered Today"), c.laundry_delivered_today, __("Completed today"), "List/RhoGuest Laundry Request"),
    card(__("Pending Folio Posting"), c.pending_folio_posting, __("Charge-to-Room queue"), "List/RhoGuest Laundry Request"),
  ].join("");

  const serviceBadges = (data.published_services || []).length
    ? data.published_services
        .map((row) => '<span class="rgd-badge">' + escape_html(row.category_name) + "</span>")
        .join("")
    : '<span class="rgd-empty-inline">' + __("No services currently published") + "</span>";

  const rows = (data.recent_laundry || []).length
    ? data.recent_laundry
        .map(
          (row) => [
            '<tr data-docname="' + escape_html(row.name) + '">',
            "<td><strong>" + escape_html(row.name) + "</strong></td>",
            "<td>" + escape_html(row.guest_name) + '<small>Room ' + escape_html(row.room_number) + "</small></td>",
            '<td><span class="rgd-status">' + escape_html(row.status) + "</span></td>",
            "<td>" + escape_html(row.billing_status) + "</td>",
            "<td>" + escape_html(money(row.estimated_total, row.currency)) + "</td>",
            "</tr>",
          ].join("")
        )
        .join("")
    : '<tr><td colspan="5" class="rgd-empty">' + __("No Laundry Requests yet") + "</td></tr>";

  body.html([
    '<div class="rgd-shell">',
    '<section class="rgd-hero">',
    "<div>",
    '<p class="rgd-kicker">RhoGuest · Digital Menu & Guest Services</p>',
    "<h2>" + __("Operations Overview") + "</h2>",
    "<p>" + __("Monitor guest-service publication, Food & Beverage and Laundry operations from one Desk page.") + "</p>",
    "</div>",
    '<div class="rgd-hero-actions">',
    '<button class="btn btn-default btn-sm" data-open-public-menu>' + __("Public Menu") + "</button>",
    '<button class="btn btn-primary btn-sm" data-open-hub>' + __("Guest Hub") + "</button>",
    "</div>",
    "</section>",
    '<section class="rgd-cards">' + cards + "</section>",
    '<section class="rgd-panel">',
    '<div class="rgd-panel-head"><div><small>' + __("PUBLIC EXPERIENCE") + "</small><h3>" + __("Published Services") + "</h3></div>",
    '<span class="rgd-hub-state ' + (data.hub_enabled ? "is-on" : "is-off") + '">' + (data.hub_enabled ? __("Hub Enabled") : __("Hub Disabled")) + "</span></div>",
    '<div class="rgd-badges">' + serviceBadges + "</div>",
    "</section>",
    '<section class="rgd-panel">',
    '<div class="rgd-panel-head"><div><small>' + __("OPERATIONS") + "</small><h3>" + __("Recent Laundry Requests") + "</h3></div>",
    '<a class="rgd-link" data-all-laundry>' + __("View all") + " →</a></div>",
    '<div class="table-responsive"><table class="table rgd-table"><thead><tr>',
    "<th>" + __("Request") + "</th><th>" + __("Guest") + "</th><th>" + __("Status") + "</th><th>" + __("Billing") + "</th><th>" + __("Estimated Total") + "</th>",
    "</tr></thead><tbody>" + rows + "</tbody></table></div>",
    "</section>",
    '<p class="rgd-generated">' + __("Updated") + ": " + escape_html(data.generated_at || "") + "</p>",
    "</div>",
  ].join(""));

  body.find("[data-route]").on("click", function () {
    const route = ($(this).attr("data-route") || "").split("/");
    if (route.length >= 2) frappe.set_route(...route);
  });

  body.find("[data-docname]").on("click", function () {
    frappe.set_route("Form", "RhoGuest Laundry Request", $(this).attr("data-docname"));
  });

  body.find("[data-all-laundry]").on("click", () => {
    frappe.set_route("List", "RhoGuest Laundry Request");
  });

  body.find("[data-open-hub]").on("click", () => window.open("/rhoguest", "_blank"));
  body.find("[data-open-public-menu]").on("click", () => {
    window.open(data.public_menu_route || "/fnb-menu", "_blank");
  });
}

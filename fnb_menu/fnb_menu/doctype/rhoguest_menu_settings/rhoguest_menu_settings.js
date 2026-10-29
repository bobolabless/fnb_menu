function normalize_route_for_preview(value) {
  let route = (value || "/fnb-menu").trim();

  if (!route.startsWith("/")) {
    route = `/${route}`;
  }

  route = route.replace(/\/{2,}/g, "/");
  if (route.length > 1) {
    route = route.replace(/\/+$/, "");
  }

  return route || "/fnb-menu";
}

function render_route_preview(frm) {
  const field = frm.get_field("route_preview");
  if (!field || !field.$wrapper) return;

  const route = normalize_route_for_preview(frm.doc.public_menu_route);
  const url = `${window.location.origin}${route}`;

  field.$wrapper.empty();

  const container = $("<div>").addClass("small text-muted");
  $("<div>").text(__("New QR codes should point to:")).appendTo(container);

  $("<a>")
    .attr({ href: route, target: "_blank", rel: "noopener noreferrer" })
    .text(url)
    .appendTo(container);

  $("<div>")
    .addClass("mt-2")
    .text(__("The internal /fnb-menu route remains available for backward compatibility."))
    .appendTo(container);

  field.$wrapper.append(container);
}

frappe.ui.form.on("RhoGuest Menu Settings", {
  refresh(frm) {
    render_route_preview(frm);

    const publicRoute = normalize_route_for_preview(frm.doc.public_menu_route);
    frm.add_custom_button(__("Preview Public Menu"), () => window.open(publicRoute, "_blank"));
    frm.add_custom_button(__("Preview Guest Services Hub"), () => window.open("/rhoguest", "_blank"));
    frm.add_custom_button(__("Open Kitchen Board"), () => window.open("/fnb-kitchen", "_blank"));

    frm.dashboard.set_headline(
      frm.doc.self_ordering_enabled
        ? '<span class="indicator-pill green">RhoGuest F&B self ordering ENABLED · verified payment required</span>'
        : '<span class="indicator-pill gray">RhoGuest F&B self ordering DISABLED · digital menu only</span>'
    );
  },

  public_menu_route(frm) {
    render_route_preview(frm);
  },
});

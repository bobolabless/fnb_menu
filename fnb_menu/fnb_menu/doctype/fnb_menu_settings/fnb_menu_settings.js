frappe.ui.form.on("FNB Menu Settings", {
  refresh(frm) {
    frm.add_custom_button(__("Preview Public Menu"), () => window.open("/fnb-menu", "_blank"));
    frm.add_custom_button(__("Open Kitchen Board"), () => window.open("/fnb-kitchen", "_blank"));

    frm.dashboard.set_headline(
      frm.doc.self_ordering_enabled
        ? '<span class="indicator-pill green">RhoHMS F&B Menu self ordering ENABLED · verified payment required</span>'
        : '<span class="indicator-pill gray">RhoHMS F&B Menu self ordering DISABLED · digital menu only</span>'
    );
  }
});

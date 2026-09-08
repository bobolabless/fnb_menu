(() => {
  "use strict";
  const cfg = window.FNB_KITCHEN_CONFIG || {};
  let busy = false;

  async function update(button) {
    if (busy) return;
    busy = true;
    button.disabled = true;
    const old = button.textContent;
    button.textContent = "Updating…";

    try {
      const body = new URLSearchParams({
        csrf_token: cfg.csrfToken || "",
        order_name: button.dataset.order,
        status: button.dataset.status
      });
      const response = await fetch(cfg.updateUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-Frappe-CSRF-Token": cfg.csrfToken || ""
        },
        body: body.toString()
      });
      const data = await response.json();
      if (!response.ok || data.exc || data.exception) {
        throw new Error(data.message || data.exception || "Could not update order.");
      }
      window.location.reload();
    } catch (error) {
      alert(error.message || "Could not update order.");
      button.disabled = false;
      button.textContent = old;
      busy = false;
    }
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".kitchen-action");
    if (button) update(button);
  });

  window.setTimeout(() => window.location.reload(), 15000);
})();

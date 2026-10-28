(() => {
  "use strict";

  const config = window.RHOGUEST_LAUNDRY_CONFIG || {};
  const form = document.getElementById("rgl-form");
  if (!form) return;

  const rows = [...document.querySelectorAll("[data-laundry-item]")];
  const totalEl = document.getElementById("rgl-total");
  const messageEl = document.getElementById("rgl-message");
  const submitBtn = document.getElementById("rgl-submit");

  const money = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: config.currency || "NGN",
    maximumFractionDigits: 2,
  });

  function clampQuantity(value) {
    const n = Number.parseInt(value || "0", 10);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(50, n));
  }

  function updateTotal() {
    let total = 0;
    rows.forEach((row) => {
      const qtyInput = row.querySelector("[data-qty]");
      if (!qtyInput) return;
      const qty = clampQuantity(qtyInput.value);
      qtyInput.value = String(qty);
      const displayRate = Number.parseFloat(row.dataset.rate || "0");
      if (Number.isFinite(displayRate)) total += displayRate * qty;
    });
    totalEl.textContent = money.format(total);
  }

  rows.forEach((row) => {
    const qty = row.querySelector("[data-qty]");
    if (!qty) return;

    row.querySelector("[data-qty-minus]")?.addEventListener("click", () => {
      qty.value = String(Math.max(0, clampQuantity(qty.value) - 1));
      updateTotal();
    });

    row.querySelector("[data-qty-plus]")?.addEventListener("click", () => {
      qty.value = String(Math.min(50, clampQuantity(qty.value) + 1));
      updateTotal();
    });

    qty.addEventListener("input", updateTotal);
  });

  function requestItems() {
    return rows.flatMap((row) => {
      const qtyInput = row.querySelector("[data-qty]");
      if (!qtyInput) return [];
      const qty = clampQuantity(qtyInput.value);
      if (qty < 1) return [];

      // Security contract: send identifiers/quantity/instruction only.
      return [{
        service_item: row.dataset.serviceItem,
        qty,
        special_instruction: row.querySelector("[data-line-note]")?.value?.trim() || "",
      }];
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    messageEl.textContent = "";

    const items = requestItems();
    if (!items.length) {
      messageEl.textContent = "Select at least one laundry item.";
      return;
    }

    const guestName = document.getElementById("rgl-guest-name").value.trim();
    const roomNumber = document.getElementById("rgl-room-number").value.trim();
    const phone = document.getElementById("rgl-phone").value.trim();
    const email = document.getElementById("rgl-email").value.trim();

    if (!guestName || !roomNumber) {
      messageEl.textContent = "Guest name and room number are required.";
      return;
    }
    if (!phone && !email) {
      messageEl.textContent = "Provide at least a phone number or email.";
      return;
    }

    const params = new URLSearchParams({
      guest_name: guestName,
      room_number: roomNumber,
      phone,
      email,
      requested_pickup_at: document.getElementById("rgl-pickup-at").value || "",
      pickup_note: document.getElementById("rgl-pickup-note").value.trim(),
      billing_preference: document.getElementById("rgl-billing").value,
      items: JSON.stringify(items),
    });

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting…";

    try {
      const response = await fetch(config.createUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-Frappe-CSRF-Token": config.csrfToken || "",
        },
        body: params.toString(),
        credentials: "same-origin",
      });
      const payload = await response.json();

      if (!response.ok || payload.exc) {
        throw new Error("The hotel system could not accept this request.");
      }

      const result = payload.message || {};
      messageEl.textContent = "Request received. Reference: " + String(result.request || "");
      form.querySelectorAll("input, textarea, select, button").forEach((element) => {
        if (element !== submitBtn) element.disabled = true;
      });
      submitBtn.textContent = "Request Submitted";
    } catch (error) {
      messageEl.textContent = error.message || "Unable to submit Laundry Request.";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Laundry Request";
    }
  });

  updateTotal();
})();

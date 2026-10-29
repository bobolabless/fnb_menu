(() => {
  "use strict";

  const config = window.RHOGUEST_FACILITY_CONFIG || {};
  const form = document.getElementById("rgf-form");
  if (!form) return;

  const totalEl = document.getElementById("rgf-total");
  const durationEl = document.getElementById("rgf-duration");
  const partyEl = document.getElementById("rgf-party-size");
  const messageEl = document.getElementById("rgf-message");
  const submitBtn = document.getElementById("rgf-submit");

  const money = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: config.currency || "NGN",
    maximumFractionDigits: 2,
  });

  function selectedItem() {
    return form.querySelector('input[name="facility_item"]:checked');
  }

  function partySize() {
    const value = Number.parseInt(partyEl.value || "1", 10);
    return Math.max(1, Math.min(50, Number.isFinite(value) ? value : 1));
  }

  function updateSummary() {
    const item = selectedItem();
    partyEl.value = String(partySize());

    if (!item) {
      durationEl.textContent = "—";
      totalEl.textContent = "—";
      return;
    }

    const duration = Number.parseInt(item.dataset.duration || "0", 10);
    const rate = Number.parseFloat(item.dataset.rate || "0");
    const basis = item.dataset.basis || "Per Reservation";
    const total = basis === "Per Person" ? rate * partySize() : rate;

    durationEl.textContent = duration ? duration + " min" : "—";
    totalEl.textContent = Number.isFinite(total) ? money.format(total) : "—";
  }

  form.querySelectorAll('input[name="facility_item"]').forEach((input) => {
    input.addEventListener("change", updateSummary);
  });
  partyEl.addEventListener("input", updateSummary);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    messageEl.textContent = "";

    const item = selectedItem();
    if (!item) {
      messageEl.textContent = "Select an access option.";
      return;
    }

    const guestName = document.getElementById("rgf-guest-name").value.trim();
    const roomNumber = document.getElementById("rgf-room-number").value.trim();
    const email = document.getElementById("rgf-email").value.trim();
    const phone = document.getElementById("rgf-phone").value.trim();
    const start = document.getElementById("rgf-start").value;

    if (!guestName || !start) {
      messageEl.textContent = "Guest name and reservation time are required.";
      return;
    }
    if (!email && !phone) {
      messageEl.textContent = "Provide at least a phone number or email.";
      return;
    }

    const params = new URLSearchParams({
      category_key: config.categoryKey,
      service_item: item.value,
      guest_name: guestName,
      room_number: roomNumber,
      email,
      phone,
      reservation_start: start,
      party_size: String(partySize()),
      guest_note: document.getElementById("rgf-note").value.trim(),
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
        throw new Error("The hotel system could not accept this reservation.");
      }

      const result = payload.message || {};
      messageEl.textContent =
        "Reservation request received. Reference: " + String(result.reservation || "");

      form.querySelectorAll("input, textarea, button").forEach((element) => {
        if (element !== submitBtn) element.disabled = true;
      });
      submitBtn.textContent = "Reservation Submitted";
    } catch (error) {
      messageEl.textContent = error.message || "Unable to submit reservation.";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Reservation Request";
    }
  });

  updateSummary();
})();

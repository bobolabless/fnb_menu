(() => {
  "use strict";

  const config = window.RHOGUEST_SPA_CONFIG || {};
  const form = document.getElementById("rgs-form");
  if (!form) return;

  const resourceSelect = document.getElementById("rgs-resource");
  const durationEl = document.getElementById("rgs-duration");
  const totalEl = document.getElementById("rgs-total");
  const messageEl = document.getElementById("rgs-message");
  const submitBtn = document.getElementById("rgs-submit");

  const money = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: config.currency || "NGN",
    maximumFractionDigits: 2,
  });

  function selectedItem() {
    return form.querySelector('input[name="spa_item"]:checked');
  }

  function updateResources() {
    const item = selectedItem();
    resourceSelect.value = "";

    [...resourceSelect.options].forEach((option, index) => {
      if (index === 0) {
        option.hidden = false;
        return;
      }
      option.hidden = !item || option.dataset.serviceItem !== item.value;
    });
  }

  function updateSummary() {
    const item = selectedItem();

    if (!item) {
      durationEl.textContent = "—";
      totalEl.textContent = "—";
      updateResources();
      return;
    }

    const duration = Number.parseInt(item.dataset.duration || "0", 10);
    const rate = Number.parseFloat(item.dataset.rate || "0");

    durationEl.textContent = duration ? duration + " min" : "—";
    totalEl.textContent = Number.isFinite(rate) ? money.format(rate) : "—";
    updateResources();
  }

  form.querySelectorAll('input[name="spa_item"]').forEach((input) => {
    input.addEventListener("change", updateSummary);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    messageEl.textContent = "";

    const item = selectedItem();
    if (!item) {
      messageEl.textContent = "Select a Spa treatment.";
      return;
    }

    const guestName = document.getElementById("rgs-guest-name").value.trim();
    const roomNumber = document.getElementById("rgs-room-number").value.trim();
    const email = document.getElementById("rgs-email").value.trim();
    const phone = document.getElementById("rgs-phone").value.trim();
    const start = document.getElementById("rgs-start").value;

    if (!guestName || !start) {
      messageEl.textContent = "Guest name and appointment time are required.";
      return;
    }
    if (!email && !phone) {
      messageEl.textContent = "Provide at least a phone number or email.";
      return;
    }

    // Security contract: no rate, amount, duration or appointment end is sent.
    const params = new URLSearchParams({
      service_item: item.value,
      spa_resource: resourceSelect.value || "",
      guest_name: guestName,
      room_number: roomNumber,
      email,
      phone,
      appointment_start: start,
      guest_note: document.getElementById("rgs-note").value.trim(),
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
        throw new Error("The hotel system could not accept this Spa appointment.");
      }

      const result = payload.message || {};
      messageEl.textContent =
        "Spa appointment request received. Reference: " +
        String(result.appointment || "");

      form.querySelectorAll("input, textarea, select, button").forEach((element) => {
        if (element !== submitBtn) element.disabled = true;
      });
      submitBtn.textContent = "Appointment Submitted";
    } catch (error) {
      messageEl.textContent = error.message || "Unable to submit Spa appointment.";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Spa Appointment";
    }
  });

  updateSummary();
})();

(() => {
  "use strict";

  const config = window.RHOGUEST_TRANSPORT_CONFIG || {};
  const form = document.getElementById("rgt-form");
  if (!form) return;

  const passengerEl = document.getElementById("rgt-passengers");
  const durationEl = document.getElementById("rgt-duration");
  const totalEl = document.getElementById("rgt-total");
  const messageEl = document.getElementById("rgt-message");
  const submitBtn = document.getElementById("rgt-submit");
  const trackBookingEl = document.getElementById("rgt-track-booking");
  const trackTokenEl = document.getElementById("rgt-track-token");
  const trackResultEl = document.getElementById("rgt-track-result");

  const money = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: config.currency || "NGN",
    maximumFractionDigits: 2,
  });

  function selectedItem() {
    return form.querySelector('input[name="transport_item"]:checked');
  }

  function passengers() {
    const value = Number.parseInt(passengerEl.value || "1", 10);
    return Math.max(1, Math.min(50, Number.isFinite(value) ? value : 1));
  }

  function updateSummary() {
    const item = selectedItem();
    passengerEl.value = String(passengers());

    if (!item) {
      durationEl.textContent = "—";
      totalEl.textContent = "—";
      return;
    }

    const duration = Number.parseInt(item.dataset.duration || "0", 10);
    const rate = Number.parseFloat(item.dataset.rate || "0");
    const basis = item.dataset.basis || "Per Reservation";
    const total = basis === "Per Person" ? rate * passengers() : rate;

    durationEl.textContent = duration ? duration + " min" : "—";
    totalEl.textContent = Number.isFinite(total) ? money.format(total) : "—";
  }

  form.querySelectorAll('input[name="transport_item"]').forEach((input) => {
    input.addEventListener("change", updateSummary);
  });
  passengerEl.addEventListener("input", updateSummary);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    messageEl.textContent = "";

    const item = selectedItem();
    if (!item) {
      messageEl.textContent = "Select a Transport service.";
      return;
    }

    const guestName = document.getElementById("rgt-guest-name").value.trim();
    const roomNumber = document.getElementById("rgt-room-number").value.trim();
    const email = document.getElementById("rgt-email").value.trim();
    const phone = document.getElementById("rgt-phone").value.trim();
    const pickupTime = document.getElementById("rgt-pickup-time").value;
    const pickupLocation = document.getElementById("rgt-pickup-location").value.trim();
    const dropoffLocation = document.getElementById("rgt-dropoff-location").value.trim();

    if (!guestName || !pickupTime || !pickupLocation || !dropoffLocation) {
      messageEl.textContent = "Guest name, pickup time and both trip locations are required.";
      return;
    }
    if (!email && !phone) {
      messageEl.textContent = "Provide at least a phone number or email.";
      return;
    }

    // Security contract: no browser-supplied rate, total, duration, end-time,
    // vehicle or driver is submitted.
    const params = new URLSearchParams({
      service_item: item.value,
      guest_name: guestName,
      room_number: roomNumber,
      email,
      phone,
      scheduled_pickup_at: pickupTime,
      pickup_location: pickupLocation,
      dropoff_location: dropoffLocation,
      passenger_count: String(passengers()),
      luggage_count: document.getElementById("rgt-luggage").value || "0",
      flight_number: document.getElementById("rgt-flight-number").value.trim(),
      trip_note: document.getElementById("rgt-note").value.trim(),
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
        throw new Error("The hotel system could not accept this Transport request.");
      }

      const result = payload.message || {};
      const saved = {
        booking: String(result.booking || ""),
        token: String(result.token || ""),
      };
      try {
        localStorage.setItem("rhoguest_transport_last_booking_v1", JSON.stringify(saved));
      } catch (_) {}

      trackBookingEl.value = saved.booking;
      trackTokenEl.value = saved.token;
      messageEl.textContent =
        "Transport request received. Reference: " + saved.booking +
        ". Your tracking details have been filled below.";
      submitBtn.textContent = "Transport Request Submitted";
    } catch (error) {
      messageEl.textContent = error.message || "Unable to submit Transport request.";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Transport Request";
    }
  });

  async function trackBooking() {
    const booking = trackBookingEl.value.trim();
    const token = trackTokenEl.value.trim();
    trackResultEl.textContent = "";

    if (!booking || !token) {
      trackResultEl.textContent = "Enter the booking reference and access token.";
      return;
    }

    const url = new URL(config.statusUrl, window.location.origin);
    url.searchParams.set("booking_name", booking);
    url.searchParams.set("token", token);

    try {
      const response = await fetch(url.toString(), { credentials: "same-origin" });
      const payload = await response.json();
      if (!response.ok || payload.exc) {
        throw new Error("Booking status could not be retrieved.");
      }

      const row = payload.message || {};
      const assignment = row.vehicle_name || row.driver_name
        ? " · " + [row.vehicle_name, row.vehicle_registration, row.driver_name].filter(Boolean).join(" · ")
        : "";

      trackResultEl.textContent =
        String(row.status || "Requested") +
        " · " + String(row.scheduled_pickup_at || "") +
        assignment;
    } catch (error) {
      trackResultEl.textContent = error.message || "Unable to retrieve booking status.";
    }
  }

  document.getElementById("rgt-track").addEventListener("click", trackBooking);

  try {
    const saved = JSON.parse(localStorage.getItem("rhoguest_transport_last_booking_v1") || "{}");
    if (saved.booking && saved.token) {
      trackBookingEl.value = saved.booking;
      trackTokenEl.value = saved.token;
    }
  } catch (_) {}

  updateSummary();
})();

/*!
 * RhoHMS F&B Menu v0.1.0
 * Complete public-menu controller
 *
 * Features:
 * - Food / Drinks menu switching
 * - Sticky + floating category navigation
 * - Active-category tracking
 * - Search
 * - Add to cart
 * - Quantity +/- controls
 * - Remove individual cart item
 * - Clear entire cart
 * - Special instructions
 * - Persistent localStorage cart
 * - Responsive category bottom sheet
 * - Checkout validation
 * - Frappe-safe POST using frappe.call when available
 * - CSRF-aware fetch fallback
 * - Detailed backend error handling
 * - Cart clears only after a valid payment URL is returned
 */

(() => {
  "use strict";

  // =========================================================
  // ROOT / CONFIG
  // =========================================================

  const root = document.getElementById("rhohms-fnb-menu");
  if (!root) return;

  const cfg = window.RHOFNB_MENU_CONFIG || {};

  const landing = document.getElementById("lmv3-landing");
  const reader = document.getElementById("lmv3-reader");

  const panels = [
    ...root.querySelectorAll("[data-menu-panel]")
  ];

  const switches = [
    ...root.querySelectorAll("[data-switch-menu]")
  ];

  const dock =
    document.getElementById("lmv32-category-dock");

  const pillsWrap =
    document.getElementById("lmv32-category-pills");

  const currentCategory =
    document.getElementById("lmv32-current-category");

  const categoryFab =
    document.getElementById("lmv32-category-fab");

  const categoryFabLabel =
    document.getElementById("lmv32-fab-label");

  const categorySheet =
    document.getElementById("lmv32-category-sheet");

  const categorySheetList =
    document.getElementById("lmv32-category-sheet-list");

  const categoryOpen =
    document.getElementById("lmv32-category-open");

  const searchInput =
    document.getElementById("lmv3-search");

  const requestedMenu = (
    root.dataset.requestedMenu || ""
  ).toLowerCase();

  let categoryObserver = null;
  let activeMenuType = "";

  // =========================================================
  // SMALL HELPERS
  // =========================================================

  function cssEscape(value) {
    if (
      window.CSS &&
      typeof window.CSS.escape === "function"
    ) {
      return window.CSS.escape(String(value));
    }

    return String(value)
      .replace(/["\\]/g, "\\$&");
  }

  function exists(type) {
    return !!root.querySelector(
      `[data-menu-panel="${cssEscape(type)}"]`
    );
  }

  function lockScroll(locked) {
    document.documentElement.style.overflow =
      locked ? "hidden" : "";

    document.body.style.overflow =
      locked ? "hidden" : "";
  }

  function activePanel() {
    return (
      panels.find((panel) => !panel.hidden) ||
      null
    );
  }

  function safeText(value) {
    return value == null
      ? ""
      : String(value);
  }

  // =========================================================
  // FRAPPE REQUEST / CSRF
  // =========================================================

  function getCsrfToken() {
    const candidates = [
      cfg.csrfToken,
      (window.frappe && window.frappe.csrf_token),
      window.csrf_token
    ];

    for (const candidate of candidates) {
      const token = String(candidate || "").trim();
      if (token && token !== "None" && token !== "null" && token !== "undefined") {
        return token;
      }
    }

    return "";
  }

  function parseServerMessages(raw) {
    if (!raw) return [];

    let values = raw;
    if (typeof values === "string") {
      try {
        values = JSON.parse(values);
      } catch (_) {
        return [values];
      }
    }

    if (!Array.isArray(values)) return [];

    return values.map((entry) => {
      if (entry === null || entry === undefined) return "";
      if (typeof entry === "object") return entry.message || entry.title || "";
      try {
        const parsed = JSON.parse(entry);
        return parsed.message || parsed.title || entry;
      } catch (_) {
        return String(entry || "");
      }
    }).filter(Boolean);
  }

  function extractBackendError(data, fallback = "Request failed.") {
    if (!data) return fallback;

    const messages = parseServerMessages(data._server_messages);
    if (messages.length) return messages.join(" ");
    if (data.message) {
      return typeof data.message === "string" ? data.message : JSON.stringify(data.message);
    }
    if (data.exception) return String(data.exception);
    if (data.exc) {
      const lines = String(data.exc).split("\\n").map((line) => line.trim()).filter(Boolean);
      if (lines.length) return lines[lines.length - 1];
    }
    if (data.exc_type) return String(data.exc_type);
    return fallback;
  }

  async function frappePost(url, args = {}) {
    const csrfToken = getCsrfToken();
    if (!csrfToken) {
      throw new Error(
        "The secure checkout token is unavailable. Refresh the menu page and try again."
      );
    }

    const body = new URLSearchParams();
    body.append("csrf_token", csrfToken);

    Object.entries(args).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        body.append(key, "");
      } else if (typeof value === "object") {
        body.append(key, JSON.stringify(value));
      } else {
        body.append(key, String(value));
      }
    });

    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "X-Frappe-CSRF-Token": csrfToken
      },
      body: body.toString()
    });

    const responseText = await response.text();
    let data = null;
    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch (_) {}
    }

    if (!response.ok) {
      throw new Error(
        data
          ? extractBackendError(data, `Server returned HTTP ${response.status}.`)
          : (responseText || `Server returned HTTP ${response.status}.`)
      );
    }

    if (data && (data.exc || data.exception)) {
      throw new Error(
        extractBackendError(data, "The server could not complete the request.")
      );
    }

    return data || {};
  }

  // =========================================================
  // SEARCH
  // =========================================================

  function applySearch(query) {
    const panel =
      activePanel();

    if (!panel) return;

    const q = (
      query || ""
    )
      .trim()
      .toLowerCase();

    panel
      .querySelectorAll(
        "[data-search]"
      )
      .forEach((item) => {
        const haystack =
          (
            item.dataset.search ||
            ""
          ).toLowerCase();

        item.hidden =
          !!q &&
          !haystack.includes(q);
      });

    panel
      .querySelectorAll(
        "[data-search-category]"
      )
      .forEach((category) => {
        const visibleItem =
          [
            ...category.querySelectorAll(
              "[data-search]"
            )
          ].some(
            (item) => !item.hidden
          );

        category.hidden =
          !visibleItem;
      });

    rebuildCategories();
  }

  searchInput?.addEventListener(
    "input",
    () => {
      applySearch(
        searchInput.value
      );
    }
  );

  // =========================================================
  // CATEGORY NAVIGATION
  // =========================================================

  function getVisibleCategories() {
    const panel =
      activePanel();

    if (!panel) return [];

    return [
      ...panel.querySelectorAll(
        ".lmv3-category"
      )
    ].filter(
      (category) =>
        !category.hidden
    );
  }

  function setActiveCategory(
    categoryId,
    label
  ) {
    if (!categoryId) return;

    root
      .querySelectorAll(
        "[data-category-target]"
      )
      .forEach((button) => {
        button.classList.toggle(
          "active",
          button.dataset.categoryTarget ===
            categoryId
        );
      });

    const text =
      label || "Categories";

    if (currentCategory) {
      currentCategory.textContent =
        text;
    }

    if (categoryFabLabel) {
      categoryFabLabel.textContent =
        text;
    }

    const activePill =
      pillsWrap?.querySelector(
        `[data-category-target="${cssEscape(categoryId)}"]`
      );

    activePill?.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest"
    });
  }

  function observeCategories(
    categories
  ) {
    categoryObserver?.disconnect();

    if (
      !(
        "IntersectionObserver"
        in window
      ) ||
      !categories.length
    ) {
      return;
    }

    categoryObserver =
      new IntersectionObserver(
        (entries) => {
          const visible =
            entries
              .filter(
                (entry) =>
                  entry.isIntersecting
              )
              .sort(
                (a, b) =>
                  b.intersectionRatio -
                  a.intersectionRatio
              )[0];

          if (!visible) return;

          setActiveCategory(
            visible.target.id,
            visible.target
              .dataset
              .categoryLabel
          );
        },

        {
          rootMargin:
            "-18% 0px -68% 0px",

          threshold:
            [0, 0.05, 0.2, 0.5]
        }
      );

    categories.forEach(
      (category) =>
        categoryObserver.observe(
          category
        )
    );
  }

  function categoryButton(
    category,
    sheet = false
  ) {
    const button =
      document.createElement(
        "button"
      );

    button.type =
      "button";

    button.className =
      sheet
        ? "lmv32-sheet-category"
        : "lmv32-category-pill";

    button.dataset.categoryTarget =
      category.id;

    button.textContent =
      category.dataset
        .categoryLabel ||
      "Category";

    button.addEventListener(
      "click",
      () => {
        category.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });

        setActiveCategory(
          category.id,
          category.dataset
            .categoryLabel
        );

        if (
          sheet &&
          categorySheet
        ) {
          categorySheet.hidden =
            true;

          lockScroll(false);
        }
      }
    );

    return button;
  }

  function rebuildCategories() {
    const categories =
      getVisibleCategories();

    if (
      !dock ||
      !pillsWrap ||
      !categorySheetList
    ) {
      return;
    }

    pillsWrap.innerHTML = "";
    categorySheetList.innerHTML =
      "";

    categories.forEach(
      (category) => {
        pillsWrap.appendChild(
          categoryButton(
            category,
            false
          )
        );

        categorySheetList.appendChild(
          categoryButton(
            category,
            true
          )
        );
      }
    );

    dock.hidden =
      categories.length === 0;

    if (categoryFab) {
      categoryFab.hidden =
        categories.length === 0 ||
        reader?.hidden;
    }

    if (categories.length) {
      setActiveCategory(
        categories[0].id,
        categories[0]
          .dataset
          .categoryLabel
      );
    }

    observeCategories(
      categories
    );
  }

  categoryOpen?.addEventListener(
    "click",
    () => {
      if (!categorySheet) return;

      categorySheet.hidden =
        false;

      lockScroll(true);
    }
  );

  categoryFab?.addEventListener(
    "click",
    () => {
      if (!categorySheet) return;

      categorySheet.hidden =
        false;

      lockScroll(true);
    }
  );

  // =========================================================
  // MENU SWITCHING
  // =========================================================

  function openMenu(
    type,
    updateUrl = true
  ) {
    if (!exists(type)) return;

    activeMenuType = type;

    if (landing) {
      landing.hidden =
        true;
    }

    if (reader) {
      reader.hidden =
        false;
    }

    panels.forEach(
      (panel) => {
        panel.hidden =
          panel.dataset.menuPanel !==
          type;
      }
    );

    switches.forEach(
      (button) => {
        button.classList.toggle(
          "active",
          button.dataset.switchMenu ===
            type
        );
      }
    );

    if (searchInput) {
      searchInput.value = "";
    }

    applySearch("");
    rebuildCategories();

    if (updateUrl) {
      history.replaceState(
        {},
        "",
        `${location.pathname}?menu=${encodeURIComponent(type)}`
      );
    }

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  }

  function showLanding() {
    activeMenuType = "";

    if (reader) {
      reader.hidden =
        true;
    }

    if (landing) {
      landing.hidden =
        false;
    }

    panels.forEach(
      (panel) => {
        panel.hidden = true;
      }
    );

    if (dock) {
      dock.hidden = true;
    }

    if (categoryFab) {
      categoryFab.hidden = true;
    }

    history.replaceState(
      {},
      "",
      location.pathname
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  }

  root.addEventListener(
    "click",
    (event) => {
      const opener =
        event.target.closest(
          "[data-open-menu]"
        );

      if (opener) {
        openMenu(
          opener.dataset.openMenu
        );

        return;
      }

      const switcher =
        event.target.closest(
          "[data-switch-menu]"
        );

      if (switcher) {
        openMenu(
          switcher.dataset.switchMenu
        );

        return;
      }

      if (
        event.target.closest(
          "[data-back-to-choice]"
        )
      ) {
        showLanding();
      }
    }
  );

  // =========================================================
  // PAGE BACKGROUND / STICKY OFFSET
  // =========================================================

  function updateStickyOffset() {
    const navbar =
      document.querySelector(
        ".navbar"
      ) ||
      document.querySelector(
        "header.navbar"
      );

    const height =
      navbar
        ?.getBoundingClientRect()
        .height || 0;

    root.style.setProperty(
      "--lm-nav-top",
      `${Math.max(
        8,
        Math.ceil(height) + 6
      )}px`
    );
  }

  function syncPageBackground() {
    const bg =
      getComputedStyle(root)
        .getPropertyValue(
          "--lm-bg"
        )
        .trim();

    if (!bg) return;

    document.body.style.background =
      bg;

    document
      .querySelectorAll(
        [
          ".web-footer",
          ".web-page-content",
          ".page_content",
          ".page-content"
        ].join(",")
      )
      .forEach((node) => {
        node.style.background =
          bg;
      });
  }

  updateStickyOffset();
  syncPageBackground();

  window.addEventListener(
    "resize",
    updateStickyOffset
  );

  // =========================================================
  // INITIAL MENU
  // =========================================================

  if (
    requestedMenu &&
    exists(requestedMenu)
  ) {
    openMenu(
      requestedMenu,
      false
    );
  } else if (
    !(
      exists("food") &&
      exists("drinks")
    )
  ) {
    if (exists("food")) {
      openMenu(
        "food",
        false
      );
    } else if (
      exists("drinks")
    ) {
      openMenu(
        "drinks",
        false
      );
    }
  }

  // =========================================================
  // CATEGORY SHEET CLOSE
  // =========================================================

  document.addEventListener(
    "click",
    (event) => {
      if (
        event.target.closest(
          "[data-close-categories]"
        )
      ) {
        if (categorySheet) {
          categorySheet.hidden =
            true;
        }

        lockScroll(false);
      }
    }
  );

  // =========================================================
  // SELF ORDERING
  // =========================================================

  if (
    !Number(
      cfg.selfOrdering || 0
    )
  ) {
    return;
  }

  const CART_KEY =
    "fnb_menu_cart_v1";

  let cart = (() => {
    try {
      const value =
        JSON.parse(
          localStorage.getItem(
            CART_KEY
          ) || "[]"
        );

      return Array.isArray(value)
        ? value
        : [];
    } catch (_) {
      return [];
    }
  })();

  const cartBar =
    document.getElementById(
      "lmv3-cart-bar"
    );

  const cartDrawer =
    document.getElementById(
      "lmv3-cart-drawer"
    );

  const checkoutModal =
    document.getElementById(
      "lmv3-checkout-modal"
    );

  const toast =
    document.getElementById(
      "lmv32-toast"
    );

  const cartCount =
    document.getElementById(
      "lmv3-cart-count"
    );

  const cartTotal =
    document.getElementById(
      "lmv3-cart-total"
    );

  const cartLines =
    document.getElementById(
      "lmv3-cart-lines"
    );

  const drawerTotal =
    document.getElementById(
      "lmv3-drawer-total"
    );

  const clearCartButton =
    document.getElementById(
      "lmv32-clear-cart"
    );

  const checkoutButton =
    document.getElementById(
      "lmv3-checkout-btn"
    );

  const checkoutForm =
    document.getElementById(
      "lmv3-checkout-form"
    );

  const payButton =
    document.getElementById(
      "lmv3-pay-btn"
    );

  const checkoutMessage =
    document.getElementById(
      "lmv3-checkout-message"
    );

  const serviceSelect =
    document.getElementById(
      "lmv3-service-type"
    );

  const roomWrap =
    document.getElementById(
      "lmv3-room-wrap"
    );

  const tableWrap =
    document.getElementById(
      "lmv3-table-wrap"
    );

  const roomInput =
    document.getElementById(
      "lmv3-room-number"
    );

  const tableInput =
    document.getElementById(
      "lmv3-table-number"
    );

  let toastTimer = null;
  let checkoutInFlight = false;

  // =========================================================
  // CART HELPERS
  // =========================================================

  function money(value) {
    try {
      return new Intl.NumberFormat(
        undefined,
        {
          style: "currency",
          currency:
            cfg.currency ||
            "NGN",
          maximumFractionDigits:
            0
        }
      ).format(
        Number(value || 0)
      );
    } catch (_) {
      return `${
        cfg.currency || ""
      } ${Number(
        value || 0
      ).toLocaleString()}`;
    }
  }

  function cartTotalValue() {
    return cart.reduce(
      (sum, row) =>
        sum +
        Number(
          row.price || 0
        ) *
        Number(
          row.qty || 0
        ),
      0
    );
  }

  function cartItemCount() {
    return cart.reduce(
      (sum, row) =>
        sum +
        Number(
          row.qty || 0
        ),
      0
    );
  }

  function persistCart() {
    try {
      localStorage.setItem(
        CART_KEY,
        JSON.stringify(cart)
      );
    } catch (_) {}
  }

  function showToast(message) {
    if (!toast) return;

    toast.textContent =
      message;

    toast.hidden = false;

    clearTimeout(
      toastTimer
    );

    toastTimer =
      setTimeout(() => {
        toast.hidden =
          true;
      }, 1800);
  }

  function closeCart() {
    if (cartDrawer) {
      cartDrawer.hidden =
        true;
    }

    lockScroll(false);
  }

  function closeCheckout() {
    if (checkoutModal) {
      checkoutModal.hidden =
        true;
    }

    lockScroll(false);
  }

  function renderCart() {
    persistCart();

    const quantity =
      cartItemCount();

    const totalValue =
      cartTotalValue();

    if (cartBar) {
      cartBar.hidden =
        quantity === 0;
    }

    categoryFab?.classList.toggle(
      "with-cart",
      quantity > 0
    );

    if (cartCount) {
      cartCount.textContent =
        quantity;
    }

    if (cartTotal) {
      cartTotal.textContent =
        money(totalValue);
    }

    if (drawerTotal) {
      drawerTotal.textContent =
        money(totalValue);
    }

    if (!cartLines) return;

    cartLines.innerHTML = "";

    if (!cart.length) {
      const empty =
        document.createElement(
          "div"
        );

      empty.className =
        "lmv32-cart-empty";

      empty.style.cssText =
        "padding:26px 0;text-align:center;opacity:.72";

      empty.textContent =
        "Your cart is empty.";

      cartLines.appendChild(
        empty
      );

      return;
    }

    cart.forEach(
      (row, index) => {
        const line =
          document.createElement(
            "div"
          );

        line.className =
          "lmv3-cart-line";

        const info =
          document.createElement(
            "div"
          );

        const title =
          document.createElement(
            "h4"
          );

        title.textContent =
          row.item_name;

        const amount =
          document.createElement(
            "small"
          );

        amount.textContent =
          money(
            Number(
              row.price || 0
            ) *
            Number(
              row.qty || 0
            )
          );

        const note =
          document.createElement(
            "input"
          );

        note.className =
          "lmv3-cart-note";

        note.type =
          "text";

        note.maxLength =
          500;

        note.placeholder =
          "Special instruction";

        note.value =
          row.special_instruction ||
          "";

        note.dataset.note =
          String(index);

        info.append(
          title,
          amount,
          note
        );

        const controls =
          document.createElement(
            "div"
          );

        controls.className =
          "lmv3-line-controls";

        const minus =
          document.createElement(
            "button"
          );

        minus.type =
          "button";

        minus.textContent =
          "−";

        minus.dataset.minus =
          String(index);

        minus.setAttribute(
          "aria-label",
          `Reduce ${row.item_name}`
        );

        const qty =
          document.createElement(
            "b"
          );

        qty.textContent =
          row.qty;

        const plus =
          document.createElement(
            "button"
          );

        plus.type =
          "button";

        plus.textContent =
          "+";

        plus.dataset.plus =
          String(index);

        plus.setAttribute(
          "aria-label",
          `Increase ${row.item_name}`
        );

        controls.append(
          minus,
          qty,
          plus
        );

        const remove =
          document.createElement(
            "button"
          );

        remove.type =
          "button";

        remove.className =
          "lmv32-remove-line";

        remove.textContent =
          "×";

        remove.dataset.remove =
          String(index);

        remove.title =
          "Remove item";

        remove.setAttribute(
          "aria-label",
          `Remove ${row.item_name}`
        );

        line.append(
          info,
          controls,
          remove
        );

        cartLines.appendChild(
          line
        );
      }
    );
  }

  function addToCart(button) {
    const itemCode =
      button.dataset.itemCode;

    const itemName =
      button.dataset.itemName ||
      "Item";

    const price =
      Number(
        button.dataset.price || 0
      );

    if (!itemCode) {
      showToast(
        "This item is not configured for self ordering."
      );

      return;
    }

    if (
      !Number.isFinite(price) ||
      price < 0
    ) {
      showToast(
        "This item has an invalid menu price."
      );

      return;
    }

    let row =
      cart.find(
        (item) =>
          item.item_code ===
          itemCode
      );

    if (row) {
      if (row.qty < 20) {
        row.qty += 1;
      }
    } else {
      row = {
        item_code:
          itemCode,

        item_name:
          itemName,

        price,
        qty: 1,

        special_instruction:
          ""
      };

      cart.push(row);
    }

    renderCart();

    showToast(
      `${itemName} added to cart`
    );

    const oldText =
      button.textContent;

    button.textContent =
      "Added ✓";

    button.disabled =
      true;

    setTimeout(() => {
      button.textContent =
        oldText;

      button.disabled =
        false;
    }, 650);
  }

  // =========================================================
  // ADD TO CART
  // =========================================================

  root.addEventListener(
    "click",
    (event) => {
      const button =
        event.target.closest(
          ".lmv3-add"
        );

      if (!button) return;

      event.preventDefault();

      addToCart(button);
    }
  );

  // =========================================================
  // CART OPEN / CLOSE
  // =========================================================

  cartBar?.addEventListener(
    "click",
    () => {
      if (!cart.length) {
        showToast(
          "Your cart is empty."
        );

        return;
      }

      cartDrawer.hidden =
        false;

      lockScroll(true);
    }
  );

  document.addEventListener(
    "click",
    (event) => {
      if (
        event.target.closest(
          "[data-close-cart]"
        )
      ) {
        closeCart();
      }

      if (
        event.target.closest(
          "[data-close-checkout]"
        )
      ) {
        closeCheckout();
      }

      const plus =
        event.target.closest(
          "[data-plus]"
        );

      if (plus) {
        const index =
          Number(
            plus.dataset.plus
          );

        if (
          cart[index] &&
          cart[index].qty < 20
        ) {
          cart[index].qty +=
            1;

          renderCart();
        }
      }

      const minus =
        event.target.closest(
          "[data-minus]"
        );

      if (minus) {
        const index =
          Number(
            minus.dataset.minus
          );

        if (cart[index]) {
          cart[index].qty -=
            1;

          if (
            cart[index].qty <=
            0
          ) {
            cart.splice(
              index,
              1
            );
          }

          renderCart();
        }
      }

      const remove =
        event.target.closest(
          "[data-remove]"
        );

      if (remove) {
        const index =
          Number(
            remove.dataset.remove
          );

        if (cart[index]) {
          const name =
            cart[index].item_name;

          cart.splice(
            index,
            1
          );

          renderCart();

          showToast(
            `${name} removed`
          );
        }
      }
    }
  );

  document.addEventListener(
    "input",
    (event) => {
      const note =
        event.target.closest(
          "[data-note]"
        );

      if (!note) return;

      const index =
        Number(
          note.dataset.note
        );

      if (cart[index]) {
        cart[index]
          .special_instruction =
          note.value.slice(
            0,
            500
          );

        persistCart();
      }
    }
  );

  // =========================================================
  // CLEAR CART
  // =========================================================

  clearCartButton?.addEventListener(
    "click",
    () => {
      if (!cart.length) {
        closeCart();
        return;
      }

      const confirmed =
        window.confirm(
          "Clear all items from your cart?"
        );

      if (!confirmed) {
        return;
      }

      cart = [];

      renderCart();
      closeCart();

      showToast(
        "Cart cleared"
      );
    }
  );

  // =========================================================
  // CHECKOUT OPEN
  // =========================================================

  checkoutButton?.addEventListener(
    "click",
    () => {
      if (!cart.length) {
        showToast(
          "Your cart is empty."
        );

        return;
      }

      if (cartDrawer) {
        cartDrawer.hidden =
          true;
      }

      if (checkoutModal) {
        checkoutModal.hidden =
          false;
      }

      lockScroll(true);
    }
  );

  // =========================================================
  // SERVICE FIELDS
  // =========================================================

  function updateServiceFields() {
    const service =
      serviceSelect?.value ||
      "";

    if (roomWrap) {
      roomWrap.hidden =
        service !==
        "Room Service";
    }

    if (tableWrap) {
      tableWrap.hidden =
        service !==
        "Dine In";
    }

    if (roomInput) {
      roomInput.required =
        service ===
        "Room Service";
    }

    if (tableInput) {
      tableInput.required =
        service ===
        "Dine In";
    }
  }

  serviceSelect?.addEventListener(
    "change",
    updateServiceFields
  );

  updateServiceFields();

  // =========================================================
  // CHECKOUT VALIDATION
  // =========================================================

  function validateCheckout() {
    if (!cart.length) {
      throw new Error(
        "Your cart is empty."
      );
    }

    const guestName =
      document
        .getElementById(
          "lmv3-guest-name"
        )
        ?.value
        .trim() || "";

    const email =
      document
        .getElementById(
          "lmv3-email"
        )
        ?.value
        .trim() || "";

    const phone =
      document
        .getElementById(
          "lmv3-phone"
        )
        ?.value
        .trim() || "";

    const serviceType =
      serviceSelect?.value ||
      "";

    const roomNumber =
      roomInput?.value
        .trim() || "";

    const tableNumber =
      tableInput?.value
        .trim() || "";

    if (!guestName) {
      throw new Error(
        "Guest name is required."
      );
    }

    if (
      !email ||
      !email.includes("@")
    ) {
      throw new Error(
        "A valid email address is required."
      );
    }

    if (!serviceType) {
      throw new Error(
        "Please select a service type."
      );
    }

    if (
      serviceType ===
        "Room Service" &&
      !roomNumber
    ) {
      throw new Error(
        "Room number is required for Room Service."
      );
    }

    if (
      serviceType ===
        "Dine In" &&
      !tableNumber
    ) {
      throw new Error(
        "Table number is required for Dine In."
      );
    }

    return {
      guest_name:
        guestName,

      email,
      phone,

      service_type:
        serviceType,

      room_number:
        roomNumber,

      table_number:
        tableNumber,

      cart:
        JSON.stringify(
          cart.map((row) => ({
            item_code:
              row.item_code,

            qty:
              Number(
                row.qty || 1
              ),

            special_instruction:
              (
                row.special_instruction ||
                ""
              ).slice(
                0,
                500
              )
          }))
        )
    };
  }

  // =========================================================
  // CHECKOUT SUBMIT
  // =========================================================

  checkoutForm?.addEventListener(
    "submit",
    async (event) => {
      event.preventDefault();

      if (checkoutInFlight) {
        return;
      }

      checkoutInFlight =
        true;

      if (checkoutMessage) {
        checkoutMessage.textContent =
          "";
      }

      if (payButton) {
        payButton.disabled =
          true;

        payButton.textContent =
          "Preparing secure payment…";
      }

      try {
        const args =
          validateCheckout();

        const response =
          await frappePost(
            cfg.checkoutUrl,
            args
          );

        const result =
          response?.message ||
          {};

        if (!result.order) {
          throw new Error(
            "Checkout was created without an order reference."
          );
        }

        if (!result.payment_url) {
          throw new Error(
            "Payment gateway did not return a payment URL."
          );
        }

        try {
          localStorage.setItem(
            "fnb_menu_last_order_v1",
            JSON.stringify({
              order:
                result.order,

              token:
                result.token ||
                "",

              payment_request:
                result.payment_request ||
                "",

              amount:
                result.amount,

              currency:
                result.currency
            })
          );
        } catch (_) {}

        /*
         * Clear only after:
         * - backend accepted the order
         * - Sales Order / Payment Request creation completed
         * - a payment URL was returned
         */
        cart = [];
        renderCart();

        window.location.assign(
          result.payment_url
        );

      } catch (error) {
        console.error(
          "FNB Menu Checkout Error:",
          error
        );

        if (checkoutMessage) {
          checkoutMessage.textContent =
            error?.message ||
            "Unable to continue to payment.";
        }

        checkoutInFlight =
          false;

        if (payButton) {
          payButton.disabled =
            false;

          payButton.textContent =
            "Continue to Payment";
        }
      }
    }
  );

  // =========================================================
  // ESCAPE KEY CLOSES OVERLAYS
  // =========================================================

  document.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key !==
        "Escape"
      ) {
        return;
      }

      let closed =
        false;

      if (
        categorySheet &&
        !categorySheet.hidden
      ) {
        categorySheet.hidden =
          true;

        closed = true;
      }

      if (
        cartDrawer &&
        !cartDrawer.hidden
      ) {
        cartDrawer.hidden =
          true;

        closed = true;
      }

      if (
        checkoutModal &&
        !checkoutModal.hidden
      ) {
        checkoutModal.hidden =
          true;

        closed = true;
      }

      if (closed) {
        lockScroll(false);
      }
    }
  );

  // =========================================================
  // INITIAL CART RENDER
  // =========================================================

  renderCart();
})();

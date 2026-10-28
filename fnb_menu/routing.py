"""RhoGuest public-route and legacy QR compatibility management.

The application keeps /fnb-menu as a stable internal endpoint. Hotels may
publish a friendlier route and retain old QR-code destinations as aliases
without editing hooks.py or restarting Bench.
"""

from __future__ import annotations

import re

import frappe
from frappe import _

INTERNAL_MENU_ROUTE = "/fnb-menu"
INTERNAL_KITCHEN_ROUTE = "/fnb-kitchen"

MANAGED_FIELD = "rhoguest_managed"
ROUTE_KEY_FIELD = "rhoguest_route_key"

_ALLOWED_ROUTE_RE = re.compile(r"^/[A-Za-z0-9][A-Za-z0-9._~/-]*$")

_RESERVED_PREFIXES = (
    "/app",
    "/api",
    "/assets",
    "/backups",
    "/desk",
    "/files",
    "/login",
    "/private",
    "/printview",
    "/socket.io",
)


def normalize_route(value: str | None) -> str:
    """Return a canonical site-local route and reject unsafe URL forms."""

    route = (value or "").strip()
    if not route:
        return ""

    if "://" in route or "?" in route or "#" in route:
        frappe.throw(
            _("Use a site-local path only, without a domain, query string or fragment.")
        )

    if not route.startswith("/"):
        route = f"/{route}"

    route = re.sub(r"/{2,}", "/", route)
    if len(route) > 1:
        route = route.rstrip("/")

    if "<" in route or ">" in route or not _ALLOWED_ROUTE_RE.fullmatch(route):
        frappe.throw(
            _(
                "Route {0} is invalid. Use letters, numbers, hyphens, "
                "underscores, dots and slashes only."
            ).format(frappe.bold(route))
        )

    return route


def validate_public_source_route(route: str) -> None:
    """Reject protected Frappe and RhoGuest application routes."""

    lower_route = route.lower()

    for prefix in _RESERVED_PREFIXES:
        if lower_route == prefix or lower_route.startswith(f"{prefix}/"):
            frappe.throw(
                _(
                    "Route {0} is reserved by Frappe and cannot be used "
                    "for a public QR route."
                ).format(frappe.bold(route))
            )

    if lower_route == INTERNAL_KITCHEN_ROUTE:
        frappe.throw(
            _(
                "{0} is the protected kitchen-board route and cannot be "
                "used as a public alias."
            ).format(frappe.bold(route))
        )


def preserve_previous_public_route(settings) -> None:
    """Retain the former primary route as an enabled legacy QR alias."""

    if not settings.keep_previous_routes:
        return

    old_doc = settings.get_doc_before_save()
    if not old_doc:
        return

    old_route = normalize_route(old_doc.get("public_menu_route"))
    new_route = normalize_route(settings.get("public_menu_route"))

    if not old_route or old_route.lower() == new_route.lower():
        return

    if old_route.lower() == INTERNAL_MENU_ROUTE:
        return

    existing = {
        normalize_route(row.route).lower()
        for row in (settings.legacy_qr_routes or [])
        if row.route
    }
    if old_route.lower() in existing:
        return

    settings.append(
        "legacy_qr_routes",
        {
            "route": old_route,
            "enabled": 1,
            "note": _("Automatically preserved when the Public Menu Route changed."),
        },
    )


def validate_rhoguest_settings(settings) -> None:
    """Normalize, deduplicate and validate route fields."""

    public_route = normalize_route(settings.public_menu_route or INTERNAL_MENU_ROUTE)
    validate_public_source_route(public_route)
    settings.public_menu_route = public_route

    seen = {public_route.lower()}

    for row in settings.legacy_qr_routes or []:
        row.route = normalize_route(row.route)
        if not row.route:
            frappe.throw(_("Every Legacy QR Route row requires a route."))

        validate_public_source_route(row.route)

        key = row.route.lower()
        if key in seen:
            frappe.throw(
                _(
                    "Route {0} is duplicated in the RhoGuest routing configuration."
                ).format(frappe.bold(row.route))
            )
        seen.add(key)

    _validate_against_external_redirects(seen)


def sync_rhoguest_routes(settings=None) -> dict[str, str]:
    """Synchronize RhoGuest-owned redirects into Website Settings only."""

    settings = settings or frappe.get_single("FNB Menu Settings")
    validate_rhoguest_settings(settings)

    desired = _desired_redirects(settings)
    website_settings = frappe.get_single("Website Settings")
    route_rows = website_settings.get("route_redirects") or []

    managed_by_source = {}
    unmanaged_sources = set()

    for row in route_rows:
        source = normalize_route(row.source) if row.source else ""
        if not source:
            continue

        if row.get(MANAGED_FIELD):
            managed_by_source[source.lower()] = row
        else:
            unmanaged_sources.add(source.lower())

    conflicts = sorted(
        source for source in desired if source.lower() in unmanaged_sources
    )
    if conflicts:
        frappe.throw(
            _(
                "RhoGuest cannot activate these routes because Website Settings "
                "already contains unmanaged redirects for them: {0}"
            ).format(", ".join(conflicts))
        )

    for row in list(route_rows):
        if not row.get(MANAGED_FIELD):
            continue

        source = normalize_route(row.source) if row.source else ""
        if not source or source not in desired:
            website_settings.remove(row)

    status = str(settings.route_redirect_http_status or "302")

    for source, target in desired.items():
        row = managed_by_source.get(source.lower())
        current_rows = website_settings.get("route_redirects") or []

        if row and row in current_rows:
            row.target = target
            row.redirect_http_status = status
            row.set(MANAGED_FIELD, 1)
            row.set(ROUTE_KEY_FIELD, source.lower())
        else:
            website_settings.append(
                "route_redirects",
                {
                    "source": source,
                    "target": target,
                    "redirect_http_status": status,
                    MANAGED_FIELD: 1,
                    ROUTE_KEY_FIELD: source.lower(),
                },
            )

    website_settings.save(ignore_permissions=True)

    from frappe.website.utils import clear_cache

    clear_cache()
    return desired


def get_public_menu_route() -> str:
    """Return the configured hotel-facing menu route."""

    route = frappe.db.get_single_value("FNB Menu Settings", "public_menu_route")
    return normalize_route(route) or INTERNAL_MENU_ROUTE


def _desired_redirects(settings) -> dict[str, str]:
    desired = {}

    public_route = normalize_route(settings.public_menu_route)
    if public_route and public_route.lower() != INTERNAL_MENU_ROUTE:
        desired[public_route] = INTERNAL_MENU_ROUTE

    for row in settings.legacy_qr_routes or []:
        if not row.enabled:
            continue

        route = normalize_route(row.route)
        if route and route.lower() != INTERNAL_MENU_ROUTE:
            desired[route] = INTERNAL_MENU_ROUTE

    return desired


def _validate_against_external_redirects(candidate_sources: set[str]) -> None:
    """Fail if a candidate source is owned by a non-RhoGuest redirect."""

    if not frappe.db.exists("DocType", "Website Settings"):
        return

    website_settings = frappe.get_single("Website Settings")

    for row in website_settings.get("route_redirects") or []:
        if row.get(MANAGED_FIELD) or not row.source:
            continue

        source = normalize_route(row.source)
        if source.lower() in candidate_sources:
            frappe.throw(
                _(
                    "Route {0} is already used by an existing Website Settings "
                    "redirect. Choose another route or remove that redirect first."
                ).format(frappe.bold(source))
            )

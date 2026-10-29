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
DEFAULT_PUBLIC_MENU_ROUTE = "/menu"

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

    if lower_route == INTERNAL_KITCHEN_ROUTE or lower_route.startswith(
        f"{INTERNAL_KITCHEN_ROUTE}/"
    ):
        frappe.throw(
            _(
                "{0} is reserved for the kitchen board and cannot be "
                "used as a public QR route."
            ).format(frappe.bold(route))
        )

    if lower_route.startswith(f"{INTERNAL_MENU_ROUTE}/"):
        frappe.throw(
            _(
                "{0} is below the stable internal menu route and cannot be "
                "used as a public QR route."
            ).format(frappe.bold(route))
        )



def validate_route_change_authority(settings) -> None:
    """Require System Manager authority for any public-routing configuration change."""

    old_doc = settings.get_doc_before_save()
    if _routing_signature(settings) == _routing_signature(old_doc):
        return

    user = frappe.session.user
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return

    frappe.throw(
        _(
            "Only Administrator or a System Manager can change RhoGuest public "
            "routes, redirect behaviour or legacy QR aliases."
        ),
        frappe.PermissionError,
    )


def _routing_signature(doc) -> tuple:
    """Return a stable comparison signature for routing-sensitive settings."""

    if not doc:
        return (INTERNAL_MENU_ROUTE, "302", 1, ())

    route = normalize_route(doc.get("public_menu_route")) or INTERNAL_MENU_ROUTE
    status = str(doc.get("route_redirect_http_status") or "302")
    keep_previous = 1 if doc.get("keep_previous_routes") is None else int(
        bool(doc.get("keep_previous_routes"))
    )

    aliases = []
    for row in doc.get("legacy_qr_routes") or []:
        aliases.append(
            (
                normalize_route(row.get("route")) if row.get("route") else "",
                int(bool(row.get("enabled"))),
                (row.get("note") or "").strip(),
            )
        )

    return (route.lower(), status, keep_previous, tuple(aliases))

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

    public_route = normalize_route(
        settings.public_menu_route or INTERNAL_MENU_ROUTE
    )
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
    _validate_against_existing_routes(seen)


def sync_rhoguest_routes(settings=None) -> dict[str, str]:
    """Synchronize RhoGuest-owned redirects into Website Settings only."""

    settings = settings or frappe.get_single("RhoGuest Menu Settings")
    validate_rhoguest_settings(settings)

    desired = _desired_redirects(settings)
    desired_keys = {source.lower() for source in desired}

    website_settings = frappe.get_single("Website Settings")
    route_rows = website_settings.get("route_redirects") or []

    managed_by_key = {}
    for row in route_rows:
        if not row.get(MANAGED_FIELD):
            continue

        key = (row.get(ROUTE_KEY_FIELD) or "").strip().lower()
        if key:
            managed_by_key[key] = row

    # Remove only redirects previously created by RhoGuest that are no longer
    # configured. Hotel-owned redirects and regex rules remain untouched.
    for row in list(route_rows):
        if not row.get(MANAGED_FIELD):
            continue

        key = (row.get(ROUTE_KEY_FIELD) or "").strip().lower()
        if not key or key not in desired_keys:
            website_settings.remove(row)

    status = str(settings.route_redirect_http_status or "302")

    for source, target in desired.items():
        key = source.lower()
        row = managed_by_key.get(key)
        current_rows = website_settings.get("route_redirects") or []

        values = {
            "source": _redirect_source_for_route(source),
            "target": target,
            "redirect_http_status": status,
            MANAGED_FIELD: 1,
            ROUTE_KEY_FIELD: key,
        }

        if row and row in current_rows:
            for fieldname, value in values.items():
                row.set(fieldname, value)
        else:
            website_settings.append("route_redirects", values)

    website_settings.save(ignore_permissions=True)

    # Route redirects are cached by Frappe. Clear only after Website Settings
    # saves successfully so the new QR route becomes active immediately.
    from frappe.website.utils import clear_cache

    clear_cache()
    return desired


def get_public_menu_route() -> str:
    """Return the configured hotel-facing menu route."""

    route = frappe.db.get_single_value("RhoGuest Menu Settings", "public_menu_route")
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


def _redirect_source_for_route(route: str) -> str:
    """Return a regex-safe Website Route Redirect source for one exact route."""

    path = route.strip("/")

    # Frappe treats Website Route Redirect source values as regular
    # expressions. Escape regex metacharacters so an old route such as
    # /menu.html matches only that literal URL and cannot shadow another page.
    escaped = re.escape(path)
    escaped = escaped.replace(r"\-", "-")
    return f"/{escaped}"


def _redirect_matches_route(source_pattern: str, route: str) -> bool:
    """Mirror Frappe v15 redirect matching without mutating external rules."""

    pattern = (source_pattern or "").strip("/ ") + "$"
    path_to_match = route.strip("/")

    try:
        return re.match(pattern, path_to_match) is not None
    except re.error:
        # Frappe itself logs malformed redirect regexes. RhoGuest must not make
        # an unrelated broken rule prevent the hotel from saving its settings.
        return False


def _validate_against_external_redirects(candidate_sources: set[str]) -> None:
    """Reject any candidate route already matched by a hotel-owned redirect."""

    if not frappe.db.exists("DocType", "Website Settings"):
        return

    website_settings = frappe.get_single("Website Settings")

    for row in website_settings.get("route_redirects") or []:
        if row.get(MANAGED_FIELD) or not row.source:
            continue

        for candidate in candidate_sources:
            if _redirect_matches_route(row.source, candidate):
                frappe.throw(
                    _(
                        "Route {0} is already matched by an existing Website "
                        "Settings redirect. Choose another route or remove that "
                        "redirect first."
                    ).format(frappe.bold(candidate))
                )


def _validate_against_existing_routes(candidate_sources: set[str]) -> None:
    """Reject routes already served by Frappe pages, Web Pages or Web Forms."""

    from frappe.website.path_resolver import resolve_from_map
    from frappe.website.router import get_pages

    static_pages = {
        f"/{route.strip('/')}".lower()
        for route in get_pages()
        if route and route.strip("/")
    }

    for candidate in candidate_sources:
        if candidate.lower() == INTERNAL_MENU_ROUTE:
            continue

        path = candidate.strip("/")

        if candidate.lower() in static_pages:
            frappe.throw(
                _("Route {0} is already used by an installed website page.").format(
                    frappe.bold(candidate)
                )
            )

        resolved = resolve_from_map(path)
        if resolved != path:
            frappe.throw(
                _(
                    "Route {0} is already claimed by an installed website route rule."
                ).format(frappe.bold(candidate))
            )

        for doctype in ("Web Page", "Web Form"):
            if not frappe.db.exists("DocType", doctype):
                continue

            if frappe.db.exists(doctype, {"route": path}) or frappe.db.exists(
                doctype, {"route": candidate}
            ):
                frappe.throw(
                    _("Route {0} is already used by an existing {1}.").format(
                        frappe.bold(candidate), doctype
                    )
                )

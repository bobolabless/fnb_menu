"""Public RhoGuest Swimming Pool reservation page."""

from fnb_menu.facility_page import build_context

no_cache = 1


def get_context(context):
    build_context(context, "swimming-pool")

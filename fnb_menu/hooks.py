app_name = "fnb_menu"
app_title = "RhoGuest"
app_publisher = "Rhocom Technology Limited"
app_description = "RhoGuest digital menu and guest-services add-on for RhoHMS."
app_email = "info@rhocom.com"
app_license = "Proprietary"

required_apps = ["erpnext"]

after_install = "fnb_menu.install.after_install"
after_migrate = "fnb_menu.install.after_migrate"

# Stable internal compatibility routes. These must remain available even when a
# hotel changes its public-facing QR/menu route in RhoGuest settings.
website_route_rules = [
    {"from_route": "/fnb-menu", "to_route": "fnb_menu"},
    {"from_route": "/fnb-kitchen", "to_route": "fnb_kitchen"},
]

doc_events = {
    "Payment Request": {
        "on_update_after_submit": "fnb_menu.payment_events.payment_request_updated"
    }
}

scheduler_events = {
    "cron": {
        "*/5 * * * *": ["fnb_menu.payment_events.sync_paid_orders"]
    }
}

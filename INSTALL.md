# RhoGuest Installation & Upgrade Quick Guide

RhoGuest is the product identity of the Frappe app whose technical package remains `fnb_menu`.

For the complete implementation guide, see **docs/RHOGUEST_SETUP_MANUAL.md**.

## Fresh installation from GitHub

```bash
cd ~/frappe-bench
bench get-app --branch main https://github.com/bobolabless/fnb_menu.git
bench --site <site> install-app fnb_menu
bench --site <site> migrate
bench build --app fnb_menu
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

## Minimum configuration

1. Open **RhoGuest** from the Frappe Desk sidebar.
2. Open **FNB Menu Settings** and select the hotel Company and Selling Price List.
3. Configure branding and public menu routing.
4. Configure and publish Food/Drinks Menu Books as required.
5. Review **RhoGuest Service Category** records. Seeded ancillary services are disabled/unpublished by design.
6. Enable the Guest Services Hub only after published services are reviewed.
7. Configure Laundry Service Items before publishing Laundry.
8. Configure payment/customer settings before enabling F&B self ordering.

## Important routes

- Desk Workspace: `/app/rhoguest` (Workspace navigation)
- Dashboard: `/app/rhoguest-dashboard`
- Guest Services Hub: `/rhoguest`
- Stable F&B menu: `/fnb-menu`
- Configurable public F&B route: set in FNB Menu Settings
- Kitchen board: `/fnb-kitchen`
- Laundry request: `/rhoguest-laundry`

## Update

```bash
cd ~/frappe-bench/apps/fnb_menu
git pull --ff-only origin main

cd ~/frappe-bench
bench --site <site> backup --with-files
bench --site <site> migrate
bench build --app fnb_menu
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

After an upgrade, verify the RhoGuest Workspace, Dashboard, public Hub, public F&B route, Kitchen board and any published ancillary-service page.

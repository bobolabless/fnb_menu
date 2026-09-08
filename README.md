# RhoHMS F&B Menu

**FNB Menu** (`fnb_menu`) is the Food & Beverage digital-menu and self-ordering add-on for **RhoHMS — Rho Hospitality Management Suite**, developed by Rhocom Technology Limited.

It provides hotel Food and Drinks menu books, themed responsive public menus, category navigation, ERPNext item/price integration, guest carts, prepaid self-ordering, Payment Request integration and a kitchen workflow.

## Standard identity

- Frappe app / GitHub repository: `fnb_menu`
- App title: `RhoHMS F&B Menu`
- Frappe module: `FNB Menu`
- Settings DocType: `FNB Menu Settings`
- Public menu: `/fnb-menu`
- Kitchen board: `/fnb-kitchen`
- Publisher: Rhocom Technology Limited
- ERPNext/Frappe: v15.x

## Install from GitHub

```bash
cd ~/frappe-bench
bench get-app --branch main https://github.com/bobolabless/fnb_menu.git
bench --site <your-site> install-app fnb_menu
bench --site <your-site> migrate
bench build --app fnb_menu
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
bench restart
```

Open **FNB Menu Settings**, select the hotel Company, Selling Price List, default Guest Customer and Payment Gateway Account, configure Food/Drinks menu books, and publish `/fnb-menu`.

## Update a live installation

```bash
cd ~/frappe-bench/apps/fnb_menu
git pull --ff-only origin main
cd ~/frappe-bench
bench --site <your-site> migrate
bench build --app fnb_menu
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
bench restart
```

## Migration from the existing Restaurant Luxury app

The current `restaurant_luxury` installation can remain installed while FNB Menu is tested. After installing this app, run:

```bash
bench --site <your-site> execute fnb_menu.migration.migrate_from_restaurant_luxury
```

The migration copies legacy menu configuration and records without deleting the old data. Test `/fnb-menu`, `/fnb-kitchen`, ordering, payment and kitchen release before retiring the legacy app.

## Security / ordering rule

Browser-supplied prices are never authoritative. Checkout resolves allowed items and prices again on the server. Public self-orders require verified payment before kitchen release.

See `INSTALL.md` and `MIGRATION_FROM_RESTAURANT_LUXURY.md`.

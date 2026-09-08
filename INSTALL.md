# Installing FNB Menu

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

## Configure

1. Open **FNB Menu Settings**.
2. Select the hotel Company.
3. Select the Selling Price List.
4. Configure the default guest Customer and Payment Gateway Account before enabling guest self-ordering.
5. Create/publish Food and Drinks **FNB Menu Book** records.
6. Open `/fnb-menu`.
7. Kitchen staff use `/fnb-kitchen`.

## Update

```bash
cd ~/frappe-bench/apps/fnb_menu
git pull --ff-only origin main
cd ~/frappe-bench
bench --site <site> migrate
bench build --app fnb_menu
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

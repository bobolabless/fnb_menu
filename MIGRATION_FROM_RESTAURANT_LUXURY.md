# Migration from `restaurant_luxury` to `fnb_menu`

FNB Menu uses new DocType names and the public routes `/fnb-menu` and `/fnb-kitchen`, so it can be installed beside the current `restaurant_luxury` app during controlled migration. The migration is non-destructive.

## 1. Install FNB Menu

```bash
cd ~/frappe-bench
bench get-app --branch main https://github.com/<YOUR-GITHUB-ORG>/fnb_menu.git
bench --site <site> install-app fnb_menu
bench --site <site> migrate
bench build --app fnb_menu
```

## 2. Copy legacy menu data

```bash
bench --site <site> execute fnb_menu.migration.migrate_from_restaurant_luxury
```

## 3. Validate before retiring the old app

- `/fnb-menu`
- `/fnb-kitchen`
- Food/Drinks switching
- category navigation and mobile layout
- item pricing and availability
- Add to Cart / delete / Clear Cart
- Room Service, Dine In and Takeaway checkout
- Payment Request / payment gateway
- payment verification before kitchen release

Only after validation should the legacy app be retired.

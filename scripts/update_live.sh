#!/usr/bin/env bash
set -euo pipefail
BENCH="${1:-$HOME/frappe-bench}"
SITE="${2:-}"
if [[ -z "$SITE" ]]; then
  echo "Usage: $0 <bench_path> <site>"
  exit 1
fi
cd "$BENCH/apps/fnb_menu"
git pull --ff-only origin main
cd "$BENCH"
bench --site "$SITE" migrate
bench build --app fnb_menu
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache || true
bench restart || true

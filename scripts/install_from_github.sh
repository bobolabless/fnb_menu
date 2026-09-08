#!/usr/bin/env bash
set -euo pipefail
BENCH="${1:-$HOME/frappe-bench}"
SITE="${2:-}"
REPO="${3:-}"
BRANCH="${4:-main}"
if [[ -z "$SITE" || -z "$REPO" ]]; then
  echo "Usage: $0 <bench_path> <site> <git_repo_url> [branch]"
  exit 1
fi
cd "$BENCH"
if [[ ! -d apps/fnb_menu ]]; then
  bench get-app --branch "$BRANCH" "$REPO"
fi
if ! bench --site "$SITE" list-apps | awk '{print $1}' | grep -qx fnb_menu; then
  bench --site "$SITE" install-app fnb_menu
fi
bench --site "$SITE" migrate
bench build --app fnb_menu
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache || true
bench restart || true
echo "FNB Menu installed. Public menu: /fnb-menu | Kitchen: /fnb-kitchen"

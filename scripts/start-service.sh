#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

export AWEILLE_DATA_DIR="${AWEILLE_DATA_DIR:-$HOME/.local/share/aweille}"
export AWEILLE_PORT="${AWEILLE_PORT:-8080}"
export AWEILLE_UID="$(id -u)"
export AWEILLE_GID="$(id -g)"

if [ ! -f "$AWEILLE_DATA_DIR/aweille.sqlite3" ]; then
    echo "Database missing: $AWEILLE_DATA_DIR/aweille.sqlite3" >&2
    echo "Prepare it with aweille-init-db before starting the service." >&2
    exit 1
fi

docker compose up --build --detach --wait --wait-timeout 60
echo "Aweille is running at http://localhost:$AWEILLE_PORT"

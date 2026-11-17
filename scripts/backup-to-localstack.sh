#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="logiflow-wms-backups"
BACKUP_DIR="$HOME/Documents/Codex/logiflow-backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/logiflow-${TIMESTAMP}.db"

POD_NAME="$(kubectl get pods -n default -l app=logiflow-wms \
  -o jsonpath='{.items[0].metadata.name}')"

if [[ -z "$POD_NAME" ]]; then
  echo "No LogiFlow WMS pod found in the default namespace."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "Using pod: $POD_NAME"
echo "Backup file: $BACKUP_FILE"

POD_BACKUP_FILE="/tmp/logiflow-backup-${TIMESTAMP}.db"

kubectl exec -n default "$POD_NAME" -- python -c '
import sqlite3
import sys

source = sqlite3.connect("/data/logiflow.db")
destination = sqlite3.connect(sys.argv[1])
try:
    source.backup(destination)
finally:
    destination.close()
    source.close()
' "$POD_BACKUP_FILE"

kubectl cp -n default \
  "${POD_NAME}:${POD_BACKUP_FILE}" \
  "$BACKUP_FILE"

kubectl exec -n default "$POD_NAME" -- rm "$POD_BACKUP_FILE"

echo "Database backup copied to Mac."

python3 -c '
import sqlite3
import sys

database = sqlite3.connect(sys.argv[1])
result = database.execute("PRAGMA integrity_check").fetchone()[0]
database.close()

if result != "ok":
    raise SystemExit(f"SQLite integrity check failed: {result}")

print(f"SQLite integrity check: {result}")
' "$BACKUP_FILE"

OBJECT_KEY="$(basename "$BACKUP_FILE")"

DOCKER_HOST="$(docker context inspect desktop-linux --format '{{.Endpoints.docker.Host}}')" \
  lstk aws s3 cp "$BACKUP_FILE" "s3://${BUCKET_NAME}/${OBJECT_KEY}"

echo "Backup uploaded to s3://${BUCKET_NAME}/${OBJECT_KEY}"
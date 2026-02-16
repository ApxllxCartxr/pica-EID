#!/bin/bash
# PRISMID Daily Backup Script
# Backs up PostgreSQL database to a timestamped file.
# Add to crontab: 0 2 * * * /path/to/backup.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
DB_NAME="${POSTGRES_DB:-prismid_db}"
DB_USER="${POSTGRES_USER:-prismid}"
DB_HOST="${DB_HOST:-postgres}"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/prismid_backup_$TIMESTAMP.sql.gz"

echo "[$(date)] Starting backup..."
pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "[$(date)] Backup saved to $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Cleanup old backups
echo "[$(date)] Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "prismid_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Backup completed successfully."

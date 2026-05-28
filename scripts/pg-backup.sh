#!/usr/bin/env bash
# scripts/pg-backup.sh - Backup do banco PostgreSQL do Keycloak via kubectl exec
# Uso: ./scripts/pg-backup.sh [diretório-destino]
# Saída: <destino>/keycloak-db-backup-YYYYMMDD-HHMMSS.dump

set -euo pipefail

NAMESPACE="keycloak-auth"
DEPLOY="postgresql-deployment"
DB_NAME="keycloak"
SECRET_NAME="keycloak-db-secret"
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/keycloak-db-backup-${TIMESTAMP}.dump"
BACKUP_FILE_TMP="${BACKUP_FILE}.tmp"

cleanup_partial_backup() {
  rm -f "$BACKUP_FILE_TMP"
}

trap cleanup_partial_backup INT TERM ERR

mkdir -p "$BACKUP_DIR"

POSTGRES_USER=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)
POSTGRES_PASSWORD=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.data.database-password}' | base64 -d)

echo "[INFO] Gerando backup do banco '${DB_NAME}' → ${BACKUP_FILE} ..."

kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY" -- \
  env "PGPASSWORD=$POSTGRES_PASSWORD" \
  pg_dump -U "$POSTGRES_USER" -d "$DB_NAME" --format=custom > "$BACKUP_FILE_TMP"

mv "$BACKUP_FILE_TMP" "$BACKUP_FILE"
trap - INT TERM ERR

echo "[OK] Backup concluído: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"

# Autoria/Implementação: claude-sonnet-4-6
# Revisão: GPT-5 Codex

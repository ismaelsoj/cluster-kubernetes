#!/usr/bin/env bash
# scripts/pg-backup.sh - Backup do banco PostgreSQL do Keycloak via kubectl exec
# Uso: ./scripts/pg-backup.sh [diretório-destino]
# Saída: <destino>/keycloak-db-backup-YYYYMMDD-HHMMSS.dump

set -euo pipefail

NAMESPACE="keycloak-auth"
DEPLOY="postgresql-deployment"
DB_NAME="keycloak"
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/keycloak-db-backup-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

POSTGRES_USER=$(kubectl get secret keycloak-db-secret -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)

echo "[INFO] Gerando backup do banco '${DB_NAME}' → ${BACKUP_FILE} ..."

kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY" -- \
  pg_dump -U "$POSTGRES_USER" -d "$DB_NAME" --format=custom > "$BACKUP_FILE"

echo "[OK] Backup concluído: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"

# Autoria/Implementação: claude-sonnet-4-6

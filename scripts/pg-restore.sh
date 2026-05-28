#!/usr/bin/env bash
# scripts/pg-restore.sh - Restore do banco PostgreSQL do Keycloak a partir de dump externo
# Uso: ./scripts/pg-restore.sh <caminho-do-backup.dump>
# AVISO: Escala Keycloak para 0 durante o restore. Keycloak ficará indisponível brevemente.

set -euo pipefail

BACKUP_FILE="${1:?Uso: $0 <caminho-do-backup.dump>}"
NAMESPACE="keycloak-auth"
DEPLOY_PG="postgresql-deployment"
DEPLOY_KC="keycloak-deployment"
DB_NAME="keycloak"
REMOTE_PATH="/tmp/keycloak-restore.dump"

[[ -f "$BACKUP_FILE" ]] || { echo "[ERRO] Arquivo não encontrado: $BACKUP_FILE" >&2; exit 1; }

POSTGRES_USER=$(kubectl get secret keycloak-db-secret -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)

echo "[INFO] Escalando Keycloak para 0 réplicas..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas=0
kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=60s 2>/dev/null || true

POSTGRES_POD=$(kubectl get pod -n "$NAMESPACE" \
  -l app.kubernetes.io/name=postgresql,app.kubernetes.io/component=database \
  -o jsonpath='{.items[0].metadata.name}')

echo "[INFO] Copiando backup para o pod (${POSTGRES_POD}:/tmp/)..."
kubectl cp "$BACKUP_FILE" "${NAMESPACE}/${POSTGRES_POD}:${REMOTE_PATH}"

echo "[INFO] Executando pg_restore no banco '${DB_NAME}'..."
kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY_PG" -- \
  pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$DB_NAME" "$REMOTE_PATH"

echo "[INFO] Removendo arquivo temporário do pod..."
kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY_PG" -- rm -f "$REMOTE_PATH"

echo "[INFO] Escalando Keycloak de volta para 1 réplica..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas=1
kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=180s

echo "[SUCESSO] Restore concluído. Valide com: kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth | grep -i 'import\|cluster-local'"

# Autoria/Implementação: claude-sonnet-4-6

#!/usr/bin/env bash
# scripts/pg-restore.sh - Restore do banco PostgreSQL do Keycloak a partir de dump externo
# Uso: ./scripts/pg-restore.sh <caminho-do-backup.dump>
# AVISO: Escala Keycloak para 0 durante o restore. Keycloak ficará indisponível brevemente.

set -euo pipefail

BACKUP_FILE="${1:?Uso: $0 <caminho-do-backup.dump>}"
NAMESPACE="keycloak-auth"
DEPLOY_KC="keycloak-deployment"
DB_NAME="keycloak"
SECRET_NAME="keycloak-db-secret"
ARGOCD_NAMESPACE="argocd"
ARGOCD_APPS_TO_CHECK=(root-app infra-app)
KEYCLOAK_READY_LABEL="app.kubernetes.io/name=keycloak"
POSTGRES_POD_LABEL="app.kubernetes.io/name=postgresql,app.kubernetes.io/component=database"
ORIGINAL_KEYCLOAK_REPLICAS="1"
POSTGRES_POD=""
REMOTE_PATH="/tmp/$(basename "$BACKUP_FILE")"
REMOTE_FILE_COPIED="false"
KEYCLOAK_SCALED_DOWN="false"

cleanup_restore() {
  if [[ "$REMOTE_FILE_COPIED" == "true" && -n "$POSTGRES_POD" ]]; then
    kubectl exec -n "$NAMESPACE" "pod/$POSTGRES_POD" -- rm -f "$REMOTE_PATH" >/dev/null 2>&1 || true
  fi

  if [[ "$KEYCLOAK_SCALED_DOWN" == "true" ]]; then
    local current_replicas
    current_replicas="$(kubectl get deploy "$DEPLOY_KC" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || true)"
    if [[ "$current_replicas" != "$ORIGINAL_KEYCLOAK_REPLICAS" ]]; then
      echo "[WARN] Restaurando Keycloak para ${ORIGINAL_KEYCLOAK_REPLICAS} réplica(s) após saída do script..."
      kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas="$ORIGINAL_KEYCLOAK_REPLICAS" >/dev/null 2>&1 || true
      kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=180s >/dev/null 2>&1 || true
    fi
  fi

  return 0
}

finish_restore() {
  local exit_code="$1"
  trap - EXIT
  cleanup_restore
  exit "$exit_code"
}

wait_for_keycloak_scale_down() {
  local attempt
  for attempt in {1..90}; do
    if [[ -z "$(kubectl get pods -n "$NAMESPACE" -l "$KEYCLOAK_READY_LABEL" -o name 2>/dev/null)" ]]; then
      return 0
    fi
    sleep 2
  done

  echo "[ERRO] Keycloak não chegou a 0 pods dentro do timeout esperado." >&2
  return 1
}

assert_argocd_self_heal_disabled() {
  local app_name
  local self_heal

  for app_name in "${ARGOCD_APPS_TO_CHECK[@]}"; do
    if ! kubectl get application "$app_name" -n "$ARGOCD_NAMESPACE" >/dev/null 2>&1; then
      continue
    fi

    self_heal="$(kubectl get application "$app_name" -n "$ARGOCD_NAMESPACE" \
      -o jsonpath='{.spec.syncPolicy.automated.selfHeal}' 2>/dev/null || true)"

    if [[ "$self_heal" == "true" ]]; then
      echo "[ERRO] O restore exige janela de manutenção com auto-heal desativado no ArgoCD." >&2
      echo "[ERRO] Desative temporariamente o auto-heal de '$app_name' e tente novamente." >&2
      return 1
    fi
  done
}

trap 'finish_restore $?' EXIT

[[ -f "$BACKUP_FILE" ]] || { echo "[ERRO] Arquivo não encontrado: $BACKUP_FILE" >&2; exit 1; }
assert_argocd_self_heal_disabled

POSTGRES_USER=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)
POSTGRES_PASSWORD=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.data.database-password}' | base64 -d)
ORIGINAL_KEYCLOAK_REPLICAS="$(kubectl get deploy "$DEPLOY_KC" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')"

POSTGRES_POD=$(kubectl get pod -n "$NAMESPACE" \
  -l "$POSTGRES_POD_LABEL" \
  -o jsonpath='{.items[0].metadata.name}')
[[ -n "$POSTGRES_POD" ]] || { echo "[ERRO] Nenhum pod PostgreSQL encontrado para o restore." >&2; exit 1; }

kubectl wait --for=condition=Ready -n "$NAMESPACE" "pod/$POSTGRES_POD" --timeout=180s >/dev/null

echo "[INFO] Copiando backup para o pod (${POSTGRES_POD}:/tmp/)..."
kubectl cp "$BACKUP_FILE" "${NAMESPACE}/${POSTGRES_POD}:${REMOTE_PATH}"
REMOTE_FILE_COPIED="true"

echo "[INFO] Validando integridade do backup antes do restore..."
kubectl exec -n "$NAMESPACE" "pod/$POSTGRES_POD" -- \
  pg_restore --list "$REMOTE_PATH" >/dev/null

echo "[INFO] Escalando Keycloak para 0 réplicas..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas=0
KEYCLOAK_SCALED_DOWN="true"
wait_for_keycloak_scale_down

echo "[INFO] Executando pg_restore no banco '${DB_NAME}'..."
kubectl exec -n "$NAMESPACE" "pod/$POSTGRES_POD" -- \
  env "PGPASSWORD=$POSTGRES_PASSWORD" \
  pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$DB_NAME" "$REMOTE_PATH"

echo "[INFO] Removendo arquivo temporário do pod..."
kubectl exec -n "$NAMESPACE" "pod/$POSTGRES_POD" -- rm -f "$REMOTE_PATH"
REMOTE_FILE_COPIED="false"

echo "[INFO] Escalando Keycloak de volta para ${ORIGINAL_KEYCLOAK_REPLICAS} réplica(s)..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas="$ORIGINAL_KEYCLOAK_REPLICAS"
kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=180s
KEYCLOAK_SCALED_DOWN="false"

echo "[SUCESSO] Restore concluído. Valide com: kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth | grep -i 'import\|cluster-local'"

# Autoria/Implementação: claude-sonnet-4-6
# Revisão: GPT-5 Codex

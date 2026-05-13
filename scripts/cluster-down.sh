#!/usr/bin/env bash
# scripts/cluster-down.sh - Destrói o cluster k3d sem resíduos
# Idempotente: sai com sucesso se o cluster não existir

set -euo pipefail

CLUSTER_NAME="cluster-kubernetes"

# ─── Verificar presença de k3d ────────────────────────────────────────────────
if ! command -v k3d >/dev/null 2>&1; then
  echo "ERRO: 'k3d' não encontrado no PATH."
  exit 1
fi

# ─── Idempotência: cluster não existe ─────────────────────────────────────────
if ! k3d cluster list 2>/dev/null | grep -q "^${CLUSTER_NAME}"; then
  echo "Cluster '${CLUSTER_NAME}' não existe. Nenhuma ação necessária."
  exit 0
fi

# ─── Deletar cluster ──────────────────────────────────────────────────────────
echo "Destruindo cluster '${CLUSTER_NAME}'..."
k3d cluster delete "${CLUSTER_NAME}"

# ─── Confirmar remoção ────────────────────────────────────────────────────────
if k3d cluster list 2>/dev/null | grep -q "^${CLUSTER_NAME}"; then
  echo "ERRO: Cluster ainda listado após deleção. Verifique manualmente com 'k3d cluster list'."
  exit 1
fi

echo "Cluster destruído com sucesso. Sem resíduos."

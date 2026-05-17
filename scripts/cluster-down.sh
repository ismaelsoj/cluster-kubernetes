#!/usr/bin/env bash
# scripts/cluster-down.sh - Destrói o cluster k3d sem resíduos
# Idempotente: sai com sucesso se o cluster não existir

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-cluster-kubernetes}"

# ─── Verificar presença de k3d ────────────────────────────────────────────────
if ! command -v k3d >/dev/null 2>&1; then
  echo "ERRO: 'k3d' não encontrado no PATH."
  exit 1
fi

# ─── Verificar Docker em execução ─────────────────────────────────────────────
# Sem Docker ativo, k3d não consegue listar clusters. Avisa e sai com sucesso.
# Nota: O cluster persistirá no Docker e deverá ser removido manualmente quando o daemon iniciar.
if ! docker info >/dev/null 2>&1; then
  echo "AVISO: Docker daemon não está em execução."
  echo "       Não é possível verificar o cluster. Certifique-se de removê-lo manualmente quando o Docker estiver ativo."
  exit 0
fi

# ─── Idempotência: cluster não existe ─────────────────────────────────────────
# Usa k3d cluster get para verificação exata por nome. Se não existe, sai com
# sucesso (operação idempotente).
if ! k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "Cluster '${CLUSTER_NAME}' não existe. Nenhuma ação necessária."
  exit 0
fi

# ─── Deletar cluster ──────────────────────────────────────────────────────────
echo "Destruindo cluster '${CLUSTER_NAME}'..."
k3d cluster delete "${CLUSTER_NAME}"

# ─── Confirmar remoção ────────────────────────────────────────────────────────
if k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "ERRO: Cluster ainda listado após deleção. Verifique manualmente com 'k3d cluster list'."
  exit 1
fi

echo "Cluster destruído com sucesso. Sem resíduos."

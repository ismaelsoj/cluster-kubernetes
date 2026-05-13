#!/usr/bin/env bash
# scripts/cluster-up.sh - Provisiona o cluster k3d conforme k3d.yaml
# Executa pre-flight checks, cria o cluster e verifica acessibilidade via kubectl

set -euo pipefail

CLUSTER_NAME="cluster-kubernetes"
K3D_CONFIG="$(git rev-parse --show-toplevel)/k3d.yaml"
TIMEOUT="${K3D_TIMEOUT:-300}"

# ─── Pre-flight: binários obrigatórios ──────────────────────────────────────
for bin in docker kubectl k3d; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERRO: '$bin' não encontrado no PATH. Instale e tente novamente."
    exit 1
  fi
done

# ─── Pre-flight: Docker em execução ─────────────────────────────────────────
if ! docker info >/dev/null 2>&1; then
  echo "ERRO: Docker daemon não está em execução. Inicie o Docker Desktop e tente novamente."
  exit 1
fi

# ─── Pre-flight: recursos Docker (aviso — não bloqueia) ─────────────────────
DOCKER_CPUS=$(docker info --format '{{.NCPU}}' 2>/dev/null || echo 0)
DOCKER_MEM_BYTES=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
DOCKER_MEM_GB=$(( DOCKER_MEM_BYTES / 1073741824 ))
if [ "$DOCKER_CPUS" -lt 4 ] || [ "$DOCKER_MEM_GB" -lt 6 ]; then
  echo "AVISO: Docker com ${DOCKER_CPUS} CPUs e ${DOCKER_MEM_GB}GB RAM."
  echo "       Recomendado: ≥4 CPUs e ≥6GB RAM (Docker Desktop → Settings → Resources)."
fi

# ─── Pre-flight: conflito de portas ──────────────────────────────────────────
for port in 8080 8443; do
  if (echo >/dev/tcp/localhost/$port) 2>/dev/null; then
    echo "ERRO: Porta ${port} já está em uso no host."
    echo "      Libere a porta antes de provisionar o cluster."
    exit 1
  fi
done

# ─── Idempotência: cluster já existe ─────────────────────────────────────────
if k3d cluster list 2>/dev/null | grep -q "^${CLUSTER_NAME}"; then
  echo "Cluster '${CLUSTER_NAME}' já existe. Verificando saúde..."
  if kubectl get nodes >/dev/null 2>&1; then
    echo "Cluster operacional. Nenhuma ação necessária."
    kubectl get nodes
    exit 0
  else
    echo "ERRO: Cluster existe mas kubectl não consegue conectar."
    echo "      Execute 'make down' e tente novamente."
    exit 1
  fi
fi

# ─── Trap para cleanup em falha ou interrupção ───────────────────────────────
_cleanup() {
  echo ""
  echo "Provisionamento interrompido. Removendo cluster parcial..."
  k3d cluster delete "${CLUSTER_NAME}" 2>/dev/null || true
}
trap _cleanup INT TERM ERR

# ─── Criar cluster ────────────────────────────────────────────────────────────
echo "Criando cluster k3d '${CLUSTER_NAME}' (timeout: ${TIMEOUT}s)..."
k3d cluster create --config "${K3D_CONFIG}" --timeout "${TIMEOUT}s"

# ─── Desabilitar trap após criação bem-sucedida ───────────────────────────────
trap - INT TERM ERR

# ─── Aguardar nós ficarem prontos ─────────────────────────────────────────────
echo "Aguardando nós ficarem prontos..."
kubectl wait --for=condition=Ready nodes --all --timeout=120s

# ─── Validação final ──────────────────────────────────────────────────────────
echo ""
echo "Cluster provisionado com sucesso!"
kubectl get nodes
echo ""
echo "Execute 'make status' para ver URLs e token M2M (disponível após Story 3.3)."

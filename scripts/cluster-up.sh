#!/usr/bin/env bash
# scripts/cluster-up.sh - Provisiona o cluster k3d conforme k3d.yaml
# Executa pre-flight checks, cria o cluster e verifica acessibilidade via kubectl

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-cluster-kubernetes}"
K3D_CONFIG="$(git rev-parse --show-toplevel)/k3d.yaml"

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
# Consulta CPUs e memória disponíveis no Docker para avisar se estão abaixo do
# recomendado. Guardas numéricas evitam abort do script caso docker info
# retorne valores inesperados (Docker remoto, versões antigas, etc).
DOCKER_CPUS=$(docker info --format '{{.NCPU}}' 2>/dev/null || echo 0)
[[ "$DOCKER_CPUS" =~ ^[0-9]+$ ]] || DOCKER_CPUS=0
DOCKER_MEM_BYTES=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
[[ "$DOCKER_MEM_BYTES" =~ ^[0-9]+$ ]] || DOCKER_MEM_BYTES=0
DOCKER_MEM_GB=$(( DOCKER_MEM_BYTES / 1073741824 ))
if [ "$DOCKER_CPUS" -lt 4 ] || [ "$DOCKER_MEM_GB" -lt 6 ]; then
  echo "AVISO: Docker com ${DOCKER_CPUS} CPUs e ${DOCKER_MEM_GB}GB RAM."
  echo "       Recomendado: ≥4 CPUs e ≥6GB RAM (Docker Desktop → Settings → Resources)."
fi

# ─── Pre-flight: conflito de portas ──────────────────────────────────────────
# Verifica se as portas que o k3d precisa expor (HTTP/HTTPS) já estão em uso.
# Usa ss (Linux) como método primário e /dev/tcp (bash built-in, macOS) como fallback.
for port in 8080 8443; do
  if ss -tlnp 2>/dev/null | grep -q ":${port} " || \
     (echo >/dev/tcp/localhost/$port) 2>/dev/null; then
    echo "ERRO: Porta ${port} já está em uso no host."
    echo "      Libere a porta antes de provisionar o cluster."
    exit 1
  fi
done

# ─── Idempotência: cluster já existe ─────────────────────────────────────────
# Verifica se o cluster já existe usando k3d cluster get (match exato por nome).
# Se existe e está saudável, sai com sucesso. Se existe mas kubectl falha,
# orienta o dev a destruir e recriar.
if k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
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
echo "Criando cluster k3d '${CLUSTER_NAME}'..."
k3d cluster create --config "${K3D_CONFIG}"

# ─── Desabilitar trap após criação bem-sucedida ───────────────────────────────
trap - INT TERM ERR

# ─── Aguardar nós ficarem prontos ─────────────────────────────────────────────
echo "Aguardando nós ficarem prontos..."
if ! kubectl wait --for=condition=Ready nodes --all --timeout=120s; then
  echo ""
  echo "AVISO: Nós não ficaram prontos dentro do timeout (120s)."
  echo "       O cluster foi criado mas pode não estar operacional."
  echo "       Execute 'kubectl get nodes' para verificar ou 'make down' para destruir."
  exit 1
fi

# ─── Validação final ──────────────────────────────────────────────────────────
echo ""
echo "Cluster provisionado com sucesso!"
kubectl get nodes
echo ""
echo "Execute 'make status' para ver URLs e token M2M (disponível após Story 3.3)."

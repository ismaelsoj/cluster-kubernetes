#!/usr/bin/env bash
# scripts/cluster-up.sh - Provisiona o cluster k3d conforme k3d.yaml
# Executa pre-flight checks, cria o cluster e verifica acessibilidade via kubectl

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-cluster-kubernetes}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
K3D_CONFIG="${REPO_ROOT}/k3d.yaml"

# Versão fixa do ArgoCD (Story 1.3) — imutável e auditável via Git
ARGOCD_VERSION="${ARGOCD_VERSION:-v3.4.2}"
ARGOCD_NAMESPACE="argocd"
ARGOCD_MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
ARGOCD_WAIT_TIMEOUT="${ARGOCD_WAIT_TIMEOUT:-180s}"
BOOTSTRAP_DIR="${REPO_ROOT}/cluster/bootstrap"
# Ordem importa: root-app primeiro (estabelece governança); infra-app e apps-app
# são tecnicamente gerenciados pelo root-app, mas aplicamos diretamente para que
# já nasçam com a branch local correta (override de targetRevision).
BOOTSTRAP_APPS=(root-app infra-app apps-app)

# Branch que o ArgoCD vai monitorar — usa a branch local detectada por padrão.
# Em CI/produção, sobrescrever com ARGO_TARGET_BRANCH=main.
ARGO_TARGET_BRANCH="${ARGO_TARGET_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

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
for port in 80 443; do
  if ss -tlnp 2>/dev/null | grep -q ":${port} " || \
     (echo >/dev/tcp/localhost/$port) 2>/dev/null; then
    echo "ERRO: Porta ${port} já está em uso no host."
    echo "      Libere a porta antes de provisionar o cluster."
    exit 1
  fi
done

# ─── Funções de bootstrap GitOps (Story 1.3) ─────────────────────────────────
# Instala o ArgoCD de forma idempotente: cria namespace se necessário, aplica
# o manifesto oficial da versão fixa e aguarda argocd-server ficar disponível.
install_argocd() {
  echo ""
  echo "==> [Bootstrap] Instalando ArgoCD ${ARGOCD_VERSION} no namespace '${ARGOCD_NAMESPACE}'..."
  kubectl create namespace "${ARGOCD_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
  # Server-side apply é obrigatório: o CRD applicationsets.argoproj.io excede o
  # limite de 256KB da annotation 'last-applied-configuration' usada pelo apply
  # client-side. --force-conflicts garante idempotência mesmo após reapply.
  kubectl apply -n "${ARGOCD_NAMESPACE}" --server-side=true --force-conflicts \
    -f "${ARGOCD_MANIFEST_URL}"

  echo "==> [Bootstrap] Aguardando 'deployment/argocd-server' ficar disponível (timeout ${ARGOCD_WAIT_TIMEOUT})..."
  if ! kubectl wait --for=condition=Available \
       --namespace "${ARGOCD_NAMESPACE}" \
       --timeout="${ARGOCD_WAIT_TIMEOUT}" \
       deployment/argocd-server; then
    echo "ERRO: ArgoCD não ficou disponível dentro do timeout (${ARGOCD_WAIT_TIMEOUT})."
    echo "      Inspecione com: kubectl get pods -n ${ARGOCD_NAMESPACE}"
    return 1
  fi
  echo "==> [Bootstrap] ArgoCD operacional."
}

# Aplica todos os manifestos App-of-Apps (root-app, infra-app, apps-app) substituindo
# targetRevision em tempo de execução pela branch local. Os arquivos em disco mantêm
# 'targetRevision: main' (canônico para CI/produção, onde a substituição é no-op).
#
# Por que aplicar TODOS os 3 (e não só o root)?
# O root-app é gerenciado por si mesmo (App-of-Apps recursivo). Se aplicássemos apenas
# o root-app via sed, os filhos infra-app/apps-app nasceriam apontando para 'main'
# (vindos do arquivo no Git) e ficariam sincronizando contra a main vazia. O root-app
# com ignoreDifferences impede a reversão do targetRevision após o seed inicial.
apply_bootstrap_apps() {
  echo ""
  echo "==> [Bootstrap] Aplicando App-of-Apps monitorando branch '${ARGO_TARGET_BRANCH}'..."
  for app in "${BOOTSTRAP_APPS[@]}"; do
    local manifest="${BOOTSTRAP_DIR}/${app}.yaml"
    if [ ! -f "${manifest}" ]; then
      echo "ERRO: Manifesto '${app}' não encontrado em '${manifest}'."
      return 1
    fi
    echo "    -> ${app}.yaml"
    sed "s|targetRevision: main|targetRevision: ${ARGO_TARGET_BRANCH}|" \
      "${manifest}" | kubectl apply -f -
  done
  echo "==> [Bootstrap] App-of-Apps aplicado. ArgoCD iniciará a sincronização recursiva."
}

# ─── Idempotência: cluster já existe ─────────────────────────────────────────
# Verifica se o cluster já existe usando k3d cluster get (match exato por nome).
# Se existe e está saudável, garante que o ArgoCD e o root-app também estão
# aplicados (bootstrap idempotente) antes de sair com sucesso.
if k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "Cluster '${CLUSTER_NAME}' já existe. Verificando saúde..."
  if kubectl get nodes >/dev/null 2>&1; then
    echo "Cluster operacional. Reconciliando bootstrap GitOps (idempotente)..."
    kubectl get nodes
    bash "${REPO_ROOT}/scripts/inject-secrets.sh"
    install_argocd
    apply_bootstrap_apps
    echo ""
    echo "Bootstrap reconciliado. Branch monitorada pelo ArgoCD: '${ARGO_TARGET_BRANCH}'."
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

# ─── Bootstrap GitOps (Story 1.3/1.5) ─────────────────────────────────────────
# A sequência de recuperação/bootstrap segue:
# criar namespaces + injetar Secrets (1.5) -> instalar ArgoCD (1.3) -> aplicar root-app (1.3)
bash "${REPO_ROOT}/scripts/inject-secrets.sh"
install_argocd
apply_bootstrap_apps

echo ""
echo "Bootstrap GitOps concluído."
echo "Branch monitorada pelo ArgoCD: '${ARGO_TARGET_BRANCH}'."
echo "Execute 'make status' para ver URLs e token M2M (disponível após Story 3.3)."

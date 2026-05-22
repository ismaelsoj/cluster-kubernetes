#!/usr/bin/env bash
# scripts/inject-secrets.sh - Injeta Secrets obrigatórios de infraestrutura no cluster
# Garante que os namespaces existam e injeta os segredos necessários para Keycloak e PostgreSQL.
# Suporta leitura do arquivo .env, prompt interativo ou geração automática segura.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENV_FILE="${REPO_ROOT}/.env"

# Parse flags
SKIP_IF_EXISTS=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-if-exists) SKIP_IF_EXISTS=true; shift ;;
    *) shift ;;
  esac
done

# Variáveis padrão (conforme regras de nomenclatura kebab-case)
NAMESPACE_KEYCLOAK="keycloak-auth"
NAMESPACE_GATEWAY="kong-gateway"
DB_USER="keycloak"
ADMIN_USER="${ADMIN_USER:-admin}"

# Pre-flight validation (P5)
if ! command -v kubectl &>/dev/null; then
  echo "❌ ERRO: kubectl não encontrado. Instale kubectl e tente novamente."
  exit 1
fi

if ! kubectl get nodes &>/dev/null 2>&1; then
  echo "❌ ERRO: Cluster não acessível via kubectl. Inicie o cluster e tente novamente."
  exit 1
fi

# Carrega arquivo .env local se existir
if [ -f "${ENV_FILE}" ]; then
  # Evita erro se o arquivo .env estiver vazio ou sem export
  set -a
  source "${ENV_FILE}"
  set +a
fi

# Detecta se está rodando em terminal interativo
IS_INTERACTIVE=false
if [ -t 0 ] && [ -t 1 ]; then
  IS_INTERACTIVE=true
fi

# Check --skip-if-exists (P11 logic)
if [ "${SKIP_IF_EXISTS}" = true ]; then
  if kubectl get secret keycloak-db-secret -n "${NAMESPACE_KEYCLOAK}" &>/dev/null 2>&1; then
    echo "✓ Secrets já existem. Skipping injection."
    exit 0
  fi
fi

# 1. Obter ou gerar senha do PostgreSQL
if [ -z "${DB_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    { set +x; } 2>/dev/null || true  # Desabilita xtrace (P6)
    read -rsp "Digite a senha para o PostgreSQL (Pressione [Enter] para gerar uma automática): " DB_PASSWORD
    echo
    set -x 2>/dev/null || true  # Re-abilita xtrace
  fi
  if [ -z "${DB_PASSWORD:-}" ]; then
    DB_PASSWORD=$(openssl rand -base64 16 2>/dev/null || od -vAn -N16 /dev/urandom | base64 2>/dev/null | tr -d '\n' | head -c 24)
    echo "🔑 Senha do PostgreSQL gerada automaticamente."
  fi
fi

# 2. Obter ou gerar senha do Admin Keycloak
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    { set +x; } 2>/dev/null || true  # Desabilita xtrace (P6)
    read -rsp "Digite a senha do administrador Keycloak (Pressione [Enter] para gerar uma automática): " ADMIN_PASSWORD
    echo
    set -x 2>/dev/null || true  # Re-abilita xtrace
  fi
  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD=$(openssl rand -base64 16 2>/dev/null || od -vAn -N16 /dev/urandom | base64 2>/dev/null | tr -d '\n' | head -c 24)
    echo "🔑 Senha do Admin Keycloak gerada automaticamente."
  fi
fi

# Bootstrap: criar namespaces antes da injeção de Secrets (idempotente via apply).
# Em estado contínuo o ArgoCD Wave 0 gerencia esses namespaces. No bootstrap inicial,
# eles precisam existir ANTES do ArgoCD ser instalado — exceção necessária ao GitOps.
echo "==> Garantindo namespaces para injeção de Secrets..."
kubectl create namespace "${NAMESPACE_KEYCLOAK}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${NAMESPACE_GATEWAY}" --dry-run=client -o yaml | kubectl apply -f -

# 3. Criar/Atualizar Secrets via kubectl no namespace keycloak-auth
echo "==> Injetando Secrets no namespace '${NAMESPACE_KEYCLOAK}'..."

# Secret para conexão com PostgreSQL
kubectl create secret generic keycloak-db-secret \
  --namespace="${NAMESPACE_KEYCLOAK}" \
  --from-literal=database-user="${DB_USER}" \
  --from-literal=database-password="${DB_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# Secret para console de administração do Keycloak
kubectl create secret generic keycloak-admin-secret \
  --namespace="${NAMESPACE_KEYCLOAK}" \
  --from-literal=admin-username="${ADMIN_USER}" \
  --from-literal=admin-password="${ADMIN_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Persistir variáveis no arquivo .env local (P2, P4, P7, P8)
# Validar .gitignore (P8)
if ! grep -q '\.env' "${REPO_ROOT}/.gitignore" 2>/dev/null; then
  echo "⚠️  AVISO: .env não está no .gitignore. Senhas podem ser commitadas!"
  echo "Adicione '.env' ao .gitignore manualmente."
fi

# Lock-file para evitar race conditions (P7)
ENV_FILE_LOCK="${ENV_FILE}.lock"
{
  flock -x 9 || true

  # Criar arquivo .env se não existir (P2: chmod 600)
  if [ ! -f "${ENV_FILE}" ]; then
    echo "# Configurações locais de Secrets - cluster-kubernetes" > "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
  fi

  # Atomic update para DB_PASSWORD (P4)
  if grep -v "^DB_PASSWORD=" "${ENV_FILE}" > "${ENV_FILE}.tmp" 2>/dev/null || echo "" > "${ENV_FILE}.tmp"; then
    echo "DB_PASSWORD=\"${DB_PASSWORD}\"" >> "${ENV_FILE}.tmp"
    mv "${ENV_FILE}.tmp" "${ENV_FILE}"
    echo "💾 Senha do PostgreSQL salva em .env"
  fi

  # Atomic update para ADMIN_PASSWORD (P4)
  if grep -v "^ADMIN_PASSWORD=" "${ENV_FILE}" > "${ENV_FILE}.tmp" 2>/dev/null || echo "" > "${ENV_FILE}.tmp"; then
    echo "ADMIN_PASSWORD=\"${ADMIN_PASSWORD}\"" >> "${ENV_FILE}.tmp"
    mv "${ENV_FILE}.tmp" "${ENV_FILE}"
    echo "💾 Senha do Admin Keycloak salva em .env"
  fi

} 9>"${ENV_FILE_LOCK}"

echo "🎉 Secrets injetados com sucesso sem salvar valores sensíveis no Git."

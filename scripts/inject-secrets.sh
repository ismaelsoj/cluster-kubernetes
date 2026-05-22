#!/usr/bin/env bash
# scripts/inject-secrets.sh - Injeta Secrets obrigatórios de infraestrutura no cluster
# Garante que os namespaces existam e injeta os segredos necessários para Keycloak e PostgreSQL.
# Suporta leitura do arquivo .env, prompt interativo ou geração automática segura.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENV_FILE="${REPO_ROOT}/.env"

# Variáveis padrão (conforme regras de nomenclatura kebab-case)
NAMESPACE_KEYCLOAK="keycloak-auth"
NAMESPACE_GATEWAY="kong-gateway"
DB_USER="keycloak"
ADMIN_USER="admin"

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

# 1. Obter ou gerar senha do PostgreSQL
if [ -z "${DB_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    read -rsp "Digite a senha para o PostgreSQL (Pressione [Enter] para gerar uma automática): " DB_PASSWORD
    echo
  fi
  if [ -z "${DB_PASSWORD:-}" ]; then
    DB_PASSWORD=$(openssl rand -base64 16 2>/dev/null || od -vAn -N16 -tx1 /dev/urandom | tr -d ' \n' | head -c 16)
    echo "🔑 Senha do PostgreSQL gerada automaticamente."
  fi
fi

# 2. Obter ou gerar senha do Admin Keycloak
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    read -rsp "Digite a senha do administrador Keycloak (Pressione [Enter] para gerar uma automática): " ADMIN_PASSWORD
    echo
  fi
  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD=$(openssl rand -base64 16 2>/dev/null || od -vAn -N16 -tx1 /dev/urandom | tr -d ' \n' | head -c 16)
    echo "🔑 Senha do Admin Keycloak gerada automaticamente."
  fi
fi

# 3. Garantir criação dos namespaces base (Wave 0)
echo "==> Garantindo a criação dos namespaces base..."
kubectl create namespace "${NAMESPACE_KEYCLOAK}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${NAMESPACE_GATEWAY}" --dry-run=client -o yaml | kubectl apply -f -

# 4. Criar/Atualizar Secrets via kubectl no namespace keycloak-auth
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

# 5. Persistir variáveis no arquivo .env local se não existirem
if [ ! -f "${ENV_FILE}" ]; then
  echo "# Configurações locais de Secrets - cluster-kubernetes" > "${ENV_FILE}"
fi

# Adiciona apenas se não existirem no arquivo
if ! grep -q "^DB_PASSWORD=" "${ENV_FILE}" 2>/dev/null; then
  echo "DB_PASSWORD=\"${DB_PASSWORD}\"" >> "${ENV_FILE}"
  echo "💾 Senha do PostgreSQL salva em .env"
fi

if ! grep -q "^ADMIN_PASSWORD=" "${ENV_FILE}" 2>/dev/null; then
  echo "ADMIN_PASSWORD=\"${ADMIN_PASSWORD}\"" >> "${ENV_FILE}"
  echo "💾 Senha do Admin Keycloak salva em .env"
fi

echo "🎉 Secrets injetados com sucesso sem salvar valores sensíveis no Git."

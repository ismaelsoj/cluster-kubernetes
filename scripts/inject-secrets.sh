#!/usr/bin/env bash
# scripts/inject-secrets.sh - Injeta Secrets obrigatórios de infraestrutura no cluster
# Garante namespaces e injeta segredos do Keycloak, PostgreSQL, Kong TLS e OAuth2-Proxy.
# Suporta leitura do arquivo .env, prompt interativo ou geração automática segura.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENV_FILE="${REPO_ROOT}/.env"
TLS_TMP_DIR=""

cleanup() {
  if [ -n "${TLS_TMP_DIR}" ] && [ -d "${TLS_TMP_DIR}" ]; then
    rm -rf "${TLS_TMP_DIR}"
  fi
}
trap cleanup EXIT

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
KONG_TLS_SECRET_NAME="kong-tls-secret"
OAUTH2_PROXY_SECRET_NAME="oauth2-proxy-secret"
KONG_TLS_COMMON_NAME="${KONG_TLS_COMMON_NAME:-localhost}"
KONG_TLS_ALT_NAMES="${KONG_TLS_ALT_NAMES:-DNS:keycloak.local,DNS:localhost,IP:127.0.0.1}"
M2M_CLIENT_SECRET="${M2M_CLIENT_SECRET:-dev-m2m-local-secret}"

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

secret_exists() {
  local namespace="$1"
  local name="$2"
  kubectl get secret "${name}" -n "${namespace}" &>/dev/null 2>&1
}

all_required_secrets_exist() {
  secret_exists "${NAMESPACE_KEYCLOAK}" "keycloak-db-secret" &&
    secret_exists "${NAMESPACE_KEYCLOAK}" "keycloak-admin-secret" &&
    secret_exists "${NAMESPACE_GATEWAY}" "${KONG_TLS_SECRET_NAME}" &&
    secret_exists "${NAMESPACE_GATEWAY}" "${OAUTH2_PROXY_SECRET_NAME}" &&
    oauth2_proxy_cookie_secret_valid_in_cluster
}

random_b64() {
  local bytes="$1"
  openssl rand -base64 "${bytes}" 2>/dev/null ||
    od -vAn -N"${bytes}" /dev/urandom | base64 2>/dev/null | tr -d '\n'
}

random_hex() {
  local bytes="$1"
  openssl rand -hex "${bytes}" 2>/dev/null ||
    od -vAn -N"${bytes}" -tx1 /dev/urandom | tr -d ' \n'
}

oauth2_proxy_cookie_secret_is_valid() {
  local secret="$1"
  case "${#secret}" in
    16|24|32) return 0 ;;
    *) return 1 ;;
  esac
}

generate_oauth2_proxy_cookie_secret() {
  # OAuth2-Proxy valida o tamanho literal do cookie secret para AES.
  # Hex de 16 bytes produz 32 caracteres ASCII, aceito como segredo de 32 bytes.
  random_hex 16
}

decode_base64() {
  if printf 'dGVzdA==' | base64 --decode >/dev/null 2>&1; then
    base64 --decode
  else
    base64 -D
  fi
}

oauth2_proxy_cookie_secret_valid_in_cluster() {
  local encoded_secret
  local decoded_secret

  encoded_secret="$(kubectl get secret "${OAUTH2_PROXY_SECRET_NAME}" \
    -n "${NAMESPACE_GATEWAY}" \
    -o jsonpath='{.data.cookie-secret}' 2>/dev/null || true)"

  if [ -z "${encoded_secret}" ]; then
    return 1
  fi

  decoded_secret="$(printf '%s' "${encoded_secret}" | decode_base64 2>/dev/null || true)"
  oauth2_proxy_cookie_secret_is_valid "${decoded_secret}"
}

upsert_env_value() {
  local key="$1"
  local value="$2"
  local tmp_file="${ENV_FILE}.tmp"

  if [ ! -f "${ENV_FILE}" ]; then
    echo "# Configurações locais de Secrets - cluster-kubernetes" > "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
  fi

  grep -v "^${key}=" "${ENV_FILE}" > "${tmp_file}" 2>/dev/null || true
  printf '%s="%s"\n' "${key}" "${value}" >> "${tmp_file}"
  mv "${tmp_file}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
}

persist_env_values() {
  upsert_env_value "DB_PASSWORD" "${DB_PASSWORD}"
  echo "💾 Senha do PostgreSQL salva em .env"

  upsert_env_value "ADMIN_PASSWORD" "${ADMIN_PASSWORD}"
  echo "💾 Senha do Admin Keycloak salva em .env"

  upsert_env_value "OAUTH2_PROXY_CLIENT_SECRET" "${OAUTH2_PROXY_CLIENT_SECRET}"
  echo "💾 Client secret do OAuth2-Proxy salvo em .env"

  upsert_env_value "OAUTH2_PROXY_COOKIE_SECRET" "${OAUTH2_PROXY_COOKIE_SECRET}"
  echo "💾 Cookie secret do OAuth2-Proxy salvo em .env"
}

prepare_tls_material() {
  TLS_TMP_DIR="$(mktemp -d)"
  TLS_CERT_PATH="${TLS_TMP_DIR}/tls.crt"
  TLS_KEY_PATH="${TLS_TMP_DIR}/tls.key"

  if [ -n "${KONG_TLS_CERT_FILE:-}" ] && [ -n "${KONG_TLS_KEY_FILE:-}" ]; then
    if [ ! -r "${KONG_TLS_CERT_FILE}" ] || [ ! -r "${KONG_TLS_KEY_FILE}" ]; then
      echo "❌ ERRO: KONG_TLS_CERT_FILE/KONG_TLS_KEY_FILE foram definidos, mas não são legíveis." >&2
      exit 1
    fi
    TLS_CERT_PATH="${KONG_TLS_CERT_FILE}"
    TLS_KEY_PATH="${KONG_TLS_KEY_FILE}"
    echo "🔐 Certificado TLS do Kong carregado de caminhos definidos no .env."
    return
  fi

  if [ -n "${KONG_TLS_CERT:-}" ] && [ -n "${KONG_TLS_KEY:-}" ]; then
    printf '%b' "${KONG_TLS_CERT}" > "${TLS_CERT_PATH}"
    printf '%b' "${KONG_TLS_KEY}" > "${TLS_KEY_PATH}"
    chmod 600 "${TLS_CERT_PATH}" "${TLS_KEY_PATH}"
    echo "🔐 Certificado TLS do Kong carregado de valores definidos no .env."
    return
  fi

  if ! command -v openssl &>/dev/null; then
    echo "❌ ERRO: openssl é necessário para gerar certificado TLS local automaticamente." >&2
    exit 1
  fi

  openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
    -days 365 \
    -subj "/CN=${KONG_TLS_COMMON_NAME}" \
    -addext "subjectAltName=${KONG_TLS_ALT_NAMES}" \
    -keyout "${TLS_KEY_PATH}" \
    -out "${TLS_CERT_PATH}" >/dev/null 2>&1
  chmod 600 "${TLS_CERT_PATH}" "${TLS_KEY_PATH}"
  echo "🔐 Certificado TLS local self-signed gerado automaticamente para o Kong."
}

# Check --skip-if-exists considerando todos os Secrets obrigatórios atuais.
if [ "${SKIP_IF_EXISTS}" = true ]; then
  if all_required_secrets_exist; then
    echo "✓ Todos os Secrets obrigatórios já existem. Skipping injection."
    exit 0
  fi
  echo "ℹ️  --skip-if-exists: há Secrets faltando; a injeção continuará de forma idempotente."
fi

# 1. Obter ou gerar senha do PostgreSQL
if [ -z "${DB_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    { set +x; } 2>/dev/null || true
    read -rsp "Digite a senha para o PostgreSQL (Pressione [Enter] para gerar uma automática): " DB_PASSWORD
    echo
    set -x 2>/dev/null || true
  fi
  if [ -z "${DB_PASSWORD:-}" ]; then
    DB_PASSWORD="$(random_b64 16)"
    echo "🔑 Senha do PostgreSQL gerada automaticamente."
  fi
fi

# 2. Obter ou gerar senha do Admin Keycloak
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  if [ "${IS_INTERACTIVE}" = true ]; then
    { set +x; } 2>/dev/null || true
    read -rsp "Digite a senha do administrador Keycloak (Pressione [Enter] para gerar uma automática): " ADMIN_PASSWORD
    echo
    set -x 2>/dev/null || true
  fi
  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD="$(random_b64 16)"
    echo "🔑 Senha do Admin Keycloak gerada automaticamente."
  fi
fi

# 3. Obter segredo do OAuth2-Proxy sem versionar valores sensíveis
if [ -z "${OAUTH2_PROXY_CLIENT_SECRET:-}" ]; then
  OAUTH2_PROXY_CLIENT_SECRET="${M2M_CLIENT_SECRET}"
  echo "🔑 Client secret local do OAuth2-Proxy carregado do fixture M2M de desenvolvimento."
fi

if [ -z "${OAUTH2_PROXY_COOKIE_SECRET:-}" ]; then
  OAUTH2_PROXY_COOKIE_SECRET="$(generate_oauth2_proxy_cookie_secret)"
  echo "🔑 Cookie secret do OAuth2-Proxy gerado automaticamente."
elif ! oauth2_proxy_cookie_secret_is_valid "${OAUTH2_PROXY_COOKIE_SECRET}"; then
  OAUTH2_PROXY_COOKIE_SECRET="$(generate_oauth2_proxy_cookie_secret)"
  echo "🔑 Cookie secret do OAuth2-Proxy no .env tinha tamanho inválido e foi regenerado."
fi

# Bootstrap: criar namespaces antes da injeção de Secrets (idempotente via apply).
# Em estado contínuo o ArgoCD Wave 0 gerencia esses namespaces. No bootstrap inicial,
# eles precisam existir ANTES do ArgoCD ser instalado — exceção necessária ao GitOps.
echo "==> Garantindo namespaces para injeção de Secrets..."
kubectl create namespace "${NAMESPACE_KEYCLOAK}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${NAMESPACE_GATEWAY}" --dry-run=client -o yaml | kubectl apply -f -

# 4. Criar/Atualizar Secrets via kubectl no namespace keycloak-auth
echo "==> Injetando Secrets no namespace '${NAMESPACE_KEYCLOAK}'..."

kubectl create secret generic keycloak-db-secret \
  --namespace="${NAMESPACE_KEYCLOAK}" \
  --from-literal=database-user="${DB_USER}" \
  --from-literal=database-password="${DB_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic keycloak-admin-secret \
  --namespace="${NAMESPACE_KEYCLOAK}" \
  --from-literal=admin-username="${ADMIN_USER}" \
  --from-literal=admin-password="${ADMIN_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Criar/Atualizar Secrets de borda no namespace kong-gateway
echo "==> Injetando Secrets no namespace '${NAMESPACE_GATEWAY}'..."
prepare_tls_material

kubectl create secret tls "${KONG_TLS_SECRET_NAME}" \
  --namespace="${NAMESPACE_GATEWAY}" \
  --cert="${TLS_CERT_PATH}" \
  --key="${TLS_KEY_PATH}" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic "${OAUTH2_PROXY_SECRET_NAME}" \
  --namespace="${NAMESPACE_GATEWAY}" \
  --from-literal=client-secret="${OAUTH2_PROXY_CLIENT_SECRET}" \
  --from-literal=cookie-secret="${OAUTH2_PROXY_COOKIE_SECRET}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 6. Persistir variáveis no arquivo .env local (P2, P4, P7, P8)
if ! grep -q '\.env' "${REPO_ROOT}/.gitignore" 2>/dev/null; then
  echo "⚠️  AVISO: .env não está no .gitignore. Senhas podem ser commitadas!"
  echo "Adicione '.env' ao .gitignore manualmente."
fi

ENV_FILE_LOCK="${ENV_FILE}.lock"
if command -v flock &>/dev/null; then
  {
    flock -x 9 || true
    persist_env_values
  } 9>"${ENV_FILE_LOCK}"
else
  persist_env_values
fi

echo "🎉 Secrets injetados com sucesso sem salvar valores sensíveis no Git."

# Autoria/Implementação: GPT-5 Codex

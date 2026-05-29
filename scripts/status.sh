#!/usr/bin/env bash
# scripts/status.sh - Exibe status dos componentes e URLs locais do cluster
# Implementacao completa: Story 3.3
# Autoria/Implementacao: GPT-5 Codex

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./token-helpers.sh
source "${SCRIPT_DIR}/token-helpers.sh"

require_commands kubectl curl python3

deployment_status() {
  local namespace="$1"
  local deployment_name="$2"
  local deployment_json

  if ! deployment_json="$(kubectl get deployment "${deployment_name}" -n "${namespace}" -o json 2>/dev/null)"; then
    printf 'indisponivel'
    return 0
  fi

  DEPLOYMENT_JSON="${deployment_json}" python3 - <<'PY'
import json
import os

data = json.loads(os.environ["DEPLOYMENT_JSON"])
status = data.get("status", {})
ready = status.get("readyReplicas", 0) or 0
replicas = status.get("replicas", 0) or 0
available = any(
    condition.get("type") == "Available" and condition.get("status") == "True"
    for condition in status.get("conditions", [])
)

label = "Ready" if available and replicas > 0 and ready == replicas else "Parcial"
if replicas == 0:
    label = "Sem replicas"

print(f"{label} ({ready}/{replicas})")
PY
}

nodes_status() {
  local nodes_json
  if ! nodes_json="$(kubectl get nodes -o json 2>/dev/null)"; then
    print_error "kubectl nao conseguiu listar os nos do cluster. Verifique se o cluster esta ativo antes de rodar 'make status'."
    return 1
  fi

  NODES_JSON="${nodes_json}" python3 - <<'PY'
import json
import os

data = json.loads(os.environ["NODES_JSON"])
items = data.get("items", [])
ready = 0

for node in items:
    conditions = node.get("status", {}).get("conditions", [])
    if any(cond.get("type") == "Ready" and cond.get("status") == "True" for cond in conditions):
        ready += 1

print(f"{ready}/{len(items)} Ready")
PY
}

cluster_nodes="$(nodes_status)"

printf 'Resumo operacional do cluster\n'
printf 'Cluster/nos: %s\n' "${cluster_nodes}"
printf '\n'
printf 'Componentes principais:\n'
printf -- '- argocd: %s\n' "$(deployment_status argocd argocd-server)"
printf -- '- keycloak-auth: %s\n' "$(deployment_status keycloak-auth keycloak-deployment)"
printf -- '- kong-gateway: %s\n' "$(deployment_status kong-gateway kong-deployment)"
printf -- '- oauth2-proxy: %s\n' "$(deployment_status kong-gateway oauth2-proxy-deployment)"
printf '\n'
printf 'URLs locais:\n'
printf -- '- gateway: %s\n' "${LOCAL_BASE_URL}"
printf -- '- oidc discovery: %s\n' "${DISCOVERY_URL}"
printf -- '- token endpoint: %s\n' "${TOKEN_ENDPOINT}"
printf -- '- rota protegida: %s\n' "${PROTECTED_URL}"
printf '\n'

token_error_file="$(mktemp "${TMPDIR:-/tmp}/cluster-kubernetes-status-token.XXXXXX")"

if token_summary="$(get_token_summary 2>"${token_error_file}")"; then
  ISSUER=""
  PREFERRED_USERNAME=""
  AUDIENCE=""
  EXP_ISO=""

  while IFS='=' read -r key value; do
    case "${key}" in
      ISSUER) ISSUER="${value}" ;;
      PREFERRED_USERNAME) PREFERRED_USERNAME="${value}" ;;
      AUDIENCE) AUDIENCE="${value}" ;;
      EXP_ISO) EXP_ISO="${value}" ;;
    esac
  done <<< "${token_summary}"

  printf 'Token M2M:\n'
  printf -- '- status: pronto para copia com `make token`\n'
  printf -- '- issuer: %s\n' "${ISSUER}"
  printf -- '- preferred_username: %s\n' "${PREFERRED_USERNAME}"
  printf -- '- aud: %s\n' "${AUDIENCE}"
  printf -- '- exp_utc: %s\n' "${EXP_ISO}"
else
  token_error="$(cat "${token_error_file}" 2>/dev/null || true)"
  rm -f "${token_error_file}"
  printf 'Token M2M:\n'
  printf -- '- status: falhou\n'
  if [ -n "${token_error}" ]; then
    printf '%s\n' "${token_error}"
  fi
  exit 1
fi

rm -f "${token_error_file}"

printf '\n'
printf 'Teste frio recomendado:\n'
printf 'curl -k -i %s\n' "${PROTECTED_URL}"
printf 'TOKEN="$(bash scripts/generate-token.sh | awk -F= '\''/^TOKEN=/{print $2; exit}'\'')"\n'
printf -- 'curl -k -i %s -H "Authorization: Bearer ${TOKEN}"\n' "${PROTECTED_URL}"

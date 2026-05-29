#!/usr/bin/env bash
# scripts/token-helpers.sh - Funcoes compartilhadas para token M2M e feedback terminal
# Autoria/Implementacao: GPT-5 Codex

set -euo pipefail

LOCAL_BASE_URL="${LOCAL_BASE_URL:-https://localhost}"
REALM_NAME="${REALM_NAME:-cluster-local}"
TOKEN_ENDPOINT="${TOKEN_ENDPOINT:-${LOCAL_BASE_URL}/realms/${REALM_NAME}/protocol/openid-connect/token}"
DISCOVERY_URL="${DISCOVERY_URL:-${LOCAL_BASE_URL}/realms/${REALM_NAME}/.well-known/openid-configuration}"
PROTECTED_URL="${PROTECTED_URL:-${LOCAL_BASE_URL}/protected/realms/${REALM_NAME}/protocol/openid-connect/userinfo}"
CLIENT_ID="${CLIENT_ID:-m2m-client}"
CLIENT_SECRET="${CLIENT_SECRET:-dev-m2m-local-secret}"
TOKEN_SCOPE="${TOKEN_SCOPE:-openid profile email}"

print_error() {
  printf 'ERRO: %s\n' "$*" >&2
}

print_warning() {
  printf 'AVISO: %s\n' "$*" >&2
}

require_commands() {
  local missing=0
  local bin
  for bin in "$@"; do
    if ! command -v "$bin" >/dev/null 2>&1; then
      print_error "comando obrigatorio nao encontrado no PATH: ${bin}"
      missing=1
    fi
  done

  if [ "$missing" -ne 0 ]; then
    return 1
  fi
}

cluster_connectivity_state() {
  if ! command -v kubectl >/dev/null 2>&1; then
    printf 'kubectl-ausente'
    return 0
  fi

  if kubectl get nodes >/dev/null 2>&1; then
    printf 'ok'
    return 0
  fi

  printf 'indisponivel'
}

print_cluster_connectivity_hint() {
  local state
  state="$(cluster_connectivity_state)"

  case "$state" in
    ok)
      return 0
      ;;
    kubectl-ausente)
      print_warning "kubectl nao encontrado; o script tentara emitir o token apenas pela borda HTTPS local."
      ;;
    indisponivel)
      print_warning "kubectl nao conseguiu falar com o cluster; tentando o endpoint HTTPS mesmo assim."
      ;;
  esac
}

request_token_response() {
  require_commands curl python3

  local response_file
  local http_code
  local curl_status
  local body

  response_file="$(mktemp "${TMPDIR:-/tmp}/cluster-kubernetes-token.XXXXXX")"

  set +e
  http_code="$(
    curl \
      --silent \
      --show-error \
      --fail-with-body \
      --insecure \
      --output "${response_file}" \
      --write-out '%{http_code}' \
      --request POST \
      "${TOKEN_ENDPOINT}" \
      --header 'Content-Type: application/x-www-form-urlencoded' \
      --data 'grant_type=client_credentials' \
      --data "client_id=${CLIENT_ID}" \
      --data "client_secret=${CLIENT_SECRET}" \
      --data-urlencode "scope=${TOKEN_SCOPE}"
  )"
  curl_status=$?
  set -e

  body="$(cat "${response_file}" 2>/dev/null || true)"
  rm -f "${response_file}"

  if [ "${curl_status}" -ne 0 ]; then
    print_error "falha ao solicitar token M2M em ${TOKEN_ENDPOINT} (HTTP ${http_code:-000})."
    if [ -n "${body}" ]; then
      printf 'Detalhes do endpoint: %s\n' "${body}" >&2
    fi
    return 1
  fi

  if [ -z "${body}" ]; then
    print_error "endpoint de token respondeu sem corpo JSON."
    return 1
  fi

  printf '%s' "${body}"
}

decode_token_summary() {
  require_commands python3

  TOKEN_RESPONSE_JSON="$(cat)"

  TOKEN_RESPONSE_JSON="${TOKEN_RESPONSE_JSON}" python3 - <<'PY'
import base64
import json
import os
import sys
from datetime import datetime, timezone

raw = os.environ["TOKEN_RESPONSE_JSON"]
if not raw.strip():
    print("ERRO: resposta JSON vazia.", file=sys.stderr)
    raise SystemExit(1)

try:
    payload = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"ERRO: resposta JSON invalida do endpoint de token: {exc}", file=sys.stderr)
    raise SystemExit(1)

access_token = payload.get("access_token")
if not access_token or not isinstance(access_token, str):
    print("ERRO: campo 'access_token' ausente na resposta do endpoint de token.", file=sys.stderr)
    raise SystemExit(1)

parts = access_token.split(".")
if len(parts) < 2:
    print("ERRO: access_token retornado nao parece um JWT valido.", file=sys.stderr)
    raise SystemExit(1)

segment = parts[1]
segment += "=" * (-len(segment) % 4)

try:
    claims = json.loads(base64.urlsafe_b64decode(segment.encode("utf-8")))
except Exception as exc:  # noqa: BLE001
    print(f"ERRO: nao foi possivel decodificar as claims do JWT: {exc}", file=sys.stderr)
    raise SystemExit(1)

exp = claims.get("exp")
exp_iso = ""
if isinstance(exp, (int, float)):
    exp_iso = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()

aud = claims.get("aud", "")
if isinstance(aud, list):
    aud = ",".join(str(item) for item in aud)

print(f"TOKEN={access_token}")
print(f"ISSUER={claims.get('iss', '')}")
print(f"SCOPE={claims.get('scope', payload.get('scope', ''))}")
print(f"AUDIENCE={aud}")
print(f"PREFERRED_USERNAME={claims.get('preferred_username', '')}")
print(f"SUBJECT={claims.get('sub', '')}")
print(f"EXP={exp if exp is not None else ''}")
print(f"EXP_ISO={exp_iso}")
PY
}

get_token_summary() {
  local token_json
  token_json="$(request_token_response)"
  printf '%s' "${token_json}" | decode_token_summary
}

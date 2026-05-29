#!/usr/bin/env bash
# scripts/generate-token.sh - Gera e exibe o token M2M de teste via Keycloak
# Implementacao completa: Story 3.3
# Autoria/Implementacao: GPT-5 Codex

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./token-helpers.sh
source "${SCRIPT_DIR}/token-helpers.sh"

print_cluster_connectivity_hint

token_summary="$(get_token_summary)"

TOKEN=""
ISSUER=""
SCOPE=""
AUDIENCE=""
PREFERRED_USERNAME=""
SUBJECT=""
EXP_ISO=""

while IFS='=' read -r key value; do
  case "${key}" in
    TOKEN) TOKEN="${value}" ;;
    ISSUER) ISSUER="${value}" ;;
    SCOPE) SCOPE="${value}" ;;
    AUDIENCE) AUDIENCE="${value}" ;;
    PREFERRED_USERNAME) PREFERRED_USERNAME="${value}" ;;
    SUBJECT) SUBJECT="${value}" ;;
    EXP_ISO) EXP_ISO="${value}" ;;
  esac
done <<< "${token_summary}"

printf 'Token M2M emitido com sucesso.\n'
printf 'TOKEN=%s\n' "${TOKEN}"
printf 'issuer=%s\n' "${ISSUER}"
printf 'scope=%s\n' "${SCOPE}"
printf 'aud=%s\n' "${AUDIENCE}"
printf 'preferred_username=%s\n' "${PREFERRED_USERNAME}"
printf 'sub=%s\n' "${SUBJECT}"
printf 'exp_utc=%s\n' "${EXP_ISO}"
printf '\n'
printf 'Teste rapido:\n'
printf 'curl -k -i %s\n' "${PROTECTED_URL}"
printf 'curl -k -i %s -H "Authorization: Bearer %s"\n' "${PROTECTED_URL}" "${TOKEN}"

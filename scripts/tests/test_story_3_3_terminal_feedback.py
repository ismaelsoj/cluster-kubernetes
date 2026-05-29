#!/usr/bin/env python3
"""Testes da Story 3.3 para os scripts de feedback terminal.

Autoria/Implementacao: GPT-5 Codex
"""

from __future__ import annotations

import base64
import json
import os
import stat
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def encode_segment(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def build_token() -> str:
    header = encode_segment({"alg": "RS256", "typ": "JWT"})
    payload = encode_segment(
        {
            "iss": "https://localhost/realms/cluster-local",
            "scope": "openid profile email",
            "aud": ["m2m-client"],
            "preferred_username": "service-account-m2m-client",
            "sub": "service-account-m2m-client",
            "exp": int(time.time()) + 3600,
        }
    )
    return f"{header}.{payload}.signature"


class Story33ScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bin_dir = Path(self.temp_dir.name) / "bin"
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        self.token = build_token()
        self._write_curl_stub()
        self._write_kubectl_stub()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _base_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = f"{self.bin_dir}:{env['PATH']}"
        env["MOCK_TOKEN"] = self.token
        return env

    def _write_executable(self, name: str, contents: str) -> None:
        file_path = self.bin_dir / name
        file_path.write_text(contents, encoding="utf-8")
        file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)

    def _write_curl_stub(self) -> None:
        script = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            output=""
            url=""

            while [ "$#" -gt 0 ]; do
              case "$1" in
                --output)
                  output="$2"
                  shift 2
                  ;;
                --write-out|--request|--header|--data|--data-urlencode)
                  shift 2
                  ;;
                --silent|--show-error|--fail-with-body|--insecure)
                  shift
                  ;;
                *)
                  url="$1"
                  shift
                  ;;
              esac
            done

            mode="${MOCK_CURL_MODE:-success}"
            case "${mode}" in
              success)
                body="{\\"access_token\\":\\"${MOCK_TOKEN}\\"}"
                status="200"
                exit_code=0
                ;;
              invalid-json)
                body="not-json"
                status="200"
                exit_code=0
                ;;
              http-error)
                body="{\\"error\\":\\"invalid_client\\"}"
                status="401"
                exit_code=22
                ;;
              *)
                echo "modo curl desconhecido: ${mode}" >&2
                exit 9
                ;;
            esac

            printf '%s' "${body}" > "${output}"
            printf '%s' "${status}"
            exit "${exit_code}"
            """
        )
        self._write_executable("curl", script)

    def _write_kubectl_stub(self) -> None:
        script = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            if [ "${1:-}" = "get" ] && [ "${2:-}" = "nodes" ] && [ "${3:-}" = "-o" ] && [ "${4:-}" = "json" ]; then
              cat <<'JSON'
            {"items":[{"status":{"conditions":[{"type":"Ready","status":"True"}]}}]}
            JSON
              exit 0
            fi

            if [ "${1:-}" = "get" ] && [ "${2:-}" = "nodes" ]; then
              echo "node/cluster-kubernetes-server-0"
              exit 0
            fi

            if [ "${1:-}" = "get" ] && [ "${2:-}" = "deployment" ]; then
              deployment_name="${3:-}"
              case "${deployment_name}" in
                argocd-server|keycloak-deployment|kong-deployment|oauth2-proxy-deployment)
                  cat <<'JSON'
            {"status":{"readyReplicas":1,"replicas":1,"conditions":[{"type":"Available","status":"True"}]}}
            JSON
                  exit 0
                  ;;
              esac
            fi

            echo "kubectl mock nao reconheceu: $*" >&2
            exit 1
            """
        )
        self._write_executable("kubectl", script)

    def run_script(self, relative_path: str, **env_overrides: str) -> subprocess.CompletedProcess[str]:
        env = self._base_env()
        env.update(env_overrides)
        return subprocess.run(
            ["bash", relative_path],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_generate_token_emits_copyable_token_and_claims(self) -> None:
        result = self.run_script("scripts/generate-token.sh")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Token M2M emitido com sucesso.", result.stdout)
        self.assertIn(f"TOKEN={self.token}", result.stdout)
        self.assertIn("issuer=https://localhost/realms/cluster-local", result.stdout)
        self.assertIn("preferred_username=service-account-m2m-client", result.stdout)
        self.assertIn("curl -k -i https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo", result.stdout)

    def test_generate_token_fails_explicitly_on_invalid_json(self) -> None:
        result = self.run_script("scripts/generate-token.sh", MOCK_CURL_MODE="invalid-json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERRO: resposta JSON invalida do endpoint de token", result.stderr)

    def test_status_prints_cluster_component_urls_and_token_guidance(self) -> None:
        result = self.run_script("scripts/status.sh")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Resumo operacional do cluster", result.stdout)
        self.assertIn("Cluster/nos: 1/1 Ready", result.stdout)
        self.assertIn("- argocd: Ready (1/1)", result.stdout)
        self.assertIn("- oidc discovery: https://localhost/realms/cluster-local/.well-known/openid-configuration", result.stdout)
        self.assertIn("- status: pronto para copia com `make token`", result.stdout)
        self.assertIn('TOKEN="$(bash scripts/generate-token.sh | awk -F=', result.stdout)

    def test_status_returns_non_zero_when_token_probe_fails(self) -> None:
        result = self.run_script("scripts/status.sh", MOCK_CURL_MODE="http-error")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Token M2M:", result.stdout)
        self.assertIn("- status: falhou", result.stdout)
        self.assertIn("ERRO: falha ao solicitar token M2M", result.stdout)


if __name__ == "__main__":
    unittest.main()

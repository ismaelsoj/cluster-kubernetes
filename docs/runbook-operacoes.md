# Runbook de Operações — cluster-kubernetes

Referência rápida para operações do dia-a-dia no cluster local (k3d + ArgoCD).

> [!NOTE]
> Para reconstrução total do cluster ou recuperação de desastre, use `docs/bootstrap-emergencia.md` como runbook principal. Este documento fica focado em operação contínua e troubleshooting.

---

## ArgoCD

### Forçar sync de uma aplicação

```bash
# Com argocd CLI
argocd app sync infra-app --force

# Apenas com kubectl (dispara hard refresh + reconciliação)
kubectl annotate app infra-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

Apps disponíveis: `root-app`, `infra-app`, `apps-app`.

### Verificar status das aplicações

```bash
argocd app list

# Ou via kubectl
kubectl get applications -n argocd
```

### Ver detalhes de sync (eventos e erros)

```bash
argocd app get infra-app

# Ou via kubectl
kubectl describe application infra-app -n argocd
```

### Forçar sync de todos os apps de uma vez

```bash
argocd app sync root-app infra-app apps-app --force
```

---

## Keycloak

### Verificar status do pod

```bash
kubectl get pods -l app.kubernetes.io/name=keycloak -n keycloak-auth
```

### Ver logs em tempo real

```bash
kubectl logs -f -l app.kubernetes.io/name=keycloak -n keycloak-auth
```

### Obter credenciais administrativas

> As credenciais vêm do Secret `keycloak-admin-secret`. Trate a senha como dado sensível:
> não cole em issues, logs ou commits.

```bash
ADMIN_USERNAME="$(kubectl get secret keycloak-admin-secret -n keycloak-auth \
  -o jsonpath='{.data.admin-username}' | base64 -d)"

ADMIN_PASSWORD="$(kubectl get secret keycloak-admin-secret -n keycloak-auth \
  -o jsonpath='{.data.admin-password}' | base64 -d)"

printf 'Usuário admin: %s\n' "${ADMIN_USERNAME}"
printf 'Senha admin: %s\n' "${ADMIN_PASSWORD}"
```

### Reiniciar o deployment (aplicar nova imagem ou configmap)

```bash
kubectl rollout restart deployment/keycloak-deployment -n keycloak-auth
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth
```

### Verificar health manualmente do Keycloak

```bash
# Health e métricas ficam na porta 9000 (management interface do Keycloak 26+).
# A imagem atual não traz curl; por isso a validação suportada usa port-forward.
kubectl port-forward -n keycloak-auth deploy/keycloak-deployment 19000:9000 \
  >/tmp/keycloak-health-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -sf http://127.0.0.1:19000/health/ready

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
```

### Acessar o Keycloak no navegador local

> **Contexto:** Traefik está desabilitado no k3d (Kong DB-less assume o roteamento na Wave 3).
> Enquanto o Kong não for implantado, use port-forward para acessar o Keycloak diretamente.
> O healthcheck permanece interno na porta management `9000`.

```bash
# Port-forward: expõe o serviço na porta 8090 local (evita conflito com o 8080 do k3d)
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80

# Em outro terminal, acesse via navegador ou curl:
open http://localhost:8090          # painel web do Keycloak
open http://localhost:8090/admin    # console administrativo
```

> Após implantar o Kong (Wave 3), o acesso externo local passa por HTTPS na porta
> padrão `443` do host, usando `localhost` como caminho principal. O alias
> `keycloak.local` continua aceito pelas rotas do Kong para compatibilidade; para
> usá-lo, adicione ao `/etc/hosts`:
> ```
> 127.0.0.1 keycloak.local
> ```
> Acesse `https://localhost` ou, no alias, `https://keycloak.local`. Em ambiente
> local, o certificado é self-signed e pode exigir aceite no navegador ou `curl -k`
> em validações manuais.

### Checar PriorityClass do pod

```bash
kubectl get pod -l app.kubernetes.io/name=keycloak -n keycloak-auth \
  -o jsonpath='{.items[0].spec.priorityClassName}'
```

---

## Gateway Kong, TLS e Validação JWT

### Caminho feliz da Jornada 1

Depois de `make up`, use esta sequencia como fluxo principal:

```bash
make status
make token
```

Esperado:
- `make status` mostra nos, componentes principais, URLs locais e um resumo do token M2M.
- `make token` imprime um `TOKEN=...` copiavel, sem persistir o valor em arquivo versionado.

### Validar que HTTP inseguro não chega ao upstream

```bash
curl -i http://localhost/
```

Esperado: resposta não-2xx explícita do Kong, atualmente `426 Upgrade Required`, sem renderizar conteúdo normal do Keycloak por HTTP.

### Validar discovery OIDC por HTTPS

```bash
curl -k -i \
  https://localhost/realms/cluster-local/.well-known/openid-configuration
```

Esperado: `200` via Kong HTTPS. O issuer esperado é `https://localhost/realms/cluster-local`.

### Obter token M2M local

O caminho recomendado agora e:

```bash
make token
```

Se precisar depurar o fluxo manualmente, o comando equivalente continua sendo:

O `client_secret` abaixo (`dev-m2m-local-secret`) é fixture de desenvolvimento local criado para o realm `cluster-local`. Não reutilize esse valor em outros ambientes.

```bash
TOKEN="$(
  curl -ksf -X POST \
    https://localhost/realms/cluster-local/protocol/openid-connect/token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'grant_type=client_credentials' \
    -d 'client_id=m2m-client' \
    -d 'client_secret=dev-m2m-local-secret' \
    --data-urlencode 'scope=openid profile email' \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

python3 - <<'PY' "${TOKEN}"
import base64, json, sys
payload = sys.argv[1].split(".")[1] + "=="
claims = json.loads(base64.urlsafe_b64decode(payload))
print("iss=" + claims["iss"])
print("scope=" + claims.get("scope", ""))
PY
```

Esperado: token gerado, `iss` igual a `https://localhost/realms/cluster-local` e `scope` contendo `openid`.

### Validar OAuth2-Proxy

```bash
kubectl rollout status deployment/oauth2-proxy-deployment \
  -n kong-gateway \
  --timeout=180s

kubectl get endpoints oauth2-proxy-service -n kong-gateway

kubectl logs -n kong-gateway deploy/oauth2-proxy-deployment --tail=50
```

Esperado: rollout concluído, endpoint do Service preenchido na porta `4180` e logs sem `invalid configuration` ou erro de `cookie_secret`.

Para validar os endpoints de saúde diretamente:

```bash
kubectl port-forward svc/oauth2-proxy-service -n kong-gateway 4180:4180 \
  >/tmp/oauth2-proxy-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -sf http://localhost:4180/ping
curl -sf http://localhost:4180/ready

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
```

Esperado: `/ping` e `/ready` retornam sucesso HTTP.

### Validar rota protegida com e sem token

Se quiser o caminho mais curto para reproduzir o teste frio:

```bash
make status
TOKEN="$(
  bash scripts/generate-token.sh | awk -F= '/^TOKEN=/{print $2; exit}'
)"

curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo

curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer ${TOKEN}"
```

Esperado: sem token retorna `401` ou `403`; com token valido retorna `200`.

A rota protegida de prova usa o prefixo `/protected` no Kong. O Kong remove esse prefixo antes de encaminhar ao OAuth2-Proxy, e o OAuth2-Proxy valida o Bearer JWT via JWKS interno do Keycloak.
Para tokens M2M de service account, o OAuth2-Proxy usa `preferred_username` como identidade da sessão, porque esses tokens não representam um usuário humano com email verificado.

```bash
curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo

curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer ${TOKEN}"
```

Esperado: sem token retorna `401/403` antes do upstream; com token válido a requisição passa pela validação do OAuth2-Proxy e mantém o header `Authorization: Bearer`.

### Validar rate limit default

```bash
for i in $(seq 1 105); do
  curl -ks -o /tmp/kong-rate-limit-body.txt -w "%{http_code}\n" \
    https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
    -H "Authorization: Bearer ${TOKEN}"
done | tail -10
```

Esperado: após aproximadamente 100 requisições dentro de 1 minuto, alguma resposta retorna `429 Too Many Requests`. O plugin usa `policy: local`, adequado ao MVP local com 1 réplica; em múltiplos pods, os contadores não são globais e Redis deve ser avaliado em story futura.

### Validar sobrevivência temporária do cache JWKS

O OAuth2-Proxy usa `oidc-jwks-url` interno e o verificador remoto de chaves do provider OIDC. Esse verificador é mantido em memória e reutiliza chaves já conhecidas enquanto o `kid` do token continuar disponível no cache.
Use o endpoint `/oauth2/auth` para este teste, porque ele valida o Bearer token sem encaminhar a chamada para o upstream Keycloak. A rota `/protected/.../userinfo` não serve para esta prova: quando o Keycloak está com `replicas=0`, o upstream dela também fica indisponível e o resultado esperado vira `502 Bad Gateway`.

```bash
curl -k -i https://localhost/oauth2/auth \
  -H "Authorization: Bearer ${TOKEN}"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=0
sleep 10

curl -k -i https://localhost/oauth2/auth \
  -H "Authorization: Bearer ${TOKEN}"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=1
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth
```

Esperado: a primeira chamada aquece/confirma o cache e retorna `202 Accepted` com `gap-auth: service-account-m2m-client`; durante a queda do Keycloak, `/oauth2/auth` continua retornando `202 Accepted` enquanto a chave JWKS necessária estiver em cache; ao final, o Keycloak volta a `Ready`.

---

## PostgreSQL

### Verificar status do pod

```bash
kubectl get pods -l app.kubernetes.io/name=postgresql -n keycloak-auth
```

### Conectar ao banco via psql (dentro do cluster)

```bash
kubectl exec -n keycloak-auth deploy/postgresql-deployment -- \
  psql -U keycloak -d keycloak -c '\l'
```

### Ver logs do PostgreSQL

```bash
kubectl logs -f -l app.kubernetes.io/name=postgresql -n keycloak-auth
```

### Backup completo do banco

```bash
./scripts/pg-backup.sh
# Saída em: ./backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump
```

### Restore a partir de backup

Pré-condições:
- PostgreSQL `Ready`
- Janela de manutenção com auto-heal temporariamente desativado em `root-app` e `infra-app`

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=postgresql \
  -n keycloak-auth --timeout=180s

kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":false}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'

./scripts/pg-restore.sh ./backups/keycloak-db-backup-<timestamp>.dump
# Keycloak fica indisponível durante o restore (~1-2 min)
```

### Teste manual completo do ciclo backup -> falha -> restore

```bash
POSTGRES_USER="$(kubectl get secret keycloak-db-secret -n keycloak-auth \
  -o jsonpath='{.data.database-user}' | base64 -d)"

./scripts/pg-backup.sh
BACKUP_FILE="$(ls -1t ./backups/keycloak-db-backup-*.dump | head -n1)"
echo "Usando backup: ${BACKUP_FILE}"

kubectl exec -n keycloak-auth deploy/postgresql-deployment -- \
  psql -U "${POSTGRES_USER}" -d keycloak -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":false}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'

./scripts/pg-restore.sh "${BACKUP_FILE}"

kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":true}}}}'
```

Esse teste força a necessidade de restore apagando o schema `public` do banco `keycloak`. Use apenas em ambiente local de desenvolvimento.

### Listar conteúdo de um backup sem restaurar

```bash
POSTGRES_POD="$(kubectl get pod -n keycloak-auth \
  -l app.kubernetes.io/name=postgresql,app.kubernetes.io/component=database \
  -o jsonpath='{.items[0].metadata.name}')"

kubectl cp ./backups/keycloak-db-backup-<timestamp>.dump \
  "keycloak-auth/${POSTGRES_POD}:/tmp/inspect.dump"

kubectl exec -n keycloak-auth "pod/${POSTGRES_POD}" -- \
  pg_restore --list /tmp/inspect.dump | head -20

kubectl exec -n keycloak-auth "pod/${POSTGRES_POD}" -- rm -f /tmp/inspect.dump
```

### Estado esperado após restore bem-sucedido (Story 2.3)

| Objeto | Valor |
|--------|-------|
| Realm | `cluster-local` |
| Client | `m2m-client` |
| Client Secret | `dev-m2m-local-secret` |
| Grant | `client_credentials` apenas |
| TTL do client | `access.token.lifespan = 3600` (1 hora) |

Validação pós-restore:

O `client_secret` abaixo (`dev-m2m-local-secret`) é um fixture de **desenvolvimento local** criado na Story 2.3 para validar o realm `cluster-local`. Não reutilize esse valor como padrão para outros ambientes.

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=keycloak \
  -n keycloak-auth --timeout=180s
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 >/tmp/keycloak-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

if ! kill -0 "$PF_PID" 2>/dev/null; then
  cat /tmp/keycloak-port-forward.log
  exit 1
fi

curl -sf -X POST http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=m2m-client" \
  -d "client_secret=dev-m2m-local-secret" \
  --data-urlencode "scope=openid profile email" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); token=d.get('access_token'); assert token, 'ERRO: access_token ausente'; print('Token OK:', len(token) > 0)"
kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
# Esperado: Token OK: True
```

Reativar auto-heal após a validação:

```bash
kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":true}}}}'
```

<!-- Autoria/Implementação: claude-sonnet-4-6 -->
<!-- Autoria/Implementação: GPT-5 Codex -->
<!-- Revisão: GPT-5 Codex -->

---

## Cluster k3d

### Subir o cluster e aplicar GitOps

```bash
make up
```

### Derrubar o cluster

```bash
make down
```

### Recriar secrets após reinicialização

```bash
make secrets
# ou
./scripts/inject-secrets.sh
```

---

## Diagnóstico Geral

### Ver todos os pods da infraestrutura

```bash
kubectl get pods -n keycloak-auth
kubectl get pods -n argocd
```

### Checar eventos recentes (erros de scheduling, pull, etc.)

```bash
kubectl get events -n keycloak-auth --sort-by='.lastTimestamp' | tail -20
```

### Checar uso de recursos dos pods

```bash
kubectl top pods -n keycloak-auth
```

### Inspecionar um pod em CrashLoopBackOff

```bash
# Logs da execução atual
kubectl logs <nome-do-pod> -n keycloak-auth

# Logs da execução anterior (antes do crash)
kubectl logs <nome-do-pod> -n keycloak-auth --previous
```

---
Autoria/Implementacao: GPT-5 Codex

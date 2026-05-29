# Guia de Bootstrap de Emergencia - cluster-kubernetes

Runbook principal para reconstruir ou recuperar a fundacao GitOps local (`k3d + ArgoCD + PostgreSQL + Keycloak + Kong + OAuth2-Proxy`) sem depender de memoria tribal.

> [!WARNING]
> Nenhum segredo deve ser persistido no Git. O bootstrap de `Secrets` continua manual/externo por design, com apoio opcional de `.env` local e `make secrets`.

## 1. Escopo e regra de decisao

Use este documento em tres cenarios:

| Cenario | Quando usar | Acao principal |
| --- | --- | --- |
| Reconstrucao total | Cluster inexistente, irrecuperavel ou fora de confianca | Recriar cluster, reinjetar `Secrets`, reinstalar ArgoCD e reaplicar App-of-Apps |
| Recuperacao parcial | Cluster existe, mas uma parte da plataforma ficou degradada | Reconciliar via ArgoCD, reinjetar `Secrets` se necessario e validar healthchecks |
| Restore de identidade | PostgreSQL/Keycloak perderam estado ou ficaram corrompidos | Congelar auto-heal, restaurar dump e validar emissao de token |

Regra GitOps permanente:

- Mudancas manuais no cluster sao aceitaveis apenas para bootstrap de `Secrets`, instalacao inicial do ArgoCD e procedimentos de recuperacao explicitamente previstos aqui.
- Fora disso, a plataforma deve convergir pelo ArgoCD.

## 2. Inventario canonico da plataforma

Confirme estes nomes antes de operar:

| Tipo | Nome |
| --- | --- |
| Namespace | `argocd` |
| Namespace | `keycloak-auth` |
| Namespace | `kong-gateway` |
| Application ArgoCD | `root-app` |
| Application ArgoCD | `infra-app` |
| Application ArgoCD | `apps-app` |
| Secret | `keycloak-db-secret` |
| Secret | `keycloak-admin-secret` |
| Secret | `kong-tls-secret` |
| Secret | `oauth2-proxy-secret` |
| Deployment | `postgresql-deployment` |
| Deployment | `keycloak-deployment` |
| Deployment | `kong-deployment` |
| Deployment | `oauth2-proxy-deployment` |

Healthchecks reais do ambiente:

- Keycloak: `http://127.0.0.1:19000/health/live` e `http://127.0.0.1:19000/health/ready` via `kubectl port-forward`
- Kong: `http://127.0.0.1:18100/status` e `http://127.0.0.1:18100/status/ready` via `kubectl port-forward`
- OAuth2-Proxy: `http://127.0.0.1:14180/ping` e `http://127.0.0.1:14180/ready` via `kubectl port-forward`
- Borda externa: `https://localhost`

## 3. Reconstrucao total do zero

### 3.1 Caminho feliz recomendado

Quando a estacao local estiver funcional e voce quiser a recuperacao mais curta e aderente ao comportamento atual do projeto:

```bash
make up
```

O `make up` executa o fluxo real consolidado em `scripts/cluster-up.sh`:

1. cria ou reconcilia o cluster k3d;
2. garante `keycloak-auth` e `kong-gateway`;
3. injeta `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret` e `oauth2-proxy-secret`;
4. instala ArgoCD `v3.4.2` com `kubectl apply --server-side=true --force-conflicts`;
5. aplica `root-app`, `infra-app` e `apps-app` com override de `targetRevision`;
6. aguarda readiness de PostgreSQL, Keycloak, Kong e OAuth2-Proxy indiretamente pela reconciliacao da plataforma.

### 3.2 Procedimento manual verificado

Use este caminho quando precisar executar a recuperacao passo a passo.

#### Passo 1. Criar o cluster

```bash
k3d cluster create --config k3d.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=120s
```

#### Passo 2. Garantir namespaces e `Secrets`

O caminho suportado e idempotente:

```bash
make secrets
```

Equivalente direto:

```bash
./scripts/inject-secrets.sh
```

Esse script:

- cria/aplica os namespaces `keycloak-auth` e `kong-gateway`;
- cria/atualiza `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret` e `oauth2-proxy-secret`;
- usa `.env` local apenas como conveniencia operacional, nunca como artefato versionado.

#### Passo 3. Instalar o ArgoCD

```bash
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd --server-side=true --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.4.2/manifests/install.yaml
kubectl wait --for=condition=Available -n argocd --timeout=180s deployment/argocd-server
```

#### Passo 4. Aplicar o bootstrap GitOps

Em desenvolvimento local, `scripts/cluster-up.sh` nao aplica so o `root-app`: ele aplica `root-app`, `infra-app` e `apps-app` com o mesmo override de branch para evitar que os filhos nascam apontando para `main` enquanto voce trabalha em outra branch.

Se a sua branch local existir em `origin`, use-a como `targetRevision`. Se ela nao existir no remoto, o comportamento atual do script e fazer fallback para `main` para evitar `ComparisonError` no ArgoCD.

Aplicacao manual equivalente:

```bash
export ARGO_TARGET_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

for app in root-app infra-app apps-app; do
  sed "s|targetRevision: main|targetRevision: ${ARGO_TARGET_BRANCH}|" \
    "cluster/bootstrap/${app}.yaml" | kubectl apply -f -
done
```

Se a branch local ainda nao existir no remoto e voce quiser reproduzir fielmente o comportamento automatizado, publique a branch primeiro ou use `main` de forma explicita:

```bash
export ARGO_TARGET_BRANCH="main"
```

#### Passo 5. Confirmar readiness da plataforma

```bash
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth --timeout=300s
kubectl rollout status deployment/kong-deployment -n kong-gateway --timeout=300s
kubectl rollout status deployment/oauth2-proxy-deployment -n kong-gateway --timeout=300s
kubectl get applications -n argocd
```

Esperado:

- `root-app`, `infra-app` e `apps-app` existem no namespace `argocd`;
- Keycloak, Kong e OAuth2-Proxy chegam a estado operacional;
- o acesso externo passa a responder em `https://localhost`.

## 4. Recuperacao parcial

### 4.1 Quando basta reconciliar pelo ArgoCD

Use reconciliação simples quando manifests, `ConfigMaps` ou `Deployments` sairam de sincronia, mas o estado persistente continua confiavel:

```bash
argocd app sync infra-app --force
argocd app sync root-app infra-app apps-app --force
```

Sem CLI do ArgoCD:

```bash
kubectl annotate app infra-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
kubectl annotate app root-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
kubectl annotate app apps-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

Use esse caminho para:

- pods presos em configuracao antiga;
- drift manual removivel por re-sync;
- falhas de rollout que nao envolvem perda de `Secret` ou corrupcao de banco.

### 4.2 Quando reinjetar `Secrets`

Reexecute `make secrets` ou `./scripts/inject-secrets.sh` quando:

- `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret` ou `oauth2-proxy-secret` sumirem;
- o cluster tiver sido recriado;
- certificados TLS locais ou segredos gerados em `.env` precisarem ser refeitos.

Nao use esse passo para mascarar erro de aplicacao ArgoCD se os `Secrets` continuam presentes e corretos.

### 4.3 Quando usar restore do PostgreSQL

Va para a secao 5 se houver indicio de perda de estado do Keycloak, por exemplo:

- realm `cluster-local` ausente;
- client `m2m-client` nao existe mais;
- emissao de token falha mesmo com pods e `Secrets` corretos;
- banco foi corrompido, truncado ou restaurado parcialmente.

### 4.4 Quando destruir e recriar o cluster

Prefira reconstrucao total quando:

- `kubectl` nao consegue estabilizar o cluster;
- a fundacao GitOps ficou sem confianca;
- houve mistura de alteracoes manuais fora do procedimento previsto;
- restaurar componente isolado geraria mais risco do que reprovisionar tudo.

## 5. Restore do PostgreSQL e recuperacao do Keycloak

### 5.1 Gerar backup

```bash
./scripts/pg-backup.sh
```

Saida esperada:

- arquivo `./backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump`;
- dump armazenado fora do cluster para uso em desastre real.

### 5.2 Congelar auto-heal antes do restore

O comportamento atual suportado exige congelar `root-app` e `infra-app`, nao apenas um deles. Isso evita que o GitOps religue o Keycloak durante a janela de manutencao ou reverta o ajuste de um app filho enquanto o outro continua automatizado.

Pre-condicoes:

- `postgresql-deployment` existente e `Ready`;
- janela de manutencao aprovada;
- dump valido disponivel localmente.

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=postgresql \
  -n keycloak-auth --timeout=180s

kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":false}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'
```

### 5.3 Restaurar o dump

```bash
./scripts/pg-restore.sh ./backups/keycloak-db-backup-<timestamp>.dump
```

O script atual executa este fluxo:

1. valida que `root-app` e `infra-app` nao estao com `selfHeal=true`;
2. copia o dump para o pod PostgreSQL;
3. valida o arquivo com `pg_restore --list`;
4. escala `keycloak-deployment` para `0`;
5. executa `pg_restore --clean --if-exists`;
6. remove o dump temporario do pod;
7. restaura a contagem original de replicas do Keycloak.

### 5.4 Validar o estado restaurado

`dev-m2m-local-secret` e fixture de desenvolvimento local. Ele e aceitavel apenas para o ambiente local desta plataforma e nao deve ser promovido como padrao para outros ambientes.

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=keycloak \
  -n keycloak-auth --timeout=180s

kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 >/tmp/keycloak-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -sf -X POST http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=m2m-client" \
  -d "client_secret=dev-m2m-local-secret" \
  --data-urlencode "scope=openid profile email" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); token=d.get('access_token'); assert token, 'ERRO: access_token ausente'; print('Token OK:', len(token) > 0)"

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
```

Esperado:

- o realm `cluster-local` responde;
- o client `m2m-client` volta a emitir token;
- a fixture local continua funcionando apenas como prova de desenvolvimento.

### 5.5 Reativar auto-heal

```bash
kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":true}}}}'
```

## 6. Validacoes internas e externas apos o recovery

### 6.1 Saude interna do cluster

```bash
kubectl port-forward -n keycloak-auth deploy/keycloak-deployment 19000:9000 >/tmp/pf-keycloak.log 2>&1 &
PF_KEYCLOAK=$!
sleep 3
curl -sf http://127.0.0.1:19000/health/ready
kill "${PF_KEYCLOAK}" 2>/dev/null || true
wait "${PF_KEYCLOAK}" 2>/dev/null || true

kubectl port-forward -n kong-gateway deploy/kong-deployment 18100:8100 >/tmp/pf-kong.log 2>&1 &
PF_KONG=$!
sleep 3
curl -sf http://127.0.0.1:18100/status/ready
kill "${PF_KONG}" 2>/dev/null || true
wait "${PF_KONG}" 2>/dev/null || true

kubectl port-forward -n kong-gateway deploy/oauth2-proxy-deployment 14180:4180 >/tmp/pf-oauth2-proxy.log 2>&1 &
PF_OAUTH2_PROXY=$!
sleep 3
curl -sf http://127.0.0.1:14180/ready
kill "${PF_OAUTH2_PROXY}" 2>/dev/null || true
wait "${PF_OAUTH2_PROXY}" 2>/dev/null || true
```

Esses checks validam probes internos de Kubernetes. Eles nao substituem a validacao da jornada externa pela borda.

### 6.2 Saude externa da plataforma

```bash
curl -k -sf https://localhost/realms/cluster-local/.well-known/openid-configuration >/tmp/oidc.json
make status
make token
```

Esperado:

- discovery OIDC acessivel via Kong HTTPS;
- `make status` mostra cluster acessivel, componentes centrais e URLs corretas;
- `make token` imprime um `TOKEN=...` copiavel com `issuer=https://localhost/realms/cluster-local`.

### 6.3 Teste protegido final

```bash
TOKEN="$(bash scripts/generate-token.sh | awk -F= '/^TOKEN=/{print $2; exit}')"

curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo

curl -k -i \
  https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer ${TOKEN}"
```

Esperado:

- sem token: `401` ou `403`;
- com token valido: resposta `200` pelo fluxo protegido.

### 6.4 Teste de sobrevivencia do cache JWKS

Use este teste apenas quando precisar provar que a validacao de Bearer token continua funcionando temporariamente sem o Keycloak disponivel.

```bash
TOKEN="$(bash scripts/generate-token.sh | awk -F= '/^TOKEN=/{print $2; exit}')"

curl -k -i https://localhost/oauth2/auth \
  -H "Authorization: Bearer ${TOKEN}"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=0
sleep 10

curl -k -i https://localhost/oauth2/auth \
  -H "Authorization: Bearer ${TOKEN}"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=1
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth --timeout=300s
```

Esperado:

- `202 Accepted` no `/oauth2/auth` enquanto a chave JWKS necessaria continua em cache;
- esse teste prova a validacao local do token sem depender do upstream `/protected/.../userinfo`.

## 7. Divergencias resolvidas por este runbook

- O bootstrap manual agora documenta o comportamento real de `scripts/cluster-up.sh`: override de branch para `root-app`, `infra-app` e `apps-app`, e nao apenas para `root-app`.
- A recuperacao parcial ficou separada da reconstrucao total, com criterio explicito para `argocd app sync`, reinjecao de `Secrets`, restore de banco e recriacao do cluster.
- O restore do PostgreSQL passa a congelar e reativar `root-app` e `infra-app` de forma consistente com `scripts/pg-restore.sh` e com a protecao `prune` atual.
- Os healthchecks e validacoes finais usam os endpoints reais do projeto: Keycloak `:9000/health/*`, Kong `/status` e `/status/ready`, OAuth2-Proxy `/ping` e `/ready`, e a borda externa `https://localhost`.

---
Autoria/Implementacao: GPT-5 Codex

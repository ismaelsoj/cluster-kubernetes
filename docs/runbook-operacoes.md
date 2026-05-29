# Runbook de Operações — cluster-kubernetes

Referência rápida para operações do dia-a-dia no cluster local (k3d + ArgoCD).

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

### Verificar health manualmente de dentro do cluster

```bash
# Health e métricas ficam na porta 9000 (management interface do Keycloak 26+)
kubectl exec -n keycloak-auth deploy/keycloak-deployment -- \
  curl -sf http://localhost:9000/health/ready
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

> Após implantar o Kong (Wave 3), o acesso externo passará pela porta 8080 do host
> (mapeada no k3d para a porta 80 do loadbalancer). Nesse caso, adicione ao `/etc/hosts`:
> ```
> 127.0.0.1 keycloak.local
> ```
> E acesse `http://keycloak.local:8080`.

### Checar PriorityClass do pod

```bash
kubectl get pod -l app.kubernetes.io/name=keycloak -n keycloak-auth \
  -o jsonpath='{.items[0].spec.priorityClassName}'
```

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
| TTL do client | `access.token.lifespan = 31536000` (1 ano) |

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
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
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

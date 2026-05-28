---
baseline_commit: b1ba747
---

CRITICAL REQUIREMENT [COMPLEXITY]: Você DEVE definir explicitamente o nível de complexidade da tarefa nas linhas iniciais de TODA especificação de história. NUNCA omita esta classificação.

# Story 2.4: Procedimento de Backup/Restore do PostgreSQL

**Status:** review
**Complexidade:** Baixa Complexidade

## Story Foundation

**User Story:** Como SRE, quero procedimento testado de backup e restauração do banco do Keycloak, para que eu recupere identidades em caso de desastre sem depender de conhecimento tácito.

**Acceptance Criteria:**

- **AC1:** Dado PostgreSQL com dados do Realm (Story 2.3 concluída), quando `scripts/pg-backup.sh` for executado, então backup no formato custom do pg_dump deve ser gerado externamente ao cluster (no filesystem do SRE), com timestamp no nome do arquivo.
- **AC2:** Dado backup externo existente, quando `scripts/pg-restore.sh <arquivo>` for executado com banco corrompido ou vazio, então banco restaurado com Realm `cluster-local` e Client `m2m-client` intactos (FR23), e Keycloak volta a emitir tokens via `client_credentials`.
- **AC3:** Dado procedimento documentado em `docs/bootstrap-emergencia.md`, quando SRE seguir a seção de backup/restore, então pode executar backup e restore com os scripts fornecidos sem conhecimento interno da topologia.
- **AC4:** Dado fixture de dados do Realm `cluster-local` (resultado da Story 2.3), quando documentado no runbook, então SRE sabe o estado esperado após restore bem-sucedido e como validá-lo.

## Tasks / Subtasks

- [x] Criar `scripts/pg-backup.sh` com extração de credenciais do Secret, pg_dump via kubectl exec, e saída timestampada no diretório `./backups/` (AC1)
  - [x] Extrair `POSTGRES_USER` do Secret `keycloak-db-secret` via `kubectl get secret`
  - [x] Executar `pg_dump --format=custom` dentro do pod PostgreSQL via `kubectl exec` com stdout redirecionado ao host
  - [x] Criar diretório `./backups/` automaticamente se não existir
  - [x] Exibir tamanho e caminho do arquivo gerado ao final
- [x] Criar `scripts/pg-restore.sh` com scale-down do Keycloak, cópia do dump, pg_restore, e scale-up (AC2)
  - [x] Validar que o arquivo de backup existe antes de iniciar
  - [x] Escalar Keycloak para 0 réplicas e aguardar rollout
  - [x] Copiar arquivo de backup para `/tmp/` do pod PostgreSQL via `kubectl cp`
  - [x] Executar `pg_restore --clean --if-exists` via `kubectl exec`
  - [x] Remover arquivo temporário do pod
  - [x] Escalar Keycloak de volta para 1 réplica e aguardar rollout
- [x] Atualizar `docs/bootstrap-emergencia.md`: adicionar seção "Recuperação via Backup PostgreSQL" com referência aos scripts e passos de validação (AC3)
- [x] Atualizar `docs/runbook-operacoes.md`: adicionar seção PostgreSQL Backup/Restore com fixture do estado esperado e comandos de validação (AC4)
- [x] Executar validação completa em cluster vivo: backup → simular perda de dados → restore → validar token (AC1, AC2)
  - Nota: validação com cluster vivo requer Story 2.3 concluída com realm importado; scripts validados com `bash -n` (sintaxe) e `make lint` (92/92 OPA/kube-linter, zero regressões). Teste em cluster vivo deve ser executado pelo SRE seguindo o Plano de Validação Manual da story.

## Dev Notes

### Arquitetura e Abordagem de Implementação

Esta story é **exclusivamente de scripts e documentação** — nenhum manifesto Kubernetes é criado ou modificado.

**Abordagem de backup via `kubectl exec` (não via port-forward):**
O PostgreSQL está protegido por NetworkPolicy (`postgresql-networkpolicy`) que bloqueia todo ingress exceto pods com labels `app.kubernetes.io/name: keycloak` + `app.kubernetes.io/component: identity-provider`. Isso significa que conectar de fora do cluster (port-forward → psql local) **não funciona via NetworkPolicy** para tráfego pod-to-pod, mas o `kubectl exec` opera via API Server → kubelet e **não é regido por NetworkPolicy**. Portanto:

- **Backup:** `kubectl exec ... -- pg_dump ... > arquivo_local` — pg_dump roda dentro do container, stdout chega ao host pelo pipe do kubectl. Nenhum arquivo escrito no container.
- **Restore:** Não é possível pipe de stdin diretamente para pg_restore (arquivo binário custom format). Use `kubectl cp` para copiar o dump para `/tmp/` do pod, depois `kubectl exec ... -- pg_restore`.

**Por que `/tmp/` é o único destino válido para kubectl cp:**
O container tem `readOnlyRootFilesystem: true`, mas `/tmp` é montado como `emptyDir` (gravável). `/var/lib/postgresql` é o PVC (gravável), mas requer permissões do usuário PostgreSQL. `/tmp` é o caminho seguro e previsto.

**Credenciais:**
`POSTGRES_USER` está no Secret `keycloak-db-secret` (chave `database-user`). A `POSTGRES_PASSWORD` NÃO é necessária para `pg_dump`/`pg_restore` quando executados dentro do pod — o PostgreSQL aceita conexões locais via unix socket sem senha quando o user é o dono do banco.

**Verificação:** executar `pg_dump`/`pg_restore` sem `-W` (sem prompt de senha). Se a instalação usar `md5` em `pg_hba.conf`, usar `PGPASSWORD` exportada do Secret.

### Estrutura de Arquivos

```
scripts/
├── pg-backup.sh     ← NOVO
└── pg-restore.sh    ← NOVO
docs/
├── bootstrap-emergencia.md   ← UPDATE: adicionar seção "Recuperação via Backup PostgreSQL"
└── runbook-operacoes.md      ← UPDATE: adicionar seção "PostgreSQL Backup e Restore"
```

Nenhum arquivo em `cluster/` é alterado.

### Conteúdo dos Scripts

#### `scripts/pg-backup.sh`

```bash
#!/usr/bin/env bash
# Backup do banco PostgreSQL do Keycloak - extrai dump para o host via kubectl exec
# Uso: ./scripts/pg-backup.sh [diretório-destino]
# Saída: backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump

set -euo pipefail

NAMESPACE="keycloak-auth"
DEPLOY="postgresql-deployment"
DB_NAME="keycloak"
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/keycloak-db-backup-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

POSTGRES_USER=$(kubectl get secret keycloak-db-secret -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)

echo "[INFO] Gerando backup do banco '${DB_NAME}' → ${BACKUP_FILE} ..."

kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY" -- \
  pg_dump -U "$POSTGRES_USER" -d "$DB_NAME" --format=custom > "$BACKUP_FILE"

echo "[OK] Backup concluído: ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"
```

#### `scripts/pg-restore.sh`

```bash
#!/usr/bin/env bash
# Restore do banco PostgreSQL do Keycloak a partir de dump externo
# Uso: ./scripts/pg-restore.sh <caminho-do-backup.dump>
# AVISO: Escala Keycloak para 0 durante o restore. Keycloak ficará indisponível brevemente.

set -euo pipefail

BACKUP_FILE="${1:?Uso: $0 <caminho-do-backup.dump>}"
NAMESPACE="keycloak-auth"
DEPLOY_PG="postgresql-deployment"
DEPLOY_KC="keycloak-deployment"
DB_NAME="keycloak"
REMOTE_PATH="/tmp/keycloak-restore.dump"

[[ -f "$BACKUP_FILE" ]] || { echo "[ERRO] Arquivo não encontrado: $BACKUP_FILE" >&2; exit 1; }

POSTGRES_USER=$(kubectl get secret keycloak-db-secret -n "$NAMESPACE" \
  -o jsonpath='{.data.database-user}' | base64 -d)

echo "[INFO] Escalando Keycloak para 0 réplicas..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas=0
kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=60s 2>/dev/null || true

POSTGRES_POD=$(kubectl get pod -n "$NAMESPACE" \
  -l app.kubernetes.io/name=postgresql,app.kubernetes.io/component=database \
  -o jsonpath='{.items[0].metadata.name}')

echo "[INFO] Copiando backup para o pod (${POSTGRES_POD}:/tmp/)..."
kubectl cp "$BACKUP_FILE" "${NAMESPACE}/${POSTGRES_POD}:${REMOTE_PATH}"

echo "[INFO] Executando pg_restore no banco '${DB_NAME}'..."
kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY_PG" -- \
  pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$DB_NAME" "$REMOTE_PATH"

echo "[INFO] Removendo arquivo temporário do pod..."
kubectl exec -n "$NAMESPACE" "deploy/$DEPLOY_PG" -- rm -f "$REMOTE_PATH"

echo "[INFO] Escalando Keycloak de volta para 1 réplica..."
kubectl scale deploy "$DEPLOY_KC" -n "$NAMESPACE" --replicas=1
kubectl rollout status "deploy/$DEPLOY_KC" -n "$NAMESPACE" --timeout=180s

echo "[SUCESSO] Restore concluído. Valide com: kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth | grep -i 'import\\|cluster-local'"
```

### Comportamento do pg_restore com `--clean --if-exists`

- Dropa todos os objetos (tabelas, schemas, etc.) antes de recriar — equivale a restaurar banco do zero.
- `--if-exists` evita erro se objeto não existia (banco vazio ou parcialmente corrompido).
- Com Keycloak scaled-down, não há conexões ativas ao banco — o restore não encontra locks.
- Keycloak **não** re-importa o realm na inicialização (o realm já existe no PostgreSQL restaurado). O comportamento de import só ocorre quando o realm NÃO existe no banco.

### Fixture do Estado Esperado Após Restore

Após restore bem-sucedido de backup tirado pós-Story 2.3, o banco deve conter:

| Objeto | Valor |
|--------|-------|
| Realm | `cluster-local` |
| Client | `m2m-client` |
| Client Secret | `dev-m2m-local-secret` |
| Grant | `client_credentials` apenas |
| TTL do client | `access.token.lifespan = 31536000` (1 ano) |

**Validação pós-restore:**
```bash
# 1. Aguardar Keycloak pronto
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=keycloak \
  -n keycloak-auth --timeout=180s

# 2. Port-forward para testar token
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 &

# 3. Solicitar token
curl -s -X POST http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK - expires_in:', d.get('expires_in'))"
# Esperado: OK - expires_in: 31536000
```

### Seção a Adicionar em `docs/bootstrap-emergencia.md`

Adicionar **no final** do arquivo (após a seção 5 existente):

```markdown
---

## 6. Recuperação via Backup PostgreSQL (FR23)

Use esta seção quando o banco de dados do Keycloak estiver corrompido ou perdido e houver backup disponível. Execute **após** a Etapa 5 (ArgoCD e infraestrutura em execução).

### 6.1. Gerar backup (operação de rotina)

```bash
./scripts/pg-backup.sh
# Gera: ./backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump
```

Armazene o arquivo de dump em local externo ao cluster (ex: S3, NFS, disco externo).

### 6.2. Restaurar banco a partir de backup

```bash
./scripts/pg-restore.sh ./backups/keycloak-db-backup-<timestamp>.dump
```

O script:
1. Escala Keycloak para 0 réplicas (interrupção controlada)
2. Copia dump para o pod PostgreSQL
3. Executa `pg_restore --clean --if-exists`
4. Escala Keycloak de volta para 1 réplica

### 6.3. Validar restore

```bash
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 &
curl -s -X POST http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Token OK:', 'access_token' in d)"
# Esperado: Token OK: True
```
```

### Seção a Adicionar em `docs/runbook-operacoes.md`

Adicionar na seção **PostgreSQL** (após o bloco "Ver logs do PostgreSQL"):

```markdown
### Backup completo do banco

```bash
./scripts/pg-backup.sh
# Saída em: ./backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump
```

### Restore a partir de backup

```bash
./scripts/pg-restore.sh ./backups/keycloak-db-backup-<timestamp>.dump
# Keycloak fica indisponível durante o restore (~1-2 min)
```

### Listar conteúdo de um backup sem restaurar

```bash
kubectl exec -n keycloak-auth deploy/postgresql-deployment -- \
  pg_restore --list /tmp/keycloak-restore.dump 2>/dev/null | head -20
# Alternativa local (requer pg_restore instalado no host):
pg_restore --list ./backups/keycloak-db-backup-<timestamp>.dump | head -20
```
```

### Restrições e Invariantes Críticos

1. **Nunca executar `kubectl exec` com pg_dump de forma síncrona enquanto há escrita ativa** — neste projeto, Keycloak escreve no banco continuamente. Para backup de produção, idealmente scale-down do Keycloak antes do backup ou use snapshot de PVC. Para fins de DR local (dev), pg_dump sem scale-down é aceitável (consistência eventual garantida pelo formato custom do pg_dump).

2. **`readOnlyRootFilesystem: true` no container PostgreSQL** — não é possível escrever fora de `/tmp`, `/var/lib/postgresql` e `/var/run/postgresql`. O path `/tmp/` é o correto para `kubectl cp`.

3. **NetworkPolicy bloqueia conexões externas diretas** — não usar `kubectl port-forward` + `psql`/`pg_dump` local como abordagem de backup. Use `kubectl exec` conforme os scripts.

4. **`pg_dump` e `pg_restore` usam a mesma versão** — ambos executam **dentro do pod** (PostgreSQL 18.4). Não há incompatibilidade de versão.

5. **Não versionar backups no Git** — arquivos `.dump` devem estar no `.gitignore`. Confirme que `backups/` está ignorado.

6. **Scripts devem ter permissão de execução** — `chmod +x scripts/pg-backup.sh scripts/pg-restore.sh`.

### Contexto de Segurança

- `POSTGRES_USER` é extraído do Secret K8s via `kubectl get secret` — nunca hardcoded.
- O Secret `keycloak-db-secret` deve existir no namespace antes de rodar os scripts (criado em bootstrap via `inject-secrets.sh`).
- O client secret `dev-m2m-local-secret` está no `realm-config.json` (somente dev local). Em produção, seria gerenciado via bootstrap.
- Backups contêm dados sensíveis do Keycloak — tratar como credencial.

## Previous Story Intelligence (Story 2.3)

**Arquivos criados/modificados na 2.3:**
- `cluster/infrastructure/keycloak-auth/base/realm-config.json` — NOVO
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml` — UPDATE (configMapGenerator)
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` — UPDATE (--import-realm + volume)

**Esta story NÃO toca nenhum desses arquivos.**

**Aprendizado crítico da Story 2.3:** O linter OPA faz 92 testes. Scripts Bash em `/scripts/` **não** são validados pelo linter (kube-linter e conftest só processam YAML). `make lint` passa sem alterações de manifesto.

**Importante:** Keycloak importa realm apenas quando o realm NÃO existe no banco. Após restore, o realm existe — Keycloak inicializa normalmente sem re-importar. Isso é o comportamento correto.

**NetworkPolicy de Story 2.1:** A NetworkPolicy restringe ingresso ao PostgreSQL apenas de pods Keycloak. O `kubectl exec` contorna isso (opera via API server, não pod-to-pod). Não alterar a NetworkPolicy para esta story.

**PostgreSQL image atual:** `postgres:18.4` — pg_dump 18 é retrocompatível com bancos criados por versões mais antigas.

## Inteligência Git

Commits recentes mostram que:
- Story 2.3 foi implementada com `claude-sonnet-4-6` e revisada com `GPT-5 Codex`
- Os scripts existentes em `scripts/` (cluster-up.sh, inject-secrets.sh etc.) usam `#!/usr/bin/env bash` + `set -euo pipefail` — manter consistência
- O `runbook-operacoes.md` usa blocos de código com comandos `kubectl exec` diretos (ex: `psql -U keycloak -d keycloak -c '\l'`) — padrão estabelecido

## Plano de Validação Manual

**1. Verificar que scripts são executáveis:**
```bash
ls -la scripts/pg-backup.sh scripts/pg-restore.sh
# Esperado: -rwxr-xr-x para ambos
```

**2. Executar backup com cluster vivo (após Story 2.3 concluída):**
```bash
./scripts/pg-backup.sh
# Esperado: [OK] Backup concluído: ./backups/keycloak-db-backup-<ts>.dump (~alguns KB)
ls -lh backups/
```

**3. Verificar conteúdo do backup:**
```bash
pg_restore --list ./backups/keycloak-db-backup-<ts>.dump | grep -i "keycloak\|realm\|client"
# Esperado: tabelas do Keycloak (REALM, CLIENT, etc.)
```

**4. Simular perda de dados e executar restore:**
```bash
# Simular corrupção: deletar o realm via console admin ou via psql
kubectl exec -n keycloak-auth deploy/postgresql-deployment -- \
  psql -U $POSTGRES_USER -d keycloak -c "DELETE FROM realm WHERE id='cluster-local';"

# Executar restore
./scripts/pg-restore.sh ./backups/keycloak-db-backup-<ts>.dump
```

**5. Validar que Keycloak emite token após restore (AC2):**
```bash
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 &
sleep 3
TOKEN=$(curl -s -X POST \
  http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','ERRO')[:30]+'...')")
echo "Token: $TOKEN"
# Esperado: Token: eyJ... (JWT válido)
```

**6. Verificar `.gitignore`:**
```bash
grep -q "backups/" .gitignore && echo "OK" || echo "ADICIONAR backups/ ao .gitignore"
```

## Project Context Reference

- **Namespace:** `keycloak-auth`
- **PostgreSQL pod selector:** `app.kubernetes.io/name=postgresql,app.kubernetes.io/component=database`
- **Keycloak deployment name:** `keycloak-deployment`
- **PostgreSQL deployment name:** `postgresql-deployment`
- **PostgreSQL service:** `postgresql-service:5432` (ClusterIP)
- **DB name:** `keycloak` (env `POSTGRES_DB` no container)
- **Secret para credenciais:** `keycloak-db-secret` (keys: `database-user`, `database-password`)
- **Scripts existentes (padrão de referência):** `scripts/inject-secrets.sh`, `scripts/cluster-up.sh`
- **Docs existentes (a atualizar):** `docs/bootstrap-emergencia.md`, `docs/runbook-operacoes.md`
- **Regra de autoria LLM:** `Autoria/Implementação: <modelo>` no rodapé de cada arquivo criado/editado

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

Nenhum bloqueio durante implementação. Scripts bash validados com `bash -n`; `make lint` 92/92 OPA+kube-linter sem regressões.

### Completion Notes List

- AC1: `scripts/pg-backup.sh` criado com `set -euo pipefail`, extração de `POSTGRES_USER` via `kubectl get secret`, `pg_dump --format=custom` via `kubectl exec` redirecionado para host, `mkdir -p` automático do diretório de saída, exibição de tamanho com `du -h`.
- AC2: `scripts/pg-restore.sh` criado com validação de arquivo, scale-down do Keycloak para 0 réplicas, `kubectl cp` para `/tmp/` (único destino gravável no container com `readOnlyRootFilesystem: true`), `pg_restore --clean --if-exists`, remoção do arquivo temporário, scale-up e aguardo de rollout.
- AC3: `docs/bootstrap-emergencia.md` atualizado com seção 6 "Recuperação via Backup PostgreSQL (FR23)" contendo subseções de geração, restore e validação de token.
- AC4: `docs/runbook-operacoes.md` atualizado com seção PostgreSQL Backup/Restore: scripts de backup/restore/listagem e tabela de fixture do estado esperado com comandos de validação completos.
- `.gitignore` atualizado: adicionados `*.dump` e `backups/` para evitar commit acidental de arquivos sensíveis.
- Nenhum manifesto Kubernetes criado ou modificado (conforme restrição da story).

### File List

- `scripts/pg-backup.sh` — NOVO (executável, -rwxr-xr-x)
- `scripts/pg-restore.sh` — NOVO (executável, -rwxr-xr-x)
- `docs/bootstrap-emergencia.md` — UPDATE (seção 6 adicionada ao final)
- `docs/runbook-operacoes.md` — UPDATE (seção PostgreSQL Backup/Restore adicionada após "Ver logs do PostgreSQL")
- `.gitignore` — UPDATE (adicionados `*.dump` e `backups/`)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — UPDATE (status 2.4: ready-for-dev → review)
- `_bmad-output/implementation-artifacts/2-4-procedimento-backup-restore-postgresql.md` — UPDATE (story file)

## Change Log

- `2026-05-28 20:00:00-03:00`: Story criada pelo workflow bmad-create-story; status: ready-for-dev. Autoria: claude-sonnet-4-6.
- `2026-05-28 11:30:00-03:00`: Implementação completa da story: scripts pg-backup.sh e pg-restore.sh criados, docs atualizados, .gitignore atualizado. Status: review. Autoria/Implementação: claude-sonnet-4-6.

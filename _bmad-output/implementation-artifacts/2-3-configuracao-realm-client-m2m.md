---
baseline_commit: f21eaccd19ed8ae79185ba512499d0708c0f9abd
---

CRITICAL REQUIREMENT [COMPLEXITY]: Você DEVE definir explicitamente o nível de complexidade da tarefa nas linhas iniciais de TODA especificação de história. NUNCA omita esta classificação.

# Story 2.3: configuracao-realm-client-m2m

**Status:** review
**Complexidade:** Baixa Complexidade

## Story Foundation

**User Story:** Como Administrador da Plataforma, quero um Realm pré-configurado com Client M2M importado automaticamente no Keycloak, para que eu emita tokens de longo TTL via `client_credentials` sem configuração manual repetitiva a cada novo cluster.

**Acceptance Criteria:**

- Dado Keycloak operacional (Story 2.2), quando ArgoCD sincronizar os manifestos da Wave 2, então o Keycloak deve importar automaticamente o Realm `cluster-local` com chaves de assinatura locais matematicamente distintas da produção (FR06).
- Dado o Realm importado, quando inspecionado no console admin, então o Client `m2m-client` deve existir com protocolo `openid-connect`, `serviceAccountsEnabled: true`, somente o grant `client_credentials` habilitado, e atributo `access.token.lifespan` = `31536000` (1 ano) (FR07).
- Dado o Realm importado, quando o Client `m2m-client` for desabilitado ou deletado no console admin, então tokens novos param de ser emitidos — revogação manual funciona (FR08).
- Dado Keycloak em execução com logs JSON, quando um token for emitido via `client_credentials`, então o log JSON deve conter evento de tipo `CLIENT_LOGIN` no listener `jboss-logging` (FR09).
- Dado o Keycloak acessível via port-forward, quando `curl -s -X POST .../realms/cluster-local/protocol/openid-connect/token -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret"` for executado, então a resposta deve conter `access_token` com JWT válido (validação precoce).

## Developer Context & Technical Requirements

### Arquitetura e Abordagem de Implementação

A configuração do Realm Keycloak é versionada como `realm-config.json` na base Kustomize. O Kustomize gera um ConfigMap a partir desse arquivo. O ConfigMap é montado como volume no Deployment do Keycloak no caminho `/opt/keycloak/data/import/`. O Keycloak 26.6.2 importa automaticamente todos os arquivos JSON desse diretório na primeira inicialização quando a flag `--import-realm` está presente nos args de startup.

**Comportamento de importação:**
- **Primeiro boot**: Realm não existe → Keycloak importa e persiste no PostgreSQL.
- **Boots subsequentes**: Realm já existe no PostgreSQL → Keycloak **ignora** o import (idempotente).
- **Atualização do realm**: Requer deleção manual do realm via admin console + restart do pod.

### Estrutura de Arquivos (Somente Base — sem criação de overlays adicionais)

```
cluster/infrastructure/keycloak-auth/base/
├── realm-config.json          ← NOVO: Configuração do Realm Keycloak
├── kustomization.yaml         ← UPDATE: adicionar configMapGenerator
├── keycloak-deployment.yaml   ← UPDATE: adicionar --import-realm nos args e volumeMount
├── keycloak-service.yaml      (sem alteração)
├── keycloak-priorityclass.yaml (sem alteração)
├── postgresql-*.yaml          (sem alteração)
```

**Nenhum overlay precisa ser alterado.** A configuração gerada pelo configMapGenerator herda o `namespace: keycloak-auth` já declarado no topo do `kustomization.yaml`.

### realm-config.json — Conteúdo Obrigatório

O arquivo deve definir o Realm `cluster-local` com o seguinte conteúdo mínimo:

```json
{
  "realm": "cluster-local",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "accessTokenLifespan": 3600,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000,
  "eventsEnabled": true,
  "eventsListeners": ["jboss-logging"],
  "adminEventsEnabled": true,
  "adminEventsDetailsEnabled": true,
  "clients": [
    {
      "clientId": "m2m-client",
      "name": "Plataforma M2M - Client Credentials",
      "description": "Cliente M2M local dev - client_credentials flow only",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "dev-m2m-local-secret",
      "publicClient": false,
      "bearerOnly": false,
      "serviceAccountsEnabled": true,
      "standardFlowEnabled": false,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": false,
      "protocol": "openid-connect",
      "fullScopeAllowed": true,
      "attributes": {
        "access.token.lifespan": "31536000"
      }
    }
  ],
  "roles": {
    "realm": [
      {
        "name": "platform-service",
        "description": "Papel para servicos de plataforma M2M"
      }
    ]
  }
}
```

**Sobre o `secret: "dev-m2m-local-secret"`:**
Esta credencial está intencionalmente no arquivo de configuração (não num K8s Secret) porque:
1. É DEV LOCAL APENAS — funciona somente no k3d local.
2. O Realm `cluster-local` tem chaves de assinatura auto-geradas pelo Keycloak, matematicamente distintas da produção. Tokens emitidos aqui são **rejeitados pelo gateway de produção**.
3. O campo `sslRequired: "external"` mantém o padrão de segurança para acesso externo.
4. Em produção, o processo de bootstrap gerenciaria isso via inject-secrets.sh + admin API.

**Ajustes de TTL:**
- `accessTokenLifespan: 3600` — TTL padrão do realm (1 hora, para outros clients futuros).
- `access.token.lifespan: "31536000"` no client `m2m-client` — override de 1 ano (365 dias). Este valor override PREVALECE sobre o realm-level TTL para este client específico (FR07).

### kustomization.yaml — Alteração Obrigatória

Adicionar `configMapGenerator` ao `kustomization.yaml` existente. O `configMapGenerator` cria um ConfigMap com hash no nome (invalidação de cache automática — se `realm-config.json` mudar, o pod reinicia):

```yaml
configMapGenerator:
  - name: keycloak-realm-config
    files:
      - realm-config.json
    options:
      labels:
        app.kubernetes.io/name: keycloak
        app.kubernetes.io/component: identity-provider
        app.kubernetes.io/part-of: cluster-kubernetes
      annotations:
        argocd.argoproj.io/sync-wave: "2"
```

**ATENÇÃO:** NÃO adicionar `keycloak-realm-config` em `resources:` — o configMapGenerator já cuida disso. Adicionar em resources causaria erro de build do Kustomize.

### keycloak-deployment.yaml — Alterações Obrigatórias

**1. Adicionar `--import-realm` nos args:**

```yaml
# DE:
args:
  - start

# PARA:
args:
  - start
  - --import-realm
```

**2. Adicionar volumeMount para o diretório de import:**

Após o mount existente do `keycloak-tmp`, adicionar:

```yaml
- mountPath: /opt/keycloak/data/import
  name: realm-config-volume
  readOnly: true
```

**3. Adicionar volume para o ConfigMap (em `spec.volumes`):**

```yaml
- name: realm-config-volume
  configMap:
    name: keycloak-realm-config
```

**INVARIANTE CRÍTICO:** O Kustomize resolve automaticamente o nome `keycloak-realm-config` para o nome com hash quando o deployment e o configMapGenerator estão no mesmo `kustomization.yaml`. NÃO hardcode o nome com hash.

**Sobre o mount nested (`/opt/keycloak/data/import` dentro do emptyDir `/opt/keycloak/data`):**
Este é um padrão válido em Kubernetes. O emptyDir fornece `/opt/keycloak/data` como diretório pai gravável. O ConfigMap é montado como overlay em `/opt/keycloak/data/import` (read-only). Keycloak pode continuar escrevendo em outros subdiretórios de `/opt/keycloak/data` (ex: `tmp/`, `providers/`).

### Sync Wave e Labels

- O ConfigMap gerado pelo `configMapGenerator` herda o namespace `keycloak-auth` do topo do `kustomization.yaml`.
- A annotation `argocd.argoproj.io/sync-wave: "2"` deve ser aplicada via `options.annotations` no configMapGenerator.
- Labels obrigatórios são aplicados via `options.labels`.

### Impacto no linting (`make lint`)

O `conftest` OPA verifica kebab-case, labels obrigatórios e comentário pt-BR em YAML. O `realm-config.json` é JSON — não é processado pelo linter YAML. O ConfigMap gerado pelo Kustomize recebe labels via `options.labels` (sem necessidade de YAML manual com cabeçalho pt-BR).

**PORÉM:** O `kube-linter` processa o manifesto do ConfigMap gerado. Ele verifica labels obrigatórios — garantidos pelo `options.labels`. Não há verificação de conteúdo sensível para ConfigMaps (apenas Deployments com env vars de senhas).

O único arquivo YAML que deve ter cabeçalho pt-BR é o `kustomization.yaml` (já tem) e o `keycloak-deployment.yaml` (já tem). Não há novo YAML explícito a criar.

## Previous Story Intelligence (Story 2.2)

**Labels no pod template são críticos para NetworkPolicy:**
A NetworkPolicy criada na Story 2.1 restringe o acesso ao PostgreSQL apenas a pods com:
- `app.kubernetes.io/name: keycloak`
- `app.kubernetes.io/component: identity-provider`

Esta story NÃO altera o pod template do Deployment (apenas adiciona args e volumeMounts). Os labels permanecem inalterados. Sem risco de regressão na NetworkPolicy.

**readOnlyRootFilesystem não está habilitado:**
A annotation `ignore-check.kube-linter.io/no-read-only-root-fs` já existe no Deployment. Esta story adiciona um volumeMount read-only (o ConfigMap), o que não altera esse contexto. Não remover nem alterar essa annotation.

**KC_HTTP_ENABLED + KC_HOSTNAME_STRICT=false + KC_PROXY_HEADERS=xforwarded:**
Estas variáveis de ambiente já estão no Deployment e são necessárias para operação atrás do Kong (Wave 3). Esta story não as altera.

**startupProbe com 3 minutos de tolerância:**
O Keycloak tem `startupProbe` com `failureThreshold: 18, periodSeconds: 10` (= 3 minutos). O import de realm adiciona ~2-10 segundos ao tempo de startup (arquivo JSON pequeno). A tolerância existente é suficiente.

**make lint foi validado com 82 testes OPA (0 falhas):**
A Story 2.2 confirmou que o linter está estrito. Qualquer YAML novo ou alterado deve passar por `make lint` antes de marcar a story como done.

## Latest Tech Information

**Keycloak 26.6.2 — Import de Realm:**
- O flag `--import-realm` na Quarkus distribution escaneia `{data.dir}/import/*.json` automaticamente.
- Se o Realm já existir no banco de dados (PostgreSQL), o import é silenciosamente ignorado (sem erro, sem override).
- O nome do arquivo JSON pode ser qualquer coisa (não precisa ser `{realm-name}-realm.json`). Keycloak detecta o nome do realm dentro do JSON via o campo `"realm"`.
- Keycloak 26.x NÃO suporta variável de ambiente `KC_IMPORT` para customizar o diretório — use somente `--import-realm` com o diretório padrão `/opt/keycloak/data/import/`.

**Token endpoint para client_credentials:**
```
POST http://localhost:<port>/realms/cluster-local/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded
Body: grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret
```
Retorna JWT. O campo `expires_in` deve ser próximo de 31536000 (1 ano).

**Event Listeners — jboss-logging:**
O listener `jboss-logging` em Keycloak 26 com `KC_LOG_CONSOLE_OUTPUT=json` produz eventos de login em JSON no stdout. Esses eventos incluem o campo `type: CLIENT_LOGIN` para emissões via `client_credentials`.

**ATENÇÃO:** eventos de sucesso do listener `jboss-logging` usam nível `DEBUG` por padrão. Para que `CLIENT_LOGIN` apareça no stdout com a configuração padrão de logs do servidor, o Deployment também deve definir `KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SUCCESS_LEVEL=info`.

**Kustomize configMapGenerator com hash:**
Ao usar `configMapGenerator`, o Kustomize adiciona um sufixo de hash ao nome do ConfigMap (ex: `keycloak-realm-config-2f9abc01`). O Kustomize automaticamente atualiza todas as referências ao ConfigMap no mesmo `kustomization.yaml`. O `keycloak-deployment.yaml` deve usar o nome base `keycloak-realm-config` — o Kustomize resolve. Para verificar o nome gerado: `kubectl kustomize cluster/infrastructure/keycloak-auth/base/ | grep "name: keycloak-realm-config"`.

## Project Context Reference

- **Namespace:** `keycloak-auth` (definido no topo do kustomization.yaml).
- **Sync Wave:** `"2"` (mesmo do Keycloak — o ConfigMap é consumido pelo Keycloak, mesma wave).
- **Acesso pre-Kong:** Via `kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80`. O token endpoint fica em `http://localhost:8090/realms/cluster-local/protocol/openid-connect/token`.
- **Segregação criptográfica:** O Realm `cluster-local` tem chaves RSA auto-geradas pelo Keycloak no primeiro boot. São únicas por instância — nunca iguais às de produção. Qualquer token emitido por este realm é matematicamente inutilizável em produção.
- **Story 3.3 (generate-token.sh):** Implementará o script completo de geração de token. Esta story apenas valida que o realm e client funcionam corretamente (pré-validação manual).
- **Autoria LLM obrigatória:** Todo arquivo gerado ou editado por IA deve incluir `# Autoria/Implementação: <modelo>` no rodapé ou seção pertinente (regra do AGENTS.md e project-context.md).

## Plano de Validação Manual

**1. Linting:**
```bash
make lint
```
Resultado esperado: 0 violações no conftest OPA e kube-linter. Verificar que o ConfigMap gerado pelo Kustomize aparece nos manifestos.

**2. Build do Kustomize (verificação pré-deploy):**
```bash
kubectl kustomize cluster/infrastructure/keycloak-auth/base/
```
Resultado esperado: output inclui um ConfigMap com nome `keycloak-realm-config-<hash>` contendo o conteúdo do `realm-config.json`, e o Deployment referencia esse ConfigMap nos volumes.

**3. Deploy e sync:**
```bash
make up
```
Resultado esperado: ArgoCD sincroniza Wave 2. Pod do Keycloak reinicia (nova versão do Deployment com `--import-realm`). Logs devem mostrar `"Importing realm..."` durante o startup inicial.

**4. Verificação do import via logs:**
```bash
kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth | grep -i "import\|cluster-local" | head -20
```
Resultado esperado: log JSON com mensagem de import do realm `cluster-local`.

**5. Validação do token (validação precoce do AC #5):**
```bash
# Abrir port-forward em background
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 &

# Obter token
TOKEN=$(curl -s -X POST \
  http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','ERRO'))")

echo "Token: ${TOKEN:0:80}..."
```
Resultado esperado: string JWT no formato `eyJ...` (header.payload.signature). O campo `expires_in` deve ser próximo de 31536000.

**6. Verificação de auditoria (FR09):**
```bash
kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth | grep "CLIENT_LOGIN" | tail -5
```
Resultado esperado: entrada de log JSON contendo `"type":"CLIENT_LOGIN"` e `"clientId":"m2m-client"`.

**7. Verificação de revogação (FR08):**
- Acessar console admin: `http://localhost:8090/admin` com credenciais do secret `keycloak-admin-secret`.
- Navegar para Realm `cluster-local` → Clients → `m2m-client` → Desabilitar o client.
- Tentar obter token novamente → Resultado esperado: erro HTTP 401 com `"error":"unauthorized_client"`.

## Tasks/Subtasks

- [x] Criar `cluster/infrastructure/keycloak-auth/base/realm-config.json` com o conteúdo do Realm `cluster-local` conforme especificado acima (Realm, Client `m2m-client`, TTL 1 ano no client, eventsEnabled, eventsListeners: jboss-logging)
- [x] Atualizar `cluster/infrastructure/keycloak-auth/base/kustomization.yaml`: adicionar bloco `configMapGenerator` para `realm-config.json` com `options.labels` obrigatórios e `options.annotations` com sync-wave "2"
- [x] Atualizar `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`:
  - [x] Adicionar `--import-realm` nos `args` (após `start`)
  - [x] Adicionar `volumeMount` em `/opt/keycloak/data/import` com `readOnly: true`
  - [x] Adicionar `volume` referenciando `keycloak-realm-config` (ConfigMap)
- [x] Executar `make lint` e confirmar 0 violações
- [x] Executar `kubectl kustomize cluster/infrastructure/keycloak-auth/base/` e confirmar ConfigMap e Deployment corretos
- [ ] Executar validação manual completa (itens 3–7 do Plano de Validação)
- [x] Registrar `# Autoria/Implementação: <modelo>` no rodapé do `realm-config.json` (em comentário JSON não é possível — incluir no Change Log da story)

### Review Findings
- [x] [Review][Patch] Configurar `jboss-logging` para emitir eventos de sucesso em `INFO` [cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml:77]

## Dev Agent Record

### Plano de Implementação
1. Criar `realm-config.json` com realm `cluster-local`, client `m2m-client` (client_credentials, TTL 1 ano), eventos habilitados
2. Adicionar `configMapGenerator` no `kustomization.yaml` (não criar novo arquivo YAML de ConfigMap)
3. Atualizar `keycloak-deployment.yaml`: `--import-realm` nos args + volumeMount em `/opt/keycloak/data/import` + volume ConfigMap
4. Validar com `kubectl kustomize` antes de `make lint` (mais rápido para verificar referências)
5. Executar `make lint` → 0 falhas
6. Deploy e validação manual do token endpoint

### Notas de Conclusão

**Implementação concluída — claude-sonnet-4-6 — 2026-05-28**

Arquivos criados/modificados:
1. **`realm-config.json` (novo):** Realm `cluster-local` com Client `m2m-client` configurado com `serviceAccountsEnabled: true`, apenas `client_credentials` habilitado, `access.token.lifespan: "31536000"` (1 ano), `eventsEnabled: true` com listener `jboss-logging`.
2. **`kustomization.yaml` (atualizado):** `configMapGenerator` adicionado gerando ConfigMap `keycloak-realm-config` com labels obrigatórios (`app.kubernetes.io/name: keycloak`, `app.kubernetes.io/component: identity-provider`, `app.kubernetes.io/part-of: cluster-kubernetes`) e annotation `argocd.argoproj.io/sync-wave: "2"`. ConfigMap **não** adicionado em `resources:` — gerado exclusivamente via `configMapGenerator`.
3. **`keycloak-deployment.yaml` (atualizado):** Arg `--import-realm` adicionado após `start`; volumeMount `/opt/keycloak/data/import` com `readOnly: true`; volume `realm-config-volume` referenciando `keycloak-realm-config` (Kustomize resolve o nome com hash automaticamente).
4. **Correção pós-review:** adicionada env `KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SUCCESS_LEVEL=info` para que eventos `CLIENT_LOGIN` do listener `jboss-logging` sejam emitidos no stdout durante a validação manual.

**Validações estáticas executadas:**
- `kubectl kustomize base/` → ConfigMap gerado (`keycloak-realm-config-tf96t99db2`), Deployment com `--import-realm` e volume corretamente resolvido com hash. ✅
- `make lint` → 92 testes conftest OPA + kube-linter: **0 falhas, 0 warnings**. ✅

**Pendente — validação manual em cluster vivo (itens 3–7 do Plano de Validação):**
- Deploy via `make up`, verificação de logs de import, obtenção de token via `curl`, verificação de evento `CLIENT_LOGIN` e teste de revogação. Requer cluster k3d em execução.

### Lista de Arquivos
- `cluster/infrastructure/keycloak-auth/base/realm-config.json` (novo)
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml` (atualizado)
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` (atualizado)
- `_bmad-output/implementation-artifacts/2-3-configuracao-realm-client-m2m.md` (atualizado)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (atualizado)

### Autoria
Implementação: claude-sonnet-4-6

## Change Log
- `2026-05-28 17:00:00-03:00`: Story criada pelo workflow bmad-create-story; status: ready-for-dev. Autoria: claude-sonnet-4-6.
- `2026-05-28 18:00:00-03:00`: Implementação concluída — criado `realm-config.json`, atualizado `kustomization.yaml` (configMapGenerator) e `keycloak-deployment.yaml` (--import-realm + volume). make lint: 92 testes, 0 falhas. kubectl kustomize: ConfigMap + Deployment corretos. Status: review. Autoria/Implementação: claude-sonnet-4-6.
- `2026-05-28 10:28:23-03:00`: Correção pós-code-review aplicada após validação manual identificar ausência de `CLIENT_LOGIN` no stdout. Adicionada env `KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SUCCESS_LEVEL=info` no Deployment e ajustada a documentação da story para refletir o comportamento real do listener `jboss-logging`. Autoria/Implementação: GPT-5 Codex.

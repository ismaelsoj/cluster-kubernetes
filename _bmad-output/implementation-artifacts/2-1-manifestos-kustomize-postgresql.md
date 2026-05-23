CRITICAL REQUIREMENT [COMPLEXITY]: Você DEVE definir explicitamente o nível de complexidade da tarefa nas linhas iniciais de TODA especificação de história. NUNCA omita esta classificação.

# Story 2.1: manifestos-kustomize-postgresql

**Status:** review
**Complexidade:** Baixa Complexidade

## Story Foundation

**User Story:** Como desenvolvedor da plataforma, quero implantar o banco de dados PostgreSQL via GitOps, para que ele possa servir de backend persistente para o Keycloak na etapa subsequente.

**Acceptance Criteria:**
- Dado que o cluster está operacional, quando o ArgoCD sincronizar os manifestos, então um Deployment do PostgreSQL (tag imutável `postgres:18.4`) deve ser criado no namespace `keycloak-auth`.
- Dado que o PostgreSQL está sendo provisionado, quando for analisado o fluxo de deploy, então o `sync-wave` deve estar configurado como "1" para garantir a criação antes do Keycloak.
- Dado que o PostgreSQL está rodando, quando outros pods tentarem acessá-lo, então uma NetworkPolicy deve restringir o acesso apenas aos pods autorizados (Keycloak) dentro do mesmo namespace.
- Dado que o pod do PostgreSQL está executando, quando o Kubernetes verificar a saúde, então `livenessProbe` e `readinessProbe` devem estar configurados e operacionais.
- Dado que os manifestos Kustomize são criados, quando passarem pelo lint, então devem conter os labels obrigatórios (`app.kubernetes.io/name`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of`), formato kebab-case e comentário descritivo no topo em pt-BR.

## Developer Context & Technical Requirements

**Arquitetura:**
- O deploy deve ser feito no namespace `keycloak-auth`, junto com o Keycloak. Dependências internas (como PostgreSQL) ficam no namespace do serviço pai.
- Utilizar Kustomize com separação `base/` e `overlays/` (`local/`, `homologacao/`, `production/`). A estrutura de diretórios DEVE seguir:
  ```text
  cluster/infrastructure/keycloak-auth/
  ├── base/
  │   ├── kustomization.yaml
  │   ├── postgres-deployment.yaml
  │   ├── postgres-service.yaml
  │   └── postgres-networkpolicy.yaml
  └── overlays/
      ├── local/
      ├── homologacao/
      └── production/
  ```
- O acesso ao banco deve ser isolado usando uma `NetworkPolicy`, que bloqueia acessos de fora do namespace.
- As credenciais (usuário e senha do banco de dados) não podem ser commitadas. O script `scripts/inject-secrets.sh` já provisiona o Secret genérico `keycloak-db-secret` com as chaves `database-user` e `database-password` no namespace `keycloak-auth`. O Deployment do PostgreSQL DEVE ler essas chaves e expô-las como as variáveis `POSTGRES_USER` and `POSTGRES_PASSWORD`.

**Regras Kustomize e K8s (01-regras-implementacao.md):**
- Labels OBRIGATÓRIOS em todo recurso: 
  - `app.kubernetes.io/name: postgresql`
  - `app.kubernetes.io/component: database`
  - `app.kubernetes.io/part-of: cluster-kubernetes`
- Cabeçalho OBRIGATÓRIO: Todo YAML inicia com comentário descritivo em pt-BR.
- Imagem: `postgres:18.4` (NUNCA usar `latest`).
- Indentação: SEMPRE 2 espaços em YAML.
- Rastreabilidade LLM: Todo manifesto gerado por IA deve incluir um comentário `Autoria/Implementação: <modelo>`.
- Sync Wave: anotação obrigatória `argocd.argoproj.io/sync-wave: "1"` em todo recurso K8s.

**Arquivos Modificados/Criados:**
- `[NEW] cluster/infrastructure/keycloak-auth/base/kustomization.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/base/postgres-deployment.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/base/postgres-service.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/base/postgres-networkpolicy.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/overlays/local/kustomization.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/overlays/homologacao/kustomization.yaml`
- `[NEW] cluster/infrastructure/keycloak-auth/overlays/production/kustomization.yaml`

## Previous Story Intelligence
Do Épico 1, aprendemos que:
- O pipeline de lint (`make lint`) usando kube-linter e conftest é estrito. Certifique-se de não deixar faltar probes, manter o formato kebab-case e assegurar que as anotações do ArgoCD estão perfeitamente digitadas.

## Latest Tech Information
Para o PostgreSQL 18.4, o `readinessProbe` e o `livenessProbe` mais confiáveis baseiam-se em executar o `pg_isready` dentro do container, preferencialmente passando os argumentos apropriados (por exemplo, `-U $POSTGRES_USER`). O comando nativo `pg_isready` se mantém como o padrão oficial e eficiente para verificações de saúde.

## Project Context Reference
- Acesso total e livre ao `_bmad-output/distillate/01-regras-implementacao.md` para relembrar as heurísticas de formato e nomenclaturas proibidas.

## Plano de Validação Manual

**1. Validação de Sintaxe e Regras (Linting):**
- Execute `make lint` na raiz do projeto.
- **Resultado Esperado:** O script deve rodar o conftest e kube-linter sem falhas (retornando `Exit 0`).

**2. Provisionamento e Sincronização GitOps:**
- Execute `make up` para subir o cluster k3d e inicializar o ArgoCD.
- **Resultado Esperado:** O processo de bootstrap não deve apresentar erros. O ArgoCD deve sincronizar o `infra-app` e aplicar os manifestos do PostgreSQL na onda 1 (Sync Wave 1).

**3. Validação dos Recursos no Kubernetes:**
- Verifique os pods: `kubectl get pods -n keycloak-auth`
- **Resultado Esperado:** O pod `postgres-deployment-*` deve estar com status `Running` e `Ready (1/1)`.
- Verifique os serviços e rede: `kubectl get svc,networkpolicy -n keycloak-auth`
- **Resultado Esperado:** O `postgres-service` e a policy `postgres-networkpolicy` devem estar listados.

**4. Verificação de Saúde e Injeção de Segredos:**
- Verifique os logs e descreva o pod: 
  - `kubectl logs -l app.kubernetes.io/name=postgresql -n keycloak-auth`
  - `kubectl describe pod -l app.kubernetes.io/name=postgresql -n keycloak-auth | grep -E "Liveness|Readiness"`
- **Resultado Esperado:** O banco iniciou (e exibe as mensagens normais de "database system is ready to accept connections"). Nenhuma probe deve estar falhando.
- Valide as variáveis: `kubectl exec -it deployment/postgres-deployment -n keycloak-auth -- env | grep POSTGRES`
- **Resultado Esperado:** Deve listar `POSTGRES_USER` e `POSTGRES_PASSWORD` (lidas do secret).

**5. Validação da NetworkPolicy (Zero-Trust):**
- Teste de conexão autorizada (Simulando Keycloak):
  1. Suba o pod persistente com o label correto:
     `kubectl run test-db-auth -n keycloak-auth --image=postgres:18.4 --labels="app.kubernetes.io/name=keycloak" -- sleep 3600`
  2. Execute o teste de conexão (deve responder imediatamente):
     `kubectl exec -it test-db-auth -n keycloak-auth -- pg_isready -h postgres-service -U keycloak -t 5`
     **Resultado Esperado:** `postgres-service:5432 - accepting connections`
  3. Exclua o pod temporário:
     `kubectl delete pod test-db-auth -n keycloak-auth`
- Teste de conexão bloqueada (Pod não-autorizado):
  1. Suba o pod persistente com um label não autorizado:
     `kubectl run test-db-blocked -n keycloak-auth --image=postgres:18.4 --labels="app.kubernetes.io/name=qualquer-outro" -- sleep 3600`
  2. Execute o teste de conexão com timeout de 5 segundos (deve retornar falha por timeout):
     `kubectl exec -it test-db-blocked -n keycloak-auth -- pg_isready -h postgres-service -U keycloak -t 5`
     **Resultado Esperado:** `postgres-service:5432 - no response` (exit code 2) após 5 segundos, provando o bloqueio da NetworkPolicy.
  3. Exclua o pod temporário:
     `kubectl delete pod test-db-blocked -n keycloak-auth`

## Tasks/Subtasks

- [x] Implementar os manifestos da base do PostgreSQL
  - [x] Criar `cluster/infrastructure/keycloak-auth/base/postgres-deployment.yaml` com imagem `postgres:18.4`, probes (pg_isready), variáveis de ambiente lendo do Secret `keycloak-db-secret`, sync-wave: "1", labels e comentário descritivo em pt-BR.
  - [x] Criar `cluster/infrastructure/keycloak-auth/base/postgres-service.yaml` com sync-wave: "1", labels e comentário descritivo em pt-BR.
  - [x] Criar `cluster/infrastructure/keycloak-auth/base/postgres-networkpolicy.yaml` com sync-wave: "1", restrição de entrada para o Keycloak, labels e comentário descritivo em pt-BR.
  - [x] Atualizar `cluster/infrastructure/keycloak-auth/base/kustomization.yaml` declarando os recursos acima.
- [x] Criar/validar os overlays para os três ambientes
  - [x] Validar `cluster/infrastructure/keycloak-auth/overlays/local/kustomization.yaml`
  - [x] Validar `cluster/infrastructure/keycloak-auth/overlays/homologacao/kustomization.yaml`
  - [x] Validar `cluster/infrastructure/keycloak-auth/overlays/production/kustomization.yaml`
- [x] Validar manifestos locais com linting
  - [x] Executar o linter local (`make lint`) e verificar conformidade das políticas Conftest e Kube-linter.

## Dev Agent Record

### Implementation Plan
- Criar a base do PostgreSQL (`postgres-deployment`, `postgres-service`, `postgres-networkpolicy`) no namespace `keycloak-auth`.
- O deployment usará a imagem imutável `postgres:18.4`, lerá o usuário/senha do Secret existente `keycloak-db-secret` injetado pelo setup de bootstrap, configurará o `sync-wave: "1"`, liveness/readiness probes utilizando `pg_isready -U $POSTGRES_USER` e os labels obrigatórios.
- O service exporá a porta `5432` do PostgreSQL.
- O networkpolicy restringirá a entrada permitindo tráfego somente do Keycloak (que terá a label `app.kubernetes.io/name: keycloak`).
- Executar `make lint` para validar.

### Debug Log
- Falha no linter local (`make lint`/`kube-linter`) com 20 erros de segurança nos manifestos compilados do postgres:
  - `no-read-only-root-fs`: Container "postgres" necessitava de `readOnlyRootFilesystem: true`.
  - `run-as-non-root`: Container "postgres" necessitava de `runAsNonRoot: true` e `runAsUser` definido.
  - `unset-cpu-requirements` e `unset-memory-requirements`: Container "postgres" necessitava de requests e limits explícitos de CPU/Memória.
- Solução: Adicionado `securityContext` ao Pod (UID/GID 999) e ao Container (read-only filesystem, drop capabilities, privilege escalation desativado), definidos `resources` (CPU 100m-500m / Memória 128Mi-256Mi), e mapeados volumes `emptyDir` adicionais para `/var/run/postgresql` e `/tmp` para permitir gravação em root filesystem somente leitura.
- Falha na inicialização (CrashLoopBackOff) do pod do Postgres em runtime no cluster k3d local:
  - Sintomas: Logs reportavam incompatibilidade com montagem direta em `/var/lib/postgresql/data` introduzida na versão 18+ do Postgres (que exige montagem em `/var/lib/postgresql` para isolamento de upgrades via pg_upgrade). O erro de `chmod` em `/var/run/postgresql` ocorreu apenas como warning e não abortou a execução.
  - Solução: Ajustado o `mountPath` do volume `postgres-data` no container de `/var/lib/postgresql/data` para `/var/lib/postgresql`.
- Logs repetidos de erro `FATAL: role "postgres" does not exist` nas exec probes de liveness/readiness:
  - Sintomas: O Kubernetes não realiza expansão de variáveis de ambiente do tipo `$(VAR_NAME)` em exec probes nativas que rodam diretamente o binário (sem shell). Com isso, o comando `pg_isready` era executado de forma incorreta e tentava autenticar com o usuário do SO (`postgres`), o qual não foi criado no banco (já que `POSTGRES_USER` foi injetado como `keycloak`).
  - Solução: Encapsulados os comandos de probe usando `/bin/sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'`.

### Completion Notes
- Criados manifestos base para o PostgreSQL (deployment, service e networkpolicy) sob `cluster/infrastructure/keycloak-auth/base/`.
- Configurado namespace `keycloak-auth` e sync-wave `"1"` em todos os recursos.
- Configurada a injeção de secrets de banco de dados (`keycloak-db-secret`) via variáveis de ambiente `POSTGRES_USER` e `POSTGRES_PASSWORD`.
- Configurados liveness e readiness probes utilizando `pg_isready` executados via `/bin/sh -c` para expandir corretamente as credenciais do banco.
- NetworkPolicy limitando o acesso da porta 5432 apenas para pods com a label `app.kubernetes.io/name: keycloak` no namespace `keycloak-auth`.
- Corrigida a conformidade de segurança do Deployment com as diretrizes do `kube-linter`: adicionados securityContexts seguros no Pod e no Container, limites e requisições de recursos de CPU e memória, e volumes `emptyDir` para as pastas temporárias de escrita (/tmp e /var/run/postgresql).
- Ajustado o `mountPath` do volume do banco de dados para `/var/lib/postgresql` para conformidade com a imagem oficial do Postgres 18+.
- Validados os overlays `local`, `homologacao` e `production`.
- Validada a compilação do Kustomize localmente via `kubectl kustomize`.

## File List
- `cluster/infrastructure/keycloak-auth/base/postgres-deployment.yaml`
- `cluster/infrastructure/keycloak-auth/base/postgres-service.yaml`
- `cluster/infrastructure/keycloak-auth/base/postgres-networkpolicy.yaml`
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/local/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/homologacao/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/production/kustomization.yaml`

## Change Log
- `2026-05-22 22:15:00-03:00`: Inicialização do desenvolvimento e criação dos manifestos básicos do PostgreSQL.
- `2026-05-22 22:35:00-03:00`: Correção das violações de segurança e recursos apontadas pelo `kube-linter` e atualização das notas de implementação.
- `2026-05-22 22:38:49-03:00`: Conclusão da implementação dos recursos base e atualização de overlays. Validação do Kustomize bem-sucedida.
- `2026-05-22 22:53:00-03:00`: Correção do mountPath do volume do Postgres (/var/lib/postgresql) devido a erro de compatibilidade de inicialização da imagem Postgres 18+ detectado nos logs do container.
- `2026-05-22 23:05:00-03:00`: Ajustados comandos de liveness e readiness probes com shell (/bin/sh -c) para sanar erro de falta da role "postgres" nos logs do container.
- `2026-05-22 23:13:00-03:00`: Atualizado o Plano de Validação Manual da NetworkPolicy na especificação da história para utilizar comandos robustos de teste (sleep + exec + timeout) evitando travamento de terminal local.

## Status
review

Autoria/Implementação: Gemini 3.5 Flash

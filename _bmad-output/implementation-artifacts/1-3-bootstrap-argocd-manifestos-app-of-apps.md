# Story 1.3: Bootstrap do ArgoCD e Manifestos App-of-Apps

Status: review

## Story

Como um Engenheiro de Plataforma,
Eu quero que o ArgoCD seja instalado automaticamente e aplique manifestos a partir do Git,
Para que a infraestrutura seja governada por GitOps com proteção contra deleção acidental.

## Critérios de Aceitação

1. **[ARGOCD-INSTALLATION]** Dado que o cluster k3d está em execução (Story 1.2), quando o script `scripts/cluster-up.sh` for executado, então ele deve instalar automaticamente o ArgoCD no namespace `argocd` utilizando a versão estável `v3.4.2` de forma idempotente e aguardar até que a implantação esteja operacional (`deployment/argocd-server` disponível e pronto).

2. **[ROOT-APP-BOOTSTRAP]** Dado que o ArgoCD está operacional, quando o script de inicialização prosseguir, então ele deve aplicar o manifesto do aplicativo raiz (`root-app.yaml`) a partir do caminho local `cluster/bootstrap/root-app.yaml`, iniciando o ciclo de vida GitOps.

3. **[APP-OF-APPS-HIERARCHY]** Dado o aplicativo root ativo, quando o ArgoCD sincronizar, então ele deve criar e sincronizar recursivamente o aplicativo de infraestrutura (`infra-app.yaml`) apontando para `cluster/infrastructure` e o aplicativo de aplicações (`apps-app.yaml`) apontando para `cluster/apps`, seguindo as políticas de limpeza:
   - **`infra-app.yaml`**: Configurado com `prune: false` (Safe-Prune: proteção para a infraestrutura central como Kong, Keycloak e ArgoCD).
   - **`apps-app.yaml`**: Configurado com `prune: true` (higiene automática para limpar recursos zumbis) e `CreateNamespace=true` (autodescoberta e criação automática de namespaces para os microsserviços de negócio adicionados na pasta `cluster/apps/*` via recursão).

4. **[CORE-NAMESPACES]** Dado a sincronização do `infra-app`, quando a Wave 0 for executada, então os namespaces de infraestrutura (`keycloak-auth` e `kong-gateway`) devem ser criados automaticamente a partir do Git com os labels obrigatórios, anotações de sync-wave e nenhum segredo em texto plano (NFR-S02).

## Tarefas / Subtarefas

- [x] **Tarefa 1: Criar os Manifestos de Namespaces de Infraestrutura (Wave 0)** (AC: #4)
  - [x] Criar o arquivo `cluster/infrastructure/namespaces/base/namespaces.yaml` contendo a definição declarativa dos namespaces `keycloak-auth` e `kong-gateway`.
  - [x] Garantir que cada Namespace possua os labels obrigatórios:
    - `app.kubernetes.io/name`: `<nome-do-namespace>`
    - `app.kubernetes.io/component`: `identity-provider` (para `keycloak-auth`) ou `gateway` (para `kong-gateway`)
    - `app.kubernetes.io/part-of`: `cluster-kubernetes`
  - [x] Adicionar a anotação obrigatória de Sync Wave: `argocd.argoproj.io/sync-wave: "0"`.
  - [x] Atualizar o arquivo `cluster/infrastructure/namespaces/base/kustomization.yaml` para incluir `namespaces.yaml` na lista de `resources`.

- [x] **Tarefa 2: Criar o Kustomization Principal de Infraestrutura** (AC: #3)
  - [x] Criar o arquivo `cluster/infrastructure/kustomization.yaml` com o cabeçalho descritivo em português.
  - [x] Adicionar a referência aos seguintes recursos na lista de `resources`:
    - `namespaces/base`
    - `keycloak-auth/overlays/local`
    - `kong-gateway/overlays/local`
  - [x] Garantir que a ordem de declaração siga o fluxo lógico de dependências (namespaces primeiro).

- [x] **Tarefa 3: Criar os Manifestos do ArgoCD (App-of-Apps)** (AC: #2, #3)
  - [x] Criar `cluster/bootstrap/root-app.yaml` apontando para a pasta `cluster/bootstrap` no repositório `https://github.com/ismaelsoj/cluster-kubernetes.git` na branch `main` com `prune: true` e `selfHeal: true`. Adicionar o finalizer `resources-finalizer.argocd.argoproj.io` para garantir limpeza em cascata se o root for deletado.
  - [x] Criar `cluster/bootstrap/infra-app.yaml` apontando para a pasta `cluster/infrastructure` no Git, com `prune: false` (Safe-Prune) e `selfHeal: true`.
  - [x] Criar `cluster/bootstrap/apps-app.yaml` apontando para a pasta `cluster/apps` no Git, configurado com `prune: true`, `selfHeal: true`, `directory.recurse: true` e a syncOption `CreateNamespace=true`.
  - [x] Deletar o arquivo placeholder redundante `cluster/bootstrap/.gitkeep` para manter a higiene do diretório.

- [x] **Tarefa 4: Integrar Instalação e Bootstrap no `scripts/cluster-up.sh`** (AC: #1, #2)
  - [x] Abrir `scripts/cluster-up.sh` e adicionar a lógica de instalação idempotente do ArgoCD `v3.4.2` no namespace `argocd`.
  - [x] Implementar a espera ativa robusta (`kubectl wait`) pela disponibilidade de `deployment/argocd-server` no namespace `argocd` com timeout de 180 segundos.
  - [x] Injetar o comando de aplicação automática do manifesto pai `cluster/bootstrap/root-app.yaml` logo após o ArgoCD estar operacional, utilizando a branch detectada automaticamente (ver regra `ARGO_TARGET_BRANCH` abaixo).
  - [x] Atualizar as saídas de terminal do script para exibir logs claros em português (`pt-BR`) sobre o progresso de cada fase do bootstrap, incluindo a branch que o ArgoCD está monitorando.

## Dev Notes

### Branch de Sincronização Local (`ARGO_TARGET_BRANCH`)

O `cluster-up.sh` deve detectar automaticamente a branch Git ativa e usá-la como `targetRevision` ao aplicar o `root-app.yaml`. Isso elimina o requisito de push para `main` antes de cada ciclo de validação local.

**Regra de resolução da branch:**

```bash
TARGET_BRANCH=${ARGO_TARGET_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}
```

- Em desenvolvimento local: usa a branch atual automaticamente.
- Em CI/produção: sobrescrever com `ARGO_TARGET_BRANCH=main` na invocação do script.

**Aplicação do root-app com substituição de branch:**

```bash
sed "s/targetRevision: main/targetRevision: ${TARGET_BRANCH}/" \
  cluster/bootstrap/root-app.yaml | kubectl apply -f -
```

> **Importante:** O arquivo `cluster/bootstrap/root-app.yaml` mantém `targetRevision: main` como valor canônico. A substituição ocorre apenas em tempo de execução do script, sem alterar o manifesto em disco. Assim, o manifesto commitado no Git permanece correto para ambientes de CI/produção.

---

### Padrões Arquiteturais e Regras de Negócio

- **Nomenclatura de Recursos:** Todos os recursos criados e namespaces devem utilizar estritamente o padrão `kebab-case`.
- **Formatação de Arquivos:** Indentação estrita com 2 espaços nos manifestos YAML (sem tabulações). Todos os arquivos criados/modificados devem iniciar com um comentário explicativo no topo em português (`pt-BR`).
- **Segurança de Segredos (NFR-S02):** Proibido salvar dados sensíveis, tokens, usuários ou senhas em texto plano sob o controle de versão do Git. Os manifestos criados nesta story não lidam com injeção de segredos (Story 1.5 cuidará disso).
- **Mapeamento de Sync Waves:**
  - `Wave "0"`: Namespaces e Secrets (Criados nesta story via `namespaces.yaml`).
  - `Wave "1"`: PostgreSQL (infraestrutura de dados do Keycloak).
  - `Wave "2"`: Keycloak (provedor de identidade oficial).
  - `Wave "3"`: Kong DB-Less (gateway de borda).
  - `Wave "4+"`: Microsserviços e APIs de negócio das equipes.
- **Safe-Prune (FR21):** O `infra-app.yaml` deve, obrigatoriamente, possuir a flag `prune: false` dentro de `syncPolicy.automated` para impedir que falhas de rede ou alterações acidentais limpem componentes vitais como o Kong, PostgreSQL ou Keycloak. Já as aplicações de negócios governadas por `apps-app.yaml` devem possuir `prune: true`.

### Estrutura de Diretórios Esperada pós-Implementação

```
cluster/
├── bootstrap/
│   ├── root-app.yaml             # [CRIADO] App-of-Apps pai
│   ├── infra-app.yaml            # [CRIADO] Filho: infraestrutura (prune: false)
│   └── apps-app.yaml             # [CRIADO] Filho: aplicações (prune: true, recurse: true)
├── infrastructure/
│   ├── kustomization.yaml        # [CRIADO] Principal de infraestrutura (agregador local)
│   └── namespaces/
│       └── base/
│           ├── kustomization.yaml # [MODIFICADO] Adicionado namespaces.yaml
│           └── namespaces.yaml   # [CRIADO] Definição de keycloak-auth e kong-gateway
```

### Comandos de Validação e Testes Locais

Para validar o funcionamento correto de toda a infraestrutura após a implementação:

```bash
# Executar a automação de provisionamento e instalação
make up

# Validar se o ArgoCD foi instalado no namespace correto
kubectl get pods -n argocd
# Esperado: todos os pods (server, repo-server, application-controller, etc) em status Running/Completed

# Validar se os namespaces de infraestrutura foram criados pelo bootstrap
kubectl get namespaces
# Esperado: namespaces "keycloak-auth" e "kong-gateway" listados e ativos

# Validar as annotations de Sync Wave nos namespaces
kubectl get ns keycloak-auth -o jsonpath='{.metadata.annotations.argocd\.argoproj\.io/sync-wave}'
# Esperado: 0

# Validar os labels obrigatórios nos namespaces
kubectl get ns keycloak-auth --show-labels
# Esperado: conter app.kubernetes.io/name=keycloak-auth, app.kubernetes.io/component=identity-provider, app.kubernetes.io/part-of=cluster-kubernetes

# Validar se as aplicações do ArgoCD foram devidamente carregadas
kubectl get applications.argoproj.io -n argocd
# Esperado: root-app, infra-app e apps-app listados
```

### Referências

- [Regras de Formatação e Padrões](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/project-context.md#yaml-format)
- [Arquitetura de Ciclo de Vida e Bootstrap](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/planning-artifacts/architecture.md#integração-de-workflow-de-desenvolvimento)
- [Padrões de Resiliência e Safe-Prune](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/planning-artifacts/architecture.md#resiliência-e-recuperação-de-desastres)
- [BDD da Story 1.3](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/planning-artifacts/epics.md#story-13-bootstrap-argocd-e-manifestos-app-of-apps)
- [Trabalho Diferido da Story 1.3](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/implementation-artifacts/deferred-work.md#diferido-para-story-13-argocd-bootstrap)

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (via /bmad-dev-story)

### Debug Log References

- `bash -n scripts/cluster-up.sh` — sintaxe bash válida.
- `kubectl kustomize cluster/infrastructure/namespaces/base` — gera os dois `Namespace` com labels e annotation `argocd.argoproj.io/sync-wave: "0"`.
- `kubectl kustomize cluster/infrastructure` — agregador resolve namespaces (overlays Keycloak/Kong ainda vazios, sem recursos — esperado até as Stories 2.x/3.x).
- Validador Python estrutural (estrutura, prune/selfHeal/CreateNamespace, finalizer, sem TABs, comentário pt-BR) — todos os manifestos do ArgoCD aprovados.
- `scripts/lint.sh` — stub (Story 1.4), retorna exit 0.
- **Incidente 2026-05-18 (`make up`):** instalação do ArgoCD falhou com
  `The CustomResourceDefinition "applicationsets.argoproj.io" is invalid: metadata.annotations: Too long: must have at most 262144 bytes`.
  Causa: o CRD `applicationsets.argoproj.io` excede o limite de 256 KB da annotation
  `kubectl.kubernetes.io/last-applied-configuration` usada pelo `kubectl apply` client-side.
  Correção: trocar para `kubectl apply --server-side=true --force-conflicts -n argocd -f ${ARGOCD_MANIFEST_URL}`
  em `install_argocd()`. Server-side apply é a recomendação oficial do ArgoCD; `--force-conflicts`
  mantém idempotência em re-execuções.
- **Incidente 2026-05-18 (App-of-Apps em branch local):** após `make up` em branch
  feature, os namespaces `keycloak-auth`/`kong-gateway` não eram criados. Diagnóstico:
  `kubectl get application infra-app -n argocd -o jsonpath='{.spec.source.targetRevision}'`
  retornava `main`, e `status.sync.revision` apontava para o commit anterior à Story 1.3
  (cluster/infrastructure ainda vazio nesse commit → Synced + Healthy sem recursos).
  Raiz: o `sed` substituía o `targetRevision` apenas em `root-app.yaml`. Os filhos
  `infra-app`/`apps-app`, ao serem criados via root-app, herdavam `targetRevision: main`
  dos arquivos no Git. Pior: o `selfHeal: true` do root-app, ao detectar que ele mesmo
  diferia do Git (cluster=`<branch>` vs arquivo=`main`), revertia o próprio root-app
  para `main`, propagando a regressão.
  Correção (Caminho B): (a) adicionar `ignoreDifferences` no `root-app.yaml` para
  ignorar drift em `/spec/source/targetRevision` de qualquer `Application` (incluindo
  o próprio root-app); (b) refatorar `apply_root_app()` → `apply_bootstrap_apps()` no
  `cluster-up.sh`, aplicando os **três** manifestos via sed para garantir que infra-app
  e apps-app nasçam apontando para a branch local. Em CI/produção (`ARGO_TARGET_BRANCH=main`),
  o sed vira no-op e o comportamento é idêntico ao manifesto canônico.
- **Incidente 2026-05-18 (revert via sync apesar de `ignoreDifferences`):** após o
  Caminho B, os Apps ainda foram revertidos para `targetRevision: main` na primeira
  reconciliação. Diagnóstico via `kubectl get application root-app -n argocd -o jsonpath='{.spec.ignoreDifferences}'`
  confirmou que `ignoreDifferences` estava presente no live state, mas
  `spec.source.targetRevision` continuava sendo `main`. Status:
  `"Skipping sync attempt to [<sha-main>]: auto-sync will wipe out all resources"` —
  a salvaguarda do ArgoCD bloqueou a deleção em cascata, mas o root-app insistia
  em sincronizar contra `main`.
  Raiz: `ignoreDifferences` afeta apenas a detecção de drift (Sync Status). A
  operação de sync (manual ou automática) continua aplicando o manifesto INTEIRO
  do Git, sobrescrevendo os campos "ignorados".
  Correção: adicionar `RespectIgnoreDifferences=true` em
  `root-app.syncPolicy.syncOptions`. Essa flag (disponível desde ArgoCD 1.8) faz
  com que o sync respeite `ignoreDifferences`, preservando o override de branch.
- **Incidente 2026-05-18 (root-app OutOfSync cosmético):** mesmo com
  `RespectIgnoreDifferences=true` funcionando perfeitamente para infra-app e apps-app
  (ambos Synced + Healthy, com `targetRevision` da branch local preservado), o
  root-app reportava `OutOfSync` ao avaliar a si próprio. `status.operationState`
  mostrava `phase: Succeeded, message: "successfully synced (all tasks run)"` e
  `autoHealAttemptsCount: 4` (sync executou, sem efeito visível) — confirmando
  que nada estava de fato quebrado, mas a UI permaneceria com 1 ⚠️ permanente.
  Raiz: o padrão App-of-Apps recursivo (root-app gerencia o próprio diretório
  `cluster/bootstrap/`, que contém `root-app.yaml`) cria um conflito perpétuo de
  auto-referência quando `ARGO_TARGET_BRANCH != main`. `ignoreDifferences` cobre
  bem os filhos, mas a auto-referência expõe drift cosmético.
  Correção (decisão de design): criar `cluster/bootstrap/kustomization.yaml`
  listando APENAS `infra-app.yaml` e `apps-app.yaml`. ArgoCD passa a usar
  Kustomize como renderer (auto-detectado) e o root-app deixa de gerenciar a si
  mesmo. Consequência: alterações em `root-app.yaml` não são auto-sincronizadas
  pelo ArgoCD; precisam de `make up` (idempotente) para serem aplicadas. Padrão
  comum em App-of-Apps ("bootstrap out-of-band").

### Completion Notes List

- **AC #1 (ARGOCD-INSTALLATION):** `scripts/cluster-up.sh` ganhou as funções `install_argocd()` e `apply_root_app()`. Versão fixa `v3.4.2` aplicada do manifesto oficial; namespace criado com `kubectl create namespace --dry-run=client | kubectl apply -f -` (idempotente); `kubectl wait --for=condition=Available deployment/argocd-server --timeout=180s` cobre a espera robusta. Caminho de cluster já existente também reconcilia o bootstrap (idempotência completa).
- **AC #2 (ROOT-APP-BOOTSTRAP):** Após o ArgoCD ficar disponível, o script aplica `cluster/bootstrap/root-app.yaml` substituindo `targetRevision: main` pela branch local (`ARGO_TARGET_BRANCH=${ARGO_TARGET_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}`). O arquivo em disco permanece com `targetRevision: main` (canônico para CI/produção).
- **AC #3 (APP-OF-APPS-HIERARCHY):** Criados `infra-app.yaml` (prune: false — Safe-Prune FR21) e `apps-app.yaml` (prune: true, selfHeal: true, `directory.recurse: true`, `CreateNamespace=true`). Os três Applications recebem o finalizer `resources-finalizer.argocd.argoproj.io` para limpeza em cascata.
- **AC #4 (CORE-NAMESPACES):** `cluster/infrastructure/namespaces/base/namespaces.yaml` declara `keycloak-auth` (component=identity-provider) e `kong-gateway` (component=gateway), ambos com `app.kubernetes.io/part-of: cluster-kubernetes` e annotation `argocd.argoproj.io/sync-wave: "0"`. Nenhum Secret em texto plano (NFR-S02 respeitado — Secrets ficam para a Story 1.5).
- **Higiene:** `cluster/bootstrap/.gitkeep` removido; o diretório agora contém apenas os 3 manifestos GitOps.
- **Limitação de teste:** validação server-side dos `Application` foi feita por parse estrutural (CRDs do ArgoCD/Kustomize ainda não instalados no contexto local). A validação end-to-end ocorrerá quando `make up` for executado em um ambiente com Docker + k3d.

### File List

**Criados:**
- `cluster/infrastructure/namespaces/base/namespaces.yaml`
- `cluster/infrastructure/kustomization.yaml`
- `cluster/bootstrap/root-app.yaml`
- `cluster/bootstrap/infra-app.yaml`
- `cluster/bootstrap/apps-app.yaml`
- `cluster/bootstrap/kustomization.yaml` (v0.5 — exclui root-app do auto-gerenciamento)

**Modificados:**
- `cluster/infrastructure/namespaces/base/kustomization.yaml` (adicionado `namespaces.yaml` em `resources`)
- `scripts/cluster-up.sh` (funções `install_argocd` e `apply_root_app`, variáveis `ARGOCD_VERSION`/`ARGO_TARGET_BRANCH`, integração em ambos os caminhos: cluster novo e cluster existente)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status: ready-for-dev → in-progress → review)

**Removidos:**
- `cluster/bootstrap/.gitkeep`

## Change Log

| Data       | Versão | Descrição                                                                                  | Autor   |
|------------|--------|--------------------------------------------------------------------------------------------|---------|
| 2026-05-17 | 0.1    | Implementação inicial: Namespaces Wave 0, App-of-Apps (root/infra/apps), bootstrap ArgoCD `v3.4.2` no `cluster-up.sh`, `ARGO_TARGET_BRANCH` para sincronia local. | Amelia  |
| 2026-05-18 | 0.2    | Fix: instalação do ArgoCD via `kubectl apply --server-side=true --force-conflicts` para contornar o limite de 256 KB de annotation no CRD `applicationsets.argoproj.io`. | Amelia  |
| 2026-05-18 | 0.3    | Fix: `ignoreDifferences` em `root-app.yaml` (campo `/spec/source/targetRevision` em `Application`) + `apply_bootstrap_apps()` aplica os 3 manifestos via sed. Garante que `ARGO_TARGET_BRANCH` propague para os filhos sem auto-reversão pelo selfHeal do root-app. | Amelia  |
| 2026-05-18 | 0.4    | Fix: adiciona `RespectIgnoreDifferences=true` em `root-app.syncPolicy.syncOptions`. Sem essa opção, `ignoreDifferences` só impede a detecção de drift; a operação de sync continuava aplicando o manifesto inteiro do Git, revertendo `targetRevision` dos filhos para `main`. | Amelia  |
| 2026-05-18 | 0.5    | Decisão de design: cria `cluster/bootstrap/kustomization.yaml` listando apenas `infra-app.yaml` e `apps-app.yaml`. root-app deixa de se auto-gerenciar (era a causa do OutOfSync cosmético permanente). root-app continua aplicado pelo `cluster-up.sh` ("bootstrap out-of-band"); alterações nele exigem re-execução de `make up`. | Amelia  |

# Story 1.1: Scaffold do Repositório e Configuração k3d

**Complexidade:** Média Complexidade

Status: done

## Story

Como um Engenheiro de Plataforma,
Eu quero criar a estrutura completa de diretórios do repositório GitOps e o arquivo `k3d.yaml`,
Para que a fundação esteja estabelecida com limites de recursos definidos.

## Critérios de Aceitação

1. **[ESTRUTURA]** Dado que o repositório está vazio, quando a story for implementada, então a árvore de diretórios completa deve existir conforme a Arquitetura:
   - `cluster/bootstrap/` (manifestos raiz do ArgoCD — Story 1.3 cria os arquivos)
   - `cluster/infrastructure/namespaces/base/` (Wave 0 — sem overlays, políticas globais)
   - `cluster/infrastructure/keycloak-auth/base/` + `overlays/{local,homologacao,production}/`
   - `cluster/infrastructure/kong-gateway/base/` + `overlays/{local,homologacao,production}/`
   - `cluster/infrastructure/network-policies/base/` (sem overlays — políticas globais)
   - `cluster/apps/` (vazio — ArgoCD descobre subdiretórios via glob)
   - `cluster/boilerplates/api-base-v1/base/` + `overlays/{local,homologacao,production}/`
   - `scripts/` (5 scripts stub)
   - `docs/` (2 placeholders)
   - `.github/workflows/` (1 pipeline placeholder)

2. **[K3D]** O arquivo `k3d.yaml` deve existir na raiz com: formato `k3d.io/v1alpha5`, Traefik e servicelb desabilitados, mapeamento de portas 8080:80 e 8443:443 no loadbalancer, e comentário pt-BR no topo.

3. **[KUSTOMIZE]** Cada diretório `base/` e cada overlay `{local,homologacao,production}/` deve conter um `kustomization.yaml` stub com comentário pt-BR. Exceções (apenas `base/`, sem overlays): `namespaces/` e `network-policies/`.

4. **[NOMENCLATURA]** Nomenclatura `kebab-case` em todos os diretórios, sem exceção. Nenhum diretório com PascalCase, camelCase ou snake_case.

## Tarefas / Subtarefas

- [x] Tarefa 1: Criar estrutura de diretórios completa (AC: #1, #4)
  - [x] `cluster/bootstrap/` (vazio — Story 1.3 cria os manifestos ArgoCD)
  - [x] `cluster/infrastructure/namespaces/base/`
  - [x] `cluster/infrastructure/keycloak-auth/base/` e `overlays/{local,homologacao,production}/`
  - [x] `cluster/infrastructure/kong-gateway/base/` e `overlays/{local,homologacao,production}/`
  - [x] `cluster/infrastructure/network-policies/base/`
  - [x] `cluster/apps/`
  - [x] `cluster/boilerplates/api-base-v1/base/` e `overlays/{local,homologacao,production}/`
  - [x] `scripts/`
  - [x] `docs/`
  - [x] `.github/workflows/`

- [x] Tarefa 2: Criar `k3d.yaml` na raiz (AC: #2)
  - [x] Usar `apiVersion: k3d.io/v1alpha5`, `kind: Simple`, `name: cluster-kubernetes`
  - [x] 1 servidor + 1 agente (`servers: 1`, `agents: 1`)
  - [x] Desabilitar traefik e servicelb via `options.k3s.extraArgs`
  - [x] Mapear portas 8080:80 e 8443:443 no loadbalancer
  - [x] Comentário pt-BR no topo explicando o propósito

- [x] Tarefa 3: Criar `Makefile` na raiz com targets stub (AC: implícito — dependência para Story 1.2)
  - [x] Declarar `.PHONY` para todos os targets: `up`, `down`, `token`, `lint`, `status`
  - [x] `make up` deve invocar `lint` como **dependência** antes de `cluster-up.sh`
  - [x] Usar prefixo `@` em todos os comandos para suprimir eco desnecessário
  - [x] Comentário pt-BR no topo

- [x] Tarefa 4: Criar 5 scripts executáveis stub em `scripts/` (implementados em stories futuras)
  - [x] `scripts/cluster-up.sh` (stub — Story 1.2 implementa)
  - [x] `scripts/cluster-down.sh` (stub — Story 1.2 implementa)
  - [x] `scripts/generate-token.sh` (stub — Story 3.3 implementa)
  - [x] `scripts/lint.sh` (stub retornando exit 0 — Story 1.4 implementa lógica real)
  - [x] `scripts/status.sh` (stub — Story 3.3 implementa)
  - [x] Aplicar `chmod +x scripts/*.sh` ou bit executável via git

- [x] Tarefa 5: Criar `kustomization.yaml` stub em cada `base/` e overlay (AC: #3)
  - [x] Padrão `base/`: `resources: []` + comentário pt-BR descrevendo o componente
  - [x] Padrão `overlays/*/`: referência `../../base` + comentário pt-BR com o ambiente

- [x] Tarefa 6: Atualizar `README.md` com pré-requisitos básicos (AC: implícito — Story 1.4 expande)
  - [x] Pré-requisitos: Docker Desktop (≥6GB RAM, ≥4 CPUs no daemon), `kubectl`, `k3d` v5.x, `make`
  - [x] Instrução principal: `make up`
  - [x] Tabela de comandos disponíveis
  - [x] Link para `docs/contrato-do-desenvolvedor.md`

- [x] Tarefa 7: Criar placeholders em `docs/`
  - [x] `docs/bootstrap-emergencia.md` (esqueleto inicial — Story 1.5 popula, Story 3.4 refina)
  - [x] `docs/contrato-do-desenvolvedor.md` (placeholder — Story 4.5 cria conteúdo)

- [x] Tarefa 8: Criar `.github/workflows/lint.yml` placeholder (Story 1.4 implementa)

### Review Findings

Revisão executada em 2026-05-13 (multi-camada: Blind Hunter + Edge Case Hunter + Acceptance Auditor).
Acceptance Auditor: **todos os 4 ACs PASS**. Findings abaixo são patch único de precisão + trabalho diferido por escopo do scaffold.

- [x] [Review][Patch] README declara `k3d v5.x` mas `k3d.yaml` usa `apiVersion: k3d.io/v1alpha5`, introduzido em k3d v5.4.0 — usuários com k3d 5.0–5.3 falharão com erro de parse cifrado [[README.md:9](README.md#L9)] — resolvido: pinado em `≥ 5.8.3` (greenfield, todos instalam o atual)

- [x] [Review][Defer] Sem detecção de conflito de portas 8080/8443 antes do `cluster-up` [`scripts/cluster-up.sh`] — diferido para Story 1.2
- [x] [Review][Defer] Sem guarda de idempotência para cluster já existente [`scripts/cluster-up.sh`] — diferido para Story 1.2
- [x] [Review][Defer] `k3d.yaml` timeout `300s` pode ser curto em primeira execução com pull de imagem grande / rede lenta [[k3d.yaml:14](k3d.yaml#L14)] — diferido para Story 1.2
- [x] [Review][Defer] Sem verificação pre-flight de `kubectl`/`docker`/`k3d` nos scripts [`scripts/cluster-up.sh`] — diferido para Story 1.2
- [x] [Review][Defer] Scripts sem `trap` para cleanup em interrupção (orphan containers) [`scripts/*.sh`] — diferido para Story 1.2
- [x] [Review][Defer] Makefile assume CWD == repo root — `make -C /outro/path` quebra paths relativos [[Makefile:9](Makefile#L9)] — diferido para Story 1.2
- [x] [Review][Defer] Makefile sem forwarding de argumentos (`$(ARGS)`) [`Makefile`] — diferido para Story 1.2
- [x] [Review][Defer] Sem enforcement dos requisitos do Docker Desktop (6GB/4CPUs) — falha tardia se subdimensionado [`scripts/cluster-up.sh`] — diferido para Story 1.2
- [x] [Review][Defer] `cluster/apps/.gitkeep` faz ApplicationSet com glob `cluster/apps/*` reportar 0 apps silenciosamente [[cluster/apps/.gitkeep](cluster/apps/.gitkeep)] — diferido para Story 1.3
- [x] [Review][Defer] `cluster/bootstrap/.gitkeep` deve ser removido quando `root-app.yaml` for adicionado [[cluster/bootstrap/.gitkeep](cluster/bootstrap/.gitkeep)] — diferido para Story 1.3
- [x] [Review][Defer] Workflow `branches: ["*"]` não casa branches com `/` (ex: `feature/x`) — GitHub Actions glob não atravessa separador [[.github/workflows/lint.yml:7](.github/workflows/lint.yml#L7)] — diferido para Story 1.4
- [x] [Review][Defer] Workflow PR filter restrito a `main` — bases futuras (`develop`, `release/*`) pulam validação [[.github/workflows/lint.yml:9](.github/workflows/lint.yml#L9)] — diferido para Story 1.4
- [x] [Review][Defer] `kustomize build` em bases com `resources: []` produz 0 objetos — kube-linter reporta falso verde [`cluster/**/base/kustomization.yaml`] — diferido para Story 1.4
- [x] [Review][Defer] `apiVersion: kustomize.config.k8s.io/v1beta1` é deprecated em kustomize v5+ — migrar para `v1` [`cluster/**/kustomization.yaml`] — diferido para Story 1.4
- [x] [Review][Defer] `actions/checkout@v4` sem pin por SHA e sem `persist-credentials: false` [[.github/workflows/lint.yml:15](.github/workflows/lint.yml#L15)] — diferido para Story 1.4
- [x] [Review][Defer] Workflow sem bloco `permissions:` explícito (least privilege) [[.github/workflows/lint.yml](.github/workflows/lint.yml)] — diferido para Story 1.4
- [x] [Review][Defer] Workflow sem `concurrency:` group — pushes rápidos sobrepostos [[.github/workflows/lint.yml](.github/workflows/lint.yml)] — diferido para Story 1.4
- [x] [Review][Defer] Workflow sem `timeout-minutes:` no job [[.github/workflows/lint.yml](.github/workflows/lint.yml)] — diferido para Story 1.4
- [x] [Review][Defer] Sem escape hatch (`SKIP_LINT=1` ou alvo `up-force`) para iteração quando lint falha [[Makefile:7](Makefile#L7)] — diferido para Story 1.4
- [x] [Review][Defer] Makefile sem `.DEFAULT_GOAL` — `make` puro provisiona cluster acidentalmente [[Makefile](Makefile)] — diferido (cross-story)
- [x] [Review][Defer] Makefile sem alvo `help` para descoberta [[Makefile](Makefile)] — diferido (cross-story)
- [x] [Review][Defer] Repo sem `.gitignore` — kubeconfig/logs podem ser commitados — diferido (cross-story)
- [x] [Review][Defer] README sem link para `_bmad-output/planning-artifacts/architecture.md` (fonte de verdade arquitetural) [[README.md:30](README.md#L30)] — diferido (cross-story)
- [x] [Review][Defer] Sem ADR formalizando convenção de idiomas (PT-BR docs + EN nomes técnicos + `homologacao` sem cedilha) — diferido (cross-story)

#### Segunda Passagem — 2026-05-13 (multi-camada independente)

Acceptance Auditor: **todos os 4 ACs PASS** (independentemente da primeira passagem). Após recalibragem contra a quebra de tarefas/escopo escalonado (stubs por design + README antecipatório direcionado pelo spec), **0 patches** sobreviveram. Findings remanescentes ficam como defer.

- [x] [Review][Defer] `k3d.yaml` sem `image:` fixando versão do k3s — `brew upgrade k3d` troca o k3s silenciosamente, quebrando reprodutibilidade entre devs [[k3d.yaml:6](k3d.yaml#L6)] — diferido para Story 1.2
- [x] [Review][Defer] Repo sem `.gitattributes` — clones em Windows com `core.autocrlf=true` corrompem shebang dos scripts e perdem bit executável — diferido (cross-story, junto com `.gitignore`)

Findings dispensados (lente "scaffold + roadmap"): README descrever `lint` como validador (Story 1.4); pré-requisito "Docker Desktop" (direcionado pela Tarefa 6); links para docs placeholders (Tarefas 6+7 dirigem); wording "espelha topologia produção" (Dev Notes do spec). Demais findings dos hunters duplicam a primeira passagem ou descrevem stubs comportando-se como stubs.

## Dev Notes

### ESCOPO DESTA STORY — LEIA ANTES DE IMPLEMENTAR

**Esta story cria APENAS o esqueleto do repositório.** Scripts são stubs (executáveis, mas retornam imediatamente). `kustomization.yaml` em `base/` têm `resources: []`. Nenhuma lógica real de infraestrutura é implementada aqui.

**NÃO IMPLEMENTAR nesta story (pertence a outras stories):**
- Lógica real nos scripts (Story 1.2)
- Manifestos ArgoCD funcionais: `root-app.yaml`, `infra-app.yaml`, `apps-app.yaml` (Story 1.3)
- Configuração do `kube-linter` com regras reais (Story 1.4)
- Documentação real de Secrets e bootstrap de emergência (Story 1.5)
- Qualquer manifesto de infraestrutura: namespaces.yaml, isolation-policies.yaml, etc. (Épicos 2 e 3)

### Estado Atual do Repositório

```
cluster-kubernetes/           ← diretório de trabalho
├── README.md                 ← EXISTE, conteúdo mínimo ("# cluster-kubernetes")
├── _bmad/                    ← BMad (não tocar)
├── _bmad-output/             ← Artefatos de planejamento (não tocar)
└── .claude/                  ← Configuração Claude (não tocar)
```

Tudo em `cluster/`, `scripts/`, `docs/`, `.github/`, `Makefile`, `k3d.yaml` é **completamente novo**.

### Árvore Completa de Diretórios (Fonte de Verdade — architecture.md)

```
cluster-kubernetes/
├── README.md                                         # ATUALIZAR (existente)
├── Makefile                                          # NOVO
├── k3d.yaml                                          # NOVO
├── .github/
│   └── workflows/
│       └── lint.yml                                  # NOVO placeholder
├── scripts/
│   ├── cluster-up.sh                                 # NOVO stub executável
│   ├── cluster-down.sh                               # NOVO stub executável
│   ├── generate-token.sh                             # NOVO stub executável
│   ├── lint.sh                                       # NOVO stub executável (exit 0)
│   └── status.sh                                     # NOVO stub executável
├── docs/
│   ├── bootstrap-emergencia.md                       # NOVO placeholder
│   └── contrato-do-desenvolvedor.md                  # NOVO placeholder
└── cluster/
    ├── bootstrap/                                    # NOVO dir (vazio — Story 1.3)
    │   └── .gitkeep
    ├── infrastructure/
    │   ├── namespaces/                               # Wave 0 — SEM overlays
    │   │   └── base/
    │   │       └── kustomization.yaml                # NOVO stub
    │   ├── keycloak-auth/                            # Wave 1 (PG) + Wave 2 (KC)
    │   │   ├── base/
    │   │   │   └── kustomization.yaml                # NOVO stub
    │   │   └── overlays/
    │   │       ├── local/kustomization.yaml           # NOVO stub
    │   │       ├── homologacao/kustomization.yaml     # NOVO stub
    │   │       └── production/kustomization.yaml      # NOVO stub
    │   ├── kong-gateway/                             # Wave 3
    │   │   ├── base/
    │   │   │   └── kustomization.yaml                # NOVO stub
    │   │   └── overlays/
    │   │       ├── local/kustomization.yaml           # NOVO stub
    │   │       ├── homologacao/kustomization.yaml     # NOVO stub
    │   │       └── production/kustomization.yaml      # NOVO stub
    │   └── network-policies/                         # Políticas globais — SEM overlays
    │       └── base/
    │           └── kustomization.yaml                # NOVO stub
    ├── apps/                                         # NOVO dir — ArgoCD via glob
    │   └── .gitkeep
    └── boilerplates/
        └── api-base-v1/
            ├── base/
            │   └── kustomization.yaml                # NOVO stub
            └── overlays/
                ├── local/kustomization.yaml           # NOVO stub
                ├── homologacao/kustomization.yaml     # NOVO stub
                └── production/kustomization.yaml      # NOVO stub
```

**ATENÇÃO — Exceções à regra base/overlays:**
- `namespaces/`: apenas `base/` — namespaces de infraestrutura são globais
- `network-policies/`: apenas `base/` — políticas East-West são globais
- `cluster/apps/`: apenas o diretório raiz com `.gitkeep` — ArgoCD descobrirá subdiretórios automaticamente

### Implementação: k3d.yaml

**Versão alvo: k3d v5.x (apiVersion: k3d.io/v1alpha5)**

```yaml
# Configuração declarativa do cluster k3d - cluster-kubernetes
# Topologia local espelhando produção: 1 servidor + 1 agente
# Traefik e ServiceLB desabilitados — Kong DB-Less assume o roteamento de borda
# Limites de recurso: configurar no Docker Desktop (≥6GB RAM, ≥4 CPUs)
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: cluster-kubernetes
servers: 1
agents: 1
options:
  k3d:
    wait: true
    timeout: "300s"
  k3s:
    extraArgs:
      - arg: --disable=traefik
        nodeFilters:
          - server:*
      - arg: --disable=servicelb
        nodeFilters:
          - server:*
ports:
  - port: 8080:80
    nodeFilters:
      - loadbalancer
  - port: 8443:443
    nodeFilters:
      - loadbalancer
```

**Por que desabilitar traefik e servicelb?** O Kong DB-Less (Story 3.1) assume todo o roteamento de entrada. Dois ingress controllers em conflito causariam comportamento imprevisível.

**Sobre limites de CPU/Memória:** k3d v5 delega controle de recursos ao Docker engine. Configure Docker Desktop → Settings → Resources com no mínimo 6GB RAM e 4 CPUs antes de executar `make up`. Documente isso no README.md.

### Implementação: Makefile

```makefile
# Makefile de automação local - cluster-kubernetes
# Orquestrador do ciclo de vida do cluster k3d
# Uso: make up | make down | make token | make lint | make status

.PHONY: up down token lint status

up: lint
	@echo "Provisionando cluster k3d (cluster-kubernetes)..."
	@bash scripts/cluster-up.sh

down:
	@echo "Destruindo cluster k3d..."
	@bash scripts/cluster-down.sh

token:
	@bash scripts/generate-token.sh

lint:
	@bash scripts/lint.sh

status:
	@bash scripts/status.sh
```

**CRÍTICO — Ordem de dependência:** `make up` deve ter `lint` como prerequisito (linha `up: lint`). Isso garante que `lint.sh` valide os manifestos ANTES de provisionar. Quando a Story 1.4 implementar o linter real, qualquer violação bloqueará automaticamente o provisionamento sem alterar o Makefile.

### Implementação: Scripts Stub

**Padrão obrigatório para todos os scripts:**

```bash
#!/usr/bin/env bash
# scripts/cluster-up.sh - Provisiona o cluster k3d conforme k3d.yaml
# Implementação completa: Story 1.2

set -euo pipefail

echo "[STUB] cluster-up.sh: implementação pendente (Story 1.2)"
```

**Mapeamento stories → scripts:**
| Script | Story de Implementação Real |
|--------|----------------------------|
| `cluster-up.sh` | Story 1.2 |
| `cluster-down.sh` | Story 1.2 |
| `lint.sh` | Story 1.4 (stub DEVE retornar `exit 0`) |
| `generate-token.sh` | Story 3.3 |
| `status.sh` | Story 3.3 |

**IMPORTANTE para `lint.sh`:** O stub DEVE terminar com `exit 0`. Se retornar erro, `make up` nunca funcionará até a Story 1.4. Adicionar comentário explícito sobre isso no arquivo.

**Permissões:** Todo script deve ter bit executável. Usar:
```bash
git update-index --chmod=+x scripts/cluster-up.sh
# (repetir para cada script)
```

### Implementação: kustomization.yaml Stubs

**Padrão para `base/`:**
```yaml
# Kustomization base - keycloak-auth - cluster-kubernetes
# Recursos (postgres, keycloak) serão adicionados na Story 2.1 e 2.2
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources: []
```

**Padrão para `overlays/<ambiente>/`:**
```yaml
# Kustomization overlay local - keycloak-auth - cluster-kubernetes
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
```

Adaptar o comentário descritivo para cada componente (`namespaces`, `keycloak-auth`, `kong-gateway`, `network-policies`, `api-base-v1`) e cada ambiente (`local`, `homologacao`, `production`).

### Implementação: README.md (Atualização)

O README.md atual contém apenas `# cluster-kubernetes`. Expandir com:

1. Título + descrição de 1 parágrafo (plataforma GitOps local-produção com Kong e Keycloak)
2. **Pré-requisitos** (seção obrigatória pelo AC da Story 1.4, antecipado aqui):
   - Docker Desktop com ≥6GB RAM e ≥4 CPUs configurados
   - `kubectl` (qualquer versão recente)
   - `k3d` v5.x (`brew install k3d` ou binário em releases)
   - `make` (padrão na maioria dos sistemas Unix)
3. **Início rápido:** `make up`
4. **Comandos disponíveis** (tabela Markdown):
   | Comando | Descrição |
   |---------|-----------|
   | `make up` | Provisiona o cluster k3d completo |
   | `make down` | Destrói o cluster sem resíduos |
   | `make token` | Gera e exibe o token M2M de teste |
   | `make lint` | Valida todos os manifestos YAML |
   | `make status` | Exibe status dos componentes e URLs locais |
5. Link para `docs/contrato-do-desenvolvedor.md`
6. Link para `docs/bootstrap-emergencia.md`

### Implementação: Placeholders em docs/

**`docs/bootstrap-emergencia.md`** (esqueleto mínimo — Story 1.5 populará):
```markdown
# Guia de Bootstrap de Emergência - cluster-kubernetes

> Esqueleto inicial — Story 1.5 documenta a sequência com placeholders.
> Story 3.4 refina com comandos e nomes reais de Secrets.

## Sequência de Recuperação (Visão Geral)

1. Criar namespaces base
2. Injetar Secrets manualmente via `kubectl create secret`
3. Instalar ArgoCD
4. Aplicar `cluster/bootstrap/root-app.yaml` — ArgoCD assume via Sync Waves
```

**`docs/contrato-do-desenvolvedor.md`** (placeholder — Story 4.5 cria conteúdo):
```markdown
# Contrato do Desenvolvedor - cluster-kubernetes

> Documentação completa criada na Story 4.5.

Este documento define como publicar APIs na plataforma usando os Boilerplates YAML.
```

### Implementação: .github/workflows/lint.yml Placeholder

```yaml
# Pipeline de CI - Validação de manifestos YAML - cluster-kubernetes
# Implementação completa: Story 1.4
name: lint

on:
  push:
    branches: ["*"]
  pull_request:
    branches: ["main"]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Placeholder
        run: echo "[PLACEHOLDER] Linter configurado na Story 1.4"
```

### Padrões Arquiteturais Obrigatórios (Toda a Plataforma)

**Nomenclatura — sem exceções:**
- Todos os diretórios e recursos K8s: `kebab-case`
- Labels obrigatórios em qualquer recurso K8s:
  ```yaml
  labels:
    app.kubernetes.io/name: <nome-do-componente>
    app.kubernetes.io/component: <valor-controlado>
    app.kubernetes.io/part-of: cluster-kubernetes
  ```
- Vocabulário controlado para `app.kubernetes.io/component`:
  `api` | `database` | `identity-provider` | `gateway` | `worker`

**Formato YAML:**
- Indentação: **2 espaços** (proibido tabs ou 4 espaços)
- Todo arquivo YAML inicia com comentário descritivo em **pt-BR**
- Tags Docker: sempre imutáveis com versão explícita — **NUNCA `latest`**

**Sync Waves (referência — implementados a partir do Épico 2):**
| Wave | Componente |
|------|-----------|
| 0 | Namespaces e Secrets |
| 1 | PostgreSQL |
| 2 | Keycloak |
| 3 | Kong DB-Less |
| 4+ | Aplicações de negócio |

### Validação dos Critérios de Aceitação

```bash
# AC#1 — Verificar existência dos diretórios críticos
ls cluster/bootstrap/ cluster/infrastructure/ cluster/apps/ \
   cluster/boilerplates/ scripts/ docs/ .github/workflows/

# AC#1 + AC#3 — Verificar separação base/overlays em componentes de infra
ls cluster/infrastructure/keycloak-auth/base/
ls cluster/infrastructure/keycloak-auth/overlays/{local,homologacao,production}/
ls cluster/infrastructure/kong-gateway/base/
ls cluster/boilerplates/api-base-v1/base/

# AC#2 — Verificar k3d.yaml
grep -E "apiVersion|kind|name|servers|agents|traefik|servicelb|8080|8443" k3d.yaml

# AC#3 — Listar todos os kustomization.yaml criados
find cluster/infrastructure cluster/boilerplates -name "kustomization.yaml" | sort

# AC#4 — Verificar ausência de PascalCase/camelCase em diretórios
find cluster/ -type d | grep -E '[A-Z]'
# Deve retornar VAZIO
```

### Notas Técnicas Adicionais

- **`cluster/apps/` e `.gitkeep`:** O ArgoCD usa glob `cluster/apps/*` para descobrir subdiretórios de APIs. Um `.gitkeep` é um **arquivo**, não um diretório, então não interfere com a descoberta. É seguro usá-lo para garantir o rastreamento pelo Git.
- **`cluster/bootstrap/.gitkeep`:** Necessário pois o diretório ficará vazio até a Story 1.3.
- **Git não rastreia diretórios vazios:** Use `.gitkeep` em qualquer diretório que ainda não tenha conteúdo real mas precisa existir.
- **Dependência crítica:** Esta story é **pré-requisito** para todas as stories do Épico 1 (1.2–1.5) e transitivamente para todos os Épicos 2, 3 e 4. Implementar completamente antes de avançar.

### Project Structure Notes

- Alinhamento com `architecture.md` — Seção "Estrutura Completa de Diretórios"
- Desvio permitido: `namespaces/` e `network-policies/` não possuem overlays (arquitetura os define como globais)
- Nenhum conflito detectado com o estado atual do repositório (sem arquivos existentes nas novas localizações)

### Referências

- [architecture.md — Estrutura Completa de Diretórios](_bmad-output/planning-artifacts/architecture.md)
- [architecture.md — Padrões de Nomenclatura](_bmad-output/planning-artifacts/architecture.md)
- [architecture.md — Padrões de Formato YAML](_bmad-output/planning-artifacts/architecture.md)
- [architecture.md — Padrões de Processo (Sync Waves, Bootstrap)](_bmad-output/planning-artifacts/architecture.md)
- [architecture.md — Handoff de Implementação (Story 0 — Scaffold)](_bmad-output/planning-artifacts/architecture.md)
- [epics.md — Épico 1, Story 1.1](_bmad-output/planning-artifacts/epics.md)
- FRs cobertos (parcialmente): FR01 (fundação make up), FR20 (estrutura GitOps base), FR22 (estrutura docs/ para Secrets)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

Story context criada pelo BMad Create Story workflow. Análise exaustiva de: epics.md, prd.md, architecture.md, research técnico (k3d/Kong/Keycloak), estado atual do repositório (git log + ls). Esta é a story fundacional — cria apenas o esqueleto. Scripts e manifestos reais chegam nas stories 1.2–1.5 e Épicos 2–4.

**Implementação concluída em 2026-05-13:**
- Estrutura completa de 25 diretórios criada conforme architecture.md (todos kebab-case)
- `cluster/bootstrap/` e `cluster/apps/` com `.gitkeep` para rastreamento git
- `k3d.yaml` com apiVersion v1alpha5, traefik/servicelb desabilitados, portas 8080/8443 mapeadas
- `Makefile` com `up: lint` como dependência crítica para bloquear provisionamento com linter falho
- 5 scripts stub com `set -euo pipefail` e bit executável `100755` via `git update-index`
- `lint.sh` retorna `exit 0` explícito — pré-requisito para `make up` funcionar até Story 1.4
- 14 `kustomization.yaml` stubs criados (10 overlays + 4 bases); namespaces e network-policies sem overlays conforme arquitetura
- `README.md` expandido com pré-requisitos Docker Desktop, tabela de comandos e links para docs
- Todos os ACs validados: AC#1 ✓ AC#2 ✓ AC#3 ✓ AC#4 ✓

### File List

**Arquivos CRIADOS:**
- `k3d.yaml`
- `Makefile`
- `scripts/cluster-up.sh`
- `scripts/cluster-down.sh`
- `scripts/generate-token.sh`
- `scripts/lint.sh`
- `scripts/status.sh`
- `docs/bootstrap-emergencia.md`
- `docs/contrato-do-desenvolvedor.md`
- `.github/workflows/lint.yml`
- `cluster/bootstrap/.gitkeep`
- `cluster/infrastructure/namespaces/base/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/local/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/homologacao/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/overlays/production/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/base/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/local/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/homologacao/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/production/kustomization.yaml`
- `cluster/infrastructure/network-policies/base/kustomization.yaml`
- `cluster/apps/.gitkeep`
- `cluster/boilerplates/api-base-v1/base/kustomization.yaml`
- `cluster/boilerplates/api-base-v1/overlays/local/kustomization.yaml`
- `cluster/boilerplates/api-base-v1/overlays/homologacao/kustomization.yaml`
- `cluster/boilerplates/api-base-v1/overlays/production/kustomization.yaml`

**Arquivos ATUALIZADOS:**
- `README.md`

## Change Log

- 2026-05-13: Implementação completa da Story 1.1 — scaffold do repositório criado (26 arquivos novos, README.md atualizado). Estrutura de diretórios, k3d.yaml, Makefile, 5 scripts stub executáveis, 14 kustomization.yaml stubs, placeholders em docs/ e .github/workflows/lint.yml. Todos os ACs validados (AC#1, AC#2, AC#3, AC#4).

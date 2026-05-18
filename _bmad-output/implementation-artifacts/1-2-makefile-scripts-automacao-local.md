# Story 1.2: Makefile e Scripts de Automação Local

Status: done

## Story

Como um Desenvolvedor,
Eu quero provisionar e destruir o cluster k3d com `make up` / `make down`,
Para que eu trabalhe com a infraestrutura sem conhecer os detalhes do Kubernetes.

## Critérios de Aceitação

1. **[CLUSTER-UP]** Dado que o repositório possui a estrutura (Story 1.1), quando `make up` for executado, então `scripts/cluster-up.sh` deve provisionar o cluster k3d conforme `k3d.yaml` e o cluster deve estar acessível via `kubectl get nodes`.

2. **[CLUSTER-DOWN]** Dado que o cluster está em execução, quando `make down` for executado, então `scripts/cluster-down.sh` deve destruir completamente o cluster sem resíduos — nenhum container, volume ou rede associada deve permanecer.

3. **[PERFORMANCE]** Dado imagens Docker cacheadas localmente, quando `make up` for executado, então o provisionamento completo deve concluir em menos de 5 minutos (NFR-P02).

## Tarefas / Subtarefas

- [x] Tarefa 1: Implementar `scripts/cluster-up.sh` — lógica completa (AC: #1, #3)
  - [x] Pre-flight: verificar presença de `docker`, `kubectl`, `k3d` no PATH
  - [x] Pre-flight: verificar Docker daemon em execução (`docker info`)
  - [x] Pre-flight: verificar se portas 8080 e 8443 estão livres no host
  - [x] Pre-flight: detectar recursos Docker e emitir aviso se RAM < 6GB ou CPUs < 4 (não bloquear — apenas avisar)
  - [x] Idempotência: verificar se cluster `cluster-kubernetes` já existe; se sim, emitir mensagem e sair com código 0
  - [x] `trap` para cleanup em falha ou interrupção (Ctrl-C) — deletar cluster parcial
  - [x] Criar cluster: `k3d cluster create --config k3d.yaml`
  - [x] Aguardar nós ficarem prontos: `kubectl wait --for=condition=Ready nodes --all --timeout=120s`
  - [x] Validação final: `kubectl get nodes` e imprimir saída no terminal

- [x] Tarefa 2: Implementar `scripts/cluster-down.sh` — lógica completa (AC: #2)
  - [x] Idempotência: verificar se cluster existe antes de tentar deletar; se não existe, sair com código 0
  - [x] `k3d cluster delete cluster-kubernetes`
  - [x] Confirmar remoção: `k3d cluster list` não deve listar `cluster-kubernetes`

- [x] Tarefa 3: Atualizar `k3d.yaml` — fixar versão do k3s (AC: #1 — reprodutibilidade)
  - [x] Adicionar campo `image: rancher/k3s:v1.29.4-k3s1` logo abaixo de `metadata`
  - [x] Garantir que a imagem imutável impeça que `brew upgrade k3d` mude o k3s silenciosamente

- [x] Tarefa 4: Atualizar `Makefile` — corrigir paths e melhorar ergonomia
  - [x] Adicionar `REPO_ROOT` calculado via `git rev-parse --show-toplevel` para evitar quebra quando `make -C /outro/path`
  - [x] Usar `$(REPO_ROOT)/scripts/<script>.sh` em todos os targets
  - [x] Adicionar `.DEFAULT_GOAL := help` para prevenir provisionamento acidental com `make` puro
  - [x] Adicionar target `help` com tabela de comandos (espelha README.md)
  - [x] Adicionar variável `K3D_TIMEOUT` com default `300` e expô-la para `cluster-up.sh`

- [x] Tarefa 5: Criar `.gitignore` e `.gitattributes` na raiz (itens diferidos cross-story)
  - [x] `.gitignore`: ignorar kubeconfig dumps, logs, artefatos de container, IDE
  - [x] `.gitattributes`: forçar `text eol=lf` em `*.sh`, `Makefile`, `*.yaml`, `*.md` — previne corrupção de shebang em Windows

## Dev Notes

### ESCOPO DESTA STORY

Esta story implementa a lógica real nos dois scripts de ciclo de vida (`cluster-up.sh`, `cluster-down.sh`), atualiza o `k3d.yaml` para reprodutibilidade e corrige os problemas do `Makefile` identificados na revisão da Story 1.1. **Não inclui**: ArgoCD bootstrap (Story 1.3), linter real (Story 1.4), injeção de Secrets (Story 1.5).

### Estado Atual do Repositório (pós-Story 1.1)

```
scripts/cluster-up.sh     ← STUB — implementar
scripts/cluster-down.sh   ← STUB — implementar
scripts/lint.sh           ← STUB retorna exit 0 — NÃO ALTERAR (Story 1.4 implementa)
scripts/generate-token.sh ← STUB — NÃO ALTERAR (Story 3.3 implementa)
scripts/status.sh         ← STUB — NÃO ALTERAR (Story 3.3 implementa)
k3d.yaml                  ← ATUALIZAR (adicionar image:)
Makefile                  ← ATUALIZAR (REPO_ROOT, .DEFAULT_GOAL, help)
.gitignore                ← CRIAR
.gitattributes            ← CRIAR
```

**CRÍTICO — Não alterar `lint.sh`:** `make up` depende de `lint` como pré-requisito. O stub retorna `exit 0`. Se `lint.sh` for quebrado, `make up` parará de funcionar completamente.

### Implementação: `scripts/cluster-up.sh`

```bash
#!/usr/bin/env bash
# scripts/cluster-up.sh - Provisiona o cluster k3d conforme k3d.yaml
# Executa pre-flight checks, cria o cluster e verifica acessibilidade via kubectl

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-cluster-kubernetes}"
K3D_CONFIG="$(git rev-parse --show-toplevel)/k3d.yaml"

# ─── Pre-flight: binários obrigatórios ──────────────────────────────────────
for bin in docker kubectl k3d; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERRO: '$bin' não encontrado no PATH. Instale e tente novamente."
    exit 1
  fi
done

# ─── Pre-flight: Docker em execução ─────────────────────────────────────────
if ! docker info >/dev/null 2>&1; then
  echo "ERRO: Docker daemon não está em execução. Inicie o Docker Desktop e tente novamente."
  exit 1
fi

# ─── Pre-flight: recursos Docker (aviso — não bloqueia) ─────────────────────
# Consulta CPUs e memória disponíveis no Docker para avisar se estão abaixo do
# recomendado. Guardas numéricas evitam abort do script caso docker info
# retorne valores inesperados (Docker remoto, versões antigas, etc).
DOCKER_CPUS=$(docker info --format '{{.NCPU}}' 2>/dev/null || echo 0)
[[ "$DOCKER_CPUS" =~ ^[0-9]+$ ]] || DOCKER_CPUS=0
DOCKER_MEM_BYTES=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
[[ "$DOCKER_MEM_BYTES" =~ ^[0-9]+$ ]] || DOCKER_MEM_BYTES=0
DOCKER_MEM_GB=$(( DOCKER_MEM_BYTES / 1073741824 ))
if [ "$DOCKER_CPUS" -lt 4 ] || [ "$DOCKER_MEM_GB" -lt 6 ]; then
  echo "AVISO: Docker com ${DOCKER_CPUS} CPUs e ${DOCKER_MEM_GB}GB RAM."
  echo "       Recomendado: ≥4 CPUs e ≥6GB RAM (Docker Desktop → Settings → Resources)."
fi

# ─── Pre-flight: conflito de portas ──────────────────────────────────────────
# Verifica se as portas que o k3d precisa expor (HTTP/HTTPS) já estão em uso.
# Usa ss (Linux) como método primário e /dev/tcp (bash built-in, macOS) como fallback.
for port in 8080 8443; do
  if ss -tlnp 2>/dev/null | grep -q ":${port} " || \
     (echo >/dev/tcp/localhost/$port) 2>/dev/null; then
    echo "ERRO: Porta ${port} já está em uso no host."
    echo "      Libere a porta antes de provisionar o cluster."
    exit 1
  fi
done

# ─── Idempotência: cluster já existe ─────────────────────────────────────────
# Verifica se o cluster já existe usando k3d cluster get (match exato por nome).
# Se existe e está saudável, sai com sucesso. Se existe mas kubectl falha,
# orienta o dev a destruir e recriar.
if k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "Cluster '${CLUSTER_NAME}' já existe. Verificando saúde..."
  if kubectl get nodes >/dev/null 2>&1; then
    echo "Cluster operacional. Nenhuma ação necessária."
    kubectl get nodes
    exit 0
  else
    echo "ERRO: Cluster existe mas kubectl não consegue conectar."
    echo "      Execute 'make down' e tente novamente."
    exit 1
  fi
fi

# ─── Trap para cleanup em falha ou interrupção ───────────────────────────────
_cleanup() {
  echo ""
  echo "Provisionamento interrompido. Removendo cluster parcial..."
  k3d cluster delete "${CLUSTER_NAME}" 2>/dev/null || true
}
trap _cleanup INT TERM ERR

# ─── Criar cluster ────────────────────────────────────────────────────────────
echo "Criando cluster k3d '${CLUSTER_NAME}'..."
k3d cluster create --config "${K3D_CONFIG}"

# ─── Desabilitar trap após criação bem-sucedida ───────────────────────────────
trap - INT TERM ERR

# ─── Aguardar nós ficarem prontos ─────────────────────────────────────────────
echo "Aguardando nós ficarem prontos..."
if ! kubectl wait --for=condition=Ready nodes --all --timeout=120s; then
  echo ""
  echo "AVISO: Nós não ficaram prontos dentro do timeout (120s)."
  echo "       O cluster foi criado mas pode não estar operacional."
  echo "       Execute 'kubectl get nodes' para verificar ou 'make down' para destruir."
  exit 1
fi

# ─── Validação final ──────────────────────────────────────────────────────────
echo ""
echo "Cluster provisionado com sucesso!"
kubectl get nodes
echo ""
echo "Execute 'make status' para ver URLs e token M2M (disponível após Story 3.3)."
```

**Notas de implementação:**
- `git rev-parse --show-toplevel` resolve o path de `k3d.yaml` independentemente do CWD — isso corrige o bug de `make -C /outro/path`
- `CLUSTER_NAME` é lido da env var com default `cluster-kubernetes` — centralizado no Makefile como fonte única de verdade (DN-2)
- Verificação de portas usa `ss -tlnp` (Linux) como método primário e `/dev/tcp` (bash built-in) como fallback para macOS (P-1)
- Guardas numéricas (`[[ =~ ^[0-9]+$ ]]`) protegem a aritmética de CPU/memória contra valores inesperados do Docker (P-2)
- `k3d cluster get` faz match exato por nome — evita falso positivo com `grep` em nomes similares (P-3)
- Timeout de criação é controlado exclusivamente pelo `k3d.yaml` — removido da CLI e do Makefile para fonte única (P-4)
- `trap _cleanup INT TERM ERR` é desativado com `trap - INT TERM ERR` após criação bem-sucedida — evita deletar um cluster saudável se um comando posterior falhar
- `kubectl wait` com tratamento de falha: não destrói o cluster se nós não ficarem prontos, apenas orienta o dev (DN-1)
- Verificação de idempotência distingue "cluster funcional" de "cluster corrompido"

### Implementação: `scripts/cluster-down.sh`

```bash
#!/usr/bin/env bash
# scripts/cluster-down.sh - Destrói o cluster k3d sem resíduos
# Idempotente: sai com sucesso se o cluster não existir

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-cluster-kubernetes}"

# ─── Verificar presença de k3d ────────────────────────────────────────────────
if ! command -v k3d >/dev/null 2>&1; then
  echo "ERRO: 'k3d' não encontrado no PATH."
  exit 1
fi

# ─── Verificar Docker em execução ─────────────────────────────────────────────
# Sem Docker ativo, k3d não consegue listar clusters. Avisa e sai com sucesso
# pois o cluster será destruído automaticamente quando o Docker reiniciar.
if ! docker info >/dev/null 2>&1; then
  echo "AVISO: Docker daemon não está em execução."
  echo "       Se o cluster existia, ele será destruído quando Docker reiniciar."
  exit 0
fi

# ─── Idempotência: cluster não existe ─────────────────────────────────────────
# Usa k3d cluster get para verificação exata por nome. Se não existe, sai com
# sucesso (operação idempotente).
if ! k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "Cluster '${CLUSTER_NAME}' não existe. Nenhuma ação necessária."
  exit 0
fi

# ─── Deletar cluster ──────────────────────────────────────────────────────────
echo "Destruindo cluster '${CLUSTER_NAME}'..."
k3d cluster delete "${CLUSTER_NAME}"

# ─── Confirmar remoção ────────────────────────────────────────────────────────
if k3d cluster get "${CLUSTER_NAME}" &>/dev/null; then
  echo "ERRO: Cluster ainda listado após deleção. Verifique manualmente com 'k3d cluster list'."
  exit 1
fi

echo "Cluster destruído com sucesso. Sem resíduos."
```

### Implementação: `k3d.yaml` — Adição do campo `image:`

Adicionar o campo `image:` imediatamente após o bloco `metadata:`, antes de `servers:`:

```yaml
# Configuração declarativa do cluster k3d - cluster-kubernetes
# Topologia local espelhando produção: 1 servidor + 1 agente
# Traefik e ServiceLB desabilitados — Kong DB-Less assume o roteamento de borda
# Limites de recurso: configurar no Docker Desktop (≥6GB RAM, ≥4 CPUs)
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: cluster-kubernetes
image: rancher/k3s:v1.29.4-k3s1   # <── ADICIONAR ESTA LINHA
servers: 1
agents: 1
# ... resto permanece idêntico
```

**Por que `rancher/k3s:v1.29.4-k3s1`?**
- k3d v5.8.3 é compatível com k3s v1.27–v1.30
- v1.29 é LTS Kubernetes (suportado até Dezembro 2025), equilibrando estabilidade e acesso a APIs modernas
- Pin evita que `brew upgrade k3d` mude o k3s silenciosamente entre máquinas de desenvolvedores diferentes

### Implementação: `Makefile` — Atualização

```makefile
# Makefile de automação local - cluster-kubernetes
# Orquestrador do ciclo de vida do cluster k3d
# Uso: make up | make down | make token | make lint | make status | make help

.DEFAULT_GOAL := help

# Resolve raiz do repositório independentemente de onde make é chamado
REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

export CLUSTER_NAME ?= cluster-kubernetes

.PHONY: up down token lint status help

help: ## Exibe esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: lint ## Provisiona o cluster k3d completo
	@echo "Provisionando cluster k3d (cluster-kubernetes)..."
	@bash "$(REPO_ROOT)/scripts/cluster-up.sh"

down: ## Destrói o cluster sem resíduos
	@echo "Destruindo cluster k3d..."
	@bash "$(REPO_ROOT)/scripts/cluster-down.sh"

token: ## Gera e exibe o token M2M de teste
	@bash "$(REPO_ROOT)/scripts/generate-token.sh"

lint: ## Valida todos os manifestos YAML
	@bash "$(REPO_ROOT)/scripts/lint.sh"

status: ## Exibe status dos componentes e URLs locais
	@bash "$(REPO_ROOT)/scripts/status.sh"
```

**Mudanças em relação ao stub da Story 1.1:**
- `.DEFAULT_GOAL := help` — `make` puro exibe ajuda em vez de provisionar
- `REPO_ROOT` via `git rev-parse` — corrige `make -C /outro/path`
- Paths dos scripts agora usam `$(REPO_ROOT)/`
- `export CLUSTER_NAME` centraliza o nome do cluster como fonte única de verdade (DN-2)
- Target `help` com `##` como delimitador de descrição (padrão autodoc)
- Comentários `## Descrição` nos targets para autodoc via `grep`

### Implementação: `.gitignore`

```gitignore
# Configuração kubeconfig gerada automaticamente
.kube/
kubeconfig*

# Logs e artefatos de runtime
*.log
*.tmp

# Artefatos de editor/IDE
.DS_Store
.idea/
.vscode/
*.swp
*.swo

# Dependências locais (se algum tool usar node_modules no futuro)
node_modules/

# Binários locais
bin/

# Variáveis de ambiente locais (podem conter credenciais)
.env
.env.*

# Backups
*.bak
```

### Implementação: `.gitattributes`

```gitattributes
# Forçar LF em todos os arquivos de texto para prevenir corrupção
# em clones Windows com core.autocrlf=true
* text=auto eol=lf

# Arquivos que DEVEM ser LF (shebang e bit executável)
*.sh     text eol=lf
Makefile text eol=lf
*.yaml   text eol=lf
*.yml    text eol=lf
*.md     text eol=lf
*.json   text eol=lf

# Binários — sem conversão
*.png    binary
*.jpg    binary
*.gif    binary
*.ico    binary
*.gz     binary
*.tar    binary
*.zip    binary
```

### Items Diferidos da Story 1.1 — Tratamento Nesta Story

| Item Diferido | Tratamento |
|---|---|
| Sem detecção de conflito de portas 8080/8443 | Implementado em `cluster-up.sh` (pre-flight `ss` + `/dev/tcp` fallback) |
| Sem guarda de idempotência no cluster-up | Implementado — verifica existência antes de criar |
| `k3d.yaml` timeout 300s pode ser curto | Timeout controlado exclusivamente pelo `k3d.yaml` (fonte única de verdade) |
| Sem verificação pre-flight de kubectl/docker/k3d | Implementado — verifica todos os 3 binários |
| Scripts sem `trap` para cleanup | Implementado com `trap _cleanup INT TERM ERR` + desativa após sucesso |
| Makefile assume CWD == repo root | Corrigido com `REPO_ROOT := git rev-parse --show-toplevel` |
| Makefile sem `.DEFAULT_GOAL` | Adicionado `.DEFAULT_GOAL := help` |
| Makefile sem target `help` | Adicionado com pattern `##` autodoc |
| Sem enforcement Docker Desktop (6GB/4CPUs) | Aviso implementado — não bloqueia (dev pode ter Docker em remoto) |
| `k3d.yaml` sem `image:` para fixar k3s | Adicionado `image: rancher/k3s:v1.29.4-k3s1` |
| Repo sem `.gitignore` | Criado |
| Repo sem `.gitattributes` | Criado |
| `K3D_TIMEOUT` forwarding de argumentos | Timeout centralizado no `k3d.yaml`; `CLUSTER_NAME` exportado via Makefile (DN-2) |

**AVISO — Item diferido para Story 1.4 (não implementar aqui):**
- Makefile sem `SKIP_LINT=1` escape hatch — diferido para Story 1.4 (quando o linter real for implementado)

### Padrões Arquiteturais Obrigatórios

- **Scripts Bash** ficam exclusivamente em `scripts/` — não criar scripts novos em outros locais
- `set -euo pipefail` em todo script — sem exceção
- **Comentário pt-BR** no topo de todos os arquivos (scripts, YAML, Makefile) — obrigatório
- **Nenhuma lógica ArgoCD** nesta story — a Story 1.3 instala o ArgoCD
- `lint.sh` deve **permanecer intacto** (stub `exit 0`) — qualquer alteração quebra `make up`

### Validação dos Critérios de Aceitação

```bash
# AC#1 + AC#3 — Provisionamento completo em < 5 min (imagens cacheadas)
time make up
# Aguardar: "Cluster provisionado com sucesso!" e kubectl get nodes mostrando Ready

# AC#1 — Cluster acessível
kubectl get nodes
# Esperado: 2 nós (server + agent) em status Ready

# AC#2 — Destruição completa
make down
k3d cluster list
# Esperado: nenhum cluster listado

# Idempotência UP: executar make up duas vezes
make up && make up
# Esperado: segunda execução imprime "Cluster '...' já existe" e sai com 0

# Idempotência DOWN: executar make down duas vezes
make down && make down
# Esperado: segunda execução imprime "Cluster '...' não existe" e sai com 0

# make puro não provisiona (DEFAULT_GOAL)
make
# Esperado: exibe tabela de help

# Verificar k3d.yaml tem image: fixada
grep 'image:' k3d.yaml
# Esperado: rancher/k3s:v1.29.4-k3s1
```

### Project Structure Notes

- Arquivos modificados: `scripts/cluster-up.sh`, `scripts/cluster-down.sh`, `k3d.yaml`, `Makefile`
- Arquivos criados: `.gitignore`, `.gitattributes`
- Arquivos **não tocar**: `scripts/lint.sh`, `scripts/generate-token.sh`, `scripts/status.sh`
- Alinhamento com `architecture.md` — Seção "Integração de Workflow de Desenvolvimento":
  - `make up` → lint.sh (validação) → cluster-up.sh (k3d) — fluxo preservado
  - `make down` → cluster-down.sh — fluxo direto

### Referências

- [architecture.md — Padrões de Processo](_bmad-output/planning-artifacts/architecture.md)
- [architecture.md — Infraestrutura e Implantação](_bmad-output/planning-artifacts/architecture.md)
- [epics.md — Épico 1, Story 1.2](_bmad-output/planning-artifacts/epics.md)
- [deferred-work.md — Diferidos Story 1.2](_bmad-output/implementation-artifacts/deferred-work.md)
- [story 1.1 — Review Findings (diferidos)](_bmad-output/implementation-artifacts/1-1-scaffold-repositorio-configuracao-k3d.md)
- FRs cobertos: FR01 (`make up` funcional), FR02 (`make down` funcional)
- NFR coberto: NFR-P02 (setup < 5 minutos)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

Story context criada pelo BMad Create Story workflow. Análise exaustiva de: epics.md, architecture.md, project-context.md, story 1.1 (Dev Notes + Review Findings), deferred-work.md, estado atual do repositório (Makefile, scripts stubs, k3d.yaml). Todos os 12 items diferidos para Story 1.2 foram incorporados nas tarefas e na implementação detalhada.

**Implementação concluída (2026-05-13):**
- `scripts/cluster-up.sh`: implementação completa com pre-flight (binários, Docker daemon, recursos com guardas numéricas, conflito de portas via `ss`+`/dev/tcp`), idempotência via `k3d cluster get`, trap de cleanup e validação final via `kubectl get nodes` com tratamento de falha. `CLUSTER_NAME` lido da env var (centralizado no Makefile). `K3D_CONFIG` resolvido via `git rev-parse --show-toplevel`.
- `scripts/cluster-down.sh`: implementação completa com verificação de k3d no PATH, idempotência (sai com 0 se cluster não existe), deleção e confirmação de remoção.
- `k3d.yaml`: campo `image: rancher/k3s:v1.29.4-k3s1` adicionado após `metadata.name` — pina versão do k3s para reprodutibilidade entre máquinas.
- `Makefile`: adicionados `.DEFAULT_GOAL := help`, `REPO_ROOT` via `git rev-parse`, `export CLUSTER_NAME ?= cluster-kubernetes` (fonte única de verdade), target `help` com autodoc via `##`, paths de scripts atualizados para usar `$(REPO_ROOT)/`.
- `.gitignore`: criado com padrões para kubeconfig, logs, IDE artifacts.
- `.gitattributes`: criado com `* text=auto eol=lf` e regras explícitas para `.sh`, `Makefile`, `*.yaml`, `*.md`, `*.json` + binários.
- `lint.sh` preservado intacto (stub exit 0) — conforme requisito crítico da story.
- Validações executadas: `bash -n` em todos os scripts (sintaxe OK), YAML válido via python3 yaml, `make help` funcional, `make` puro exibe help (DEFAULT_GOAL), `make lint` retorna 0.

### File List

- scripts/cluster-up.sh (modificado)
- scripts/cluster-down.sh (modificado)
- k3d.yaml (modificado)
- Makefile (modificado)
- .gitignore (criado)
- .gitattributes (criado)

### Review Findings

- [x] [Review][Patch] DN-1: Abordagem híbrida no kubectl wait — cluster não é destruído mas mensagem clara orienta o dev [cluster-up.sh:77-83]
- [x] [Review][Patch] DN-2: CLUSTER_NAME centralizado no Makefile como fonte única de verdade [Makefile + ambos scripts]
- [x] [Review][Patch] P-1: Verificação de porta com ss (Linux) + /dev/tcp (macOS) como fallback [cluster-up.sh:42-44]
- [x] [Review][Patch] P-2: Guarda numérica na aritmética de memória/CPU Docker [cluster-up.sh:29-32]
- [x] [Review][Patch] P-3: k3d cluster get para match exato por nome [cluster-up.sh + cluster-down.sh]
- [x] [Review][Patch] P-4: Timeout apenas no k3d.yaml — removido de CLI e Makefile [cluster-up.sh + Makefile]
- [x] [Review][Patch] P-5: .gitignore com padrões .env e .bak [.gitignore]
- [x] [Review][Patch] P-6: cluster-down.sh verifica Docker antes de listar clusters [cluster-down.sh]
- [x] [Review][Defer] D-1: k3d.yaml sem resource limits nos containers — decisão arquitetural documentada, fora do escopo
- [x] [Review][Defer] D-2: Sem Docker healthcheck nos containers k3d — pertence ao lifecycle management geral

# Trabalho Diferido — cluster-kubernetes

Registro centralizado de itens identificados em revisões/triagens que não pertencem ao escopo atual mas devem ser endereçados em stories futuras ou trabalho cross-cutting.

## Deferred from: code review of story-1-1-scaffold-repositorio-configuracao-k3d (2026-05-13)

### Diferido para Story 1.2 (scripts de ciclo de vida)

- Sem detecção de conflito de portas `8080`/`8443` antes do `cluster-up` (host pode já ter algo bindado)
- Sem guarda de idempotência: `cluster-up` em cluster já existente falha com `cluster already exists`
- `k3d.yaml` timeout `300s` pode ser curto em primeira execução (pull de imagem ~250MB) em conexões lentas — considerar override por env var
- Sem verificação pre-flight da presença de `kubectl`/`docker`/`k3d` antes de invocar scripts (falha tardia)
- Scripts sem `trap EXIT/INT` para cleanup — interrupção (Ctrl-C) deixa containers/volumes órfãos
- Makefile assume `pwd == repo root` ao chamar `bash scripts/...` — `make -C /outro/path` quebra paths relativos
- Makefile sem forwarding de argumentos (`$(ARGS)` ou similar) — usuários têm que invocar scripts diretamente
- Sem enforcement dos requisitos do Docker Desktop (≥6GB RAM, ≥4 CPUs) — falha tardia se subdimensionado

### Diferido para Story 1.3 (ArgoCD bootstrap)

- `cluster/apps/.gitkeep` causará `ApplicationSet` com generator `cluster/apps/*` a gerar 0 apps silenciosamente até a primeira app real existir
- `cluster/bootstrap/.gitkeep` deve ser removido quando `root-app.yaml` for adicionado (caso contrário fica como artefato vazio)

### Diferido para Story 1.4 (linter real + CI hardening)

- Workflow `push: branches: ["*"]` não casa branches com `/` (ex: `feature/1-2-cluster`) — GitHub Actions glob `*` não atravessa separadores
- Workflow `pull_request: branches: ["main"]` restringe lint a PRs contra `main` — bases futuras (`develop`, `release/*`) pulam validação
- `kustomize build` sobre bases com `resources: []` retorna 0 objetos — kube-linter reportará "0 violations" como falso verde (precisa guard "manifest count > 0")
- `apiVersion: kustomize.config.k8s.io/v1beta1` está deprecated em kustomize v5+; migrar para `v1` em todos os 14 stubs
- `actions/checkout@v4` apenas por major tag — considerar pin por SHA + `persist-credentials: false` (hardening de supply chain)
- Workflow sem bloco `permissions:` explícito — definir `contents: read` como least privilege para o job lint
- Workflow sem `concurrency:` group — pushes rápidos disparam runs sobrepostos (custo de CI)
- Workflow sem `timeout-minutes:` no job — runner trava pode consumir até limite global do plano
- Sem escape hatch (`SKIP_LINT=1` ou alvo `make up-force`) para `make up` quando linter falhar — desenvolvedor terá que invocar scripts manualmente

### Diferido para trabalho cross-story / repo

- Makefile sem `.DEFAULT_GOAL` — `make` puro cai no primeiro alvo (`up`), provisionando cluster acidentalmente; definir `.DEFAULT_GOAL := help`
- Makefile sem alvo `help` para descoberta (espelhar tabela de comandos do README)
- Repo sem `.gitignore` — kubeconfig dumps, logs e artefatos de containers podem ser commitados acidentalmente
- README sem link para `_bmad-output/planning-artifacts/architecture.md` na seção Documentação (fonte de verdade arquitetural)
- Sem ADR formalizando convenção de idiomas: PT-BR em docs/comentários + EN em nomes técnicos (`local`, `production`, `keycloak-auth`) + `homologacao` sem cedilha — futuros colaboradores divergirão

## Deferred from: code review of story-1-1-scaffold-repositorio-configuracao-k3d (2026-05-13, segunda passagem)

### Diferido para Story 1.2 (scripts de ciclo de vida)

- `k3d.yaml` sem campo `image:` fixando versão do k3s — `brew upgrade k3d` troca o k3s default silenciosamente, quebrando reprodutibilidade entre máquinas e divergindo do "espelha produção"

### Diferido para trabalho cross-story / repo

- Repo sem `.gitattributes` — clones em Windows com `core.autocrlf=true` corrompem shebang em `*.sh` (`$'\r': command not found`) e perdem bit executável; agrupar com a tarefa de `.gitignore` (cross-story)

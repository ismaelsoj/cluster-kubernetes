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

## Deferred from: code review of story-1-2-makefile-scripts-automacao-local (2026-05-15)

### Diferido para trabalho cross-story / repo

- `k3d.yaml` sem resource limits (`memory`, `cpuCount`) definidos nos containers k3d — decisão arquitetural documentada ("configurar no Docker Desktop"), não é escopo dos scripts de automação
- Containers k3d sem Docker healthcheck definido — pertence ao lifecycle management geral do cluster, não aos scripts de ciclo de vida

## Deferred from: code review of 1-4-linter-yaml-pipeline-ci-readme (2026-05-18)

- Output vazio de `kustomize build` (exit 0, 0 bytes) é indistinguível de stub intencional — diretórios de stubs de infraestrutura por design produzem 0 manifestos; o guard de `total_manifests > 0` mitiga no agregado mas não reporta qual diretório falhou silenciosamente. Avaliar em story futura de hardening do lint.

## Deferred from: code review of 1-4-linter-yaml-pipeline-ci-readme (2026-05-18, segunda passagem)

- ~~**[policy/kebab-case.rego:21-23]** `is_exception` com colon-check excessivamente amplo — `contains(val, ":")` isenta qualquer nome com `:`~~ (Descartado: A política real no repositório já utiliza uma lista estrita de correspondência exata para `exceptions`, eliminando qualquer risco de validações amplas ou vulneráveis).
- ~~**[scripts/lint.sh:90-93, 112-115]** Docker fallback sensível ao diretório de chamada — `docker run --rm -v "$(pwd):/dir"` quebra se `lint.sh` for invocado fora da raiz do repositório.~~ (Implementado na Story 1.4 usando `$(git rev-parse --show-toplevel)` no volume)
- **[policy/kebab-case.rego:9]** `kebab_case_pattern` rejeita nomes com ponto — operadores externos como cert-manager geram recursos com `.` no nome (ex: `cert-manager.io`). Não afeta escopo atual mas causará falsos positivos quando operadores forem integrados. Adicionar mecanismo de exceções por prefixo/sufixo em story futura.
- ~~**[scripts/lint.sh:60]** Mensagem de erro pouco informativa quando diretórios de scan ausentes — se `cluster/bootstrap`, `cluster/infrastructure` e `cluster/apps` não existirem (clone raso, branch errado), `find` produz zero resultados silenciosamente e a mensagem de erro é genérica (`0 manifestos`).~~ (Implementado na Story 1.4 com loop de validação explícita de existência de diretórios obrigatórios no topo do script)
- ~~**[.github/workflows/lint.yml:20]** Instalar `conftest` nativamente no runner do GitHub Actions para otimizar o tempo de execução e evitar o pull da imagem Docker a cada pipeline run.~~ (Implementado a pedido do dev em PR-review)

## Deferred from: feature branch-tracking-work-tracker (2026-05-19)

### Diferido para melhoria futura do .tracker/work-tracker.py

- **Detached HEAD capturado como SHA de branch:** `build_branch_timeline` captura verbatim o alvo de cada checkout — em detached HEAD, o "nome de branch" é um SHA abreviado (ex: `a3f9c21`). O relatório exibirá o SHA como se fosse nome de branch. Adicionar pós-processamento: se o destino parecer um SHA (regex `^[0-9a-f]{7,40}$`), substituir por `"(detached HEAD)"`.
- **Tempo inter-ping em sessões com troca de branch:** quando uma sessão atravessa um checkout (ambos os pings pertencem a branches diferentes), o gap de duração entre eles é inteiramente atribuído à branch do ping anterior. A branch posterior recebe apenas suas próprias interações, sem a fração de tempo que lhe seria proporcional. Corrigir exigiria interpolar o timestamp exato do checkout dentro do gap.

## Deferred from: feature ferramenta-dimensao-relatorio (2026-05-19)

### Diferido para melhoria futura do .tracker/work-tracker.py

- **Sessões cruzando meia-noite:** `date_str = sess[0]["dt_br"].strftime(...)` atribui toda a sessão à data do primeiro evento. Sessões que cruzam meia-noite acumulam horas, sessões e interações do dia seguinte no dia anterior. Corrigir exigiria dividir a sessão no limite da meia-noite e distribuir a duração proporcionalmente.
- **Antigravity change events sem `active_model`:** eventos de tipo `is_change=True` do Antigravity não possuem o campo `active_model`. O filtro `is_ping` os mantém fora do loop de sessões, mas a ausência do campo é um risco de KeyError se o filtro mudar. Adicionar `active_model: None` nesses eventos na coleta ou reforçar a guarda no loop.
- **Inconsistência de padrão de guarda de tabelas vazias:** a Tabela 1 usa `for ... ; if not daily_stats:` (guarda após loop) enquanto a Tabela 2 usa `if branch_stats: for ... ; else:` (guarda antes). Ambas corretas hoje, mas o padrão divergente é armadilha de manutenção. Padronizar para o padrão `if/else` antes do loop.

## Deferred from: code review of spec-fix-antigravity-model-extraction-regex (2026-05-19)

### Diferido para melhoria futura do .tracker/work-tracker.py

- **Regex `(.*?)\.` em Pass 1/2 do Antigravity quebra com modelos cujo nome de exibição contém ponto:** payload `"to Gemini 3.1 Pro."` captura `"Gemini 3"` (truncamento no primeiro `.`). Pre-existente em Pass 2 antes desta spec, mantido no estado atual. Corrigir exigiria sentinela mais robusta (ex: `(.*?)(?:\.\s|\.$)` ou ancorar a um delimitador específico do payload da IDE).
- **`re.search` captura apenas o primeiro `<USER_SETTINGS_CHANGE>` por linha JSON:** se uma única entry contiver múltiplas trocas, somente a primeira é vista. Pre-existente. Migrar para `re.finditer` se necessário.
- **`-\d{8}\b` na normalização pode comer sufixos numéricos não-data legítimos:** ex. `model-12345678-beta` perde `-12345678`. Nenhum modelo dos dados atuais (Claude/Gemini) sofre — latente. Refinar para padrão de data real (`-20\d{6}\b`) se relevante no futuro.

## Deferred from: code review of 2-1-manifestos-kustomize-postgresql (2026-05-22)

- **Memory limit 256Mi para produção** — Overlays `homologacao` e `production` estão vazios; os limites da base (256Mi RAM / 500m CPU) são adequados para dev local mas insuficientes para carga real do Keycloak. Adicionar patches de recursos por ambiente em story futura de hardening dos overlays.
- **Overlays idênticos sem diferenciação por ambiente** — Todos os três overlays referenciam apenas a base, sem patches. Diferenciação (resources, replicas, storageClass) é escopo de stories futuras conforme ambientes forem definidos.
- **`infra-app` hardcoded para overlay `local`** — O ArgoCD aplica sempre o overlay local para todos os ambientes. Requer decisão de arquitetura sobre como selecionar overlay por ambiente no App-of-Apps.
- **Race condition: ArgoCD sync antes do Secret `keycloak-db-secret`** — Se o bootstrap falhar silenciosamente ao criar o Secret, o Deployment entra em `CreateContainerConfigError`. Mitigação estrutural (ExternalSecret ou InitContainer de guarda) pertence ao processo de bootstrap.
- **Dependência frágil namespace via Wave ordering** — `CreateNamespace=false` no `infra-app` + Wave 0 cria o namespace. Se Wave 0 falhar, Wave 1 falha sem mensagem clara. Endereçar em hardening do bootstrap.

## Deferred from: code review of 1-5-procedimento-secrets-documentacao-emergencia (2026-05-22)

### Diferido para melhoria de segurança de geração de senhas (Story 3.x ou cross-story)

- **[scripts/inject-secrets.sh:38, 50]** Fallback de geração de senha enfraquecido — quando openssl não está disponível, o fallback `od -vAn -N16 -tx1 /dev/urandom | ... | head -c 16` trunca bytes hex, resultando em ~64 bits de entropia vs. 128 bits do openssl. Afeta principalmente CI/CD em containers Alpine ou ambientes minimais. **Razão para defer:** AC atendido, funcionalidade OK. Melhoria de segurança, não bloqueador. Endereçar quando harmonizar geração de senhas com sistema de secrets centralizado (Story 3.4+).

## Deferred from: triagem de arquitetura e backlog (2026-05-25)

### Diferido para arquitetura futura do repositório (Monorepo)

- **Migração do `.tracker` para estrutura de Monorepo ou Repositório Isolado:** O rastreador de tempo (`.tracker`) vive dentro do repositório de infraestrutura de Kubernetes (`cluster-kubernetes`). Essa proximidade mistura os históricos de commit e polui as estatísticas de infraestrutura com commits e dados locais de tracking de trabalho. Planejar a separação física do tracker em um repositório próprio ou a reestruturação formal do repositório para um monorepo real com barreiras rígidas de escopo e CI/CD.

## Deferred from: code review of spec-rastreamento-de-tokens-claude-code (2026-05-25)

### Diferido para melhoria futura do .tracker/work-tracker.py

- **Sobrescrita de tokens no processamento do mesmo bloco de pings:** no parser de logs do Claude Code, cada evento de ping é adicionado a uma lista `pings`. Caso ocorra mais de um item do tipo `"assistant"` na mesma linha de logs, os campos de tokens do `ping` serão sobrescritos em vez de acumulados. Se os logs do Claude Code distribuírem o consumo do mesmo ping em múltiplas interações dentro do mesmo evento, isso causará subnotificação de tokens. [.tracker/work-tracker.py:149-156] — Razão para adiar: Escopo atendido, a estrutura atual atende as sessões registradas em dados reais no TDD. Endereçar em refatoração de estabilidade de logs.

---

## Deferred from: code review of spec-export-json-csv (2026-05-25)

### Diferido para melhoria futura do .tracker/work-tracker.py e test_tracker.py

- **`export_markdown_report` não usa escrita atômica (`.tmp`+`os.replace`):** A função abre `report_path` diretamente para escrita. Se o processo for interrompido, o arquivo `.md` fica truncado. Os novos exportadores JSON/CSV implementam atomicidade corretamente; inconsistência a corrigir em refatoração futura do .tracker. [`.tracker/work-tracker.py:~1020-1033`]
- **Race condition em chamadas concorrentes a `emit_events`:** Se dois processos exportam formatos diferentes em paralelo com o mesmo `masked_id`, ambos escrevem `dev-<id>.jsonl.tmp` simultaneamente. Improvável em uso normal de um dev local; endereçar se o tracker for usado em contextos de CI paralelo. [`.tracker/work-tracker.py:~1037,~1060`]
- **Ordenação não-determinística dos eventos na exportação JSON:** `load_all_events` usa `glob.glob` que retorna arquivos em ordem de inode (não garantida). O JSON exportado pode ter ordem diferente entre execuções, dificultando diffs. Pré-existente em `load_all_events`. [`.tracker/work-tracker.py:~1037-1045`]
- **Campo `total_sessions` vs `sessions` no schema `dev_summary`:** O evento `dev_summary` persiste `total_sessions` no JSONL, mas a spec nota "campo `sessions` para `dev_summary`". A lógica CSV compensa lendo `total_sessions`. Inconsistência de nomenclatura pré-existente no schema de eventos. [`.tracker/work-tracker.py:~1116`]
- **Permissões de arquivo não preservadas na substituição atômica:** `os.replace(tmp, dest)` não herda permissões do arquivo existente; o `.tmp` é criado com `umask` padrão. Sem impacto em uso local, mas relevante em repos compartilhados com permissões especiais.
- **Tokens de eventos legados: ambiguidade string vazia vs zero:** Eventos `activity_daily/branch` gerados antes de BKL-001 não possuem campos de token, resultando em células vazias no CSV. Eventos pós-BKL-001 terão `0` mesmo sem atividade. A distinção "sem dados" vs "zero" não está documentada no schema. [`.tracker/work-tracker.py:~1132`]

*Revisão/Code Review: Claude Sonnet 4.6 (claude-sonnet-4-6) via Claude Code — 2026-05-25*


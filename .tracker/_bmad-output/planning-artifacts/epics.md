---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - .tracker/BACKLOG.md
  - .tracker/project-context.md
  - .tracker/work-tracker-architecture.md
  - .tracker/specs/spec-tracker-orientado-a-eventos.md
  - .tracker/specs/spec-branch-tracking-work-tracker.md
  - .tracker/specs/spec-ferramenta-dimensao-relatorio.md
  - .tracker/specs/spec-fix-antigravity-model-extraction-regex.md
  - .tracker/specs/spec-tempo-total-desenvolvedores-e-branches.md
projectScope: ".tracker/ — Rastreador de Tempo Ativo (IA)"
parentProject: "cluster-kubernetes"
sourceBranch: "time-tracker"
backlogScope: "Itens abertos + bloqueados para planejamento; itens concluídos mantidos apenas no inventário histórico, sem épicos/histórias"
generatedAt: "2026-05-27 16:10:00-03:00"
authoringModel: "Claude Opus 4.7 (Cursor)"
---

# Rastreador de Tempo Ativo (IA) — Epic Breakdown

> **Subprojeto autocontido** vivendo em `.tracker/` dentro do repositório `cluster-kubernetes`.
> **Linguagem-alvo:** Python 3.x stdlib pura. **Interface:** GNU Make. **Saída:** Markdown + JSON + CSV + JSONL (eventos canônicos).
>
> Este documento decompõe os requisitos consolidados a partir de `BACKLOG.md`, dos 5 specs
> existentes e das ADRs do `work-tracker-architecture.md` em épicos orientados a valor de usuário
> (desenvolvedor/auditor) e histórias implementáveis pelo agente Dev.

## Overview

O Rastreador de Tempo Ativo (IA) é um micro-sistema analítico privado, offline, que minera os
logs locais de **Antigravity** e **Claude Code** e consolida métricas em tabelas Markdown
compartilhadas de forma anônima (SHA-256). O escopo coberto por este Epic Breakdown abrange:

1. **Histórico de entregas** — features já implementadas (FRs com status `✅ Concluído`) mantidas apenas para auditoria e rastreabilidade. **Não geram épicos nem histórias.**
2. **Roadmap ativo** — somente features, bugs e débito técnico ainda pendentes de implementação.
3. **Itens deferred** identificados em reviews adversariais que ainda não viraram BKL formal.
4. **Limitações upstream bloqueadas** — rastreadas em Parking Lot, sem histórias implementáveis até desbloqueio externo.

## Requirements Inventory

### Functional Requirements

> Cada FR representa uma capacidade entregável de valor ao desenvolvedor/auditor. Itens marcados
> `✅ Concluído` foram entregues por specs em `.tracker/specs/` e estão listados para auditoria.

**Funcionalidades já entregues (histórico — base para auditoria):**

- **FR1 — Rastreamento dinâmico de modelo LLM por turno (Claude Code) [✅ Concluído]:** o script extrai o campo `"model"` de cada turno dos JSONL em `~/.claude/projects/` de forma 100% determinística (ADR-05).
- **FR2 — Rastreamento dinâmico de modelo LLM por turno (Antigravity) [✅ Concluído]:** detecção de `<USER_SETTINGS_CHANGE>` em `transcript.jsonl` (`~/.gemini/antigravity-ide/brain/*/.system_generated/logs/`) com Pass 1 (modelo inicial) + Pass 2 (trocas subsequentes); coerção `content = data.get("content") or ""` (ADR-05, spec-fix-antigravity).
- **FR3 — Agrupamento por sessões ativas [✅ Concluído]:** gap máximo configurável (default 45 min via `--gap`), padding mínimo de 15 min para engajamento (ADR-02).
- **FR4 — Prevenção de dupla contagem por mesclagem global [✅ Concluído]:** concatenação cronológica global de todos os timestamps antes do agrupamento de sessão; alocação de ociosidade ao modelo da interação anterior; filtro anti-poluição de pings órfãos (ADR-03).
- **FR5 — Privacidade por mascaramento SHA-256 [✅ Concluído]:** identidade do dev mascarada como `dev-<hash8>` derivada de `usuario@hostname` (ADR-04).
- **FR6 — Propagação cronológica de estado de modelo [✅ Concluído]:** modelo de fábrica `Gemini 3.1 Pro (High)`; trocas via `<USER_SETTINGS_CHANGE>` propagam para sessões subsequentes (ADR-06).
- **FR7 — Relatório por dimensão Dia × Ferramenta × Modelo LLM [✅ Concluído]:** Tabela 1 do `TEMPO_DE_TRABALHO.md` com coluna `Ferramenta` (Claude Code ou Antigravity) entre `Dia` e `Modelo LLM`; seção de totais por ferramenta (spec-ferramenta-dimensao).
- **FR8 — Relatório por Branch / História [✅ Concluído]:** parsing de `.git/logs/HEAD` (reflog) para reconstruir timeline de checkouts; cada ping mapeado para branch ativa via `get_branch_at()`; Tabela 2 com `Dia × Branch × Ferramentas × Modelos × Tempo × Interações` (spec-branch-tracking).
- **FR9 — Consolidação multi-desenvolvedor [✅ Concluído]:** Resumo Geral no topo do `TEMPO_DE_TRABALHO.md` somando tempo total + tabela global por branch consolidada; blocos de outros devs preservados (imutabilidade) (spec-tempo-total-desenvolvedores).
- **FR10 — Saída de console agrupada por ferramenta [✅ Concluído]:** métricas formatadas com cores ANSI agrupadas por `[Ferramenta]` antes do total combinado (spec-ferramenta-dimensao).
- **FR11 — Arquitetura orientada a eventos com camada de dados JSONL [✅ Concluído — BKL-007 atendido]:** eventos `activity_daily`, `activity_branch`, `dev_summary` gravados em `.tracker/events/dev-<hash>.jsonl`; `TEMPO_DE_TRABALHO.md` passa a ser pura renderização (ADR-07, spec-tracker-orientado-a-eventos).
- **FR12 — Bootstrap one-shot de eventos legacy [✅ Concluído]:** `bootstrap_events.py` captura `TEMPO_DE_TRABALHO.md` legado como eventos `legacy: true` congelados; idempotente; modelos de Antigravity pré-migração rotulados `Indeterminado (pré-migração)` com `model_confidence: "indeterminado"` (ADR-07).
- **FR13 — Migração da fonte do Antigravity para `transcript.jsonl` [✅ Concluído — BKL-026 fechado]:** glob ajustado de `overview.txt` (truncado) para `transcript.jsonl` (sem truncamento, preserva `<USER_SETTINGS_CHANGE>`) (spec-tracker-orientado-a-eventos).
- **FR14 — Refactor de `main()` em funções puras composáveis [✅ Concluído — BKL-005 fechado]:** `collect_events()` → `merge_and_sort()` → `compute_sessions()` → `aggregate_stats()` → `render_report()` (spec-tracker-orientado-a-eventos).
- **FR15 — Suite de testes unitários [✅ Concluído — BKL-006 fechado]:** `scratch/test_tracker.py` cobrindo parsers, normalização, branch timeline, lógica de sessão (gap, padding, meia-noite), `aggregate_sessions`, filtro `legacy_boundary`, `emit_events`.
- **FR16 — Escrita atômica em `emit_events()` [✅ Concluído — BKL-027 fechado]:** escrita em arquivo temporário + `os.replace(tmp, file_path)` garantindo atomicidade no mesmo filesystem (code review 2026-05-21).
- **FR17 — Rastreamento de tokens do Claude Code [✅ Concluído — BKL-001 fechado, commit `1b952e6`]:** extração de `message.usage.{input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}` dos entries `assistant` em JSONL; agregação por modelo no relatório; formatadores `format_tokens_pt()` e `format_tokens_abbreviated()` para apresentação.
- **FR18 — Export estruturado JSON/CSV [✅ Concluído — BKL-003 fechado, commits `d678aa5` + `1399e04`]:** flags `--format json` e `--format csv` para exportar eventos consolidados em formato estruturado consumível por Pandas/Jupyter/planilhas; renderizadores dedicados `export_json_report()` e `export_csv_report()`; cobertura de testes para validação dos formatos.

**Funcionalidades pendentes (roadmap ativo):**

- **FR19 — Tendência temporal (Week-over-Week) [🔄 Aberto — BKL-008]:** sumário semanal/mensal com total de horas por janela + delta percentual. **Depende:** BKL-031 (modularização) recomendada antes.
- **FR20 — Estimativa de custo por modelo (USD) [🚫 Removido do escopo, 2026-05-27]:** decisão do produto: o tracker NÃO trabalhará com preços/custo. Preços variam entre plataformas, planos e contratos, gerando manutenção e ambiguidade indesejada. Tokens continuam sendo coletados (FR17) para outros usos analíticos, mas não serão multiplicados por tabela de preços.
- **FR21 — Versionamento do formato de relatório [🔄 Aberto — BKL-013]:** adicionar `format_version: N` no header do `TEMPO_DE_TRABALHO.md` para permitir migração programática futura.
- **FR22 — Detecção automática de anomalias [🔄 Aberto — BKL-019]:** flag automático para sessões < 5 min, interações sem tempo registrado, modelos com 0 sessões mas > 0 interações; ajuda a identificar outliers e context switching improdutivo. **Depende:** BKL-031 (modularização) recomendada antes.
- **FR23 — Métrica de tamanho de conversa [🔄 Aberto — BKL-020]:** rastrear turnos por sessão; diferenciar sessões exploratórias (muitos turnos curtos) de sessões produtivas (poucos turnos longos).

**Funcionalidade investigada e bloqueada:**

- **FR24 — Rastreamento de tokens do Antigravity [⛔ Inviável — BKL-002]:** logs `transcript.jsonl` e armazenamento binário `.pb` do Antigravity não expõem `usage` localmente. Ação acompanhada: monitorar atualizações da IDE; recomendar a inclusão do campo aos desenvolvedores do Antigravity.
- **FR25 — Cursor como terceira fonte de tempo ativo [🔄 Aberto — BKL-032]:** coletar atividade local do Cursor como fonte comparável a Claude Code e Antigravity, usando SQLite local (`~/.cursor/ai-tracking/ai-code-tracking.db`) em modo read-only, agrupamento por `conversationId/source/model` e enriquecimento opcional com métricas nativas (`v1/v2AiPercentage`, linhas tab/composer/human) sem redefinir o produto para code provenance analytics.

### NonFunctional Requirements

- **NFR1 — Zero dependências externas:** Python stdlib pura (`os`, `re`, `json`, `csv`, `glob`, `hashlib`, `socket`, `datetime`); GNU Make. Restrição absoluta — qualquer nova feature deve respeitar.
- **NFR2 — Operação 100% offline:** sem chamadas de rede; toda análise opera sobre logs locais.
- **NFR3 — Idempotência de execução:** rodar `--export` 2× consecutivas produz `TEMPO_DE_TRABALHO.md` idêntico (`diff` vazio).
- **NFR4 — Imutabilidade de blocos de outros desenvolvedores:** o bloco do dev local é substituído in-place via hash ID; blocos de outros devs nunca são alterados.
- **NFR5 — Fuso de Brasília GMT-3 em toda exibição:** hoje hardcoded; melhoria para `zoneinfo.ZoneInfo("America/Sao_Paulo")` para suporte a DST e múltiplos fusos. (BKL-014)
- **NFR6 — Type hints `mypy --strict` e logging estruturado:** substituir `try/except: pass` por logging estruturado para facilitar debugging. (BKL-021) **Recomendação do BACKLOG:** endereçar módulo a módulo após BKL-031.
- **NFR7 — Consistência de padrão de guarda de tabelas vazias:** Tabela 1 vs Tabela 2 usam padrões diferentes (`for…; if not:` vs `if: for…; else:`); padronizar. (BKL-024)
- **NFR8 — `normalize_model_name()` como lookup table:** 44 linhas de heurísticas dependentes de conhecimento prévio dos modelos. Migrar para lookup table + fallback determinístico para reduzir fragilidade. (BKL-015)
- **NFR9 — Segurança de paths:** caminhos de varredura ancorados em `os.path.expanduser`, sem travessia de diretório; logs purificados contra quebras de linha e caracteres não-JSON.
- **NFR10 — Anonimato em repositórios públicos:** identidade externa deve ser sempre `dev-<hash8>`; nenhum dado pessoal (user/host) deve vazar para o GitHub.
- **NFR11 — Seam Kafka pronto para evolução:** `emit_events()` é o único ponto de saída, projetado para receber um `KafkaEventSink` no futuro sem alterar o restante do pipeline (ADR-07).
- **NFR12 — Compatibilidade Linux/macOS:** validar em ambos os SOs; sem assumir GNU coreutils além do disponível no macOS.
- **NFR13 — Modularização em pacote Python `tracker/` [🔄 Aberto — BKL-031, Prioridade Alta]:** o script único atingiu 1203 linhas com 8 responsabilidades distintas. Migrar para estrutura modular: `tracker/{cli,models,utils,git_tracking,parsers/,events,sessions,renderers/}.py`. Regras: zero alteração de comportamento (move + import puro); `work-tracker.py` vira shim de 2 linhas; nenhum arquivo > 250 linhas; testes mantidos atualizando apenas imports. **Pré-requisito estrutural** para FR19 (BKL-008), FR22 (BKL-019), FR25 (BKL-032) e NFR6 (BKL-021). Estimativa: 3–4h migração + 1h imports nos testes.

### Additional Requirements

> Bugs identificados em code reviews, edge cases deferidos e débito técnico. Tratados aqui
> conforme classificação `c1` (separados de FR/NFR) escolhida na validação de pré-requisitos.

**Bugs ativos (Backlog) — 9 itens:**

- **BUG1 — Detached HEAD capturado como SHA de branch [🔄 BKL-010, Prioridade Média]:** `build_branch_timeline` registra verbatim o alvo de checkout; em detached HEAD o "nome" vira SHA abreviado. Correção: pós-processamento `if re.match(r'^[0-9a-f]{7,40}$', name): name = "(detached HEAD)"`.
- **BUG2 — Sessões cruzando meia-noite atribuídas ao dia do primeiro evento [🔄 BKL-011, Prioridade Média]:** `date_str = sess[0]["dt_br"].strftime(...)` atribui toda a sessão à data do primeiro evento; sessões 23:30 → 01:30 alocam horas do dia seguinte ao dia anterior. Correção: dividir a sessão no limite das 00:00 e distribuir proporcionalmente.
- **BUG3 — Gap entre ferramentas diferentes descartado silenciosamente [🔄 BKL-012, Prioridade Média]:** `if sess[i]["tool"] != sess[i+1]["tool"]: continue` (L628) perde o gap quando o dev alterna Antigravity → Claude Code → Antigravity. Tempo total reportado fica menor que o real. Correção: remover o guard de tool e atribuir o gap ao modelo do evento anterior, independentemente da ferramenta.
- **BUG4 — `to_brasilia()` ignora datetimes timezone-aware [🔄 BKL-016, Prioridade Baixa]:** `dt.replace(tzinfo=None)` descarta tzinfo antes da conversão; se `parse_iso()` retornar tz-aware, a subtração de 3h fica errada. Correção: usar `astimezone(BRT_TZ)` ou converter explicitamente.
- **BUG5 — Change events sem filtro `belongs_to_repo` [🔄 BKL-018, Prioridade Baixa]:** em `analyze_antigravity()`, eventos `is_change` (trocas de modelo) são emitidos sem filtro de repositório. Decisão arquitetural pendente: intencional (modelo é global) ou poluição de outros repos? Documentar e ajustar.
- **BUG6 — Inter-branch gap attribution incorreto [🔄 BKL-022, Prioridade Baixa]:** quando uma sessão atravessa um checkout, o gap entre pings de branches diferentes é inteiramente atribuído à branch anterior. Correção: dividir o gap proporcionalmente entre as branches.
- **BUG7 — Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON [🔄 BKL-023, Prioridade Baixa]:** `re.search` captura apenas a primeira ocorrência; trocas adicionais na mesma entry são silenciosamente descartadas. Correção: `re.findall` + iterar.
- **BUG8 — `get_branch_at()` retorna `"main"` vs spec diz `"Desconhecida"` [🔄 BKL-025, Prioridade Baixa]:** L247 e L255 retornam `"main"` como fallback quando o ping é anterior a qualquer checkout; a spec original (`spec-branch-tracking`) diz `"Desconhecida"`. Decidir qual é a verdade e alinhar.
- **BUG9 — `extract_repo_name()` é código morto [🔄 BKL-017, Prioridade Baixa, classificado como "Código morto"]:** função chamada (L343) mas `repo_name` não usado para filtragem (filtro real é `belongs_to_repo` com path matching). Candidato a remoção simples.

**Bugs concluídos (histórico — base para auditoria) — 5 itens:**

- **BUG10 — Regex `(.*?)\.` trunca nomes de modelo com ponto [✅ BKL-004]:** payload `"to Gemini 3.1 Pro."` era capturado como `"Gemini 3"`. Corrigido com regex `(?:\. No need|\.?\s*$)` (spec-fix-antigravity).
- **BUG11 — Antigravity truncava eventos de troca de modelo [✅ BKL-026]:** resolvido via migração para `transcript.jsonl` em `~/.gemini/antigravity-ide/brain/` (spec-tracker-orientado-a-eventos).
- **BUG12 — Escrita não-atômica em `emit_events()` [✅ BKL-027]:** corrigido por escrita em arquivo temporário + `os.replace()` (code review 2026-05-21).
- **BUG13 — `load_all_events()` sem try/except por linha [✅ BKL-028]:** corrigido com `try/except json.JSONDecodeError` no loop, alinhando-se ao padrão já adotado em `emit_events()`.
- **BUG14 — `last_updated_str` hardcoded como `"23:59:59"` [✅ BKL-029]:** corrigido renomeando o campo para `last_active_date` sem componente de hora hardcoded.

**Débito técnico ativo (não-mapeado em NFR):**

- **DEBT1 — `normalize_model_name()` como ponto de fragilidade [🔄 BKL-015]:** 44 linhas de heurísticas; migrar para lookup table + fallback. (Também rastreado como NFR8.)

**Edge cases deferidos em reviews (ainda não viraram BKL) — 6 itens:**

> Estes itens foram identificados em reviews adversariais dos specs mas não foram promovidos a BKL formal. Permanecem latentes para futura triagem.

- **DEFER1 — `model_confidence: "confirmado"` aplicado ao fallback de fábrica:** quando não há `USER_SETTINGS_CHANGE` no transcript, o fallback `"Gemini 3.1 Pro (High)"` é rotulado como `"confirmado"` embora seja inferido. Spec sugere novo nível `"inferido"` (deferred em spec-tracker-orientado-a-eventos).
- **DEFER2 — `dev-` prefix check sempre cai no branch else:** `if not masked_id.startswith("dev-")` é sempre False em `work-tracker.py:453` (verificado em 2026-05-27); branch `"dev-{masked_id}.jsonl"` nunca é executado. Pre-existente.
- **DEFER3 — Console report: subtotais por ferramenta podem divergir do total exibido:** `tool_model_totals` acumula horas legacy de `activity_daily` enquanto `total_combined_hours` usa `legacy_hours` do `dev_summary`; rounding pode diferir. Cosmético, sem impacto nos dados. Pre-existente.
- **DEFER4 — Ausência de warning quando path antigo do Antigravity existe mas o novo não:** UX improvement; não é crash. (deferred em spec-tracker-orientado-a-eventos)
- **DEFER5 — `parse_hours_from_str` com `group(2)` nunca alcançado:** dead code confuso (regex tem 1 grupo); funcionalmente idêntico ao original. Pre-existente.
- **DEFER6 — `-\d{8}\b` em `normalize_model_name` pode comer sufixos numéricos não-data legítimos:** entrada hipotética `model-12345678-beta` perderia `-12345678`. Nenhum modelo atual afetado, latente.

### UX Design Requirements

Não aplicável. O `.tracker/` é uma **CLI Python sem interface gráfica**; a "UX" se manifesta apenas em:

- Saída de console com cores ANSI agrupada por ferramenta (já implementada em FR10).
- Markdown estruturado do `TEMPO_DE_TRABALHO.md` (já implementado em FR7-FR9).
- Export estruturado em JSON/CSV (já implementado em FR18).
- Interface de comandos via Makefile (`make track-time`, `make bootstrap`).

Nenhum requisito UX-DR é extraído.

### FR Coverage Map

**Concluídos — inventário histórico, sem histórias no Step 3**

- **FR1-FR18:** já implementados e preservados no inventário para rastreabilidade. Não geram épicos, histórias ou ACs neste fluxo.

**Roadmap ativo — gera épicos e histórias**

- **FR19:** Epic 3 — Inteligência Analítica Fundamental (tendência temporal Week-over-Week).
- **FR20:** 🚫 Removido do escopo (decisão de produto, 2026-05-27). Não gera história.
- **FR21:** Epic 2 — Modularização Habilitadora e Contratos Evolutivos (versionamento do formato de relatório/dados).
- **FR22:** Epic 4 — Anomalias e Padrões de Conversa (detecção automática de anomalias).
- **FR23:** Epic 4 — Anomalias e Padrões de Conversa (tamanho da conversa / turnos por sessão).
- **FR24:** Epic 6 — Parking Lot de Limitações Upstream (tokens Antigravity bloqueados; sem história implementável até desbloqueio externo).
- **FR25:** Epic 5 — Cursor como Terceira Fonte de Tempo Ativo.

### NFR Coverage Map

- **NFR1, NFR2, NFR3, NFR4, NFR9, NFR10, NFR11, NFR12:** invariantes globais obrigatórios para todas as histórias novas (stdlib pura, offline, idempotência, imutabilidade, segurança de paths, anonimato, seam Kafka, compatibilidade Linux/macOS).
- **NFR5:** Epic 1 — Confiabilidade das Métricas (timezone e precisão temporal).
- **NFR6, NFR7, NFR8, NFR13:** Epic 2 — Modularização Habilitadora e Contratos Evolutivos (type hints/logging, guardas consistentes, lookup/fallback de modelos, pacote `tracker/`).

### Additional Requirements Coverage Map

- **BUG1-BUG8:** Epic 1 — Confiabilidade das Métricas (correções de precisão em branch, tempo, timezone, gaps, modelo e metadados).
- **BUG9:** Epic 2 — Modularização Habilitadora e Contratos Evolutivos (remoção de código morto durante migração estrutural).
- **BUG10-BUG14:** concluídos; inventário histórico sem histórias neste fluxo.
- **DEBT1:** Epic 2 — Modularização Habilitadora e Contratos Evolutivos.
- **DEFER1-DEFER6:** riscos latentes; só geram histórias se promovidos explicitamente durante o refinamento.

## Epic List

### Epic 1: Confiabilidade das Métricas
Usuários conseguem confiar nos números do tracker porque edge cases de tempo, timezone, branch, modelo e alternância entre ferramentas deixam de distorcer os totais.
**FRs covered:** Nenhum FR novo; cobre Additional Requirements BUG1-BUG8 e NFR5.
**User Outcome:** métricas atuais mais corretas antes de qualquer nova análise derivada.
**Implementation Notes:** executar antes de modularização/analytics; cada bug deve ter fixture com ground truth e teste de regressão.

### Epic 2: Modularização Habilitadora e Contratos Evolutivos
Desenvolvedores e agentes conseguem evoluir o tracker com fronteiras de módulo claras, testes menores e contratos versionados, sem alterar comportamento observável.
**FRs covered:** FR21
**User Outcome:** evolução mais barata e segura para novas fontes e analytics.
**Implementation Notes:** BKL-031 é pré-requisito explícito para Cursor e analytics; `work-tracker.py` vira shim; output bit-exact antes/depois; nenhum módulo novo deve ultrapassar 250 linhas.

### Epic 3: Inteligência Analítica Fundamental
Usuários conseguem responder perguntas de gestão sobre tendência de esforço a partir de dados confiáveis e já coletados.
**FRs covered:** FR19
**Fora do escopo:** FR20 — removido por decisão de produto (2026-05-27).
**User Outcome:** sair de “quanto tempo trabalhei?” para “como o esforço está evoluindo ao longo do tempo?”.
**Dependencies:** depende de Epic 1 (precisão) e Epic 2 (modularização).

### Epic 4: Anomalias e Padrões de Conversa
Usuários conseguem identificar outliers, context switching improdutivo e perfis de sessão por quantidade de turnos, sem confundir isso com métricas determinísticas de tendência temporal.
**FRs covered:** FR22, FR23
**User Outcome:** insights comportamentais sobre uso de IA, com limiares e heurísticas explícitas.
**Dependencies:** depende de Epic 1 e Epic 2; deve usar datasets/fixtures com expectativas numéricas fixadas.

### Epic 5: Cursor como Terceira Fonte de Tempo Ativo
Usuários conseguem incluir o Cursor como terceira fonte de atividade IA comparável a Claude Code e Antigravity, preservando métricas nativas do Cursor como enriquecimento opcional sem redefinir o produto para code provenance analytics.
**FRs covered:** FR25
**User Outcome:** visão unificada do tempo ativo com IA incluindo Cursor Composer/Tab, modelo usado e atividade por `conversationId`.
**Implementation Notes:** pós-BKL-031; `sqlite3` read-only; `schema_guard`; fixture Cursor.0 obrigatória; agrupar `ai_code_hashes` por `(conversationId, source, model)` e janela temporal para evitar inflar sessões; `scored_commits` enriquece, não substitui `.git/logs/HEAD`.

### Epic 6: Parking Lot de Limitações Upstream
Usuários e mantenedores têm rastreabilidade explícita de capacidades desejadas mas bloqueadas por fornecedores, sem manter épicos ativos eternamente incompletos.
**FRs covered:** FR24
**User Outcome:** limitação de tokens Antigravity (e futuramente Cursor, se aplicável) fica visível, monitorável e fora do caminho crítico.
**Implementation Notes:** reativar somente quando upstream expuser `usage` local confiável; até lá, documentar limitação e manter coleta por tempo ativo.


## Epic 1: Confiabilidade das Métricas

Usuários conseguem confiar nos números do tracker porque edge cases de tempo, timezone, branch, modelo e alternância entre ferramentas deixam de distorcer os totais.

**Requisitos cobertos:** BUG1, BUG2, BUG3, BUG4, BUG5, BUG6, BUG7, BUG8, NFR5
**Resultado esperado:** fixtures com ground truth + correções regressivas para precisão temporal, atribuição de branch/modelo e consistência de fuso.

### Story 1.1: Criar fixtures ground-truth para tempo, timezone e gaps

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG2, BUG3, BUG4, NFR5

As a maintainer do tracker,
I want fixtures determinísticas para cálculos de tempo, timezone e gaps,
So that correções de duração sejam validadas sem depender de logs locais reais ou interpretação manual.

**Acceptance Criteria:**

**Given** fixtures sintéticas versionadas em `.tracker/tests/fixtures/precision/time/`
**When** a suíte de testes do tracker for executada
**Then** deve haver expected explícito para sessões cruzando meia-noite, alternância entre ferramentas e datetimes timezone-aware
**And** cada fixture deve declarar entradas, saída esperada e bug coberto.

**Given** uma fixture de sessão cruzando meia-noite
**When** a agregação de sessões for testada
**Then** o expected deve demonstrar a distribuição correta entre os dois dias BRT.

**Given** uma fixture de alternância Antigravity → Claude Code → Antigravity
**When** a sessão for processada
**Then** o expected deve preservar o gap entre ferramentas em vez de descartá-lo.

**Given** uma fixture com timestamps ISO timezone-aware e naive
**When** `parse_iso()` e `to_brasilia()` forem exercitados em conjunto
**Then** o expected deve validar conversão correta sem descartar `tzinfo` antes da hora.

### Story 1.2: Criar fixtures ground-truth para branch e reflog

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG1, BUG6, BUG8

As a maintainer do tracker,
I want fixtures determinísticas para branch, reflog e checkouts durante sessões,
So that a atribuição de esforço por branch seja validada com ground truth explícito.

**Acceptance Criteria:**

**Given** fixtures sintéticas versionadas em `.tracker/tests/fixtures/precision/git/`
**When** a suíte de testes do tracker for executada
**Then** deve haver expected explícito para detached HEAD, ping anterior ao primeiro checkout e checkout entre pings.

**Given** uma entrada de reflog cujo destino de checkout é SHA abreviado ou completo
**When** `build_branch_timeline()` for testado
**Then** o expected deve usar `(detached HEAD)` como branch renderizada.

**Given** um ping anterior a qualquer entrada da timeline
**When** `get_branch_at()` for testado
**Then** o expected deve usar `Desconhecida` como fallback documentado.

**Given** uma sessão com checkout entre dois pings dentro do gap máximo
**When** `activity_branch` for testado
**Then** o expected deve explicitar a distribuição de tempo por branch usando a divisão do gap no timestamp exato do checkout.

### Story 1.3: Criar fixtures ground-truth para Antigravity e estado de modelo

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG5, BUG7

As a maintainer do tracker,
I want fixtures determinísticas para mudanças de modelo do Antigravity,
So that estado global de modelo e múltiplos `<USER_SETTINGS_CHANGE>` sejam testados sem depender de transcripts reais.

**Acceptance Criteria:**

**Given** fixtures sintéticas versionadas em `.tracker/tests/fixtures/precision/antigravity/`
**When** a suíte de testes do tracker for executada
**Then** deve haver expected explícito para múltiplas mudanças de modelo na mesma linha JSON e para change events sem evidência do repositório atual.

**Given** múltiplos `<USER_SETTINGS_CHANGE>` na mesma entrada `transcript.jsonl`
**When** `analyze_antigravity()` for testado
**Then** o expected deve preservar a ordem das mudanças válidas e propagar o último modelo válido.

**Given** um change event do Antigravity sem evidência de path do repositório atual
**When** o parser for testado
**Then** o expected deve tratar a mudança como estado global da IDE, conforme decisão deste épico.


### Story 1.4: Corrigir sessões cruzando meia-noite

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG2, NFR5

As a usuário do relatório de tempo,
I want sessões que atravessam a meia-noite divididas entre os dias corretos,
So that o total diário reflita quando o trabalho realmente aconteceu.

**Acceptance Criteria:**

**Given** uma sessão com eventos antes e depois de 00:00 no fuso de Brasília
**When** o tracker calcular `activity_daily`
**Then** as horas devem ser distribuídas entre as datas correspondentes
**And** nenhuma hora posterior à meia-noite deve ser atribuída ao dia anterior.

**Given** uma sessão que não cruza meia-noite
**When** o tracker calcular os totais diários
**Then** o resultado deve permanecer idêntico ao comportamento atual.

**Given** a fixture ground-truth de meia-noite da Story 1.1
**When** a suite de testes for executada
**Then** deve haver teste de regressão cobrindo a divisão no limite de 00:00 BRT.

### Story 1.5: Corrigir gap descartado entre ferramentas diferentes

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG3

As a usuário que alterna entre Claude Code e Antigravity,
I want o tracker contabilizando gaps dentro da mesma sessão mesmo quando a ferramenta muda,
So that o tempo ativo combinado não seja subestimado.

**Acceptance Criteria:**

**Given** dois eventos consecutivos dentro do gap máximo da sessão e com ferramentas diferentes
**When** o tracker calcular a duração da sessão
**Then** o gap entre os eventos deve ser contabilizado
**And** a duração deve ser atribuída ao modelo/ferramenta do evento anterior, conforme ADR-03.

**Given** dois eventos consecutivos fora do gap máximo configurado
**When** o tracker calcular sessões
**Then** eles devem continuar sendo sessões separadas.

**Given** a fixture de alternância entre ferramentas da Story 1.1
**When** a suite de testes for executada
**Then** o total de horas esperado deve incluir os gaps entre ferramentas.

### Story 1.6: Corrigir conversão de datetimes timezone-aware em `to_brasilia()`

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** BUG4, NFR5

As a maintainer do tracker,
I want `to_brasilia()` tratando datetimes timezone-aware corretamente,
So that timestamps com offset explícito não sejam convertidos com erro silencioso.

**Acceptance Criteria:**

**Given** um `datetime` timezone-aware com offset UTC ou outro fuso
**When** `to_brasilia()` for chamado
**Then** o horário deve ser convertido para `America/Sao_Paulo` ou offset BRT equivalente sem descartar `tzinfo` antes da conversão.

**Given** um `datetime` naive já tratado pelo fluxo atual
**When** `to_brasilia()` for chamado
**Then** a compatibilidade com o comportamento existente deve ser preservada ou documentada explicitamente no teste.

**Given** entradas ISO com e sem timezone
**When** `parse_iso()` e `to_brasilia()` forem exercitados em conjunto
**Then** a suite deve validar ambos os caminhos.

### Story 1.7: Corrigir detached HEAD capturado como SHA de branch

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** BUG1

As a usuário que trabalha temporariamente em detached HEAD,
I want o relatório exibindo `(detached HEAD)` em vez de um SHA como nome de branch,
So that a tabela por branch permaneça legível e semanticamente correta.

**Acceptance Criteria:**

**Given** uma entrada de reflog cujo destino de checkout é um SHA abreviado ou completo
**When** `build_branch_timeline()` processar a linha
**Then** o nome da branch registrado deve ser `(detached HEAD)`.

**Given** uma entrada de reflog cujo destino é uma branch válida
**When** `build_branch_timeline()` processar a linha
**Then** o nome da branch deve ser preservado sem alteração.

**Given** a fixture de detached HEAD da Story 1.2
**When** a tabela de branch for renderizada
**Then** nenhuma linha deve exibir SHA como branch ativa.

### Story 1.8: Alinhar fallback de `get_branch_at()` como `Desconhecida`

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** BUG8

As a maintainer do tracker,
I want o fallback de branch anterior ao primeiro checkout alinhado entre código, spec e testes,
So that futuras alterações não alternem silenciosamente entre `main` e `Desconhecida`.

**Acceptance Criteria:**

**Given** um ping anterior a qualquer entrada da timeline de checkout
**When** `get_branch_at()` for chamado
**Then** o retorno deve ser exatamente `Desconhecida`.

**Given** a documentação ou spec de branch tracking do `.tracker`
**When** a Story 1.8 for concluída
**Then** código, teste e documentação devem usar o mesmo literal `Desconhecida` para pings anteriores ao primeiro checkout.

**Given** timeline ausente ou vazia
**When** o tracker processar eventos
**Then** o fallback operacional deve ser documentado e testado separadamente, sem conflitar com o caso “ping anterior à timeline existente”.

### Story 1.9: Corrigir atribuição de gap entre branches

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG6

As a usuário que troca de branch durante uma sessão ativa,
I want o tempo entre pings próximos ao checkout atribuído de forma consistente,
So that o esforço por branch/história não seja distorcido.

**Acceptance Criteria:**

**Given** uma sessão com checkout entre dois pings dentro do gap máximo
**When** o tracker calcular `activity_branch`
**Then** o gap deve ser dividido no timestamp exato do checkout
**And** a parcela entre o ping anterior e o checkout deve ser atribuída à branch anterior
**And** a parcela entre o checkout e o ping posterior deve ser atribuída à branch posterior.

**Given** dois pings na mesma branch
**When** o tracker calcular `activity_branch`
**Then** o comportamento existente deve ser preservado.

**Given** a fixture de checkout entre pings da Story 1.2
**When** os testes forem executados
**Then** a distribuição esperada por branch deve bater com o ground truth.

### Story 1.10: Tratar múltiplos `<USER_SETTINGS_CHANGE>` na mesma linha JSON

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG7

As a usuário do Antigravity,
I want o tracker reconhecendo todas as trocas de modelo presentes em uma mesma linha JSON,
So that o modelo ativo propagado na linha do tempo não fique atrasado ou incorreto.

**Acceptance Criteria:**

**Given** uma linha `transcript.jsonl` com múltiplas ocorrências de `<USER_SETTINGS_CHANGE>`
**When** `analyze_antigravity()` processar a linha
**Then** todas as ocorrências devem ser avaliadas em ordem textual/cronológica determinística.

**Given** uma ocorrência cujo destino seja `None` ou inválido
**When** o parser processar as mudanças
**Then** ela deve ser ignorada conforme guarda existente, sem sobrescrever o modelo ativo com `None`.

**Given** a fixture de múltiplas mudanças da Story 1.3
**When** o parser for testado
**Then** o último modelo válido esperado deve ser propagado para os pings subsequentes.

### Story 1.11: Documentar change events do Antigravity como estado global da IDE

**Complexidade:** Média Complexidade
**Requisitos cobertos:** BUG5

As a maintainer do tracker,
I want uma decisão explícita sobre change events globais do Antigravity e o filtro `belongs_to_repo`,
So that o tracker não misture estado de modelo de outros repositórios sem intenção documentada.

**Acceptance Criteria:**

**Given** um `<USER_SETTINGS_CHANGE>` em transcript sem evidência de pertencer ao repositório atual
**When** `analyze_antigravity()` processar o evento
**Then** a mudança deve ser tratada como estado global da IDE para propagação de modelo.

**Given** pings do repositório atual após uma mudança global de modelo
**When** o modelo ativo for atribuído
**Then** o tracker deve aplicar o estado global mais recente do Antigravity de forma determinística.

**Given** risco de poluição entre repositórios
**When** a documentação for atualizada
**Then** ela deve explicar que modelo Antigravity é estado global da IDE, não propriedade do repo, e que apenas pings de atividade continuam filtrados pelo repositório quando houver evidência de path.

**Given** fixtures da Story 1.3 com mudança de modelo global e pings do repo atual
**When** a suíte de testes for executada
**Then** o modelo propagado deve bater com a decisão documentada.


## Epic 2: Modularização Habilitadora e Contratos Evolutivos

Desenvolvedores e agentes conseguem evoluir o tracker com fronteiras de módulo claras, testes menores e contratos versionados, sem alterar comportamento observável.

**Requisitos cobertos:** FR21, NFR6, NFR7, NFR8, NFR13, BUG9, DEBT1
**Resultado esperado:** `.tracker/work-tracker.py` vira shim; lógica migra para pacote `.tracker/tracker/`; outputs permanecem bit-exact salvo mudanças explicitamente versionadas; base preparada para Cursor e analytics.
**Dependencies:** Epic 1 concluído. Os goldens da Story 2.1 devem congelar o tracker já corrigido para BUG1-BUG8/NFR5, evitando transformar bugs conhecidos em contrato permanente.

**Acceptance Criteria obrigatórios para TODAS as histórias deste épico (cláusula transversal):**

**Given** os golden tests pré-modularização aprovados na Story 2.1
**When** qualquer história deste épico for finalizada (Story 2.2 em diante)
**Then** a suíte golden completa deve ser executada localmente
**And** o resultado deve ser 100% pass sem nenhuma diff em Markdown, JSON, CSV ou saída de console
**Or**, quando a história introduzir mudança intencional de output (ex.: Story 2.7 versionamento, Story 2.8 logging estruturado, Story 2.9 normalização), o expected da suíte golden deve ser atualizado no mesmo PR, com `format_version` incrementado quando aplicável e justificativa documentada no Change Log e na descrição da história.

**Given** outputs preservados bit-exact pelo objetivo da história
**When** uma diff inesperada for detectada
**Then** a história não pode ser marcada como concluída até a diff ser reconciliada ou explicitamente promovida a mudança versionada.

### Story 2.1: Congelar comportamento atual com golden tests pré-modularização

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR6, NFR7, NFR13

As a maintainer do tracker,
I want uma suíte golden pré-refactor cobrindo os outputs principais após o Epic 1,
So that a modularização possa mover código sem alterar comportamento observável já corrigido.

**Acceptance Criteria:**

**Given** fixtures determinísticas para eventos, sessões, relatório Markdown, JSON, CSV e console com Epic 1 já aplicado
**When** a suíte de testes for executada antes da modularização
**Then** ela deve registrar o comportamento atual como baseline aprovado
**And** os arquivos expected devem ser versionados junto ao projeto.

**Given** uma mudança posterior que altere output sem versionamento explícito
**When** os golden tests forem executados
**Then** a suíte deve falhar e apontar a diferença.

**Given** o requisito de stdlib pura
**When** os testes forem adicionados
**Then** nenhuma dependência externa deve ser introduzida.

**Given** a Story 2.1 concluída
**When** qualquer história subsequente do Epic 2 começar
**Then** ela deve usar esta suíte como porta de saída obrigatória, executando-a no fim do trabalho e exigindo 100% pass antes de marcar a história como concluída.

### Story 2.2: Criar pacote `tracker/` e transformar `work-tracker.py` em shim

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR13

As a developer agent,
I want um pacote Python `tracker/` com entrypoint estável,
So that o script atual possa ser mantido como compatibilidade enquanto a lógica real fica modularizada.

**Acceptance Criteria:**

**Given** a estrutura `.tracker/tracker/` criada
**When** `python3 .tracker/work-tracker.py` for executado
**Then** o comportamento deve ser idêntico ao baseline da Story 2.1
**And** `.tracker/work-tracker.py` deve conter apenas o shim necessário para chamar `tracker.cli.main()`.

**Given** o pacote modular criado
**When** `python3 -c "from tracker.cli import main"` for executado a partir de `.tracker/`
**Then** o import deve funcionar sem erro.

**Given** arquivos novos no pacote
**When** sua contagem de linhas for verificada
**Then** nenhum módulo novo deve ultrapassar 250 linhas.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.2 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass sem nenhuma diff em Markdown, JSON, CSV ou console; qualquer diff inesperada bloqueia a conclusão.

### Story 2.3: Extrair modelos de dados e utilitários compartilhados

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR6, NFR8, NFR13, DEBT1

As a maintainer do tracker,
I want tipos e utilitários compartilhados isolados em módulos próprios,
So that parsers, agregadores e renderers usem contratos explícitos em vez de dicionários dispersos.

**Acceptance Criteria:**

**Given** o pacote `tracker/`
**When** `models.py` e `utils.py` forem criados
**Then** estruturas como eventos, sessões, estatísticas diárias/branch e funções de parsing/formatação devem migrar para esses módulos sem alterar comportamento.

**Given** `normalize_model_name()` migrado para `utils.py`
**When** a suíte de testes existente for executada
**Then** todos os casos de normalização atuais devem continuar passando.

**Given** DEBT1 ainda pendente
**When** a função for movida
**Then** a história deve deixar ponto de extensão claro para lookup table + fallback em Story 2.9, sem alterar semântica nesta etapa.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.3 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass; nenhuma alteração comportamental de `normalize_model_name()` ou utilitários é permitida nesta história — apenas movimentação de código.

### Story 2.4: Extrair coletores e rastreamento Git para módulos dedicados

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR13, BUG9

As a developer agent,
I want coletores de fontes e rastreamento Git em módulos dedicados,
So that novas fontes como Cursor possam ser adicionadas sem editar um monólito de 1200 linhas.

**Acceptance Criteria:**

**Given** o pacote `tracker/`
**When** `parsers/claude_code.py`, `parsers/antigravity.py` e `git_tracking.py` forem criados
**Then** `analyze_claude_code()`, `analyze_antigravity()`, `build_branch_timeline()` e `get_branch_at()` devem migrar preservando comportamento.

**Given** `extract_repo_name()` não participa de filtragem efetiva
**When** o rastreamento Git for extraído
**Then** a função deve ser removida se realmente morta, ou documentada com uso real se ainda necessária.

**Given** os golden tests da Story 2.1
**When** os módulos forem extraídos
**Then** outputs Markdown/JSON/CSV/console devem permanecer bit-exact.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.4 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass; qualquer remoção/movimentação de `extract_repo_name()` deve preservar o output dos relatórios.

**Given** os parsers extraídos
**When** o pacote `tracker/parsers/` for finalizado
**Then** deve existir contrato explícito (protocolo Python ou docstring formal) `Collector` com `name`, `is_available() -> bool`, `collect(repo_path) -> Iterable[Event]` e `schema_version`
**And** `claude_code.py` e `antigravity.py` devem aderir ao contrato
**And** o contrato deve ser reutilizável pela Story 5.3 sem renegociação.

### Story 2.5: Extrair store de eventos e agregação de sessões

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR6, NFR7, NFR11, NFR13

As a maintainer do tracker,
I want persistência JSONL e cálculo de sessões em módulos isolados,
So that correções de precisão e novas métricas possam ser testadas sem acionar CLI/renderers.

**Acceptance Criteria:**

**Given** o pacote `tracker/`
**When** `events.py` e `sessions.py` forem criados
**Then** funções como `load_manifest()`, `emit_events()`, `load_all_events()`, `collect_events()`, `build_live_events()`, `compute_sessions()` e `aggregate_sessions()` devem migrar preservando comportamento.

**Given** eventos legacy e live existentes
**When** `emit_events()` for testado após a migração
**Then** eventos legacy devem continuar preservados e eventos live devem continuar substituídos atomicamente.

**Given** a suíte de testes de sessões
**When** os módulos forem extraídos
**Then** testes de gap, padding, branch e tokens devem continuar passando.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.5 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass; eventos legacy preservados e arquivo `dev-*.jsonl` resultante deve bater byte a byte com o baseline.

**Given** a extração de `events.py` e `sessions.py`
**When** o pacote modular for finalizado
**Then** `emit_events()` deve permanecer o único ponto de gravação em `dev-*.jsonl`
**And** nenhum outro módulo do pacote pode escrever diretamente nesses arquivos, preservando NFR11 e o seam para `KafkaEventSink` futuro
**And** um teste deve verificar essa invariante por inspeção estática simples ou AST.

### Story 2.6: Extrair renderers Markdown, console, JSON e CSV

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR7, NFR13

As a maintainer do tracker,
I want cada formato de saída em renderer próprio,
So that mudanças em Markdown, console, JSON ou CSV não contaminem os demais formatos.

**Acceptance Criteria:**

**Given** o pacote `tracker/renderers/`
**When** `markdown.py`, `console.py`, `json_export.py` e `csv_export.py` forem criados
**Then** cada formato deve manter output idêntico ao baseline da Story 2.1.

**Given** `--format markdown|json|csv` já existente
**When** a CLI for executada em cada formato
**Then** o renderer correto deve ser acionado e os arquivos esperados devem ser gerados.

**Given** tabelas ou datasets vazios
**When** cada renderer processar dados sem linhas
**Then** o padrão de guarda deve ser consistente e coberto por teste.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.6 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass para os quatro formatos (Markdown, JSON, CSV, console).

### Story 2.7: Adicionar versionamento explícito de formato de dados e relatório

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR21

As a consumidor dos relatórios do tracker,
I want um `format_version` explícito nos outputs,
So that mudanças futuras de schema/layout possam ser migradas programaticamente.

**Acceptance Criteria:**

**Given** a geração de `TEMPO_DE_TRABALHO.md`
**When** o relatório for renderizado
**Then** o header deve incluir o campo `format_version`.

**Given** os exports JSON e CSV
**When** os arquivos forem gerados
**Then** o versionamento deve aparecer de forma adequada ao formato sem quebrar consumidores atuais sem decisão explícita.

**Given** uma futura mudança incompatível
**When** o `format_version` for incrementado
**Then** a mudança deve ser rastreável no Change Log e nos testes de contrato.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.7 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** as únicas diffs permitidas são a introdução do campo `format_version` (e equivalentes em JSON/CSV) com expected da suíte golden atualizado no mesmo PR
**And** a atualização do expected deve ser justificada no Change Log do artefato.

**Given** o `format_version` introduzido
**When** a Story 2.7 for concluída
**Then** deve existir registry centralizado (`.tracker/docs/format-version-registry.md` ou seção equivalente em `work-tracker-architecture.md`) listando versão atual, data, descrição da mudança e story de origem
**And** esse registry deve ser a fonte canônica para histórias futuras que incrementem versão (3.3, 4.6, 5.6, 6.3).

### Story 2.8a: Introduzir logging estruturado nos módulos extraídos

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR6

As a maintainer do tracker,
I want logging estruturado nos módulos extraídos,
So that falhas de parsing fiquem diagnosticáveis sem mascarar erros relevantes.

**Acceptance Criteria:**

**Given** blocos `try/except: pass` remanescentes
**When** forem revisados nos módulos extraídos
**Then** exceções esperadas devem registrar aviso estruturado e continuar quando apropriado
**And** exceções inesperadas não devem ser silenciadas sem justificativa.

**Given** erros de parsing em uma fonte
**When** o tracker processar outras fontes
**Then** a falha isolada deve ser reportada e não derrubar o relatório inteiro, salvo erro fatal documentado.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.8a for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass; logging adicional vai para stderr/log e não deve poluir os outputs Markdown/JSON/CSV/console cobertos pelos goldens.

### Story 2.8b: Adicionar type hints incrementais nas APIs públicas dos módulos extraídos

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR6

As a maintainer do tracker,
I want type hints incrementais nas APIs públicas dos módulos extraídos,
So that regressões fiquem mais fáceis de detectar sem transformar a história em refatoração ampla.

**Acceptance Criteria:**

**Given** funções públicas dos módulos `tracker/`
**When** type hints forem adicionados
**Then** assinaturas principais devem declarar entradas e saídas sem introduzir dependências externas.

**Given** tipos compartilhados entre módulos
**When** type hints forem adicionados
**Then** `TypedDicts` e aliases existentes devem ser reutilizados antes de criar novas estruturas.

**Given** funções privadas ou helpers internos complexos
**When** a Story 2.8b for implementada
**Then** elas podem receber type hints quando ajudarem a estabilizar a API pública, mas não são escopo obrigatório.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.8b for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass.

### Story 2.9: Substituir normalização frágil de modelos por lookup table + fallback

**Complexidade:** Média Complexidade
**Requisitos cobertos:** NFR8, DEBT1

As a maintainer do tracker,
I want `normalize_model_name()` baseado em lookup table e fallback determinístico,
So that novos modelos não exijam mudanças heurísticas frágeis a cada lançamento.

**Acceptance Criteria:**

**Given** modelos conhecidos de Claude, Gemini, GPT e Cursor
**When** `normalize_model_name()` for chamada
**Then** a lookup table deve produzir os mesmos rótulos esperados pelos testes atuais.

**Given** um modelo desconhecido
**When** `normalize_model_name()` for chamada
**Then** o fallback deve preservar informação suficiente para relatório legível sem apagar versões, sufixos úteis ou pontos no nome.

**Given** o caso latente `model-12345678-beta`
**When** a normalização for testada
**Then** o sufixo numérico legítimo não deve ser removido por regra agressiva de data.

**Given** a Story 2.1 concluída e a suíte golden disponível
**When** a Story 2.9 for finalizada
**Then** a suíte golden completa deve ser executada como porta de saída obrigatória
**And** o resultado deve ser 100% pass para todos os modelos cobertos hoje; qualquer diff intencional em rótulos de modelos exige atualização do expected no mesmo PR com justificativa documentada.


## Epic 3: Inteligência Analítica Fundamental

Usuários conseguem responder perguntas de gestão sobre tendência de esforço a partir de dados confiáveis e já coletados.

**Requisitos cobertos:** FR19
**Fora do escopo:** FR20 — removido por decisão de produto (2026-05-27). Tokens continuam sendo coletados via FR17 para usos analíticos, mas não serão multiplicados por tabela monetária.
**Dependências:** Epic 1 (precisão das métricas), Epic 2 (modularização e contratos).
**Resultado esperado:** métricas determinísticas de tendência temporal em Markdown/JSON/CSV, com dataset de referência e sem dependência externa.

### Story 3.1: Criar dataset de referência para analytics determinístico

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR19, NFR1, NFR3

As a maintainer do tracker,
I want um dataset congelado com eventos, tokens e datas distribuídas em múltiplas semanas,
So that tendência temporal possa ser validada com expectativas numéricas fixas.

**Acceptance Criteria:**

**Given** fixtures versionadas em `.tracker/tests/fixtures/analytics/`
**When** a suíte de analytics for executada
**Then** deve haver expected explícito para horas por semana e delta percentual em múltiplas semanas.

**Given** o requisito de stdlib pura
**When** o dataset e testes forem adicionados
**Then** nenhuma dependência externa deve ser introduzida para calcular ou validar analytics.

**Given** os golden tests do Epic 2
**When** a Story 3.1 for finalizada
**Then** os outputs existentes devem permanecer 100% pass ou qualquer novo campo deve estar versionado e documentado.

### Story 3.2: Calcular tendência semanal de tempo ativo

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR19

As a usuário do tracker,
I want ver a tendência semanal de horas ativas,
So that eu consiga responder se o esforço com IA está aumentando, diminuindo ou estável.

**Acceptance Criteria:**

**Given** eventos `activity_daily` distribuídos em ao menos três semanas
**When** o agregador de tendência for executado
**Then** ele deve produzir total de horas por semana e delta percentual vs. semana anterior.

**Given** a primeira semana da série
**When** o delta for calculado
**Then** o valor deve ser exatamente `N/A`, sem divisão por zero.

**Given** uma semana anterior com zero horas
**When** houver horas na semana atual
**Then** o delta deve ser representado de forma explícita e testada, sem crash e sem infinito não tratado.

**Given** o dataset da Story 3.1
**When** a suíte for executada
**Then** os totais semanais e deltas devem bater com o expected.

### Story 3.3: Renderizar tendência temporal em Markdown, JSON e CSV

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR19, FR21

As a consumidor dos relatórios do tracker,
I want a tendência temporal disponível nos formatos existentes,
So that eu consiga revisar no Markdown e analisar programaticamente em JSON/CSV.

**Acceptance Criteria:**

**Given** a métrica de tendência semanal calculada
**When** `--format markdown` for usado
**Then** o relatório deve exibir uma seção de tendência com semana, horas e delta percentual.

**Given** a métrica de tendência semanal calculada
**When** `--format json` ou `--format csv` for usado
**Then** os dados de tendência devem ser exportados em campos/colunas versionados e documentados.

**Given** uma execução sem dados suficientes para tendência
**When** os renderers forem chamados
**Then** a seção deve exibir estado vazio consistente e não quebrar o relatório.

**Given** os golden tests do Epic 2
**When** a Story 3.3 alterar outputs
**Then** `format_version` deve ser incrementado quando aplicável e os expecteds devem ser atualizados no mesmo PR com justificativa no Change Log.


## Epic 4: Anomalias e Padrões de Conversa

Usuários conseguem identificar outliers, context switching improdutivo e perfis de sessão por quantidade de turnos, sem confundir isso com métricas determinísticas de tendência.

**Requisitos cobertos:** FR22, FR23
**Dependências:** Epic 1 (precisão das métricas), Epic 2 (modularização), Epic 3 opcional para reaproveitar datasets analíticos
**Prioridade:** revisar ao iniciar; este épico agrega mais valor após Epic 3 produzir dataset não-trivial e após feedback de uso real do relatório.
**Resultado esperado:** heurísticas documentadas para anomalias e métricas de turnos por sessão em Markdown/JSON/CSV, sempre com limiares explícitos e fixtures de validação.

### Story 4.1: Definir dataset e limiares de referência para anomalias

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR22, FR23, NFR3

As a maintainer do tracker,
I want datasets e limiares explícitos para anomalias e padrões de conversa,
So that insights heurísticos sejam testáveis e não dependam de interpretação subjetiva.

**Acceptance Criteria:**

**Given** fixtures versionadas em `.tracker/tests/fixtures/anomalies/`
**When** a suíte de anomalias for executada
**Then** deve haver expected explícito para sessões curtas, interações sem tempo, modelos com contagens inconsistentes e quantidade de turnos por sessão.

**Given** limiares como sessão curta, alto número de turnos ou baixa duração por turno
**When** os limiares forem definidos
**Then** cada valor deve estar documentado em constante/configuração local com justificativa curta.

**Given** uma mudança futura de limiar
**When** a suíte for atualizada
**Then** o Change Log do artefato deve explicar a mudança e atualizar os expecteds no mesmo PR.

### Story 4.2: Detectar sessões curtas e interações sem tempo registrado

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR22

As a usuário do tracker,
I want o relatório sinalizando sessões curtas e interações que não geraram tempo ativo,
So that eu consiga identificar ruído, sessões improdutivas ou falhas de coleta.

**Acceptance Criteria:**

**Given** uma sessão abaixo do limiar de duração definido na Story 4.1
**When** o detector de anomalias for executado
**Then** a sessão deve ser marcada como `short_session`.

**Given** interações registradas sem tempo ativo associado
**When** o detector de anomalias for executado
**Then** elas devem ser marcadas como `interaction_without_time`.

**Given** sessões normais acima do limiar
**When** o detector for executado
**Then** elas não devem ser marcadas como anomalias.

**Given** as fixtures da Story 4.1
**When** a suíte for executada
**Then** as anomalias detectadas devem bater exatamente com o expected.

### Story 4.3: Detectar inconsistências entre modelos, sessões e interações

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR22

As a usuário que audita o relatório,
I want inconsistências entre modelos, sessões e interações destacadas,
So that eu consiga investigar casos onde a coleta ou agregação parece incoerente.

**Acceptance Criteria:**

**Given** um modelo com zero sessões e mais de zero interações
**When** o detector de anomalias for executado
**Then** o caso deve ser marcado como `model_interactions_without_sessions`.

**Given** um modelo com sessões e interações consistentes
**When** o detector for executado
**Then** nenhuma anomalia deve ser emitida para esse modelo.

**Given** dados agregados por ferramenta e modelo
**When** inconsistências forem detectadas
**Then** a anomalia deve preservar contexto suficiente: data, ferramenta, modelo, sessões e interações.

**Given** as fixtures da Story 4.1
**When** a suíte for executada
**Then** cada inconsistência esperada deve aparecer uma única vez, sem duplicação entre renderers.

### Story 4.4: Rastrear turnos por sessão

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR23

As a usuário do tracker,
I want saber quantos turnos/interações existem em cada sessão,
So that eu consiga diferenciar sessões exploratórias de sessões produtivas com poucos turnos longos.

**Acceptance Criteria:**

**Given** uma sessão com múltiplos eventos de usuário/assistente coletados
**When** `compute_sessions()` ou agregador equivalente for executado
**Then** a sessão deve registrar `turn_count` derivado das interações.

**Given** sessões com ferramentas diferentes dentro do mesmo intervalo ativo
**When** turnos forem contabilizados
**Then** a contagem deve respeitar a mesma definição de sessão já corrigida no Epic 1.

**Given** eventos sem conteúdo relevante ou pings órfãos filtrados
**When** turnos por sessão forem calculados
**Then** esses eventos não devem inflar a métrica.

**Given** as fixtures da Story 4.1
**When** a suíte for executada
**Then** o número de turnos por sessão deve bater com o expected.

### Story 4.5: Classificar padrões de conversa por sessão

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR23

As a usuário que revisa hábitos de trabalho com IA,
I want sessões classificadas por padrão de conversa,
So that eu consiga distinguir exploração, execução focada e possível context switching.

**Acceptance Criteria:**

**Given** sessões com duração, turnos e ferramentas conhecidas
**When** o classificador de padrões for executado
**Then** cada sessão deve receber uma classificação documentada, como `exploratory`, `focused` ou `context_switching`, conforme limiares da Story 4.1.

**Given** dados insuficientes para classificar uma sessão
**When** o classificador for executado
**Then** a sessão deve receber estado `unclassified`, sem erro.

**Given** uma mudança de classificação futura
**When** os limiares forem alterados
**Then** os testes e documentação devem ser atualizados no mesmo PR.

### Story 4.6: Renderizar anomalias e padrões em Markdown, JSON e CSV

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR22, FR23, FR21

As a consumidor dos relatórios do tracker,
I want anomalias e padrões de conversa exportados nos formatos existentes,
So that eu possa revisar no Markdown e analisar programaticamente em JSON/CSV.

**Acceptance Criteria:**

**Given** anomalias detectadas e sessões classificadas
**When** `--format markdown` for usado
**Then** o relatório deve exibir seção de anomalias/padrões com rótulo, severidade quando aplicável, data, ferramenta/modelo e contexto mínimo para investigação.

**Given** anomalias detectadas e sessões classificadas
**When** `--format json` ou `--format csv` for usado
**Then** os dados devem ser exportados em campos/colunas versionados e documentados.

**Given** nenhuma anomalia detectada
**When** os renderers forem chamados
**Then** a seção deve exibir estado vazio consistente, sem sugerir falha de coleta.

**Given** os golden tests do Epic 2
**When** a Story 4.6 alterar outputs
**Then** `format_version` deve ser incrementado quando aplicável e os expecteds devem ser atualizados no mesmo PR com justificativa no Change Log.



## Epic 5: Cursor como Terceira Fonte de Tempo Ativo

Usuários conseguem incluir o Cursor como terceira fonte de atividade IA comparável a Claude Code e Antigravity, preservando métricas nativas do Cursor como enriquecimento opcional sem redefinir o produto para code provenance analytics.

**Requisitos cobertos:** FR25
**Dependências:** Epic 2 (modularização), NFR1, NFR2, NFR9, NFR10, NFR12
**Resultado esperado:** coletor Cursor read-only com schema guard, fixtures, agrupamento de atividade por `conversationId/source/model`, integração ao pipeline de eventos/sessões e renderização multi-formato.

### Story 5.1: Cursor.0 — Criar fixture ground-truth e snapshot de schema do Cursor

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25, NFR1, NFR2, NFR9

As a maintainer do tracker,
I want fixtures reais anonimizadas e snapshot do schema local do Cursor,
So that a integração seja testada sem tocar no banco real do usuário e sem depender de schema implícito.

**Acceptance Criteria:**

**Given** um snapshot anonimizado de `~/.cursor/ai-tracking/ai-code-tracking.db`
**When** a fixture for versionada em `.tracker/tests/fixtures/cursor/`
**Then** ela deve conter casos mínimos para `ai_code_hashes`, `scored_commits`, múltiplos `conversationId`, múltiplos modelos e pelo menos um commit com métricas nativas.

**Given** transcripts Cursor anonimizados
**When** forem adicionados à fixture
**Then** devem preservar estrutura suficiente (`role`, `message`) para testar correlação sem vazar conteúdo sensível.

**Given** o schema atual do SQLite do Cursor
**When** `schema_v_YYYY-MM-DD.sql` for gerado
**Then** o DDL esperado deve ser versionado para detectar drift upstream.

**Given** a fixture Cursor
**When** a suíte for executada
**Then** deve haver `expected.json` com sessões/eventos esperados, contagens de hashes, modelos, fontes e enrichment por commit
**And** o expected deve cobrir registros sem `conversationId`, registros sem `model` e registros sem evidência suficiente do repositório atual sendo descartados com warning estruturado.

### Story 5.2: Implementar leitura read-only e `schema_guard` para banco local do Cursor

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25, NFR2, NFR9

As a usuário do tracker,
I want o coletor Cursor lendo o banco local em modo read-only e validando o schema antes de processar,
So that o tracker não corrompa dados do Cursor nem quebre quando o schema upstream mudar.

**Acceptance Criteria:**

**Given** o caminho `~/.cursor/ai-tracking/ai-code-tracking.db`
**When** o coletor Cursor abrir o banco
**Then** a conexão deve usar SQLite URI em modo read-only com `mode=ro`.

**Given** as tabelas `ai_code_hashes` e `scored_commits`
**When** `schema_guard` for executado
**Then** ele deve validar as colunas mínimas esperadas antes da coleta.

**Given** uma coluna obrigatória ausente ou renomeada
**When** o coletor Cursor for executado
**Then** a fonte Cursor deve ser ignorada com warning estruturado
**And** Claude Code e Antigravity devem continuar processando normalmente.

**Given** a fixture com schema alterado
**When** a suíte for executada
**Then** o teste deve comprovar degradação graciosa sem crash global.

**Given** o banco `~/.cursor/ai-tracking/ai-code-tracking.db` potencialmente em uso pelo Cursor
**When** o coletor Cursor abrir o banco
**Then** deve copiar `*.db`, `*.db-wal` e `*.db-shm` para diretório temporário (`tempfile.mkdtemp()` + `shutil.copy2`), abrir o snapshot em modo read-only e limpar o diretório após a leitura
**And** não deve usar `immutable=1` em produção, para evitar ignorar escritas recentes ainda no WAL
**And** falhas de cópia devem desabilitar a fonte Cursor com warning estruturado, sem crash global.

### Story 5.3: Coletar eventos de atividade Cursor a partir de `ai_code_hashes`

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25

As a usuário que usa Cursor Composer/Tab,
I want o tracker reconhecendo atividade do Cursor por modelo, fonte e conversa,
So that o tempo ativo com Cursor apareça junto às demais ferramentas de IA.

**Acceptance Criteria:**

**Given** linhas em `ai_code_hashes` com `conversationId`, `source`, `model` e timestamp
**When** `analyze_cursor()` for executado
**Then** deve produzir eventos intermediários com ferramenta `Cursor`, fonte nativa (`composer`/`tab`), modelo e timestamp normalizado para Brasília.

**Given** linhas sem `conversationId` ou modelo
**When** o coletor processar os registros
**Then** deve descartar esses registros com warning estruturado, sem crash.

**Given** a fixture Cursor da Story 5.1
**When** a suíte for executada
**Then** eventos coletados devem bater com `expected.json`.

**Given** dados do Cursor fora do repositório atual
**When** o coletor for executado
**Then** apenas dados com evidência explícita de pertencimento ao workspace/repositório atual devem ser considerados
**And** evidência suficiente deve vir somente de `workspaceFolder`, `repoPath` ou path associado via `scored_commits`
**And** registros sem evidência suficiente devem ser descartados com warning estruturado.

### Story 5.4: Agrupar hashes Cursor em sessões comparáveis

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25

As a usuário do relatório consolidado,
I want múltiplos hashes gerados por uma mesma conversa Cursor agrupados em sessões comparáveis,
So that uma única interação de Composer não infle artificialmente a contagem de sessões/interações.

**Acceptance Criteria:**

**Given** múltiplos `ai_code_hashes` com mesmo `(conversationId, source, model)` dentro de uma janela curta (default: 60s, configurável)
**When** o coletor Cursor emitir eventos
**Then** deve emitir um único evento sintético por janela, com `hash_count` como metadado
**And** o evento deve seguir o mesmo formato dos demais eventos do pipeline, sendo agregado por `compute_sessions()` existente (FR3/FR4/ADR-02/ADR-03)
**And** Cursor não deve ter session builder paralelo ao pipeline global.

**Given** hashes do mesmo `conversationId` separados por gap maior que o limiar documentado
**When** o agrupamento for executado
**Then** eles devem formar sessões separadas.

**Given** hashes com modelos ou fontes diferentes
**When** o agrupamento for executado
**Then** a separação por modelo/fonte deve ser preservada.

**Given** a fixture Cursor da Story 5.1
**When** a suíte for executada
**Then** um caso com dezenas de hashes em poucos segundos deve resultar em uma sessão lógica, não dezenas de sessões.

### Story 5.5: Enriquecer eventos Cursor com métricas nativas de `scored_commits`

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25

As a usuário que quer contexto adicional do Cursor,
I want métricas nativas como `% AI` e linhas tab/composer/human preservadas quando disponíveis,
So that eu tenha enriquecimento útil sem tornar essas métricas obrigatórias para todos os coletores.

**Acceptance Criteria:**

**Given** commits presentes em `scored_commits`
**When** eventos Cursor forem enriquecidos
**Then** campos opcionais como `ai_percentage_native`, `lines_by_origin`, `cursor_scored` e `commit_context` devem ser preservados quando disponíveis.

**Given** um commit ausente em `scored_commits`
**When** o enriquecimento for executado
**Then** o evento deve continuar válido com `cursor_scored=false`, sem descartar atividade.

**Given** `.git/logs/HEAD` e `scored_commits.branchName`
**When** houver divergência de branch
**Then** `.git/logs/HEAD` deve permanecer fonte canônica para tempo ativo, enquanto `scored_commits` atua como enriquecimento documentado.

**Given** os dados enriquecidos
**When** forem agregados
**Then** métricas nativas do Cursor não devem ser somadas como equivalentes diretas de tokens ou turnos de Claude/Antigravity.

### Story 5.6: Integrar Cursor ao pipeline de eventos, export e CLI

**Complexidade:** Média Complexidade
**Requisitos cobertos:** FR25, FR21

As a usuário do tracker,
I want Cursor aparecendo nos mesmos comandos e relatórios das demais ferramentas,
So that eu tenha uma visão consolidada do uso de IA sem fluxo separado.

**Acceptance Criteria:**

**Given** o coletor Cursor implementado
**When** `make -f .tracker/Makefile track-time` ou CLI equivalente for executado
**Then** a saída deve incluir Cursor quando houver dados disponíveis, sem quebrar Claude Code e Antigravity.

**Given** `--format markdown`, `--format json` ou `--format csv`
**When** dados Cursor forem exportados
**Then** a ferramenta `Cursor` deve aparecer em campos/colunas compatíveis com os outros coletores
**And** métricas nativas opcionais devem aparecer em seção/campos próprios, sem redefinir totais de tempo.
**And** quando o formato expuser disponibilidade de tokens para Cursor, o valor deve ser `tokens_indisponiveis`.

**Given** ambiente sem Cursor instalado ou sem banco local
**When** o tracker for executado
**Then** o coletor Cursor deve ser ignorado com warning estruturado em stderr, sem crash.

**Given** alteração de output por adição de Cursor
**When** a suíte golden for executada
**Then** `format_version` deve ser incrementado quando aplicável e expecteds devem ser atualizados no mesmo PR.

### Story 5.7: Documentar limitações, privacidade e operação do coletor Cursor

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR25, NFR10, NFR12

As a usuário e mantenedor do tracker,
I want documentação clara sobre como o coletor Cursor funciona e quais dados ele lê,
So that eu entenda privacidade, limitações e manutenção futura antes de habilitar ou auditar a integração.

**Acceptance Criteria:**

**Given** o coletor Cursor implementado
**When** a documentação `.tracker/README.md` ou artefato equivalente for atualizada
**Then** deve explicar caminhos locais lidos, modo read-only, ausência de tokens, schema upstream volátil e métricas opcionais preservadas.

**Given** métricas nativas de `% AI` por commit
**When** a documentação descrevê-las
**Then** deve deixar claro que são enriquecimento opcional e não redefinem o produto para code provenance analytics.

**Given** preocupação de privacidade
**When** logs/exports forem descritos
**Then** deve ficar explícito que conteúdo sensível de transcripts não deve ser exportado e que identidade continua mascarada.

**Given** drift de schema upstream
**When** a documentação for lida
**Then** deve existir instrução de como coletar novo snapshot de schema e atualizar fixtures.



## Epic 6: Parking Lot de Limitações Upstream

Usuários e mantenedores têm rastreabilidade explícita de capacidades desejadas mas bloqueadas por fornecedores, sem manter épicos ativos eternamente incompletos. Este épico é documental, com um contrato de output para indisponibilidade de tokens; não é épico de implementação de coletor.

**Requisitos cobertos:** FR24
**Dependencies:** Stories 6.1 e 6.2 são documentais e podem rodar a qualquer momento; Story 6.3 depende de Epic 2 (Stories 2.6 e 2.7) e deve ser coordenada com Epic 5 para cobrir Cursor.
**Resultado esperado:** limitação de tokens Antigravity documentada como bloqueio upstream, com critério objetivo de reativação, contrato de output padronizado e sem implementação especulativa.

### Story 6.1: Registrar limitação upstream de tokens Antigravity como decisão de produto

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR24

As a maintainer do tracker,
I want a limitação de tokens do Antigravity registrada como decisão explícita,
So that o backlog não permaneça ambíguo sobre uma capacidade que não é implementável localmente hoje.

**Acceptance Criteria:**

**Given** os logs `transcript.jsonl` e armazenamento `.pb` do Antigravity sem campo local de `usage`
**When** a documentação do tracker for revisada
**Then** deve constar que tokens Antigravity são limitação upstream e não backlog implementável atual.

**Given** FR24 no `epics.md`
**When** o roadmap for lido
**Then** FR24 deve aparecer no Parking Lot, não em épico ativo de implementação.

**Given** usuários comparando Claude Code, Antigravity e Cursor
**When** lerem relatórios ou docs
**Then** deve ficar claro que ausência de tokens não significa `0` tokens nem falha de coleta de tempo ativo.

### Story 6.2: Definir gatilho de reativação para métricas bloqueadas por fornecedor

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR24

As a maintainer do tracker,
I want critérios objetivos para reativar itens bloqueados por fornecedor,
So that uma mudança futura no Antigravity ou Cursor possa virar história implementável sem rediscutir todo o escopo.

**Acceptance Criteria:**

**Given** uma versão futura do Antigravity expondo `usage` localmente
**When** o campo estiver disponível em JSONL, SQLite ou arquivo local legível com stdlib pura
**Then** FR24 pode ser reaberto como história implementável.

**Given** o campo exposto apenas via API remota, telemetry cloud ou formato binário não documentado
**When** a capacidade for avaliada
**Then** ela deve permanecer bloqueada, pois viola operação offline, stdlib pura ou baixa manutenção.

**Given** uma nova fonte IA com limitação semelhante
**When** ela for adicionada ao tracker
**Then** deve usar o mesmo padrão de Parking Lot: limitação documentada, gatilho explícito, sem implementação especulativa.

### Story 6.3: Padronizar notas de indisponibilidade de tokens por ferramenta

**Complexidade:** Baixa Complexidade
**Requisitos cobertos:** FR21, FR24, FR25

As a consumidor dos relatórios do tracker,
I want notas padronizadas quando uma ferramenta não expõe tokens,
So that eu não interprete ausência de tokens como `0` tokens ou erro silencioso.

**Acceptance Criteria:**

**Given** uma ferramenta sem tokens locais disponíveis (Antigravity ou Cursor)
**When** relatórios Markdown/JSON/CSV forem gerados
**Then** deve haver representação padronizada com o literal `tokens_indisponiveis`.

**Given** uma ferramenta com tokens disponíveis (Claude Code)
**When** relatórios forem gerados
**Then** tokens reais devem continuar aparecendo normalmente.

**Given** consumidores programáticos de JSON/CSV
**When** lerem o campo de disponibilidade
**Then** devem conseguir distinguir `0` para tokens reais coletados iguais a zero, `tokens_indisponiveis` para ferramenta sem tokens locais disponíveis e `null` para campo não aplicável.

**Given** mudança de output para padronizar a nota
**When** a suíte golden for atualizada
**Then** `format_version` deve ser incrementado quando aplicável e a mudança documentada no Change Log.


<!-- Épicos e histórias serão preenchidos nas etapas 2 e 3 -->

---

**Autoria/Implementação:** Claude Opus 4.7 (Cursor)
**Revisão:** GPT-5 (Codex)

## Change Log

| Data/Hora | Etapa | Descrição |
|-----------|-------|-----------|
| 2026-05-27 15:11:00-03:00 | Step 1 | Extração inicial de requisitos (branch incorreta): 24 FRs, 12 NFRs, 14 bugs, 1 débito, 6 deferreds. Fonte: BACKLOG.md + 5 specs + work-tracker-architecture.md. |
| 2026-05-27 15:25:00-03:00 | Step 1 | Verificação no código apontou FR17 e FR18 como abertos (premissa correta para a branch incorreta usada na extração). |
| 2026-05-27 15:31:00-03:00 | Step 1 | **Correção de branch (time-tracker) + re-extração completa.** Atualizações: (a) FR17/BKL-001 → ✅ Concluído (commit `1b952e6`); (b) FR18/BKL-003 → ✅ Concluído (`d678aa5` + `1399e04`); (c) BUG1 antigo (BKL-004 regex) → ✅ Concluído (renomeado para BUG10 no histórico); (d) BUG11 antigo (BKL-028) → ✅ Concluído (renomeado para BUG13); (e) BUG12 antigo (BKL-029) → ✅ Concluído (renomeado para BUG14); (f) **NFR13 NOVO (BKL-031)** — Modularização do script em pacote `tracker/`, prioridade alta, pré-requisito de FR19/FR20/FR22/NFR6. Totais: 24 FRs (18 concluídos + 5 abertos + 1 inviável), 13 NFRs, 14 bugs (9 ativos + 5 concluídos), 1 débito ativo, 6 deferreds. |
| 2026-05-27 16:07:00-03:00 | Step 2 | Lista de épicos aprovada após Party Mode e decisão de JTBD para Cursor: baselines históricos separados do roadmap ativo; sequência ativa definida como Confiabilidade das Métricas → Modularização Habilitadora → Inteligência Analítica Fundamental → Anomalias/Padrões → Cursor como terceira fonte de tempo ativo; FR24 movido para Parking Lot de limitações upstream. |
| 2026-05-27 16:10:00-03:00 | Step 2 | Ajuste solicitado pelo usuário: itens já concluídos permanecem apenas no inventário histórico e **não** geram épicos/histórias. Step 3 focará exclusivamente no que falta implementar: Epic 1-6 do roadmap ativo. FR25 adicionado para Cursor como terceira fonte de tempo ativo. |
| 2026-05-27 16:13:00-03:00 | Step 3 | Epic 1 detalhado com 9 histórias focadas apenas em itens pendentes de confiabilidade das métricas, cada uma com complexidade explícita e critérios de aceite testáveis. |
| 2026-05-27 16:15:00-03:00 | Step 3 | Epic 2 detalhado com 9 histórias de modularização, contratos evolutivos, versionamento, logging/type hints e normalização de modelos, preservando comportamento via golden tests. |
| 2026-05-27 16:19:00-03:00 | Step 3 | Reforço de regressão no Epic 2: cláusula transversal de AC obrigatória em todas as histórias do épico exige executar a suíte golden ao final e exigir 100% pass; mudanças intencionais de output só com atualização documentada do expected e `format_version` quando aplicável. |
| 2026-05-27 16:20:00-03:00 | Step 3 | Epic 3 detalhado com 6 histórias para analytics determinístico: dataset de referência, tendência semanal, renderização multi-formato, catálogo local de preços e custo estimado por modelo Claude Code. |
| 2026-05-27 16:22:00-03:00 | Step 3 | Decisão de produto: tracker NÃO trabalha com preços/custo. FR20 marcado como removido do escopo. Epic 3 re-escopado para apenas tendência temporal (3 histórias: dataset, cálculo semanal, renderização). Stories 3.4-3.6 (catálogo de preços, custo, renderização de custo) removidas. |
| 2026-05-27 16:24:00-03:00 | Step 3 | Epic 4 detalhado com 6 histórias para anomalias e padrões de conversa: dataset/limiares, sessões curtas, inconsistências modelo/sessão/interação, turnos por sessão, classificação de padrões e renderização multi-formato. |
| 2026-05-27 16:26:00-03:00 | Step 3 | Epic 5 detalhado com 7 histórias para Cursor como terceira fonte de tempo ativo: fixture/schema, leitura read-only com schema guard, coleta, agrupamento de hashes em sessões, enriquecimento opcional, integração CLI/export e documentação. |
| 2026-05-27 16:28:00-03:00 | Step 3 | Epic 6 detalhado com 3 histórias de Parking Lot: registrar limitação upstream de tokens Antigravity, definir gatilho de reativação e padronizar notas de indisponibilidade de tokens por ferramenta. |
| 2026-05-27 16:44:00-03:00 | Step 3 | Party Mode final aplicado: Story 1.1 dividida em 3 fixtures (tempo/git/Antigravity); decisões fixadas (`get_branch_at` = `Desconhecida`, change events Antigravity = estado global da IDE, Cursor emite eventos sintéticos); Story 2.1 depende do Epic 1 concluído; contratos `Collector`, `emit_events`/NFR11 e registry de `format_version` adicionados; Cursor read-only passa a usar snapshot SQLite com WAL/SHM; Epic 6 rebaixado para documental + contrato de output; Epic 4 marcado para revisão de prioridade ao iniciar. |
| 2026-05-27 16:44:30-03:00 | Step 3 | Step 3 concluído após ajustes finais do Party Mode. Documento pronto para validação final do Step 4. |
| 2026-05-27 16:46:00-03:00 | Step 4 | Validação final concluída: placeholders zerados, 39 histórias ativas, FR20 sem histórias por decisão de produto, requisitos ativos cobertos, lints sem erros. Workflow concluído. |
| 2026-05-27 22:54:37-03:00 | Correct Course | Sprint Change Proposal aprovado e aplicado: BKL-032 vinculado a FR25; Story 1.9 fixada com divisão pelo timestamp do checkout; Story 5.3 fixada com descarte e warning estruturado; Story 2.8 dividida em 2.8a/2.8b; literais canônicos de output fixados. |

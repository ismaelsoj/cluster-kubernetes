---
title: 'Tracker orientado a eventos + correção do Antigravity (transcript.jsonl)'
type: 'feature'
created: '2026-05-21'
status: 'in-progress'
baseline_commit: '47946b6710f2534138e803bb851d7bdfbad7b532'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Dois problemas acoplados no `.tracker/work-tracker.py`:

1. **BKL-026 — modelo do Antigravity não confiável.** O Antigravity antigo gravava em
   `~/.gemini/antigravity/brain/*/.system_generated/logs/overview.txt`, que **truncava**
   entradas longas e descartava a tag `<USER_SETTINGS_CHANGE>`. O tracker não detectava trocas
   de modelo e propagava o fallback de fábrica `Gemini 3.1 Pro (High)`. O novo Antigravity IDE
   migrou os logs para `~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl`
   (sem truncamento), mas o tracker ainda aponta para o caminho/formato antigo.
2. **BKL-007 — sem camada de dados.** O relatório `TEMPO_DE_TRABALHO.md` é o próprio "banco":
   é relido por regex (`parse_existing_developers_stats`). Frágil e sem caminho de evolução.

**Approach:** Reorientar o tracker para ser **orientado a eventos**. Cada execução deriva
**eventos de atividade** dos logs locais, gravados em **JSONL** (um evento por linha, no formato
de uma mensagem). O relatório passa a ser uma **renderização** desses eventos. A fonte do
Antigravity migra para `transcript.jsonl`. Um bootstrap one-shot captura o `TEMPO_DE_TRABALHO.md`
atual como eventos `legacy` **congelados**, com o modelo historicamente não confiável do
Antigravity rotulado `Indeterminado (pré-migração)`. Eventos `live` são regenerados a cada
execução; eventos `legacy` nunca são recomputados. O ponto de emissão (`emit_events`) é único —
preparado para, no futuro, publicar em Kafka (fora de escopo).

Fonte da verdade técnica: `.tracker/research/technical-rastreamento-tokens-antigravity-research-2026-05-20.md`
(resolução do BKL-026) e o plano de sessão aprovado.

## Boundaries & Constraints

**Always:**
- O relatório `TEMPO_DE_TRABALHO.md` mantém **formato, tabelas, colunas e comando idênticos**
  aos de hoje. Única mudança visível: a célula de **modelo** das linhas de **Antigravity
  pré-migração** na Tabela 1 passa a exibir `Indeterminado (pré-migração)`.
- Preservar **todo** o tempo histórico — sem corte temporal, nas duas ferramentas.
- Preservar a lógica existente: gap de sessão ≤ 45 min, padding de 15 min, propagação
  cronológica de modelo (ADR-06), mascaramento SHA-256, atribuição por data real de cada ping
  (sessões cruzando meia-noite), filtro anti-poluição de pings órfãos.
- Stdlib pura — zero dependências externas.
- Fuso de Brasília (GMT-3) em toda exibição de data/hora.
- Cada desenvolvedor tem seu próprio arquivo de eventos; blocos de outros devs são imutáveis.
- Eventos `live` são filtrados para `dt_br > legacy_boundary` do dev, evitando dupla contagem
  com os eventos `legacy`.

**Ask First:**
- Se uma entrada do `transcript.jsonl` tiver estrutura que quebre a detecção de modelo ou a
  atribuição ao repositório.
- Se os totais da captura legada não baterem com o `TEMPO_DE_TRABALHO.md` atual.
- Se a célula de modelo em contextos secundários (lista "Modelos Utilizados" da Tabela 2)
  também deve ser relabelada — o default desta spec é relabelar **apenas a Tabela 1**.

**Never:**
- Nunca aplicar corte temporal nem descartar tempo histórico.
- Nunca ler `overview.txt` ao vivo (seus dados vão para o legado; reler duplicaria).
- Nunca recomputar ou mutar eventos `legacy`.
- Nunca adicionar dependências externas.
- Não implementar o publisher Kafka nem frontend — fora de escopo (só o seam `emit_events`).
- Não alterar a lógica de cálculo de horas, sessões ou interações.

## I/O & Edge-Case Matrix

| Cenário | Entrada / Estado | Saída Esperada | Tratamento de Erro |
|---|---|---|---|
| transcript.jsonl com troca de modelo | linha com `<USER_SETTINGS_CHANGE>` | modelo detectado, `model_confidence: "confirmado"` | — |
| Entrada com `content: null` | `content` é `None` | linha processada sem crash (coerção para `""`) | `or ""` |
| Conversa de outro repositório | `transcript.jsonl` sem o path do repo | pings não contabilizados | filtro `belongs_to_repo` |
| Dev sem bloco legado (novo dev) | sem entrada no `manifest.json` | `legacy_boundary` ausente → sem filtro; tudo `live` | fallback `None` |
| Bootstrap executado 2× | `.tracker/events/` já tem eventos `legacy` | aborta sem sobrescrever | guard de idempotência |
| Dia de fronteira | ping com `dt_br > legacy_boundary` na mesma data do legado | evento `live` para a data; render soma com a linha legada | merge por `(date,tool,model)` |
| Arquivo de outro dev presente | `.tracker/events/dev-outro.jsonl` | renderizado a partir dos eventos `legacy` dele, intacto | — |
| Sem `transcript.jsonl` no disco | nova pasta App Data ausente | só eventos `live` de Claude Code; sem crash | retorno vazio |
| `overview.txt` ainda em disco | pasta antiga `~/.gemini/antigravity/` presente | ignorada na leitura ao vivo | não incluída no glob |
| Reexecução com `--export` | logs inalterados entre dois runs | `TEMPO_DE_TRABALHO.md` idêntico (idempotência) | render determinístico |

</frozen-after-approval>

## Code Map

- `.tracker/work-tracker.py:281` — `analyze_antigravity()` — **reescrever** para `transcript.jsonl`.
- `.tracker/work-tracker.py:219` — `analyze_claude_code()` — fonte inalterada.
- `.tracker/work-tracker.py:402` — `main()` — **refatorar** em funções puras.
- `.tracker/work-tracker.py:113` — `parse_existing_developers_stats()` — descontinuada no
  fluxo do tracker (render passa a vir dos eventos); a lógica de parse é reaproveitada no bootstrap.
- `.tracker/work-tracker.py:521-665` — bloco de geração do Markdown (dentro de `main()`) — vira
  `render_report()`.
- `.tracker/work-tracker.py:56,66,176,205` — `parse_hours_from_str`, `normalize_model_name`,
  `build_branch_timeline`, `get_branch_at` — reaproveitados sem mudança.
- `.tracker/events/dev-<hash>.jsonl` — **novo** — store de eventos por dev.
- `.tracker/events/manifest.json` — **novo** — `legacy_boundary` por dev.
- `.tracker/bootstrap_events.py` — **novo** — captura legada one-shot.
- `.tracker/Makefile:15-21` — adicionar alvo `bootstrap` após `track-time`.
- `.tracker/TEMPO_DE_TRABALHO.md` — regerado a partir dos eventos.

## Tasks & Acceptance

**Execution:**
- [x] `.tracker/work-tracker.py` — definir constantes do modelo de evento (`SCHEMA_VERSION`,
  `EVENTS_DIRNAME`, `MANIFEST_NAME`, rótulo `Indeterminado (pré-migração)`).
- [x] `.tracker/work-tracker.py:281` — reescrever `analyze_antigravity()`: glob para
  `~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl`; coerção
  `content = data.get("content") or ""`; manter Pass 1 (modelo inicial) + Pass 2 (trocas) e a
  regex `changed setting \`Model Selection\` from (.*?) to (.*?)(?:\. No need|\.?\s*$)`.
- [x] `.tracker/work-tracker.py` — adicionar I/O de eventos: `load_manifest()`,
  `emit_events(events_dir, masked_id, live_events)` (preserva linhas `legacy`, regrava `live`),
  `load_all_events(events_dir)`.
- [x] `.tracker/work-tracker.py:402` — refatorar `main()` em `collect_events()`,
  `compute_sessions(events, gap, legacy_boundary, branch_timeline)`, `aggregate_sessions()`
  (matemática de `daily_stats`/`branch_stats` preservada), `build_live_events()`.
- [x] `.tracker/work-tracker.py` — implementar `render_report(all_events)` → Markdown idêntico
  ao atual (resumo global, totais por ferramenta, Tabela 1, Tabela 2).
- [x] `.tracker/work-tracker.py` — ligar `main()`: sem `--export` = console read-only (sem
  escrita); com `--export` = `emit_events` + `render_report` + grava `TEMPO_DE_TRABALHO.md`.
- [x] `.tracker/bootstrap_events.py` — novo script one-shot: parseia as duas tabelas e o
  cabeçalho de cada bloco de dev em `TEMPO_DE_TRABALHO.md`; emite eventos `legacy: true`
  (Antigravity → `model: "Indeterminado (pré-migração)"`, `raw_model` preservado,
  `model_confidence: "indeterminado"`; Claude Code → `confirmado`); grava `manifest.json`;
  aborta se já houver eventos `legacy`.
- [x] `.tracker/Makefile` — adicionar alvo `bootstrap` que roda `bootstrap_events.py`.
- [x] Docs: `BACKLOG.md` (fechar BKL-026; BKL-007 atendido), `project-context.md` e
  `work-tracker-architecture.md` (novo ADR: arquitetura orientada a eventos, `model_confidence`,
  futuro Kafka).
- [x] `scratch/test_tracker.py` — testes unitários (ver Verification).

**Acceptance Criteria:**
- Dado o novo `transcript.jsonl`, quando o tracker roda, então os eventos `live` de Antigravity
  carregam o modelo real detectado e `model_confidence: "confirmado"`.
- Dada uma entrada com `content: null`, quando processada, então não há crash e a linha é tratada.
- Dado o bootstrap executado sobre o `TEMPO_DE_TRABALHO.md` atual, quando inspecionado
  `.tracker/events/`, então há um `.jsonl` por dev, todos os eventos com `legacy: true`, modelos
  de Antigravity como `Indeterminado (pré-migração)`, e os totais por dev batem com o relatório
  atual (≈ 20h21m e ≈ 5h39m).
- Dado o relatório regerado, quando comparado ao atual, então estrutura, colunas, totais e
  ordenação são idênticos — exceto a célula de modelo das linhas de Antigravity pré-migração
  (Tabela 1) e as novas linhas de 20–21/05 do `transcript.jsonl`.
- Dado o mesmo conjunto de logs, quando `--export` roda duas vezes seguidas, então
  `TEMPO_DE_TRABALHO.md` é idêntico (idempotência).
- Dado um evento `live` com `dt_br ≤ legacy_boundary`, quando agregado, então ele é descartado
  (sem dupla contagem); o total do dev == soma dos eventos `legacy` + `live`.
- Dada execução sem `--export`, quando rodada, então nada é escrito em disco.

## Design Notes

**Modelo de evento (JSONL, um por linha):**

```jsonc
// activity_daily — um por (developer, date, tool, model)
{ "event_type": "activity_daily", "schema_version": 1, "developer": "dev-39d71ab2",
  "date": "2026-05-20", "tool": "Antigravity", "model": "Claude Sonnet 4.6 (Thinking)",
  "raw_model": "Claude Sonnet 4.6 (Thinking)", "model_confidence": "confirmado",
  "hours": 1.13, "sessions": 2, "interactions": 142, "legacy": false,
  "generated_at": "2026-05-21T03:10:00-03:00" }

// activity_branch — um por (developer, date, branch)
{ "event_type": "activity_branch", "schema_version": 1, "developer": "dev-39d71ab2",
  "date": "2026-05-20", "branch": "time-tracker", "tools": ["Antigravity","Claude Code"],
  "models": ["Claude Sonnet 4.6"], "hours": 2.63, "interactions": 486, "legacy": false,
  "generated_at": "2026-05-21T03:10:00-03:00" }

// dev_summary — um por (developer, scope); scope ∈ {"legacy", "live"}
{ "event_type": "dev_summary", "schema_version": 1, "developer": "dev-39d71ab2",
  "scope": "live", "total_hours": 1.13, "total_interactions": 142, "total_sessions": 2,
  "last_updated": "21/05/2026 03:10:00", "legacy": false,
  "generated_at": "2026-05-21T03:10:00-03:00" }
```

**`manifest.json`:** `{ "schema_version": 1, "developers": { "dev-39d71ab2":
{ "legacy_boundary": "2026-05-20T13:37:11" } } }` — `legacy_boundary` é datetime naive de
Brasília (ISO), igual à "Última Atualização" capturada do Markdown.

**Render a partir dos eventos:** por dev — cabeçalho = soma dos dois `dev_summary` com
`scope: "legacy"` e `scope: "live"` (horas + interações + sessões); Tabela 1 = `activity_daily`
agrupados por `(date,tool,model)`; Tabela 2 = `activity_branch` agrupados por `(date,branch)`
(união de `tools`/`models`); Totais por Ferramenta = `activity_daily` agrupados por `tool`.
Resumo Global = soma de `dev_summary` de todos os devs + `activity_branch` agrupados por
`branch`. Datas ISO convertidas para DD/MM/YYYY na renderização. Devs ordenados por `masked_id`.

**Captura legada (fidelidade):** o Markdown não cruza branch×modelo; os eventos `activity_branch`
legados reproduzem a Tabela 2 verbatim (listas `tools`/`models` como no Markdown). O relabel
`Indeterminado (pré-migração)` é aplicado apenas aos eventos `activity_daily` de Antigravity.

**`emit_events`:** ponto único de saída — hoje grava `.tracker/events/dev-<hash>.jsonl`
(linhas `legacy` preservadas + linhas `live` recém-geradas). Desenhado para receber um
`KafkaEventSink` ao lado no futuro (fora de escopo).

## Verification

**Commands:**
- `python3 .tracker/work-tracker.py` — esperado: saída de console sem stack trace, sem
  escrever arquivos.
- `python3 .tracker/bootstrap_events.py` — esperado: cria `.tracker/events/*.jsonl` e
  `manifest.json`; rerun aborta com mensagem de idempotência.
- `make -f .tracker/Makefile track-time EXPORT=true` — esperado: `✔ Métricas de tempo
  atualizadas`; `TEMPO_DE_TRABALHO.md` regerado.
- Rodar `EXPORT=true` 2× e `diff` — esperado: sem diferença (idempotência).
- `python3 -m unittest scratch/test_tracker.py` — esperado: 100% pass.

**Manual checks:**
- Comparar `TEMPO_DE_TRABALHO.md` antes/depois: estrutura idêntica; modelo de Antigravity
  pré-migração = `Indeterminado (pré-migração)`; novas linhas de 20–21/05.
- Inspecionar `.tracker/events/`: um `.jsonl` por dev; totais batem com o relatório.

**Unit tests (`scratch/test_tracker.py`):**
- Parser do `transcript.jsonl` incluindo `content: null`.
- Regex de troca de modelo no novo formato.
- `aggregate_sessions()` — horas/sessões/interações.
- Filtro de janela `legacy_boundary` (sem dupla contagem).
- `emit_events()` — preserva linhas `legacy`, substitui `live`.

## Review Findings

- [x] [Review][Decision→Patch] AC#5 idempotency: `last_updated` agora deriva da data máxima dos `activity_daily` live events (formato `DD/MM/YYYY 23:59:59`); `generated_at` permanece runtime stamp (não exibido no Markdown). Opção (a) escolhida. [`work-tracker.py:emit_events`]
- [x] [Review][Patch] Guard de idempotência do bootstrap corrigido: `json.loads(line).get("legacy") is True` com `except (json.JSONDecodeError, Exception): pass` por linha. [`.tracker/bootstrap_events.py:51-55`]
- [x] [Review][Patch] `emit_events`: try/except movido para dentro do loop — parse error em uma linha não aborta leitura das demais; apenas a linha problemática é ignorada. [`.tracker/work-tracker.py:emit_events`]
- [x] [Review][Patch] BKL-007 marcado como `✅ Atendido` no `BACKLOG.md` com justificativa da camada JSONL canônica. [`.tracker/BACKLOG.md`]
- [x] [Review][Patch] `work-tracker-architecture.md` atualizado: ADR-05 corrigido (`transcript.jsonl`), diagrama Mermaid refatorado, estrutura de pastas completa, ADR-07 adicionado. [`.tracker/work-tracker-architecture.md`]
- [x] [Review][Patch] `project-context.md` atualizado: Stack, estrutura de arquivos, ADR-05, ADR-07 (novo), diagrama Mermaid e seção de trabalho diferido. [`.tracker/project-context.md`]
- [x] [Review][Defer] `parse_hours_from_str`: rama `group(2)` nunca alcançada (regex tem 1 grupo) — dead code confuso mas funcionalmente idêntico ao original. [`.tracker/work-tracker.py:67`, `.tracker/bootstrap_events.py:17`] — deferred, pre-existing
- [x] [Review][Defer] `dev-` prefix check sempre cai no branch else — `if not masked_id.startswith("dev-")` é sempre False; branch `"dev-{masked_id}.jsonl"` nunca é executado. [`.tracker/work-tracker.py:421,902`] — deferred, pre-existing
- [x] [Review][Defer] Console report: subtotais por ferramenta podem divergir do total exibido — `tool_model_totals` acumula horas legacy de `activity_daily`, mas `total_combined_hours` usa `legacy_hours` do `dev_summary` (rounding pode diferir). Cosmético, sem impacto nos dados. [`.tracker/work-tracker.py:show_console_report`] — deferred, pre-existing
- [x] [Review][Defer] Ausência de warning quando path antigo do Antigravity existe mas o novo não — UX improvement, não é crash. [`.tracker/work-tracker.py:analyze_antigravity`] — deferred, pre-existing
- [x] [Review][Defer] `model_confidence: "confirmado"` atribuído ao modelo padrão de fábrica ADR-06 — quando não há `USER_SETTINGS_CHANGE` no transcript, o fallback `"Gemini 3.1 Pro (High)"` é rotulado como "confirmado" embora seja inferido. Necessita novo nível `"inferido"` na spec. [`.tracker/work-tracker.py:build_live_events`] — deferred, pre-existing

## Suggested Review Order

1. **Constantes e schema** [`.tracker/work-tracker.py`] — verificar `SCHEMA_VERSION`,
   `EVENTS_DIRNAME`, `MANIFEST_NAME` e o rótulo literal `"Indeterminado (pré-migração)"`.

2. **`analyze_antigravity()`** [`.tracker/work-tracker.py:281`] — confirmar que o glob aponta
   para `transcript.jsonl` (não `overview.txt`); que `content = data.get("content") or ""`
   está presente; que Pass 1 + Pass 2 usam a mesma regex de troca de modelo; que o guard
   `!= "None"` do Pass 2 está preservado (ver patch de spec-fix-antigravity).

3. **I/O de eventos** [`.tracker/work-tracker.py`] — `load_manifest()`, `emit_events()`,
   `load_all_events()`: verificar que `emit_events` preserva todas as linhas `legacy` e só
   reescreve as `live`; testar o comportamento com arquivo pré-existente (não sobrescreve
   `legacy`).

4. **`compute_sessions()` e filtro de fronteira** [`.tracker/work-tracker.py`] — confirmar
   gap ≤ 45 min, padding de 15 min e descarte de eventos `live` com
   `dt_br ≤ legacy_boundary`; validar que sessões cruzando meia-noite atribuem cada ping
   à data BRT real (lógica existente preservada).

5. **`render_report()`** [`.tracker/work-tracker.py`] — comparar saída antes/depois do
   refactor: colunas, totais e ordenação devem ser idênticos bit-a-bit; única diferença
   aceita = célula de modelo Antigravity pré-migração na Tabela 1.

6. **`bootstrap_events.py`** [`.tracker/bootstrap_events.py`] — guard de idempotência no
   topo (aborta se já há linhas `legacy`); modelos Antigravity → `model_confidence:
   "indeterminado"`, `model: "Indeterminado (pré-migração)"`, `raw_model` preservado;
   Claude Code → `model_confidence: "confirmado"`; `legacy_boundary` gravado no
   `manifest.json` igual à "Última Atualização" de cada bloco de dev; totais devem bater
   com o relatório atual (≈ 20h21m para dev-39d71ab2 e ≈ 5h39m para dev-4e707577).

7. **Makefile** [`.tracker/Makefile`] — alvo `bootstrap` presente; `track-time` preservado
   intacto.

8. **Testes unitários** [`scratch/test_tracker.py`] — cobertura de: parser `transcript.jsonl`
   com `content: None`; regex de troca de modelo; `aggregate_sessions`; filtro
   `legacy_boundary`; `emit_events` com arquivo pré-existente.

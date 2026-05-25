Esta seção cobre arquitetura, stack, ADRs, pipeline de dados e comandos de uso. Parte 1 de 4.

---

## Produto

- **Nome:** Rastreador de Tempo Ativo (IA) — micro-sistema analítico privado e offline em `.tracker/`
- **Repositório pai:** `cluster-kubernetes` (GitOps para cluster Kubernetes local k3d + ArgoCD)
- **Propósito:** Auditar tempo produtivo com Antigravity (IDE) e Claude Code (CLI); rastreamento tridimensional tempo × modelo LLM × ferramenta, por branch/história, multi-dev anônimo
- **Premissa de isolamento:** toda lógica, automações e relatórios vivem exclusivamente em `.tracker/`; Makefile principal e `scripts/` são de infra k8s — não misturar

## Stack

- Python 3.x stdlib pura (`os`, `re`, `json`, `glob`, `hashlib`, `socket`, `datetime`); zero dependências externas
- Interface DX: GNU Make (`.tracker/Makefile`)
- Fuso: Brasília GMT-3 em toda exibição e cálculo
- Saída analítica: Markdown GFM
- Fontes de dados:
  - Claude Code: `~/.claude/projects/*.jsonl` — chave `"model"` 100% determinística em cada turno
  - Antigravity: `~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl` — tag `<USER_SETTINGS_CHANGE>` preservada integralmente (sem truncamento)
  - **NUNCA** ler `~/.gemini/antigravity/brain/*/overview.txt` ao vivo (formato legado com truncamento ~1024 chars; dados já capturados como eventos `legacy`)

## Estrutura de Arquivos

```
.tracker/
├── Makefile                    # DX: make track-time / make bootstrap
├── README.md                   # Guia do dev
├── work-tracker-architecture.md# Spec de arquitetura (ADRs)
├── work-tracker.py             # Analytics Engine: collect→compute→emit→render
├── bootstrap_events.py         # Bootstrap one-shot: legado TEMPO_DE_TRABALHO.md → JSONL legacy
├── BACKLOG.md                  # 29 itens (features, bugs, dívida técnica)
├── project-context.md          # Contexto consolidado (redundante com distillate)
├── TEMPO_DE_TRABALHO.md        # Relatório Markdown (renderização pura dos eventos)
├── events/
│   ├── dev-<hash>.jsonl        # Store canônico por dev: activity_daily / activity_branch / dev_summary
│   └── manifest.json           # legacy_boundary por dev (datetime naive BRT ISO)
├── specs/                      # Specs de features/bugfixes
├── reviews/                    # Prompts e resultados de code review
├── research/                   # Pesquisas técnicas
├── tracker-distillate/         # Este distillate (4 partes)
└── scratch/test_tracker.py     # Testes unitários (unittest)
```

## Decisões de Arquitetura (ADRs)

**ADR-01 — Isolamento de Escopo:** `.tracker/` contém tudo; raiz limpa para infra k8s.

**ADR-02 — Session Gap:** gap máximo entre interações = 45 min; sessões < 15 min recebem padding automático para 15 min (engajamento mínimo).

**ADR-03 — Prevenção de Dupla Contagem:**
- Todos os timestamps (ambas ferramentas) concatenados e ordenados cronologicamente antes do agrupamento
- Tempo ocioso creditado ao modelo da interação anterior imediata
- Pings órfãos sem prompt de usuário descartados (filtro anti-poluição)

**ADR-04 — Privacidade SHA-256:** `dev-[hash]` = SHA-256 truncado 8 chars de `usuario@hostname`; 2 devs ativos: `dev-39d71ab2`, `dev-4e707577`

**ADR-05 — Rastreamento Dinâmico por Modelo:**
- Claude Code: chave `"model"` no JSONL, 100% determinístico
- Antigravity: `<USER_SETTINGS_CHANGE>` em `transcript.jsonl`; coerção `content = data.get("content") or ""` para entries com `content: null`; filtro `belongs_to_repo` por path

**ADR-06 — Propagação Cronológica de Estado (Zero-Config):**
- Modelo de fábrica padrão: `Gemini 3.1 Pro (High)` (estado inicial do Antigravity)
- Pass 1: ancora modelo inicial 1ms antes do primeiro turno do `transcript.jsonl`
- Pass 2: rastreia mudanças via `<USER_SETTINGS_CHANGE>` — regex: `changed setting \`Model Selection\` from (.*?) to (.*?)(?:\. No need|\.?\s*$)`
- Guard: `if is_change and new_model and new_model != "None":` (evita propagação de None)
- Nova conversa herda último modelo confirmado na linha do tempo global

**ADR-07 — Arquitetura Orientada a Eventos (fonte canônica = JSONL):**
- Eventos por dev em `.tracker/events/dev-<hash>.jsonl` (um por linha)
- Tipos: `activity_daily` (dev × date × tool × model), `activity_branch` (dev × date × branch), `dev_summary` (dev × scope)
- `legacy: true` = capturado do `TEMPO_DE_TRABALHO.md` histórico via `bootstrap_events.py` (one-shot, idempotente); nunca recomputados
- `legacy: false` = eventos live, filtrados para `dt_br > legacy_boundary` do dev
- `model_confidence`: `"confirmado"` para live com `USER_SETTINGS_CHANGE` detectado e fallback ADR-06; `"indeterminado"` para legacy Antigravity (fonte era `overview.txt` truncado)
- `TEMPO_DE_TRABALHO.md` é renderização pura de `render_report()`; nunca mais lido como dado
- Seam futuro: `emit_events()` é o único ponto de saída — projetado para receber `KafkaEventSink` (fora de escopo atual)

## Schema de Eventos (JSONL)

```jsonc
// activity_daily — um por (developer, date, tool, model)
{"event_type":"activity_daily","schema_version":1,"developer":"dev-39d71ab2",
 "date":"2026-05-20","tool":"Antigravity","model":"Claude Sonnet 4.6 (Thinking)",
 "raw_model":"Claude Sonnet 4.6 (Thinking)","model_confidence":"confirmado",
 "hours":1.13,"sessions":2,"interactions":142,"legacy":false,
 "generated_at":"2026-05-21T03:10:00-03:00"}

// activity_branch — um por (developer, date, branch)
{"event_type":"activity_branch","schema_version":1,"developer":"dev-39d71ab2",
 "date":"2026-05-20","branch":"time-tracker","tools":["Antigravity","Claude Code"],
 "models":["Claude Sonnet 4.6"],"hours":2.63,"interactions":486,"legacy":false}

// dev_summary — um por (developer, scope∈{"legacy","live"})
{"event_type":"dev_summary","schema_version":1,"developer":"dev-39d71ab2",
 "scope":"live","total_hours":1.13,"total_interactions":142,"total_sessions":2,
 "last_updated":"21/05/2026 03:10:00","legacy":false}
```

## manifest.json (estado atual)

```json
{"schema_version":1,"developers":{
  "dev-39d71ab2":{"legacy_boundary":"2026-05-20T13:37:11"},
  "dev-4e707577":{"legacy_boundary":"2026-05-20T13:39:49"}
}}
```

## Pipeline de Dados

```
Makefile → work-tracker.py --export
  SHA-256(user@host) → masked_id
  analyze_claude_code() → ~/.claude/projects/*.jsonl → pings com model
  analyze_antigravity() → transcript.jsonl (Pass1+Pass2) → pings com model + belongs_to_repo filter
  merge global cronológico → filtro anti-poluição → UTC→BRT
  compute_sessions(gap=45min, padding=15min) → sessions
  build_live_events() → activity_daily / activity_branch / dev_summary
  emit_events() [atômico: escrita em .tmp → os.replace()] → preserva legacy, reescreve live
  load_all_events() → render_report() → TEMPO_DE_TRABALHO.md
```

## Padrões de Consistência

- Imutabilidade de blocos de outros devs no `TEMPO_DE_TRABALHO.md`
- Deduplicação dinâmica: bloco do dev atual substituído in-place
- Fuso BRT estrito em toda exibição
- `emit_events()`: try/except por linha (linha JSONL corrompida não aborta arquivo)
- `load_all_events()`: try/except por linha (padrão idêntico ao `emit_events`)
- `daily_stats[date][tool][model]` e `branch_stats[date][branch][tool][model]` (4 níveis após ADR ferramenta-dimensão)

## Comandos

```bash
make -f .tracker/Makefile track-time          # console read-only (sem escrita)
make -f .tracker/Makefile track-time EXPORT=true  # emit_events + render + grava MD
make -f .tracker/Makefile bootstrap           # bootstrap one-shot (roda uma vez)
python3 -m unittest scratch/test_tracker.py   # testes unitários
```

## Modelos Rastreados (normalize_model_name)

- Antigravity: `Gemini 3.1 Pro (High)`, `Gemini 3.1 Pro (Low)`, `Gemini 3 Flash`, `Claude Sonnet 4.6 (Thinking)`, `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`
- Claude Code: `Claude Sonnet 4.6`, `Claude Opus 4.7`, `Claude Haiku 4.5`
- Formato padrão para modelos Claude: `Claude Sonnet 4.6` (com prefixo "Claude")
- Regex de remoção de sufixo de data: `-\d{8}\b`; hífen→ponto limitado a versões curtas `X-Y`

---
*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

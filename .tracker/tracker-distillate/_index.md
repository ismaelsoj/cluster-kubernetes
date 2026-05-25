---
type: bmad-distillate
sources:
  - "../README.md"
  - "../BACKLOG.md"
  - "../events/manifest.json"
  - "../docs-archive/project-context.md"
  - "../docs-archive/work-tracker-architecture.md"
  - "../docs-archive/plano-de-implementacao-llm.md"
  - "../docs-archive/research/technical-identificar-modelo-llm-antigravity-research-2026-05-19.md"
  - "../docs-archive/research/technical-rastreamento-tokens-antigravity-research-2026-05-20.md"
  - "../docs-archive/reviews/review-tempo-total-desenvolvedores-prompt.md"
  - "../specs/archive/spec-tracker-orientado-a-eventos.md"
  - "../specs/archive/spec-branch-tracking-work-tracker.md"
  - "../specs/archive/spec-ferramenta-dimensao-relatorio.md"
  - "../specs/archive/spec-fix-antigravity-model-extraction-regex.md"
  - "../specs/archive/spec-tempo-total-desenvolvedores-e-branches.md"
downstream_consumer: general
created: "2026-05-25"
updated: "2026-05-25"
token_estimate: 6706
source_total_tokens: 27912
compression_ratio: "4.2:1"
parts: 4
---

## Orientação

- Distillate do subprojeto `.tracker/` — Rastreador de Tempo de Desenvolvimento com IA (Antigravity + Claude Code).
- Fontes originais: 14 documentos (27.912 tokens) — arquitetados em `docs-archive/`, `specs/archive/` e `BACKLOG.md` (ativo).
- Consumidor: qualquer agente que precise entender o projeto para implementar, revisar ou evoluir o tracker.
- 4 seções autocontidas — carregue apenas as relevantes para a tarefa.
- **Regra de acesso:** leia apenas este `_index.md` + as seções pertinentes; nunca leia os arquivos-fonte originais para contexto de agente.
- **Governança:** ver `.tracker/AGENTS.md` para regras completas de acesso e restrições de implementação.
- **Specs:** todas as 5 specs foram arquivadas em `specs/archive/` — `specs/` ativo está vazio.

## Manifesto de Seções

| Arquivo | Conteúdo |
|---|---|
| [01-arquitetura-e-visao-geral.md](./01-arquitetura-e-visao-geral.md) | Stack, ADRs (01–07), schema de eventos JSONL, manifest.json, pipeline de dados, comandos, modelos rastreados |
| [02-specs-features-concluidas.md](./02-specs-features-concluidas.md) | 4 specs `done` (fix-regex, branch-tracking, ferramenta-dimensão, tempo-total) + spec `in-progress` tracker-orientado-a-eventos (tasks ✅, aguardando validação) |
| [03-backlog-e-divida-tecnica.md](./03-backlog-e-divida-tecnica.md) | 30 itens do backlog por prioridade com status real: BKL-001 a BKL-029 (features, bugs, dívida técnica, bloqueados) |
| [04-pesquisa-tecnica.md](./04-pesquisa-tecnica.md) | Pesquisas sobre identificação de LLM e rastreamento de tokens; fontes descartadas e conclusões definitivas |

## Itens Transversais (Cross-Cutting)

- Python 3.x stdlib pura; zero dependências externas; compatível Linux/macOS.
- Fuso horário: Brasília GMT-3 em toda exibição e cálculo.
- Privacidade: identidade mascarada por SHA-256 8 chars (`dev-[hash]`), calculado de `usuario@hostname`. Devs ativos: `dev-39d71ab2` (boundary `2026-05-20T13:37:11`), `dev-4e707577` (boundary `2026-05-20T13:39:49`).
- Isolamento: toda lógica, automações e relatórios vivem exclusivamente em `.tracker/`.
- Imutabilidade: blocos de outros desenvolvedores em `TEMPO_DE_TRABALHO.md` nunca são alterados.
- Fonte de dados canônica: `.tracker/events/dev-<hash>.jsonl` (eventos JSONL); `TEMPO_DE_TRABALHO.md` é renderização pura, nunca mais relida como dado.
- Todas as specs arquivadas em `specs/archive/`; `specs/` ativo vazio. A última spec (`spec-tracker-orientado-a-eventos`) tinha todas as tasks ✅ e foi arquivada após validação.
- Seam futuro: `emit_events()` projetado para receber `KafkaEventSink` (fora de escopo atual).
- Antigravity tokens: ⛔ inviável (sem exposição em `transcript.jsonl`); Claude Code tokens: ✅ viável via campo `usage` (BKL-001, pronto para implementação).

---
*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

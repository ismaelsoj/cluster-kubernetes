---
type: bmad-spec
slug: tracker-contexto-agente
companions:
  - implementation-status.md
  - planning.md
  - research-decisions.md
sources:
  - ../tracker-distillate/_index.md
  - ../tracker-distillate/01-arquitetura-e-visao-geral.md
  - ../tracker-distillate/02-specs-features-concluidas.md
  - ../tracker-distillate/03-backlog-e-divida-tecnica.md
  - ../tracker-distillate/04-pesquisa-tecnica.md
  - ../specs/spec-rastreamento-de-tokens-claude-code.md
  - ../specs/spec-export-json-csv.md
  - ../specs/spec-backfill-tokens-legados.md
  - ../_bmad-output/planning-artifacts/epics.md
  - ../_bmad-output/planning-artifacts/implementation-readiness-report-2026-05-27.md
  - ../_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-27.md
---

# SPEC

## Why

O contexto atual da `.tracker/` já foi destilado, mas ainda induz sobrecarga porque a porta de entrada mistura regras, histórico e estado mutável. O objetivo deste kernel é reduzir o contexto padrão para o mínimo confiável e empurrar detalhes para companions abertos sob demanda.

## Capabilities

- `CAP-1`
  - `intent`: Dar a qualquer agente uma porta de entrada única, curta e confiável para trabalhar na `.tracker/`.
  - `success`: O agente entende propósito, invariantes, fontes canônicas e roteamento de leitura sem abrir arquivos históricos.

- `CAP-2`
  - `intent`: Separar estado operacional atual de histórico e planejamento expansivo.
  - `success`: Tarefas de implementação, revisão, pesquisa e planejamento conseguem carregar apenas o companion relevante.

- `CAP-3`
  - `intent`: Reduzir releituras defensivas causadas por inconsistências entre resumos e artefatos ativos.
  - `success`: O contexto v2 registra explicitamente o estado atual real de specs e do roadmap, inclusive quando o material antigo ficou defasado.

## Constraints

- `.tracker/` continua sendo subprojeto isolado; não misturar contexto de infra Kubernetes.
- Fonte canônica de dados permanece `.tracker/events/dev-<hash>.jsonl`; `TEMPO_DE_TRABALHO.md` segue sendo renderização.
- Python stdlib pura, operação offline e fuso de Brasília continuam invariantes.
- `tracker-distillate/` antigo passa a ser histórico de referência; a entrada padrão para agentes deve ser `tracker-distillate-v2/SPEC.md`.
- Abrir specs ativas ou `epics.md` só quando a tarefa exigir detalhe de execução não coberto pelos companions.

## Non-goals

- Reescrever ou apagar o distillate antigo nesta etapa.
- Substituir specs de história, backlog ou artefatos de planejamento como fonte de execução detalhada.
- Resolver bugs funcionais do tracker.

## Success signal

Um agente consegue iniciar trabalho na `.tracker/` lendo `SPEC.md` e, no máximo, um companion adicional para a maioria das tarefas comuns. A abertura de `epics.md`, `specs/` e arquivos arquivados vira exceção, não caminho feliz.

## Assumptions

- O usuário quer preservar o material existente e introduzir uma camada v2 mais barata, em vez de uma migração destrutiva.

## Open Questions

- Nenhuma nesta iteração.

---
Autoria/Implementação: GPT-5 Codex

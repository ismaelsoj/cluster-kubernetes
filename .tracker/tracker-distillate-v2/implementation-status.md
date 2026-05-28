# Status de Implementacao

Use este companion para tarefas de implementacao, bugfix, code review e validacao de comportamento atual.

## Estado atual confiavel

- Fonte de entrada para agentes: `.tracker/tracker-distillate-v2/SPEC.md`
- Fonte canônica de dados: `.tracker/events/dev-<hash>.jsonl`
- Relatorio derivado: `.tracker/TEMPO_DE_TRABALHO.md`
- Implementacao principal: `.tracker/work-tracker.py`
- Bootstrap legado: `.tracker/bootstrap_events.py`
- Testes: `.tracker/test_tracker.py`

## Invariantes tecnicos

- Python 3.x stdlib pura; sem dependencias externas.
- Toda exibicao e calculo usam horario de Brasilia.
- Escritas em JSONL devem ser atomicas com `.tmp` seguido de `os.replace()`.
- Nunca reler `TEMPO_DE_TRABALHO.md` como fonte de dados live.
- Nunca usar `overview.txt` do Antigravity ao vivo; a fonte valida e `transcript.jsonl`.

## Features ativas e status real

- `BKL-001` rastreamento de tokens do Claude Code: concluido.
- `BKL-003` exportacao JSON/CSV: concluido no corpo da historia, apesar de frontmatter ainda divergente.
- `BKL-030` backfill de tokens legados do Claude Code: pronto para desenvolvimento.

## Riscos e inconsistencias conhecidas

- O distillate antigo afirma que `specs/` ativo esta vazio, mas hoje ha specs ativas em `.tracker/specs/`.
- `BKL-003` tem status divergente entre frontmatter e corpo da spec.
- A secao de pesquisa antiga ainda diz que `BKL-001` estava pendente.
- O backlog antigo reutiliza o identificador `BKL-030` para dois itens distintos.

## Quando abrir mais contexto

- Abra `.tracker/specs/spec-backfill-tokens-legados.md` para implementar o backfill.
- Abra `.tracker/specs/spec-export-json-csv.md` apenas se a tarefa tocar exportadores ou alinhar status da historia.
- Abra `.tracker/specs/spec-rastreamento-de-tokens-claude-code.md` apenas para comportamento detalhado de tokens Claude Code.
- Abra `.tracker/events/manifest.json` apenas para validar `legacy_boundary`.

---
Autoria/Implementação: GPT-5 Codex

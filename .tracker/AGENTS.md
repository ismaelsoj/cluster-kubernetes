# AGENTS.md — Regras para Agentes de IA no Subprojeto `.tracker/`

## Porta de entrada obrigatoria

Leia primeiro `.tracker/tracker-distillate-v2/SPEC.md`.

Carregue apenas os companions necessarios:

- `implementation-status.md` para implementacao, review e bugfix
- `planning.md` para priorizacao e roadmap
- `research-decisions.md` para limites tecnicos de coleta

## Invariantes

- `.tracker/` e um subprojeto isolado e offline.
- Fonte canonica: `.tracker/events/dev-<hash>.jsonl`
- `TEMPO_DE_TRABALHO.md` e renderizacao, nao fonte de dados
- Python stdlib pura
- Fuso horario de Brasilia em toda exibicao e calculo
- Escrita em JSONL deve ser atomica com `.tmp` e `os.replace()`
- Antigravity live usa `transcript.jsonl`, nunca `overview.txt`

## Leitura sob demanda

- `work-tracker.py`, `bootstrap_events.py`, `test_tracker.py` para codigo
- `.tracker/specs/*.md` apenas quando a tarefa exigir criterios detalhados
- `.tracker/_bmad-output/planning-artifacts/epics.md` apenas para decomposicao completa
- `events/manifest.json` apenas para validar `legacy_boundary`

## Nao usar como contexto padrao

- `docs-archive/`
- `specs/archive/`
- `TEMPO_DE_TRABALHO.md`
- `tracker-distillate/` antigo, exceto para auditoria historica

## Git

- Seguir o `AGENTS.md` do repositorio pai
- Nunca executar `git add` ou `git commit` sem autorizacao explicita do usuario

---
Autoria/Implementação: GPT-5 Codex

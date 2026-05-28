# Research Decisions

Use este companion apenas quando a tarefa depender de limites tecnicos de coleta, especialmente modelo LLM e tokens.

## Decisoes fechadas

- Tokens do Antigravity continuam inviaveis hoje porque `transcript.jsonl` nao expoe `usage` e os `.pb` nao sao uma fonte local utilizavel.
- A fonte correta do Antigravity para atividade live e `~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl`.
- `overview.txt` e legado truncado e nao deve voltar ao fluxo live.
- Claude Code continua sendo a unica fonte atual com `usage` local confiavel para tokens.

## Decisoes abertas mas roteadas

- Se a tarefa envolver tokens do Claude Code, a fonte existe e a referencia detalhada esta em `.tracker/specs/spec-rastreamento-de-tokens-claude-code.md`.
- Se a tarefa envolver backfill de tokens legados, a referencia ativa esta em `.tracker/specs/spec-backfill-tokens-legados.md`.

## O que nao precisa ser reaberto

- Logs de erro antigos do Antigravity
- `state.vscdb`
- `conversations/*.pb`
- `docs-archive/research/`

---
Autoria/Implementação: GPT-5 Codex

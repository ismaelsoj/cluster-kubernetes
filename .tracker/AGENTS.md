# AGENTS.md — Regras para Agentes de IA no Subprojeto `.tracker/`

> Este arquivo é lido automaticamente por Antigravity, Cursor, Claude Code e outros agentes compatíveis.
> Contém políticas de contexto específicas do subprojeto `.tracker/` que SOBREPÕEM as regras genéricas do repositório pai, exceto onde indicado o contrário.

---

## Contexto do Subprojeto

Este diretório é um micro-sistema analítico privado e offline: o **Rastreador de Tempo de Desenvolvimento com IA**.
Ele rastreia o tempo produtivo com **Antigravity** (IDE) e **Claude Code** (CLI), consolidando métricas por modelo LLM, ferramenta e branch/história.

---

## Porta de Entrada Obrigatória

**ANTES de qualquer ação neste subprojeto, leia:**

```
.tracker/tracker-distillate/_index.md
```

O `_index.md` é o único ponto de acesso para contexto de agente. Ele contém:
- Orientação geral do projeto
- Manifesto das 4 seções autocontidas do distillate
- Itens transversais críticos (cross-cutting)

Carregue **apenas as seções relevantes** para a tarefa em andamento — não carregue todas de uma vez.

---

## Regras de Acesso a Arquivos

### ✅ Leia

| Arquivo / Pasta | Quando |
|---|---|
| `tracker-distillate/_index.md` | Sempre (porta de entrada) |
| `tracker-distillate/01-arquitetura-e-visao-geral.md` | Tarefas de arquitetura, ADRs, pipeline, comandos |
| `tracker-distillate/02-specs-features-concluidas.md` | Implementar, revisar ou evoluir features existentes |
| `tracker-distillate/03-backlog-e-divida-tecnica.md` | Priorização, triagem de bugs, planejamento de sprint |
| `tracker-distillate/04-pesquisa-tecnica.md` | Investigações sobre modelos LLM, rastreamento de tokens |
| `events/manifest.json` | Verificar `legacy_boundary` por dev |
| `BACKLOG.md` | Consulta detalhada de itens de backlog (secundário ao distillate) |
| `work-tracker.py` | Implementação de código |
| `bootstrap_events.py` | Implementação de código |
| `test_tracker.py` | Testes unitários |

### ❌ Nunca Leia Diretamente para Contexto

| Arquivo / Pasta | Motivo |
|---|---|
| `docs-archive/` | Arquivos históricos — **NUNCA** ler para contexto; distillate é mais atualizado e comprimido |
| `specs/archive/` | Todas as specs estão aqui arquivadas — **NUNCA** ler para contexto |
| `research/` | Pasta vazia (arquivos movidos para `docs-archive/research/`) |
| `reviews/` | Pasta vazia (arquivos movidos para `docs-archive/reviews/`) |
| `TEMPO_DE_TRABALHO.md` | Relatório de saída (renderização pura dos eventos) — não é fonte de dados |
| `~/.gemini/antigravity/brain/*/overview.txt` | Legado truncado — **proibido** ao vivo |

---

## Regras de Implementação

- **Stdlib pura:** nunca adicionar dependências externas ao Python
- **Fuso horário:** sempre Brasília GMT-3 em toda exibição e cálculo
- **Fonte canônica:** `.tracker/events/dev-<hash>.jsonl` — nunca reler `TEMPO_DE_TRABALHO.md` como dado
- **Imutabilidade:** blocos de outros desenvolvedores em `TEMPO_DE_TRABALHO.md` nunca são alterados
- **Escrita atômica:** qualquer escrita em `.jsonl` deve usar padrão `.tmp` → `os.replace()` (previne perda de dados legacy)
- **Antigravity logs:** sempre usar `~/.gemini/antigravity-ide/brain/*/transcript.jsonl`; nunca `overview.txt`
- **Tokens Antigravity:** ⛔ inviável — não tentar implementar sem nova atualização da IDE
- **Tokens Claude Code:** ✅ disponíveis em campo `usage` dos JSONL (BKL-001)

## Git Workflow

- Seguir as regras do `AGENTS.md` do repositório pai (branch descritiva a partir de `main`; commits diretos em `main` proibidos)
- Commits autônomos de `git add` / `git commit` são **PROIBIDOS** — aguardar autorização explícita do usuário

---

*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

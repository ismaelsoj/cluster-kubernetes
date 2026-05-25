Esta seção cobre as 4 specs implementadas (done) e a spec em andamento (in-progress com todas as tasks concluídas). Parte 2 de 4.

---

## Specs com Status `done`

### spec-fix-antigravity-model-extraction-regex (bugfix, 2026-05-19)
- **Problema:** Pass 1 de `analyze_antigravity()` extraía `group(1)` ("from" = `"None"`) em vez de `group(2)` ("to" = modelo real) → tracker caía no fallback de fábrica
- **Solução:** Regex do Pass 1 ajustada para captura única do "to"; variável renomeada de `first_old_model` → `first_active_model`
- **Escopo expandido:** nova função `normalize_model_name()` centraliza normalização de nomes de modelos em 3 call sites (Pass 1, Pass 2, `analyze_claude_code`)
- **Patches críticos aprovados:**
  - Pass 2 sem guarda `!= "None"` → corrigido: `if is_change and new_model and new_model != "None":`
  - Regex `(\d+)-(\d+)` limitada a versões curtas para não fundir versões distintas
  - Labels históricos `TEMPO_DE_TRABALHO.md` migrados: `Sonnet 4.6` → `Claude Sonnet 4.6`
- **Deferred:** regex `(.*?)\.` trunca modelos com ponto (ex: `"Gemini 3.1 Pro."` → `"Gemini 3"`) — ainda aberto como BKL-004

### spec-branch-tracking-work-tracker (feature, 2026-05-19)
- **Problema:** sem visibilidade de esforço por branch/história
- **Solução:** 
  - `build_branch_timeline(repo_root)` lê `.git/logs/HEAD` diretamente (sem subprocess); filtra linhas de checkout; retorna `[(entry_dt_utc, branch_name)]` ordenada
  - `get_branch_at(timeline, ping_dt)` — retorna `"main"` se timeline vazia, `"Desconhecida"` se ping anterior a todo reflog
  - Bucket `branch_stats[date][branch]` populado por ping; tabela `🌿 Detalhamento Diário por Branch` adicionada ao export
- **Constraints:** sem subprocess git; sem dependências externas; linhas corrompidas do reflog ignoradas silenciosamente
- **Edge case:** detached HEAD capturado como SHA abreviado — deferred como BKL-010

### spec-ferramenta-dimensao-relatorio (feature, 2026-05-19)
- **Problema:** pipeline descartava campo `tool` — impossível saber tempo Antigravity vs Claude Code
- **Solução:** 
  - `daily_stats[date][tool][model]` e `branch_stats[date][branch][tool][model]` (nova dimensão intermediária)
  - Nova seção `🛠️ Totais por Ferramenta` antes da Tabela 1
  - Tabela 1 ganha coluna `Ferramenta`; ordenação: date → tool → model
  - Tabela 2 ganha colunas `Ferramentas` + `Modelos Utilizados`
  - Console: métricas agrupadas por ferramenta com cabeçalhos `[Ferramenta]`
- **Regra:** nunca inferir ferramenta pelo nome do modelo — sempre usar `ev["tool"]`

### spec-tempo-total-desenvolvedores-e-branches (feature, 2026-05-19)
- **Problema:** tempo exibido apenas por dev individual, sem consolidação total
- **Solução:**
  - `parse_hours_from_str()` e `parse_existing_developers_stats()` extraem tempos dos outros devs do `TEMPO_DE_TRABALHO.md`
  - Painel `## 📊 Resumo Geral Consolidado (Todos os Desenvolvedores)` no início do arquivo
  - Tabela `🌿 Tempo Total por Branch` consolidada de todos os devs
  - Bloco antigo do dev substituído in-place; blocos de outros devs preservados integralmente

---

## Spec com Status `in-progress` (todas as tasks ✅)

### spec-tracker-orientado-a-eventos (feature, 2026-05-21) — aguardando validação final

**Problema duplo:**
1. BKL-026: Antigravity antigo gravava em `overview.txt` (truncava `<USER_SETTINGS_CHANGE>`); tracker apontava para caminho/formato antigo
2. BKL-007: `TEMPO_DE_TRABALHO.md` era a própria fonte da verdade (relido por regex `parse_existing_developers_stats`) — frágil

**Solução implementada:**
- Antigravity migrou para `transcript.jsonl` (sem truncamento, `<USER_SETTINGS_CHANGE>` intacto)
- `analyze_antigravity()` reescrita para glob `~/.gemini/antigravity-ide/brain/*/transcript.jsonl`
- Arquitetura orientada a eventos: I/O `load_manifest()`, `emit_events()`, `load_all_events()`
- `emit_events()` atômico: escrita em `.tmp` → `os.replace()` (evita perda de dados legacy em crash)
- `main()` refatorado em: `collect_events()`, `compute_sessions()`, `aggregate_sessions()`, `build_live_events()`
- `render_report(all_events)` substitui geração inline em `main()`
- `bootstrap_events.py` (one-shot, idempotente): parseia `TEMPO_DE_TRABALHO.md` → eventos `legacy: true`; Antigravity → `model: "Indeterminado (pré-migração)"`, `model_confidence: "indeterminado"`; Claude Code → `model_confidence: "confirmado"`; grava `manifest.json`; guard: aborta se já há linhas `legacy`
- `Makefile` ganha alvo `bootstrap`

**Tasks todas concluídas [x]; Review Findings todos resolvidos [x]:**
- `[Review][Decision→Patch]` `last_updated` deriva da data máxima dos `activity_daily` live (`DD/MM/YYYY 23:59:59`)
- `[Review][Patch]` Guard de idempotência do bootstrap: `json.loads(line).get("legacy") is True`
- `[Review][Patch]` `emit_events`: try/except movido para dentro do loop (linha corrompida não aborta)
- BKL-026 fechado; BKL-007 marcado como ✅ Atendido

**Deferred (pre-existing, não introduzidos por esta spec):**
- `parse_hours_from_str`: branch `group(2)` nunca alcançado (regex 1 grupo) — dead code
- `dev-` prefix check: `if not masked_id.startswith("dev-")` sempre False — branch morto
- `model_confidence: "confirmado"` para fallback de fábrica — semânticamente deveria ser `"inferido"` (novo nível na spec)
- `last_updated_str = max_dt.strftime(...) + " 23:59:59"` — semanticamente incorreto (BKL-029 ainda aberto)

**Constraints permanentes:**
- `TEMPO_DE_TRABALHO.md` mantém formato/tabelas/colunas/comando idênticos; única mudança visível: células Antigravity pré-migração na Tabela 1 = `Indeterminado (pré-migração)`
- Nunca ler `overview.txt` ao vivo; nunca recomputar eventos `legacy`; stdlib pura; sem Kafka nem frontend

---
*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

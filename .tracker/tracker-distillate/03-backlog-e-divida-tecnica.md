Esta seção cobre o backlog priorizado com status atual de cada item. Parte 3 de 4.

---

## Resumo do Backlog

| Tipo | Qtd |
|---|---|
| Feature | 8 |
| Bug / Bug potencial | 12 |
| Dívida técnica | 6 |
| Pesquisa / Bloqueado | 2 |
| Código morto | 1 |
| Divergência de spec | 1 |
| **Total** | **30** |

Origem: Party Mode review 2026-05-20 (Mary/Analista, Winston/Arquiteto, Amelia/Dev, John/PM) + code review gauntlet 2026-05-21 + deferred work de specs anteriores.

---

## Prioridade Alta — Abertos

### BKL-001: Rastreamento de Tokens (Claude Code)
- **Tipo:** Feature | **Status:** Pronto para desenvolvimento (Spec criada)
- Campo `usage` nos JSONL do Claude Code: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`
- Localização: `message.usage` em entries do tipo `assistant`
- Impacto: estimar custo por modelo, responder "Opus vs Sonnet", métricas de investimento além de esforço

### BKL-002: Rastreamento de Tokens (Antigravity) — ⛔ Inviável
- **Tipo:** Pesquisa / Limitação Técnica | **Status:** Bloqueado
- `transcript.jsonl` não expõe `usage` / tokens; `.pb` criptografado; sem SQLite acessível
- Ação: monitorar atualizações do Antigravity; sugerir Feature Request para chave `"usage": {"input_tokens": X, "output_tokens": Y}`
- Rastreamento permanece baseado apenas em tempo ativo para Antigravity

### BKL-003: Export JSON/CSV
- **Tipo:** Feature | **Status:** Pronto para implementação
- Flags `--format json` e `--format csv` para análise externa (Jupyter, Pandas, planilhas)
- Sem impacto no core; Markdown permanece como view principal

### BKL-004: Regex de modelo trunca nomes com ponto *(pre-existing)*
- **Tipo:** Bug | **Status:** Aberto
- Payload `"to Gemini 3.1 Pro."` → regex `(.*?)\.` captura `"Gemini 3"` (trunca no primeiro `.`)
- Correção proposta: `(.*?)(?:\.\s|\.?$)` ou sentinela específico do payload da IDE

---

## Prioridade Alta — Concluídos ✅

- **BKL-005:** Refatorar `main()` ✅ — separado em `collect_events()`, `compute_sessions()`, `aggregate_sessions()`, `render_report()`
- **BKL-006:** Testes unitários ✅ — `scratch/test_tracker.py` (parser `transcript.jsonl`, regex, `aggregate_sessions`, `legacy_boundary`, `emit_events`)
- **BKL-007:** Persistência JSON canônica ✅ — atendido por arquitetura orientada a eventos (JSONL em `.tracker/events/`); `TEMPO_DE_TRABALHO.md` é renderização pura
- **BKL-026:** Antigravity truncava eventos ✅ — migrado para `transcript.jsonl`; path atualizado para `~/.gemini/antigravity-ide/brain/`
- **BKL-027:** Escrita não-atômica em `emit_events()` ✅ — corrigido: escrita em `.tmp` + `os.replace()`

---

## Prioridade Média — Abertos

### BKL-008: Tendência Temporal (Week-over-Week)
- Total de horas por semana com delta percentual; responde "estamos acelerando ou desacelerando?"

### BKL-009: Estimativa de Custo por Modelo
- Depende de BKL-001; tokens × tabela de preços = custo USD por modelo (restrito ao Claude Code; Antigravity é assinatura opaca)

### BKL-010: Detached HEAD como SHA de branch
- Correção: se destino do checkout match `^[0-9a-f]{7,40}$`, substituir por `"(detached HEAD)"`

### BKL-011: Sessões cruzando meia-noite
- Toda sessão atribuída à data do primeiro evento; sessões cruzando 00:00 acumulam horas do dia seguinte no dia anterior
- Correção: dividir sessão no limite da meia-noite e distribuir proporcionalmente

### BKL-012: Gap entre ferramentas diferentes descartado silenciosamente
- Linha `if sess[i]["tool"] != sess[i+1]["tool"]: continue` perde gaps Antigravity↔Claude Code → subestimação do tempo real em sessões com alternância frequente

### BKL-028: `load_all_events()` sem try/except por linha
- `except Exception: pass` no nível do arquivo — uma linha JSONL corrompida interrompe leitura do arquivo inteiro
- Correção: mover para `json.JSONDecodeError` dentro do loop, idêntico ao padrão de `emit_events()`

### BKL-029: `last_updated_str` hardcodado como `"23:59:59"`
- Semanticamente incorreto: afirma que última atividade foi às 23:59:59 quando o timestamp real está em `generated_at`
- Correção: usar `generated_at_str` para `last_updated`, ou renomear campo para `last_active_date`

---

## Prioridade Baixa — Abertos

- **BKL-013:** Versionamento do formato de dados — campo `format_version: X` no header do relatório
- **BKL-014:** Fuso hardcoded — usar `zoneinfo.ZoneInfo("America/Sao_Paulo")` (Python 3.9+) para DST
- **BKL-015:** `normalize_model_name()` frágil — 44 linhas de heurísticas; considerar lookup table + fallback
- **BKL-016:** `to_brasilia()` ignora timezone-aware — `dt.replace(tzinfo=None)` descarta tzinfo antes da conversão; subtração de 3h errada se `parse_iso()` retornar aware datetime
- **BKL-017:** `extract_repo_name()` nunca usado efetivamente — candidato a remoção (código morto)
- **BKL-018:** Change events sem filtro `belongs_to_repo` — eventos `is_change` emitidos sem filtro de repositório; pode ser poluição de outros repos
- **BKL-019:** Detecção de Anomalias — flag automático para sessões < 5 min, interações sem tempo, modelos com 0 sessões + > 0 interações
- **BKL-020:** Tamanho da Conversa — rastrear turnos por sessão (exploratória vs produtiva)
- **BKL-021:** Type Hints e logging — `mypy --strict`; substituir `try/except: pass` por logging estruturado
- **BKL-022:** Inter-branch gap attribution — gap entre pings de branches diferentes inteiramente atribuído à branch anterior
- **BKL-023:** Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON — `re.search` captura apenas a primeira ocorrência
- **BKL-024:** Inconsistência de guarda de tabelas vazias — Tabela 1 vs Tabela 2 usam padrões diferentes (`for...; if not:` vs `if: for...; else:`)
- **BKL-025:** `get_branch_at()` retorna `"main"` vs spec diz `"Desconhecida"` — divergência de spec; decidir e alinhar

---
*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

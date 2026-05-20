---
title: 'Corrigir extração do modelo Antigravity no work-tracker (Pass 1)'
type: 'bugfix'
created: '2026-05-19'
status: 'done'
route: 'one-shot'
---

# Corrigir extração do modelo Antigravity no work-tracker (Pass 1)

## Intent

**Problem:** No Pass 1 de `analyze_antigravity()` em `.tracker/work-tracker.py`, a regex extraía `group(1)` (o "from" — quase sempre `"None"` em payloads de inicialização da IDE), fazendo o filtro descartar o evento e o tracker cair no fallback de fábrica. Em consequência, métricas mensais e orçamentos do Antigravity ficavam atribuídos ao modelo errado.

**Approach:** Ajustar a regex do Pass 1 para a forma de captura única do "to" (mesma forma já usada no Pass 2), renomear `first_old_model`/`old_m` para `first_active_model`/`new_m` refletindo a semântica correta e atualizar o comentário com a justificativa documentada na pesquisa.

**Escopo expandido (aprovado no code review de 2026-05-19):** além da correção do Pass 1, esta spec passa a cobrir a função utilitária `normalize_model_name()` — centraliza a normalização de nomes de modelos LLM (remoção de sufixos de data, normalização de separadores de versão, capitalização, acrônimos `GPT`/`CLI`/`OSS`, prefixo `Claude`) — e seu uso em três call sites: Pass 1 e Pass 2 de `analyze_antigravity()` e o mapeamento de modelo em `analyze_claude_code()` (que substitui o antigo bloco `if/elif` inline). O novo formato de rótulo para modelos Claude (`Claude Sonnet 4.6` em vez de `Sonnet 4.6`) é o padrão definitivo; as linhas históricas do `TEMPO_DE_TRABALHO.md` são migradas para esse formato.

## Suggested Review Order

1. [Diff do Pass 1 corrigido](../../.tracker/work-tracker.py#L285-L320) — verificar que a regex agora captura o "to" e que `first_active_model` é normalizado e ancorado em `first_dt - 1ms`.
2. [Pass 2 inalterado](../../.tracker/work-tracker.py#L335-L360) — confirmar que as duas regex agora têm a mesma forma (captura única do "to"), eliminando a armadilha de manutenção.
3. [Propagação cronológica](../../.tracker/work-tracker.py#L394-L407) — confirmar que `current_anti_model` é atualizado pelos eventos `is_change` e atribuído aos pings.
4. [Documento de pesquisa](../planning-artifacts/research/technical-identificar-modelo-llm-antigravity-research-2026-05-19.md) — fonte da verdade para a decisão arquitetural.

## Review Findings

_Code review executado em 2026-05-19 (3 camadas adversariais: Blind Hunter, Edge Case Hunter, Acceptance Auditor)._

### Decisões Resolvidas (code review 2026-05-19)

- [x] [Review][Decision] **Escopo da spec excedido pelo diff** — RESOLVIDO: escopo expandido aceito; spec emendada (ver seção Intent → "Escopo expandido"). Sem mudança de código.
- [x] [Review][Decision] **Regressão de rótulos no `analyze_claude_code`** — RESOLVIDO: rename aceito (`Claude Sonnet 4.6` é o padrão); o histórico do `TEMPO_DE_TRABALHO.md` será migrado → vira patch.
- [x] [Review][Decision] **Regex `(\d+)-(\d+)` agressiva** — RESOLVIDO: padrão será restringido para não capturar sufixos de build longos → vira patch.

### Patches

- [x] [Review][Patch] **Pass 2 do Antigravity sem guarda `!= "None"`** [.tracker/work-tracker.py:338-342](.tracker/work-tracker.py#L338-L342) — Pass 1 protege contra `current_anti_model = "None"` ([.tracker/work-tracker.py:310](.tracker/work-tracker.py#L310)). Pass 2 não tem essa guarda: um `<USER_SETTINGS_CHANGE>` cujo "to" seja literal `None` (ou input inválido normalizado para `"None"`) propaga `"None"` como `current_anti_model` para pings subsequentes, criando uma linha de relatório espúria. Patch: trocar `if is_change:` por `if is_change and new_model and new_model != "None":` no bloco `events.append` (linha 344). Fonte: Edge Case Hunter.
- [x] [Review][Patch] **Restringir regex `(\d+)-(\d+)` de normalização** [.tracker/work-tracker.py:80](.tracker/work-tracker.py#L80) — Limitar a substituição hífen→ponto a versões curtas `X-Y` para não fundir versões distintas (ex: `gpt-4-1106-preview`). Resolução da Decision 3.
- [x] [Review][Patch] **Migrar rótulos históricos do `TEMPO_DE_TRABALHO.md`** [.tracker/TEMPO_DE_TRABALHO.md](.tracker/TEMPO_DE_TRABALHO.md) — Find/replace das linhas `Sonnet 4.6`/`Opus 4.7`/`Haiku 4.5` sem prefixo para `Claude Sonnet 4.6`/`Claude Opus 4.7`/`Claude Haiku 4.5`, unificando com o novo formato. Resolução da Decision 2.

### Deferred

- [x] [Review][Defer] **Regex `(.*?)\.` quebra com modelos cujo nome contém ponto** [.tracker/work-tracker.py:303,339](.tracker/work-tracker.py#L303) — Para um payload `"to Gemini 3.1 Pro."` o regex não-greedy captura `"Gemini 3"` (trunca no primeiro `.`). Pre-existente em Pass 2 antes desta spec; não introduzido pelo diff. Fonte: Edge Case Hunter.
- [x] [Review][Defer] **Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON** [.tracker/work-tracker.py:303,339](.tracker/work-tracker.py#L303) — `re.search` retorna apenas a primeira ocorrência; trocas adicionais na mesma entry são silenciosamente descartadas. Pre-existente em Pass 2. Fonte: Edge Case Hunter.
- [x] [Review][Defer] **`-\d{8}\b` pode comer sufixos numéricos não-data legítimos** [.tracker/work-tracker.py:76](.tracker/work-tracker.py#L76) — Entrada hipotética `model-12345678-beta` perderia `-12345678`. Latente: nenhum modelo dos dados atuais (Claude/Gemini) sofre. Fonte: Edge Case Hunter.

### Dismissed (não acionáveis)

Falsos positivos / cosméticos / hipotéticos: divergência fallback de fábrica (verificado: `normalize_model_name("Gemini 3.1 Pro (High)")` retorna a mesma string); colisão `sonnet`/`opus`/`haiku` em substrings de modelos hipotéticos não-Anthropic; capitalização inconsistente de `4o`/`4O` (documentada em comentário); linha em branco dupla; reatribuição de parâmetro; tratamento de `0` como falsy; filtro literal `"None"` com input vazio.

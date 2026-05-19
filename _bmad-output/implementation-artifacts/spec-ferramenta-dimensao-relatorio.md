---
title: 'Ferramenta como Dimensão Explícita no Relatório'
type: 'feature'
created: '2026-05-19'
status: 'done'
baseline_commit: 'b3284ae900f14e9f2c3c5fa849e0378bf0af9a3b'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O pipeline de agregação (`daily_stats`, `branch_stats`) e o relatório descartam o campo `tool` já presente em cada evento, agrupando tudo apenas por modelo LLM. Não é possível saber quanto tempo foi gasto em cada ferramenta (Claude Code vs. Antigravity), especialmente relevante porque o Antigravity também roda modelos Claude.

**Approach:** Propagar `tool` como chave de agrupamento em `daily_stats` e `branch_stats`, surfacear essa nova dimensão nas tabelas do relatório Markdown (nova coluna + nova seção de totais) e na saída de console.

## Boundaries & Constraints

**Always:**
- Manter inalterada a lógica de coleta (`analyze_claude_code`, `analyze_antigravity`), filtragem de pings vazios, mesclagem global, propagação de modelo (ADR-06), cálculo de sessões e gap de 45 min, padding de 15 min, anonimização SHA-256.
- Valores válidos para `tool`: `"Claude Code"` e `"Antigravity"`.
- Ordenação da Tabela 1: data → ferramenta → modelo.
- Imutabilidade de blocos de outros desenvolvedores no relatório.

**Ask First:**
- Se surgir evento com `tool` ausente ou valor inesperado durante os testes.

**Never:**
- Inferir ferramenta pelo nome do modelo — usar sempre `ev["tool"]`.
- Alterar a lógica de cálculo de horas, sessões ou interações.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Ambas ferramentas, mesmo dia | Eventos Claude Code e Antigravity com mesmo `date` | Tabela 1: linha por `(date, tool, model)`; seção de totais soma cada ferramenta separada | — |
| Mesmo modelo em duas ferramentas | `Sonnet 4.6` em Claude Code e Antigravity | Linhas distintas na Tabela 1; totais por ferramenta não colapsam o modelo | — |
| Branch com uma só ferramenta | `branch_stats[d][b]` tem só `"Claude Code"` | Ferramentas = "Claude Code"; Modelos = apenas os dessa ferramenta | — |

</frozen-after-approval>

## Code Map

- `.tracker/work-tracker.py:46` -- `format_hours(hours)` — converte float para "Xh YYm"
- `.tracker/work-tracker.py:140` -- `ev["tool"] = "Claude Code"` (em `analyze_claude_code`)
- `.tracker/work-tracker.py:204,238,248` -- `ev["tool"] = "Antigravity"` (em `analyze_antigravity`)
- `.tracker/work-tracker.py:319` -- definição de `daily_stats` — atualmente `[date][model]`
- `.tracker/work-tracker.py:320` -- definição de `branch_stats` — atualmente `[date][branch][model]`
- `.tracker/work-tracker.py:328,337-338,359-360` -- acessos de leitura/escrita em `daily_stats`
- `.tracker/work-tracker.py:334,338,364` -- acessos de leitura/escrita em `branch_stats`
- `.tracker/work-tracker.py:398-408` -- geração da Tabela 1 (Detalhamento Diário)
- `.tracker/work-tracker.py:414-427` -- geração da Tabela 2 (Detalhamento por Branch)
- `.tracker/work-tracker.py:451-457` -- saída de console: métricas por modelo
- `.tracker/TEMPO_DE_TRABALHO.md` -- relatório gerado; validar output manualmente

## Tasks & Acceptance

**Execution:**
- [x] `.tracker/work-tracker.py:319-320` -- Adicionar `tool` como nível intermediário: `daily_stats[date][tool][model]` e `branch_stats[date][branch][tool][model]` — pré-requisito para todas as demais tarefas
- [x] `.tracker/work-tracker.py:328,337-338,359-360,452-454` -- Atualizar todos os acessos a `daily_stats` para incluir `ev["tool"]` na chave, mantendo semântica idêntica
- [x] `.tracker/work-tracker.py:334,338,364` -- Atualizar todos os acessos a `branch_stats` para incluir `ev["tool"]` na chave
- [x] `.tracker/work-tracker.py:398-408` -- Adicionar coluna `Ferramenta` entre `Dia de Trabalho` e `Modelo LLM` na Tabela 1; atualizar loop para iterar `daily_stats[d][tool][model]` com ordenação `date → tool → model`
- [x] `.tracker/work-tracker.py` (inserir antes da Tabela 1) -- Seção `### 🛠️ Totais por Ferramenta` com tabela `| Ferramenta | Tempo Ativo | Interações |` somando sobre todos os dias e modelos por ferramenta
- [x] `.tracker/work-tracker.py:414-427` -- Substituir coluna `Modelos Utilizados` por `Ferramentas` + `Modelos Utilizados`; extrair ferramentas de `branch_stats[d][b].keys()`, modelos iterando todas as ferramentas
- [x] `.tracker/work-tracker.py:451-457` -- Saída de console: adicionar bloco agrupado por ferramenta antes do total combinado

**Acceptance Criteria:**
- Dado eventos de Claude Code e Antigravity, quando o relatório é gerado, então a Tabela 1 contém coluna `Ferramenta` com valores `**Claude Code**` ou `**Antigravity**` em cada linha.
- Dado mesmo modelo em duas ferramentas no mesmo dia, quando gerado, então aparecem linhas separadas por ferramenta (não colapsadas) na Tabela 1.
- Dado qualquer estado de eventos, quando gerado, então a seção `### 🛠️ Totais por Ferramenta` aparece imediatamente antes da Tabela 1 com totais corretos por ferramenta.
- Dado eventos com branch ativa, quando gerado, então a Tabela 2 exibe coluna `Ferramentas` com ferramentas distintas daquela branch/dia e `Modelos Utilizados` com todos os modelos daquela branch/dia.
- Dado execução sem `--export`, quando impresso no console, então métricas aparecem agrupadas por ferramenta com cabeçalhos `[Ferramenta]` antes do total combinado.
- Dado os mesmos eventos de entrada, quando comparado antes e depois da mudança, então os totais combinados de horas e interações são idênticos.

## Design Notes

**Estrutura `daily_stats` após mudança:**
```python
daily_stats[date_str][tool_name][model_name] = {"hours": 0.0, "sessions": 0, "interactions": 0}
```

**Extração de modelos na Tabela 2 (nova lógica):**
```python
tools = sorted(branch_stats[d][b].keys())
models = sorted({m for t in branch_stats[d][b].values() for m in t.keys()})
```

**`model_totals` para console** deve ser recalculado iterando `daily_stats[d][tool][model]` (dois níveis antes de acessar model) para não quebrar o total combinado.

## Verification

**Manual checks:**
- Executar `python3 .tracker/work-tracker.py` e verificar em `.tracker/TEMPO_DE_TRABALHO.md`: (1) coluna `Ferramenta` na Tabela 1, (2) seção `🛠️ Totais por Ferramenta` antes da Tabela 1, (3) colunas `Ferramentas` e `Modelos Utilizados` na Tabela 2.
- Verificar no console que as métricas aparecem agrupadas por ferramenta com cabeçalhos `[Ferramenta]`.
- Confirmar que os totais combinados (horas + interações) são idênticos aos de antes da mudança.

## Suggested Review Order

**Estrutura de dados central**

- Nova dimensão `tool` adicionada como nível intermediário em `daily_stats` e `branch_stats`
  [`work-tracker.py:319`](../../.tracker/work-tracker.py#L319)

**Loop de acumulação — sessões e interações**

- Chave de sessão muda de `(model)` para `(tool, model)` — garante separação por ferramenta
  [`work-tracker.py:326`](../../.tracker/work-tracker.py#L326)

- Duração distribuída por `tool_model_duration_minutes[tool][model]` em vez de modelo puro
  [`work-tracker.py:340`](../../.tracker/work-tracker.py#L340)

- Padding de 15 min aplicado à última ferramenta/modelo — lógica inalterada, nova chave
  [`work-tracker.py:356`](../../.tracker/work-tracker.py#L356)

- Acúmulo de horas em `daily_stats[date][tool][model]`; `total_hours` preservado inalterado
  [`work-tracker.py:359`](../../.tracker/work-tracker.py#L359)

**Geração do relatório Markdown**

- Nova seção `🛠️ Totais por Ferramenta` gerada somando horas e interações por ferramenta
  [`work-tracker.py:404`](../../.tracker/work-tracker.py#L404)

- Tabela 1: coluna `Ferramenta` inserida; loop itera `date → tool → model`
  [`work-tracker.py:427`](../../.tracker/work-tracker.py#L427)

- Tabela 2: `Ferramentas` extraída de `branch_stats[d][b].keys()`; modelos achatados via comprehension
  [`work-tracker.py:445`](../../.tracker/work-tracker.py#L445)

**Saída de console**

- Métricas agrupadas por `[Ferramenta]` antes do total combinado
  [`work-tracker.py:489`](../../.tracker/work-tracker.py#L489)

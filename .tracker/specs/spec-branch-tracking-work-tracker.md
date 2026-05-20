---
title: 'Rastreamento de Tempo por Branch no work-tracker'
type: 'feature'
created: '2026-05-19'
status: 'done'
baseline_commit: 'deb11b49f12be8407ac9b228b15f41b28dbb7285'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `work-tracker.py` consolida tempo apenas por Dia e Modelo LLM. Não há visibilidade de quanto esforço foi investido por branch/história, impossibilitando análise de custo por feature.

**Approach:** Parsear `.git/logs/HEAD` para reconstruir uma timeline de checkouts; mapear cada ping de IA para a branch ativa no momento exato; acumular um novo bucket `branch_stats[dia][branch][modelo]`; renderizar tabela extra no bloco `--export`.

## Boundaries & Constraints

**Always:**
- Toda a lógica de branch reside em `.tracker/work-tracker.py` — sem novos arquivos.
- Atribuição de branch é determinística: para cada timestamp de ping, encontrar a entrada de checkout mais recente no reflog com `entry_dt <= ping_dt`.
- Se `.git/logs/HEAD` não existir ou estiver vazio, atribuir `"main"` a todos os pings.
- Linhas corrompidas do reflog são ignoradas silenciosamente (sem raise).

**Ask First:**
- Se o teste manual produzir mais de 15 branches distintas no relatório, avaliar com o desenvolvedor se agrupamento por prefixo (`feature/*`) é desejável antes de prosseguir.

**Never:**
- Não executar `git reflog` como subprocess — ler `.git/logs/HEAD` diretamente.
- Não modificar a seção de Detalhamento Diário global existente.
- Não introduzir dependências externas além da stdlib Python.

## I/O & Edge-Case Matrix

| Cenário | Entrada | Saída Esperada | Tratamento de Erro |
|---------|---------|---------------|--------------------|
| Reflog presente, múltiplas branches | `.git/logs/HEAD` com checkouts entre `main` e `time-tracker` | Pings antes do checkout → `main`; após → `time-tracker` | N/A |
| Reflog ausente ou vazio | Arquivo não existe | Todos os pings recebem branch `"main"` | fallback `"main"` |
| Ping anterior a qualquer entrada de checkout | Timestamp menor que todo reflog | Branch `"main"` | retorno explícito |
| Linha corrompida no reflog | Linha sem timestamp válido | Linha ignorada, demais processadas | `try/except`, continua |
| `--export` sem pings coletados | Nenhum evento | Tabela de branch exibe `N/A` (igual à tabela diária existente) | N/A |

</frozen-after-approval>

## Code Map

- `.tracker/work-tracker.py:1-385` — arquivo único a modificar; contém `analyze_claude_code`, `analyze_antigravity` e `main()`
- `.git/logs/HEAD` — fonte de dados do reflog (somente leitura); formato: `<old_sha> <new_sha> Author <email> <unix_ts> <tz>\t<message>`

## Tasks & Acceptance

**Execution:**
- [x] `.tracker/work-tracker.py` -- adicionar `build_branch_timeline(repo_root)` após `format_hours` -- lê `.git/logs/HEAD`, filtra linhas de checkout (`checkout: moving from X to Y`), retorna lista de `(entry_dt_utc, branch_name)` ordenada cronologicamente; retorna `[]` se arquivo ausente ou sem checkouts
- [x] `.tracker/work-tracker.py` -- adicionar `get_branch_at(timeline, ping_dt)` após `build_branch_timeline` -- varre a timeline do fim para o início, retorna a `branch_name` da primeira entrada com `entry_dt <= ping_dt`; retorna `"main"` se timeline vazia, `"Desconhecida"` se ping é anterior a toda a timeline
- [x] `.tracker/work-tracker.py` -- em `main()`, chamar `branch_timeline = build_branch_timeline(repo_root)` antes do loop de construção de `ping_events`
- [x] `.tracker/work-tracker.py` -- após a construção de `ping_events`, anotar cada evento com `ev["branch"] = get_branch_at(branch_timeline, ev["dt_br"])`
- [x] `.tracker/work-tracker.py` -- criar `branch_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0})))` e populá-lo no loop de sessões usando `branch_stats[date_str][ev["branch"]][ev["active_model"]]`, replicando a mesma lógica de duração de `daily_stats`
- [x] `.tracker/work-tracker.py` -- no bloco `--export`, após a tabela de Detalhamento Diário existente em `new_block`, acrescentar seção `### 🌿 Detalhamento Diário por Branch / História (Brasília)` com colunas `| Dia de Trabalho | Branch Ativa | Modelos Utilizados | Tempo Ativo | Interações |`; agregar `branch_stats` por `(dia, branch)`, listando modelos distintos separados por vírgula em ordem alfabética

**Acceptance Criteria:**
- Dado que `.git/logs/HEAD` contém ao menos um checkout, quando `work-tracker.py --export` é executado, então `TEMPO_DE_TRABALHO.md` contém a seção `### 🌿 Detalhamento Diário por Branch / História` com ao menos uma linha de dados.
- Dado que `.git/logs/HEAD` não existe, quando `work-tracker.py --export` é executado, então o relatório é gerado sem erro e todas as linhas de branch exibem `main`.
- Dado que existe ping cujo timestamp é anterior a qualquer entrada do reflog, quando o script processa esse ping, então a coluna Branch exibe `Desconhecida`.
- Dado que a tabela de branch é gerada, quando `TEMPO_DE_TRABALHO.md` é inspecionado, então a tabela diária global preexistente permanece inalterada.

## Design Notes

**Parsing do `.git/logs/HEAD`:**
Cada linha tem o formato `<old> <new> Author <email> <unix_ts> <tz>\tcheckout: moving from <X> to <Y>`. A mensagem está separada por tab. Extrair `<Y>` com `re.search(r"checkout: moving from .+ to (.+)", msg)` e converter `<unix_ts>` com `datetime.utcfromtimestamp(int(unix_ts))`.

**Coluna "Modelos Utilizados":**
Para cada combinação `(dia, branch)`, coletar todos os modelos distintos e renderizá-los como `", ".join(sorted(models))` para output determinístico.

## Suggested Review Order

**Reconstrução da timeline de branches (reflog)**

- Ponto de entrada: parsing do `.git/logs/HEAD`; filtro de checkouts + conversão UTC→Brasília.
  [`work-tracker.py:56`](../../.tracker/work-tracker.py#L56)

- Lookup binário/linear: retorna branch ativa em `ping_dt`; fallbacks para timeline vazia e pings pré-históricos.
  [`work-tracker.py:85`](../../.tracker/work-tracker.py#L85)

**Anotação dos pings e acumulação por branch**

- Branch timeline construída antes do parsing de eventos; anotação de `ev["branch"]` por ping.
  [`work-tracker.py:275`](../../.tracker/work-tracker.py#L275)

- Loop de anotação: cada ping recebe branch via `get_branch_at`.
  [`work-tracker.py:302`](../../.tracker/work-tracker.py#L302)

- Bucket tridimensional `branch_stats[dia][branch][modelo]`; lógica de duração espelha `daily_stats`.
  [`work-tracker.py:320`](../../.tracker/work-tracker.py#L320)

**Renderização no relatório exportado**

- Seção `🌿` sempre escrita após tabela global; linhas de dados ou fallback `N/A`.
  [`work-tracker.py:414`](../../.tracker/work-tracker.py#L414)

## Verification

**Commands:**
- `python3 .tracker/work-tracker.py` -- expected: saída no terminal sem stack trace
- `python3 .tracker/work-tracker.py --export && grep -A 5 "Detalhamento Diário por Branch" .tracker/TEMPO_DE_TRABALHO.md` -- expected: seção presente com cabeçalho de tabela
- `make -f .tracker/Makefile track-time EXPORT=true` -- expected: `✔ Métricas de tempo atualizadas com sucesso`

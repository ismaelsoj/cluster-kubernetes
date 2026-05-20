# 📋 Backlog — Rastreador de Tempo de Desenvolvimento (IA)

Registro centralizado de melhorias, novas funcionalidades e dívida técnica identificados em revisões e sessões de análise. Cada item está categorizado por tipo e prioridade para refinamento futuro.

> [!NOTE]
> Este backlog foi criado a partir do Party Mode review (2026-05-20) com os agentes Mary (Analista), Winston (Arquiteto), Amelia (Dev) e John (PM), além de itens previamente rastreados no `deferred-work.md`.

---

## 🥇 Prioridade Alta — Alto Impacto, Viabilidade Comprovada

### BKL-001: Rastreamento de Tokens (Claude Code)
- **Tipo:** Feature
- **Origem:** Party Mode (Amelia, John, Mary, Winston)
- **Status:** Pronto para implementação
- **Descrição:** O JSONL do Claude Code já contém o campo `usage` com dados ricos:
  - `input_tokens` — tokens de entrada
  - `output_tokens` — tokens de saída
  - `cache_creation_input_tokens` — tokens de criação de cache
  - `cache_read_input_tokens` — tokens lidos do cache
- **Impacto:** Permite estimar custo por modelo, responder "quanto estamos gastando com Opus vs Sonnet" e gerar métricas de investimento além de métricas de esforço.
- **Nota Técnica:** Dados disponíveis em `message.usage` nos entries do tipo `assistant` nos arquivos JSONL.

### BKL-002: Rastreamento de Tokens (Antigravity) — Inviável Atualmente
- **Tipo:** Pesquisa / Limitação Técnica
- **Origem:** Party Mode (investigação 2026-05-20)
- **Status:** ⛔ Bloqueado — sem dados disponíveis
- **Descrição:** Os logs `overview.txt` do Antigravity **não contêm** informações de tokens (`usage`, `token`, `cost`, `billing`). Os dados de consumo ficam:
  - Nos arquivos `.pb` (Protocol Buffers criptografados — inacessíveis sem schema)
  - Nos endpoints internos do backend da IDE (não persistidos localmente)
- **Ação:** Monitorar atualizações do Antigravity que possam expor dados de uso nos logs. Até lá, o rastreamento de tokens fica restrito ao Claude Code.

### BKL-003: Export JSON/CSV
- **Tipo:** Feature
- **Origem:** Party Mode (Amelia, John, Winston)
- **Descrição:** Adicionar flag `--format json` e `--format csv` para exportar os dados em formato estruturado, desbloqueando análise externa (Jupyter, Pandas, planilhas).
- **Impacto:** Desbloqueia toda a camada de análise sem precisar mudar o core. O Markdown permanece como view principal, mas dados ficam acessíveis para uso programático.

### BKL-004: Regex de modelo trunca nomes com ponto
- **Tipo:** Bug (pre-existente)
- **Origem:** Deferred work (code review 2026-05-19)
- **Descrição:** Regex `(.*?)\.` em Pass 1/2 do Antigravity trunca nomes de modelo com ponto no nome de exibição. Payload `"to Gemini 3.1 Pro."` captura `"Gemini 3"`.
- **Correção proposta:** Usar sentinela mais robusto: `(.*?)(?:\.\s|\.?$)` ou ancorar ao delimitador específico do payload da IDE.

---

## 🥈 Prioridade Média — Melhorias de Qualidade Significativas

### BKL-005: Refatorar `main()` (296 linhas)
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Amelia, Winston)
- **Descrição:** Separar em funções puras composáveis:
  - `collect_events()` → coleta de ambas as ferramentas
  - `merge_and_sort()` → mesclagem cronológica
  - `compute_sessions()` → agrupamento por gap
  - `aggregate_stats()` → acumulação de métricas
  - `render_report()` → geração de saída
- **Impacto:** Testabilidade, manutenibilidade, capacidade de testar lógica de negócios isoladamente.

### BKL-006: Testes Unitários
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Amelia)
- **Descrição:** Criar suite de testes para:
  - `parse_iso()` — 4 formatos + fallback
  - `normalize_model_name()` — edge cases de normalização
  - `build_branch_timeline()` / `get_branch_at()` — mapeamento de branches
  - `parse_existing_developers_stats()` — re-ingestão de Markdown
  - Lógica de sessão (gap, padding, midnight crossing)
- **Impacto:** Garantir regressão zero em futuras mudanças (698 linhas sem testes é risco alto).

### BKL-007: Persistência JSON canônica (separar dados de apresentação)
- **Tipo:** Feature / Arquitetura
- **Origem:** Party Mode (Winston)
- **Descrição:** Persistir dados em `.tracker/data.json` como formato canônico e gerar Markdown como view. Eliminaria toda a complexidade de `parse_existing_developers_stats()` (regex parsing do próprio output) e tornaria consolidação multi-dev trivial (deep merge de JSONs).
- **Trade-off:** Mudança arquitetural significativa. O Markdown atual como fonte da verdade funciona, mas é frágil. Qualquer mudança no layout de tabela quebra a re-ingestão.

### BKL-008: Tendência Temporal (Week-over-Week)
- **Tipo:** Feature
- **Origem:** Party Mode (Mary, John)
- **Descrição:** Adicionar sumário de tendência semanal/mensal no relatório. Responde: "Estamos acelerando ou desacelerando?" Pode ser simples: total de horas por semana com delta percentual.

### BKL-009: Estimativa de Custo por Modelo
- **Tipo:** Feature
- **Origem:** Party Mode (Mary, John, Winston)
- **Descrição:** Usando tokens coletados (BKL-001), estimar custo em USD por modelo com base em tabela de preços. Transforma o relatório de "métrica de esforço" em "métrica de investimento".
- **Dependência:** BKL-001 (tokens do Claude Code)
- **Nota:** Preços do Antigravity são opacos (cobrados por assinatura, não por token), então a estimativa seria restrita ao Claude Code.

### BKL-010: Detached HEAD capturado como SHA de branch
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (feature branch-tracking 2026-05-19)
- **Descrição:** `build_branch_timeline` captura verbatim o alvo de checkout. Em detached HEAD, o "nome de branch" é um SHA abreviado.
- **Correção proposta:** Pós-processamento: se destino parecer SHA (`^[0-9a-f]{7,40}$`), substituir por `"(detached HEAD)"`.

### BKL-011: Sessões cruzando meia-noite
- **Tipo:** Bug
- **Origem:** Deferred work (feature ferramenta-dimensao 2026-05-19)
- **Descrição:** `date_str = sess[0]["dt_br"].strftime(...)` atribui toda a sessão à data do primeiro evento. Sessões que cruzam meia-noite acumulam horas do dia seguinte no dia anterior.
- **Correção proposta:** Dividir a sessão no limite da meia-noite e distribuir proporcionalmente.

### BKL-012: Gap entre ferramentas diferentes descartado silenciosamente
- **Tipo:** Bug
- **Origem:** Party Mode (Amelia)
- **Descrição:** Linha 487: `if sess[i]["tool"] != sess[i+1]["tool"]: continue`. Quando dev alterna Antigravity → Claude Code → Antigravity, os gaps entre ferramentas são perdidos. O tempo total reportado é menor que o real.
- **Impacto:** Subestimação do tempo de trabalho em sessões com alternância frequente de ferramenta.

---

## 🥉 Prioridade Baixa — Melhorias Incrementais

### BKL-013: Versionamento do formato de dados
- **Tipo:** Feature
- **Origem:** Party Mode (Winston)
- **Descrição:** Adicionar `format_version: X` no header do relatório para permitir migração programática quando o layout de tabela mudar.

### BKL-014: Fuso Horário hardcoded (UTC-3)
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Winston)
- **Descrição:** Usar `zoneinfo.ZoneInfo("America/Sao_Paulo")` (Python 3.9+) ou `datetime.timezone(timedelta(hours=-3))` para tratar DST e suportar múltiplos fusos sem mudança.

### BKL-015: `normalize_model_name()` como ponto de fragilidade
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Winston)
- **Descrição:** 44 linhas de heurísticas dependem de conhecimento prévio dos modelos. Cada novo modelo pode precisar de ajustes. Considerar lookup table + fallback para normalização desconhecida.

### BKL-016: `to_brasilia()` ignora timezone-aware datetimes
- **Tipo:** Bug potencial
- **Origem:** Party Mode (Amelia)
- **Descrição:** `dt.replace(tzinfo=None)` na linha 424 descarta timezone info antes da conversão. Se `parse_iso()` retornar datetime com `tzinfo`, a subtração de 3h está errada.

### BKL-017: `extract_repo_name()` nunca usado efetivamente
- **Tipo:** Código morto
- **Origem:** Party Mode (Amelia)
- **Descrição:** A função é chamada mas `repo_name` não é usado para filtragem. O filtro real usa `belongs_to_repo` com path matching direto. Candidato a remoção.

### BKL-018: Change events sem filtro `belongs_to_repo`
- **Tipo:** Bug potencial
- **Origem:** Party Mode (Amelia)
- **Descrição:** Em `analyze_antigravity()`, eventos `is_change` (trocas de modelo) são emitidos sem filtro de repositório. Pode ser intencional (modelo muda globalmente) ou poluição de eventos de outros repos. Clarificar e documentar a decisão.

### BKL-019: Detecção de Anomalias
- **Tipo:** Feature
- **Origem:** Party Mode (Mary)
- **Descrição:** Flag automático para: sessões < 5 min, interações sem tempo registrado, modelos com 0 sessões mas > 0 interações. Ajuda a identificar outliers e contexto switching improdutivo.

### BKL-020: Tamanho da Conversa (turnos por sessão)
- **Tipo:** Feature
- **Origem:** Party Mode (Amelia)
- **Descrição:** Rastrear número de turnos por sessão — diferencia sessões exploratórias (muitos turnos curtos) de sessões produtivas (poucos turnos longos).

### BKL-021: Type Hints e logging
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Amelia)
- **Descrição:** Adicionar type hints (`mypy --strict`) e substituir `try/except: pass` por logging estruturado para facilitar debugging.

### BKL-022: Inter-branch gap attribution
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (feature branch-tracking 2026-05-19)
- **Descrição:** Quando sessão atravessa checkout, gap entre pings de branches diferentes é inteiramente atribuído à branch anterior.

### BKL-023: Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (code review 2026-05-19)
- **Descrição:** `re.search` captura apenas a primeira ocorrência; trocas adicionais na mesma entry são descartadas.

### BKL-024: Inconsistência de padrão de guarda de tabelas vazias
- **Tipo:** Dívida técnica
- **Origem:** Deferred work (feature ferramenta-dimensao 2026-05-19)
- **Descrição:** Tabela 1 usa `for...; if not:` (guarda após loop) vs Tabela 2 usa `if: for...; else:` (guarda antes). Padronizar.

### BKL-025: `get_branch_at()` retorna `"main"` vs spec diz `"Desconhecida"`
- **Tipo:** Bug / divergência de spec
- **Origem:** Party Mode (Amelia)
- **Descrição:** Linha 215 retorna `"main"` como fallback quando ping é anterior a qualquer checkout. A spec original dizia `"Desconhecida"`. Decidir qual é a verdade e alinhar.

---

## 📊 Resumo por Tipo

| Tipo | Quantidade |
|------|-----------|
| Feature | 8 |
| Bug / Bug potencial | 8 |
| Dívida técnica | 6 |
| Pesquisa / Bloqueado | 1 |
| Código morto | 1 |
| Divergência de spec | 1 |

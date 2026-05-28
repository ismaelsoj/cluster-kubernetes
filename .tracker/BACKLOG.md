# 📋 Backlog — Rastreador de Tempo de Desenvolvimento (IA)

Registro centralizado de melhorias, novas funcionalidades e dívida técnica. Ordenado por prioridade de implementação; itens concluídos consolidados ao final.

> [!NOTE]
> Origem: Party Mode review (2026-05-20) com Mary (Analista), Winston (Arquiteto), Amelia (Dev) e John (PM); Code Review Gauntlet (2026-05-21); análise de crescimento (2026-05-25). Última reorganização: 2026-05-25.

---

## 🥇 Prioridade Alta

### BKL-031: Modularizar `work-tracker.py` em pacote Python `tracker/`
- **Tipo:** Dívida técnica crítica
- **Origem:** Análise de crescimento orgânico (2026-05-25) — 1203 linhas, 8 responsabilidades distintas
- **Descrição:** O script atingiu o ponto de inflexão onde o modelo "single-file script" impede evolução sustentável. BKL-005 (✅) separou `main()` em funções — mas todas continuam no mesmo arquivo. Cada nova feature engorda o mesmo monólito; sem fronteiras de módulo, o acoplamento cresce inevitavelmente e os testes cobrem o sistema inteiro em vez de unidades isoladas. A refatoração é uma migração estrutural pura (move + import): zero alteração de comportamento.
- **Estrutura proposta:**
  ```
  .tracker/
  ├── work-tracker.py          # shim: from tracker.cli import main; main()
  └── tracker/
      ├── __init__.py
      ├── cli.py               # argparse + main()
      ├── models.py            # TypedDicts: Event, Session, DailyStats, BranchStats
      ├── utils.py             # parse_iso, to_brasilia, format_hours, format_tokens_*,
      │                        # normalize_model_name, parse_hours_from_str, date_to_iso
      ├── git_tracking.py      # build_branch_timeline, get_branch_at, extract_repo_name
      ├── parsers/
      │   ├── __init__.py
      │   ├── claude_code.py   # analyze_claude_code()
      │   └── antigravity.py   # analyze_antigravity()
      ├── events.py            # load_manifest, emit_events, load_all_events,
      │                        # collect_events, build_live_events
      ├── sessions.py          # compute_sessions, aggregate_sessions, _empty_stats
      └── renderers/
          ├── __init__.py
          ├── markdown.py      # render_report, export_markdown_report
          ├── console.py       # show_console_report
          ├── json_export.py   # export_json_report
          └── csv_export.py    # export_csv_report
  ```
- **Regras de migração:**
  1. **Zero alteração de comportamento** — cada função é movida intacta; bugs existentes ficam para seus próprios BKLs
  2. **`work-tracker.py` vira shim** — 2 linhas; Makefile não muda
  3. **`test_tracker.py` atualiza imports** — `from tracker.X import Y`
  4. **TypedDicts em `models.py`** — Python 3.8+, stdlib pura; sem breaking change nos callers
  5. **`__all__` em cada módulo** — explicita a API pública
- **Critérios de aceite:**
  - `make -f .tracker/Makefile track-time` produz saída idêntica antes/depois
  - Todos os testes existentes passando após atualização de imports
  - Nenhum arquivo novo ultrapassa 250 linhas
  - `python3 -c "from tracker.cli import main"` funciona sem erros
- **Impacto:** Pré-requisito estrutural para BKL-008, BKL-019 e BKL-032; habilita BKL-021 (type hints) módulo a módulo; teto de crescimento sai de "1 arquivo × N linhas" para "N arquivos × ~200 linhas"
- **Estimativa:** 3–4h (migração) + 1h (imports nos testes)
- **Dependência:** Nenhuma

---

## 🥈 Prioridade Média

### BKL-012: Gap entre ferramentas diferentes descartado silenciosamente
- **Tipo:** Bug
- **Origem:** Party Mode (Amelia)
- **Descrição:** `if sess[i]["tool"] != sess[i+1]["tool"]: continue` (L628). Quando dev alterna Antigravity → Claude Code → Antigravity, os gaps entre ferramentas são perdidos — o tempo total reportado é menor que o real.
- **Impacto:** Subestimação direta de horas em sessões com alternância frequente de ferramenta.
- **Correção proposta:** Remover o guard de tool e atribuir o gap ao modelo do evento anterior, independentemente da ferramenta.

### BKL-011: Sessões cruzando meia-noite
- **Tipo:** Bug
- **Origem:** Deferred work (feature ferramenta-dimensao 2026-05-19)
- **Descrição:** `date_str = sess[0]["dt_br"].strftime(...)` atribui toda a sessão à data do primeiro evento. Sessões que cruzam 00:00 acumulam horas do dia seguinte no dia anterior.
- **Correção proposta:** Dividir a sessão no limite da meia-noite e distribuir proporcionalmente.

### BKL-008: Tendência Temporal (Week-over-Week)
- **Tipo:** Feature
- **Origem:** Party Mode (Mary, John)
- **Descrição:** Sumário de tendência semanal/mensal no relatório. Responde: "Estamos acelerando ou desacelerando?" Pode ser simples: total de horas por semana com delta percentual.

### BKL-032: Cursor como terceira fonte de tempo ativo
- **Tipo:** Feature
- **Origem:** Decisão de produto (2026-05-27)
- **Descrição:** Coletar atividade local do Cursor como terceira fonte de tempo ativo, comparável a Claude Code e Antigravity, usando o banco SQLite local `~/.cursor/ai-tracking/ai-code-tracking.db` em modo read-only com `schema_guard`. O coletor deve agrupar atividade por `conversationId/source/model`, preservar métricas nativas do Cursor como enriquecimento opcional e não redefinir o produto como analytics de proveniência de código.
- **Dependência:** BKL-031 (modularização)
- **Nota:** A leitura do banco deve ser defensiva, offline, sem escrita no banco real e com degradação graciosa quando Cursor não estiver instalado ou quando o schema upstream divergir.

### BKL-010: Detached HEAD capturado como SHA de branch
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (feature branch-tracking 2026-05-19)
- **Descrição:** `build_branch_timeline` captura verbatim o alvo de checkout. Em detached HEAD, o "nome de branch" é um SHA abreviado.
- **Correção proposta:** Pós-processamento: se destino match `^[0-9a-f]{7,40}$`, substituir por `"(detached HEAD)"`.

---

## 🥉 Prioridade Baixa

### BKL-016: `to_brasilia()` ignora timezone-aware datetimes
- **Tipo:** Bug potencial
- **Origem:** Party Mode (Amelia)
- **Descrição:** `dt.replace(tzinfo=None)` descarta timezone info antes da conversão. Se `parse_iso()` retornar datetime com `tzinfo`, a subtração de 3h está errada.

### BKL-018: Change events sem filtro `belongs_to_repo`
- **Tipo:** Bug potencial
- **Origem:** Party Mode (Amelia)
- **Descrição:** Em `analyze_antigravity()`, eventos `is_change` (trocas de modelo) são emitidos sem filtro de repositório. Pode ser intencional (modelo muda globalmente) ou poluição de eventos de outros repos. Decisão arquitetural pendente de documentação.

### BKL-023: Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON descartados
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (code review 2026-05-19)
- **Descrição:** `re.search` captura apenas a primeira ocorrência; trocas adicionais na mesma entry são descartadas silenciosamente.
- **Correção proposta:** Substituir por `re.findall` e iterar sobre todas as ocorrências.

### BKL-022: Inter-branch gap attribution
- **Tipo:** Bug (menor)
- **Origem:** Deferred work (feature branch-tracking 2026-05-19)
- **Descrição:** Quando sessão atravessa checkout, o gap entre pings de branches diferentes é inteiramente atribuído à branch anterior.

### BKL-025: `get_branch_at()` retorna `"main"` — spec diz `"Desconhecida"`
- **Tipo:** Bug / divergência de spec
- **Origem:** Party Mode (Amelia)
- **Descrição:** L247 e L255 retornam `"main"` como fallback quando ping é anterior a qualquer checkout. A spec original dizia `"Desconhecida"`. Decidir e alinhar.

### BKL-021: Type Hints e logging estruturado
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Amelia)
- **Descrição:** Adicionar type hints (`mypy --strict`) e substituir `try/except: pass` por logging estruturado. Mais fácil de endereçar módulo a módulo após BKL-031.
- **Dependência recomendada:** BKL-031 (modularização)

### BKL-015: `normalize_model_name()` como ponto de fragilidade
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Winston)
- **Descrição:** 44 linhas de heurísticas dependem de conhecimento prévio dos modelos. Cada novo modelo pode exigir ajuste manual. Considerar lookup table + fallback para normalização desconhecida.

### BKL-014: Fuso Horário hardcoded (UTC-3)
- **Tipo:** Dívida técnica
- **Origem:** Party Mode (Winston)
- **Descrição:** Usar `zoneinfo.ZoneInfo("America/Sao_Paulo")` (Python 3.9+) para tratar DST corretamente e suportar múltiplos fusos sem mudança de código.

### BKL-024: Inconsistência de padrão de guarda de tabelas vazias
- **Tipo:** Dívida técnica
- **Origem:** Deferred work (feature ferramenta-dimensao 2026-05-19)
- **Descrição:** Tabela 1 usa `for...; if not:` (guarda após loop) vs Tabela 2 usa `if: for...; else:` (guarda antes). Padronizar para um único estilo.

### BKL-019: Detecção de Anomalias
- **Tipo:** Feature
- **Origem:** Party Mode (Mary)
- **Descrição:** Flag automático para: sessões < 5 min, interações sem tempo registrado, modelos com 0 sessões mas > 0 interações. Ajuda a identificar outliers e context-switching improdutivo.

### BKL-020: Tamanho da Conversa (turnos por sessão)
- **Tipo:** Feature
- **Origem:** Party Mode (Amelia)
- **Descrição:** Rastrear número de turnos por sessão — diferencia sessões exploratórias (muitos turnos curtos) de sessões produtivas (poucos turnos longos).

### BKL-013: Versionamento do formato de dados
- **Tipo:** Feature
- **Origem:** Party Mode (Winston)
- **Descrição:** Adicionar `format_version: X` no header do relatório para permitir migração programática quando o layout de tabela mudar.

### BKL-017: `extract_repo_name()` — código morto
- **Tipo:** Código morto
- **Origem:** Party Mode (Amelia)
- **Descrição:** A função é chamada (L343) mas `repo_name` não é usado para filtragem. O filtro real usa `belongs_to_repo` com path matching direto. Candidato a remoção simples.

---

## ⛔ Bloqueados

### BKL-002: Rastreamento de Tokens (Antigravity) — Inviável Atualmente
- **Tipo:** Pesquisa / Limitação Técnica
- **Origem:** Party Mode (2026-05-20) / Pesquisa Técnica (2026-05-20)
- **Descrição:** Os logs `transcript.jsonl` do Antigravity e o armazenamento binário `.pb` **não expõem** dados de consumo de tokens de forma acessível localmente.
- **Ação:** Monitorar atualizações do Antigravity; sugerir Feature Request para incluir `"usage": {"input_tokens": X, "output_tokens": Y}` nos logs JSONL futuros. O rastreamento permanece baseado em tempo ativo para o Antigravity.

---

## 🚫 Removidos do Escopo

### BKL-009: Estimativa de Custo por Modelo
- **Tipo:** Feature removida
- **Origem:** Party Mode (Mary, John, Winston); decisão de produto (2026-05-27)
- **Decisão:** Removido definitivamente do escopo. O tracker não trabalhará com preços, custo monetário ou estimativas em USD em nenhuma ferramenta.
- **Justificativa:** Preços variam entre plataformas, planos e contratos, gerando manutenção contínua e ambiguidade indesejada.
- **Nota:** Tokens continuam sendo coletados quando disponíveis (FR17) para usos analíticos, mas não serão multiplicados por tabela de preços.

---

## ✅ Concluídos

| ID | Descrição | Tipo | Entrega |
|----|-----------|------|---------|
| BKL-001 | Rastreamento de Tokens (Claude Code) | Feature | commit `1b952e6` |
| BKL-003 | Export JSON/CSV (`--format json/csv`) | Feature | commits `d678aa5` + `1399e04` |
| BKL-004 | Regex truncava nomes de modelo com ponto | Bug | regex `(?:\. No need\|\.?\s*$)` |
| BKL-005 | Refatorar `main()` (296 linhas) em funções composáveis | Dívida técnica | — |
| BKL-006 | Suite de testes unitários (`test_tracker.py`) | Dívida técnica | — |
| BKL-007 | Persistência JSON canônica (arquitetura orientada a eventos) | Arquitetura | `.tracker/events/` |
| BKL-026 | Antigravity truncava eventos (`overview.txt` → `transcript.jsonl`) | Bug | — |
| BKL-027 | Escrita não-atômica em `emit_events()` | Bug (integridade) | `os.replace()` após `.tmp` |
| BKL-028 | `load_all_events()` sem `try/except` por linha | Bug | `json.JSONDecodeError` no loop |
| BKL-029 | `last_updated_str` hardcodado como `"23:59:59"` | Bug | campo renomeado para `last_active_date` |

---

## 📊 Resumo — Itens Abertos

| Tipo | Abertos |
|------|---------|
| Feature | 5 |
| Bug / Bug potencial | 8 |
| Dívida técnica | 5 |
| Pesquisa / Bloqueado | 1 |
| Código morto | 1 |
| **Total aberto** | **20** |
| ✅ Concluídos | 10 |
| 🚫 Removidos do escopo | 1 |
| **Total geral** | **31** |

---

**Autoria/Implementação:** Party Mode review (2026-05-20) + reorganizações históricas registradas no documento
**Revisão:** GPT-5 (Codex)

## Change Log

| Data/Hora (BRT) | Autor | Alteração |
|---|---|---|
| 2026-05-27 22:54:37-03:00 | GPT-5 (Codex) | BKL-009 movido para removidos do escopo; BKL-032 criado para Cursor como terceira fonte de tempo ativo; resumo de itens atualizado. |

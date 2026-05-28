---
stepsCompleted: [1, 2, 3, 4, 5, 6]
includedDocuments:
  prd:
    - .tracker/BACKLOG.md
  architecture:
    - .tracker/docs-archive/work-tracker-architecture.md
  epics:
    - .tracker/_bmad-output/planning-artifacts/epics.md
  sprintChangeProposal:
    - .tracker/_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-27.md
  ux: []
missingDocuments:
  - ux
generatedAt: "2026-05-27 23:06:04-03:00"
authoringModel: "GPT-5"
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-27
**Project:** cluster-kubernetes / .tracker

## Step 1: Document Discovery

### Documentos Selecionados Para Avaliação

**PRD / Requisitos**
- `.tracker/BACKLOG.md` — documento equivalente a PRD para o subprojeto tracker.

**Arquitetura**
- `.tracker/docs-archive/work-tracker-architecture.md` — documento equivalente a arquitetura para o subprojeto tracker.

**Épicos e Histórias**
- `.tracker/_bmad-output/planning-artifacts/epics.md` — breakdown de épicos e histórias recém-estruturado.

**Sprint Change Proposal**
- `.tracker/_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-27.md` — proposta aprovada a considerar como ajuste vinculante da avaliação.

**UX**
- Nenhum documento UX encontrado. Marcado como ausente/não aplicável até confirmação em análise posterior.

### Issues de Descoberta

- Nenhuma duplicidade whole/sharded detectada.
- O fluxo IR será executado com equivalentes de PRD e arquitetura específicos do subprojeto `.tracker/`, pois ele é um domínio autocontido dentro do repositório.
- Esta rodada reexecuta a avaliação considerando explicitamente o Sprint Change Proposal aprovado em `2026-05-27`.


## Step 2: PRD Analysis

### Functional Requirements

FR1: Modularizar `.tracker/work-tracker.py` em pacote Python `.tracker/tracker/`, mantendo `work-tracker.py` como shim (`from tracker.cli import main; main()`), com migração estrutural pura e zero alteração de comportamento. A estrutura alvo inclui módulos para CLI, models, utils, git_tracking, parsers, events, sessions e renderers.

FR2: Corrigir descarte silencioso de gaps entre ferramentas diferentes. Quando a sessão alternar entre Antigravity e Claude Code, o gap deve ser contabilizado em vez de descartado, atribuindo-o ao modelo do evento anterior independentemente da ferramenta.

FR3: Corrigir sessões que cruzam meia-noite. Sessões atravessando `00:00` devem ser divididas no limite da meia-noite e distribuídas proporcionalmente entre as datas corretas.

FR4: Implementar tendência temporal semanal/mensal no relatório, respondendo se o uso está acelerando ou desacelerando, com total de horas por semana e delta percentual.

FR5: Coletar atividade local do Cursor como terceira fonte de tempo ativo, comparável a Claude Code e Antigravity, usando o banco SQLite local `~/.cursor/ai-tracking/ai-code-tracking.db` em modo read-only com `schema_guard`. O coletor deve agrupar atividade por `conversationId/source/model`, preservar métricas nativas do Cursor como enriquecimento opcional e não redefinir o produto como analytics de proveniência de código.

FR6: Corrigir captura de detached HEAD como SHA de branch. Quando o destino de checkout corresponder a `^[0-9a-f]{7,40}$`, substituir o nome capturado por `"(detached HEAD)"`.

FR7: Corrigir `to_brasilia()` para não descartar timezone info antes da conversão. Se `parse_iso()` retornar `datetime` com `tzinfo`, a conversão deve preservar semântica temporal correta.

FR8: Decidir e implementar/documentar o comportamento de eventos `is_change` sem filtro `belongs_to_repo` em `analyze_antigravity()`, evitando poluição por eventos de outros repositórios se isso não for intencional.

FR9: Corrigir parsing de múltiplos `<USER_SETTINGS_CHANGE>` na mesma linha JSON do Antigravity, substituindo captura única por captura iterável de todas as ocorrências.

FR10: Corrigir atribuição de gaps entre branches. Quando uma sessão atravessar checkout, a atribuição do gap entre pings de branches diferentes deve ser tratada explicitamente em vez de ir integralmente para a branch anterior sem decisão documentada.

FR11: Alinhar fallback de `get_branch_at()` com a spec. O retorno anterior a qualquer checkout deve ser decidido e padronizado entre `"main"` e `"Desconhecida"`.

FR12: Adicionar type hints e logging estruturado, substituindo padrões `try/except: pass`, preferencialmente módulo a módulo após a modularização.

FR13: Reduzir fragilidade de `normalize_model_name()`, avaliando lookup table com fallback para normalização desconhecida em vez de heurísticas acopladas a modelos conhecidos.

FR14: Substituir fuso horário hardcoded UTC-3 por `zoneinfo.ZoneInfo("America/Sao_Paulo")` quando aplicável, para tratar DST e suportar múltiplos fusos sem alteração de código.

FR15: Padronizar o padrão de guarda de tabelas vazias, eliminando divergência entre guarda após loop e guarda antes do loop.

FR16: Implementar detecção de anomalias para sessões com menos de 5 minutos, interações sem tempo registrado e modelos com zero sessões mas mais de zero interações.

FR17: Rastrear tamanho da conversa em turnos por sessão, diferenciando sessões exploratórias de sessões produtivas.

FR18: Adicionar `format_version: X` no cabeçalho do relatório para permitir migração programática quando o layout de tabela mudar.

FR19: Remover ou justificar `extract_repo_name()` como código morto, já que `repo_name` não participa da filtragem real.

FR20: Manter rastreamento de tokens do Antigravity como bloqueado/inviável até que logs locais exponham dados de uso. Ação esperada: monitorar updates e/ou registrar feature request upstream.

FR21: Manter tokens coletados quando disponíveis, especialmente de Claude Code, para usos analíticos não monetários.

Total FRs: 21 requisitos abertos/bloqueados extraídos do backlog.

### Non-Functional Requirements

NFR1: A modularização deve ser uma migração estrutural pura, com zero alteração de comportamento observável.

NFR2: `make -f .tracker/Makefile track-time` deve produzir saída idêntica antes/depois da modularização.

NFR3: Todos os testes existentes devem continuar passando após atualização de imports.

NFR4: Nenhum arquivo novo criado pela modularização deve ultrapassar 250 linhas.

NFR5: `python3 -c "from tracker.cli import main"` deve funcionar sem erros.

NFR6: A implementação deve permanecer em Python 3.x com stdlib pura; `TypedDicts` devem ser compatíveis com Python 3.8+.

NFR7: O Makefile do tracker não deve mudar por causa da modularização; o shim deve preservar a interface operacional existente.

NFR8: Melhorias de logging estruturado devem substituir falhas silenciosas sem esconder erros de parsing relevantes.

NFR9: O produto não deve trabalhar com preços, custo monetário ou estimativas em USD em nenhuma ferramenta; `BKL-009` foi removido definitivamente do escopo.

NFR10: Mudanças em formato de relatório devem ser versionáveis para preservar compatibilidade de consumidores programáticos.

NFR11: A leitura do banco local do Cursor deve ser defensiva, offline, sem escrita no banco real e com degradação graciosa quando Cursor não estiver instalado ou quando o schema upstream divergir.

Total NFRs: 11 requisitos não funcionais/constraints extraídos.

### Additional Requirements

- Itens concluídos (`BKL-001`, `BKL-003`, `BKL-004`, `BKL-005`, `BKL-006`, `BKL-007`, `BKL-026`, `BKL-027`, `BKL-028`, `BKL-029`) formam baseline histórico e não devem gerar histórias novas, salvo regressão explícita.
- `BKL-031` é dependência estrutural recomendada para `BKL-008`, `BKL-019`, `BKL-021` e dependência explícita de `BKL-032`.
- `BKL-009` foi removido definitivamente do escopo por decisão de produto em `2026-05-27`; qualquer história de custo monetário deve ser tratada como obsoleta.
- `BKL-021` tem dependência recomendada de `BKL-031`.
- `BKL-002` deve permanecer fora do plano implementável enquanto a limitação upstream do Antigravity persistir.
- `BKL-032` adiciona uma nova fronteira de integração local com Cursor e precisa ser avaliado junto do Sprint Change Proposal aprovado.

### PRD Completeness Assessment

O backlog é suficiente como PRD operacional para planejamento técnico do tracker: ele lista prioridades, tipo, origem, descrição, correção proposta em vários bugs, dependências e critérios de aceite para a modularização crítica. A principal lacuna é que nem todos os BKLs possuem critérios de aceite explícitos; muitos têm apenas descrição/correção proposta. O IR deve verificar se o `epics.md` compensou essa lacuna com ACs testáveis por história.


## Step 3: Epic Coverage Validation

### Epic FR Coverage Extracted

- Epic 1 cobre correções de confiabilidade e precisão: gaps entre ferramentas, meia-noite, timezone, detached HEAD, fallback de branch, change events do Antigravity, múltiplos `<USER_SETTINGS_CHANGE>` e divisão de gap entre branches.
- Epic 2 cobre modularização, contratos evolutivos, `format_version`, golden tests, type hints/logging, guardas de tabelas, normalização de modelos e remoção/justificativa de código morto.
- Epic 3 cobre tendência temporal semanal/mensal e declara custo/preço/USD fora do escopo.
- Epic 4 cobre detecção de anomalias e padrões de conversa, incluindo turnos por sessão.
- Epic 5 cobre Cursor como terceira fonte de tempo ativo, com SQLite read-only, `schema_guard`, descarte determinístico com warning estruturado e integração aos formatos existentes.
- Epic 6 cobre Parking Lot de limitações upstream, especialmente tokens Antigravity e contrato `tokens_indisponiveis`.

Observação de rastreabilidade: a numeração de FRs do `epics.md` inclui histórico concluído (`FR1`-`FR18`) e por isso não coincide com a numeração extraída nesta rodada a partir do `BACKLOG.md`. A matriz abaixo usa a numeração da Step 2 deste relatório.

### Coverage Matrix

| FR Step 2 | Origem | PRD Requirement | Epic Coverage | Status |
|---|---|---|---|---|
| FR1 | BKL-031 | Modularizar `work-tracker.py` em pacote `tracker/` com shim e zero alteração de comportamento. | Epic 2, Stories 2.1-2.6, 2.8, 2.9 | Covered |
| FR2 | BKL-012 | Corrigir descarte de gaps entre ferramentas diferentes. | Epic 1, Stories 1.1 e 1.5 | Covered |
| FR3 | BKL-011 | Dividir sessões que cruzam meia-noite. | Epic 1, Stories 1.1 e 1.4 | Covered |
| FR4 | BKL-008 | Adicionar tendência temporal semanal/mensal. | Epic 3, Stories 3.1-3.3 | Covered |
| FR5 | BKL-032 | Coletar atividade local do Cursor como terceira fonte de tempo ativo. | Epic 5, Stories 5.1-5.7 | Covered |
| FR6 | BKL-010 | Renderizar detached HEAD como `(detached HEAD)`. | Epic 1, Stories 1.2 e 1.7 | Covered |
| FR7 | BKL-016 | Corrigir conversão timezone-aware em `to_brasilia()`. | Epic 1, Stories 1.1 e 1.6 | Covered |
| FR8 | BKL-018 | Decidir/documentar change events Antigravity sem `belongs_to_repo`. | Epic 1, Stories 1.3 e 1.11 | Covered |
| FR9 | BKL-023 | Processar múltiplos `<USER_SETTINGS_CHANGE>` na mesma linha JSON. | Epic 1, Stories 1.3 e 1.10 | Covered |
| FR10 | BKL-022 | Corrigir atribuição de gap entre branches. | Epic 1, Stories 1.2 e 1.9 | Covered |
| FR11 | BKL-025 | Alinhar fallback de `get_branch_at()`. | Epic 1, Stories 1.2 e 1.8 | Covered |
| FR12 | BKL-021 | Adicionar type hints e logging estruturado. | Epic 2, Story 2.8 | Covered |
| FR13 | BKL-015 | Reduzir fragilidade de `normalize_model_name()`. | Epic 2, Story 2.9 | Covered |
| FR14 | BKL-014 | Substituir UTC-3 hardcoded por `zoneinfo`. | Epic 1, Story 1.6; também NFR5 | Covered |
| FR15 | BKL-024 | Padronizar guardas de tabelas vazias. | Epic 2, Story 2.6 | Covered |
| FR16 | BKL-019 | Detectar anomalias. | Epic 4, Stories 4.1-4.3, 4.6 | Covered |
| FR17 | BKL-020 | Rastrear turnos por sessão. | Epic 4, Stories 4.1, 4.4-4.6 | Covered |
| FR18 | BKL-013 | Adicionar `format_version`. | Epic 2, Story 2.7; reforçado em 3.3, 4.6, 5.6, 6.3 | Covered |
| FR19 | BKL-017 | Remover/justificar `extract_repo_name()` como código morto. | Epic 2, Story 2.4 | Covered |
| FR20 | BKL-002 | Manter tokens Antigravity como bloqueio upstream. | Epic 6, Stories 6.1-6.3 | Covered |
| FR21 | Decisão de produto / FR17 histórico | Manter tokens coletados quando disponíveis para usos analíticos não monetários. | Epic 3 usa dataset com tokens sem custo; Epic 6 distingue tokens reais, indisponíveis e `null`; FR20/custo permanece removido | Covered |

### Missing Requirements

Nenhum FR ativo extraído da Step 2 ficou sem caminho de implementação.

Conflitos previamente identificados foram resolvidos nos artefatos considerados nesta rodada:

- `BKL-009` agora está em “Removidos do Escopo” no `BACKLOG.md`, alinhado ao Epic 3 e ao Sprint Change Proposal.
- `BKL-032` agora existe no `BACKLOG.md`, restaurando rastreabilidade upstream para o Epic 5 / Cursor.
- Story 2.8 está dividida em `2.8a` e `2.8b`.
- Story 1.9, Story 5.3, Story 5.6 e Story 6.3 possuem decisões/literais canônicos conforme proposal aprovado.

### Coverage Statistics

- Total PRD FRs extraídos na Step 2: 21
- FRs cobertos em épicos/histórias/Parking Lot/constraint explícito: 21
- FRs faltantes: 0
- FRs em conflito de escopo: 0
- Coverage percentage: 100%


## Step 4: UX Alignment Assessment

### UX Document Status

Not Found. Nenhum documento `*ux*.md` ou estrutura sharded de UX foi encontrado no escopo `.tracker/`.

### Alignment Issues

Nenhum desalinhamento bloqueante identificado para UX formal. O produto descrito é um utilitário local de linha de comando, com interface via GNU Make/CLI e saídas em console, Markdown, JSON, CSV e JSONL.

O `epics.md` declara explicitamente que UX Design Requirements não se aplicam porque o `.tracker/` é uma CLI Python sem interface gráfica. O Sprint Change Proposal reforça que o impacto fica restrito a DX/CLI, `stderr`, Markdown, JSON, CSV e fixtures.

### Warnings

- A ausência de UX formal é aceitável para o escopo atual porque não há aplicação web/mobile nem UI gráfica implícita.
- A experiência do usuário ainda existe como DX/CLI: comandos Make, mensagens de console, estrutura do Markdown, estados vazios em renderers e warnings estruturados. Esses pontos estão cobertos principalmente pelos Epics 2, 3, 4, 5 e 6.
- Qualquer mudança futura que introduza UI gráfica, dashboard ou fluxo interativo deve criar artefato UX próprio antes de entrar no sprint planning.


## Step 5: Epic Quality Review

### Overall Assessment

O `epics.md` está pronto o bastante para orientar sprint planning: há sequência clara, rastreabilidade por FR/BKL/NFR, histórias em formato user story, critérios de aceite majoritariamente em Given/When/Then e dependências apenas para trás ou para artefatos já planejados. O documento também trata corretamente o tracker como produto brownfield/CLI, não como greenfield.

Os problemas major da rodada anterior foram corrigidos: `BKL-009` saiu do escopo aberto, `BKL-032` foi criado, Story 1.9 tem regra determinística, Story 5.3 tem comportamento canônico, Story 2.8 foi dividida e literais de output foram fixados.

### Critical Violations

Nenhuma violação crítica estrutural foi encontrada.

- Não há dependência circular entre épicos.
- Não há Epic N dependendo de Epic N+1 para funcionar.
- Não há épico puramente sem valor quando o usuário-alvo correto é considerado: mantenedor/usuário do tracker, auditor do relatório e agente Dev que evolui o utilitário.

### Major Issues

Nenhum major issue bloqueante encontrado nesta rodada.

### Minor Concerns

1. **Sequenciamento vs. prioridade do backlog.**
   - Evidência: `BKL-031` aparece como prioridade alta no `BACKLOG.md`, mas o `epics.md` executa Epic 1 (confiabilidade) antes do Epic 2 (modularização).
   - Avaliação: aceitável, porque o Epic 2 congela goldens após correções de precisão para não transformar bugs conhecidos em contrato permanente. Ainda assim, o sprint planning deve explicitar essa escolha para não parecer que a prioridade alta de BKL-031 foi ignorada.

2. **Epic 2 é tecnicamente orientado, mas tem valor de mantenedor.**
   - Avaliação: aceitável neste produto porque o usuário-alvo inclui mantenedores/agentes e o valor é evolução segura do tracker. O cuidado no sprint planning é preservar fatias verificáveis por output e golden tests, sem agrupar migração demais.

3. **Histórias de fixtures são infraestrutura de teste.**
   - Evidência: Stories 1.1, 1.2, 1.3, 2.1, 3.1, 4.1 e 5.1.
   - Avaliação: aceitável em brownfield de métricas, desde que cada uma produza artefato executável e destrave a correção seguinte.

4. **Fixture Cursor exige cautela de privacidade.**
   - Evidência: Story 5.1 pede snapshot anonimizado de banco/transcripts Cursor.
   - Avaliação: critérios cobrem anonimização e não vazamento, mas o sprint planning deve destacar que fixtures podem ser sintéticas ou fortemente anonimizadas; conteúdo sensível não deve entrar no repositório.

5. **Epic 6 é documental/contratual.**
   - Avaliação: está claro no texto, mas o sprint planning deve tratá-lo como baixa prioridade ou encaixe de documentação/contrato, não como trilha crítica.

### Best Practices Compliance Checklist

- Epic 1: user value claro, independente, sem forward dependency crítica, ACs testáveis.
- Epic 2: valor técnico/mantenedor aceitável, dependências para trás, bons gates de golden tests, Story 2.8 já recortada.
- Epic 3: valor claro, dependências corretas, custo/preço removido do escopo.
- Epic 4: valor claro, labels/enums de anomalia canônicos.
- Epic 5: valor claro, dependência correta em Epic 2, comportamento Cursor determinístico.
- Epic 6: valor documental claro como Parking Lot, contrato literal estável para indisponibilidade de tokens.

### Recommendation Before Sprint Planning

Pode iniciar sprint planning. Recomenda-se apenas registrar explicitamente a decisão de sequenciamento “Epic 1 antes de BKL-031/Epic 2” e tratar a privacidade das fixtures Cursor como nota de execução.


## Step 6: Summary and Recommendations

### Overall Readiness Status

**READY**

O subprojeto `.tracker/` está pronto para sprint planning. A nova rodada confirmou alinhamento entre `BACKLOG.md`, arquitetura, `epics.md` e o Sprint Change Proposal aprovado em `2026-05-27`.

### Critical Issues Requiring Immediate Action

Nenhuma issue crítica encontrada.

### Major Issues Requiring Action Before Sprint Planning

Nenhuma major issue bloqueante encontrada.

### Minor Issues / Execution Notes

1. Registrar no sprint planning que a sequência escolhida é Epic 1 antes de BKL-031/Epic 2, apesar de `BKL-031` estar marcado como prioridade alta no backlog. A justificativa é congelar goldens após corrigir bugs de precisão, evitando transformar bugs conhecidos em contrato permanente.
2. Tratar fixtures Cursor com cautela de privacidade. A Story 5.1 deve usar dados sintéticos ou snapshot fortemente anonimizado, sem conteúdo sensível.
3. Manter Epic 6 como documentação/contrato de output, não como trilha crítica de implementação.

### Recommended Next Steps

1. Executar `bmad-sprint-planning` para gerar o plano de implementação a partir dos épicos corrigidos.
2. Priorizar explicitamente a sequência Epic 1 → Epic 2 → Epic 3/4/5, ou registrar uma exceção se decidir antecipar a modularização.
3. Ao criar histórias de implementação, preservar os literais canônicos aprovados: `N/A`, `short_session`, `interaction_without_time`, `model_interactions_without_sessions`, `exploratory`, `focused`, `context_switching`, `unclassified` e `tokens_indisponiveis`.

### Final Note

Este assessment identificou 0 issues críticas, 0 major issues bloqueantes e 5 preocupações menores de execução/planejamento. As preocupações menores não impedem sprint planning; servem como guardrails para evitar ambiguidade durante a implementação.

### Assessor

Avaliação: GPT-5 (Codex)
Data/Hora: 2026-05-27 23:06:04-03:00

---

Autoria/Implementação: GPT-5 (Codex)

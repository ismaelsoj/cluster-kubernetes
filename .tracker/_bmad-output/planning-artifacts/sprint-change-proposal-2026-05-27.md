---
project: "cluster-kubernetes / .tracker"
generatedAt: "2026-05-27 22:51:28-03:00"
changeTrigger: "Implementation Readiness identificou conflitos de rastreabilidade e critérios de aceite ambíguos antes do sprint planning."
mode: "Incremental"
status: "Aprovado para implementação"
authoringModel: "GPT-5 (Codex)"
---

# Sprint Change Proposal — Rastreador de Tempo Ativo IA

## 1. Issue Summary

A rodada de Implementation Readiness de 2026-05-27 identificou que o plano de sprint do subprojeto `.tracker/` ainda contém conflitos entre o backlog operacional (`.tracker/BACKLOG.md`) e o breakdown de épicos (`.tracker/_bmad-output/planning-artifacts/epics.md`).

Os principais problemas são:

- `BKL-009` ainda aparece como feature aberta de custo por modelo no backlog, enquanto `epics.md` já registra a decisão de produto de remover custo/preço/USD do escopo.
- `FR25` / Cursor como terceira fonte de tempo ativo está detalhado no Epic 5, mas não possui BKL correspondente no backlog.
- Story 1.9 e Story 5.3 deixam regras analíticas para decisão durante implementação, o que tornaria os critérios de aceite não determinísticos.
- Várias histórias usam “ou equivalente” em contratos de output que precisam de literais estáveis para golden tests.
- Story 2.8 combina logging estruturado e type hints em um escopo amplo demais, aumentando risco de refatoração grande e difícil de revisar.

Decisão de produto confirmada: o tracker não trabalhará com preços/custo monetário em nenhuma ferramenta. Tokens continuam sendo coletados quando disponíveis, mas não serão multiplicados por tabela de preços.

## 2. Impact Analysis

### Epic Impact

- **Epic 1 — Confiabilidade das Métricas:** Story 1.9 precisa fixar a regra canônica para gap entre branches. Decisão escolhida: dividir o gap pelo timestamp exato do checkout.
- **Epic 2 — Modularização Habilitadora e Contratos Evolutivos:** Story 2.8 deve ser dividida em duas histórias menores: logging estruturado e type hints incrementais.
- **Epic 3 — Inteligência Analítica Fundamental:** deve remover resíduo de custo na Story 3.1 e manter apenas tendência temporal. Story 3.2 deve usar literal canônico `N/A`.
- **Epic 4 — Anomalias e Padrões de Conversa:** labels de anomalia e classificação devem virar enums/literais canônicos.
- **Epic 5 — Cursor como Terceira Fonte de Tempo Ativo:** Story 5.3 deve fixar descarte com warning estruturado para linhas incompletas e filtro por evidência explícita de repo/workspace. Story 5.6 deve fixar comportamento de ambiente sem Cursor.
- **Epic 6 — Parking Lot de Limitações Upstream:** Story 6.3 deve fixar representação canônica para tokens indisponíveis e distinguir `0`, `tokens_indisponiveis` e `null`.

### Story Impact

- **Story 1.2:** atualizar o contrato da fixture de branch para refletir divisão do gap no checkout.
- **Story 1.9:** substituir regra ambígua por divisão determinística no timestamp do checkout.
- **Story 2.8:** recortar em `2.8a — Logging estruturado` e `2.8b — Type hints incrementais`.
- **Story 3.1:** remover “custo por modelo”.
- **Story 3.2:** fixar `N/A` como delta da primeira semana.
- **Stories 4.2, 4.3, 4.5:** remover “ou equivalente” e fixar literais.
- **Stories 5.1, 5.3, 5.6:** fixar comportamento canônico para Cursor, incluindo expected da fixture.
- **Story 6.3:** fixar literal de indisponibilidade de tokens.

### Artifact Conflicts

- **BACKLOG.md:** requer mover `BKL-009` para seção de removidos do escopo, adicionar novo BKL para Cursor e atualizar resumo de itens abertos.
- **epics.md:** requer limpeza de custo/preço/USD residual, decisões canônicas nas ACs e Change Log com timestamp BRT.
- **Arquitetura:** sem alteração obrigatória imediata. O coletor Cursor e o contrato de tokens podem gerar atualização arquitetural futura quando implementados.
- **UX:** não aplicável; o produto é CLI sem UI gráfica. Impacto fica restrito a DX/CLI, stderr, Markdown, JSON, CSV e fixtures.

### Technical Impact

- Nenhuma mudança de código é necessária nesta correção de curso.
- Fixtures físicas citadas ainda não existem no workspace atual (`.tracker/tests/fixtures/...`); portanto, a correção imediata deve atualizar contratos nas histórias. A criação/edição de `expected.json` fica para a execução das respectivas histórias.
- Golden tests futuros dependerão dos literais fixados neste proposal.

## 3. Recommended Approach

Recomendação: **Direct Adjustment**.

As mudanças são moderadas e podem ser resolvidas por ajuste direto nos artefatos de planejamento, sem rollback e sem redefinição de MVP. O objetivo é remover ambiguidades antes do sprint planning, preservando a sequência de épicos já aprovada.

Decisões aprovadas para aplicar:

- **Story 1.9:** dividir gap entre branches pelo timestamp exato do checkout.
- **Story 5.3(a):** descartar registros Cursor sem `conversationId` ou sem `model`, com warning estruturado, sem crash.
- **Story 5.3(b):** considerar dados Cursor apenas quando houver evidência explícita de repo/workspace atual; sem evidência suficiente, descartar com warning estruturado.
- **Story 2.8:** dividir em `2.8a — Logging estruturado` e `2.8b — Type hints incrementais`.

Literais canônicos propostos para aprovação final:

- Primeira semana sem delta anterior: `N/A`.
- Anomalias: `short_session`, `interaction_without_time`, `model_interactions_without_sessions`.
- Classificação de sessão: `exploratory`, `focused`, `context_switching`, `unclassified`.
- Tokens indisponíveis: `tokens_indisponiveis`.
- Ambiente sem Cursor instalado: warning estruturado em stderr.
- Campo não aplicável em export estruturado: `null`.
- Tokens reais zero: `0`.

Estimativa: baixa a média, concentrada em documentação/planejamento.

Risco: baixo, desde que as mudanças sejam aplicadas antes do sprint planning e que `git add`/`git commit` permaneçam sob autorização explícita do usuário.

## 4. Detailed Change Proposals

### BACKLOG.md

#### BKL-009

**OLD:**

`BKL-009 — Estimativa de Custo por Modelo` aparece em Prioridade Média como feature aberta.

**NEW:**

Mover para nova seção `🚫 Removidos do Escopo`, com:

- data: `2026-05-27`;
- decisão: custos/preços monetários fora do escopo definitivo;
- justificativa: preços variam por plataforma, plano e contrato;
- nota: tokens continuam coletados via FR17 para usos analíticos, sem multiplicação por preço.

**Rationale:** alinhar backlog com decisão de produto já registrada em `epics.md`.

#### Novo BKL para Cursor

**OLD:**

Não há BKL upstream para FR25.

**NEW:**

Adicionar novo item, sugerido como `BKL-032: Cursor como terceira fonte de tempo ativo`, em Prioridade Média, com:

- tipo: Feature;
- origem: decisão de produto 2026-05-27;
- descrição alinhada ao Epic 5;
- dependência: `BKL-031`;
- fonte: `~/.cursor/ai-tracking/ai-code-tracking.db`;
- modo: read-only com `schema_guard`;
- comportamento esperado: integrar Cursor como fonte de tempo ativo comparável, preservando métricas nativas como enriquecimento opcional.

**Rationale:** restaurar rastreabilidade upstream do Epic 5.

#### Resumo de itens abertos

**OLD:** Feature 5, Total aberto 20, Total geral 30.

**NEW:** Feature 5, Total aberto 20, Removidos do escopo 1, Total geral 31.

**Rationale:** remover BKL-009 dos abertos e adicionar BKL-032 como feature aberta mantém o total de abertos estável, mas registra explicitamente o item removido.

### epics.md

#### Story 1.2

**OLD:**

“checkout entre pings” sem expected literal de regra.

**NEW:**

Expected da fixture deve demonstrar divisão do gap no timestamp exato do checkout.

**Rationale:** preparar fixture para Story 1.9.

#### Story 1.9

**OLD:**

“o gap deve ser dividido ou atribuído conforme regra documentada na história”

**NEW:**

“o gap deve ser dividido no timestamp exato do checkout: a parcela entre o ping anterior e o checkout fica na branch anterior; a parcela entre o checkout e o ping posterior fica na branch posterior.”

**Rationale:** regra determinística, auditável e testável.

#### Story 2.8

**OLD:**

Uma única história combina logging estruturado, revisão de `try/except: pass` e type hints.

**NEW:**

Criar:

- `Story 2.8a: Introduzir logging estruturado nos módulos extraídos`
- `Story 2.8b: Adicionar type hints incrementais nas APIs públicas dos módulos extraídos`

**Rationale:** reduzir escopo por história e facilitar review.

#### Story 3.1

**OLD:**

“tendência temporal e custo por modelo”

**NEW:**

“tendência temporal”

**Rationale:** custo/preço removido do escopo.

#### Story 3.2

**OLD:**

“`N/A` ou equivalente documentado”

**NEW:**

“exatamente `N/A`”

**Rationale:** literal estável para golden tests.

#### Stories 4.2, 4.3, 4.5

**OLD:**

Labels com “ou equivalente”.

**NEW:**

Fixar:

- `short_session`
- `interaction_without_time`
- `model_interactions_without_sessions`
- `exploratory`
- `focused`
- `context_switching`
- `unclassified`

**Rationale:** enums canônicos para export/render.

#### Story 5.1

**OLD:**

`expected.json` sem comportamento canônico explícito para descarte de linhas incompletas ou fora de repo.

**NEW:**

`expected.json` deve conter casos esperados para:

- registros válidos;
- registros sem `conversationId` descartados com warning;
- registros sem `model` descartados com warning;
- registros sem evidência suficiente de repo/workspace descartados com warning.

**Rationale:** fixture deve exercitar as decisões da Story 5.3.

#### Story 5.3

**OLD:**

“fallback documentado ou descartar” e “quando houver evidência suficiente”.

**NEW:**

Descartar com warning estruturado quando faltar `conversationId` ou `model`. Considerar evidência suficiente de repo/workspace apenas quando campos como `workspaceFolder`, `repoPath`, paths associados via `scored_commits` ou campo equivalente validado por `schema_guard` apontarem para o repositório atual. Sem evidência suficiente, descartar com warning estruturado.

**Rationale:** comportamento determinístico e seguro contra poluição de dados de outros repositórios.

#### Story 5.6

**OLD:**

“mensagem amigável ou warning estruturado”

**NEW:**

Warning estruturado em stderr.

**Rationale:** stdout/export ficam limpos para consumo programático.

#### Stories 5.6 e 6.3

**OLD:**

`tokens_indisponiveis` ou equivalente.

**NEW:**

Fixar `tokens_indisponiveis`, com distinção:

- `0`: tokens reais coletados e iguais a zero;
- `tokens_indisponiveis`: ferramenta não expõe tokens localmente;
- `null`: campo não aplicável ao formato/contexto.

**Rationale:** evita interpretar ausência de tokens como custo zero ou erro silencioso.

## 5. Implementation Handoff

### Scope Classification

**Moderate:** requer reorganização de backlog e refinamento de histórias antes do sprint planning, mas não exige rollback, replanejamento fundamental ou alteração de arquitetura.

### Handoff Recipients

- **Product Owner / Developer agents:** aplicar ajustes em `BACKLOG.md` e `epics.md`.
- **Developer agent:** após aprovação, executar patches documentais sem alterar código e sem executar `git add`/`git commit`.
- **Usuário humano:** aprovar explicitamente a implementação e autorizar qualquer operação Git futura.

### Success Criteria

- `BKL-009` não aparece mais como item aberto.
- `BKL-032` ou equivalente registra Cursor no backlog.
- `FR20` permanece removido do escopo em `epics.md`.
- Nenhuma AC relevante mantém “ou equivalente” onde há contrato de output.
- Story 1.9 e Story 5.3 não deixam decisões analíticas para implementação.
- Story 2.8 fica recortada em duas histórias menores.
- Todos os artefatos editados mantêm `Autoria/Implementação` e `Revisão`.
- Change Log de histórias/planejamento usa timestamp BRT no formato `AAAA-MM-DD HH:MM:SS-03:00`.

---

**Autoria/Implementação:** GPT-5 (Codex)
**Revisão:** Aprovado por Ismael em 2026-05-27

## Change Log

| Data/Hora (BRT) | Autor | Alteração |
|---|---|---|
| 2026-05-27 22:51:28-03:00 | GPT-5 (Codex) | Criação do Sprint Change Proposal com decisões incrementais escolhidas pelo usuário para Story 1.9, Story 5.3 e Story 2.8. |
| 2026-05-27 22:54:37-03:00 | GPT-5 (Codex) | Proposal aprovado pelo usuário para aplicação em `BACKLOG.md` e `epics.md`. |

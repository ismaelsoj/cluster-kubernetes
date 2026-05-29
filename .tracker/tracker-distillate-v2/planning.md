# Planning

Use este companion para priorizacao, refinamento e leitura rapida do roadmap sem abrir o `epics.md` completo.

## Mapa de leitura

- Para priorizacao rapida: leia apenas esta pagina.
- Para criterios detalhados de uma historia aberta: abra o arquivo de spec correspondente, se existir.
- Para decomposicao completa de epicos e historias: abra `.tracker/_bmad-output/planning-artifacts/epics.md` somente sob demanda.

## Roadmap ativo resumido

- `Epic 1` Confiabilidade das metricas
  - foco: corrigir meia-noite, gaps entre ferramentas, timezone-aware, detached HEAD, fallback de branch, gaps entre branches, multiplos `USER_SETTINGS_CHANGE`
  - usar quando a tarefa alterar corretude numerica

- `Epic 2` Modularizacao habilitadora
  - foco: quebrar `work-tracker.py` em modulos, versionar formatos, logging, type hints, lookup table de modelos
  - usar quando a tarefa mexer em estrutura, contratos e mantenabilidade

- `Epic 3` Inteligencia analitica fundamental
  - foco: tendencia temporal week-over-week
  - depende de confiabilidade e modularizacao

- `Epic 4` Anomalias e padroes de conversa
  - foco: detectar outliers, inconsistencias e perfis de sessao

- `Epic 5` Cursor como terceira fonte
  - foco: adicionar Cursor sem redefinir o produto

- `Epic 6` Parking lot upstream
  - foco: registrar e monitorar limitacoes bloqueadas por fornecedor, sem empurrar implementacao falsa

## Mapa rapido por epic

- `Epic 1`
  - fixtures ground-truth
  - meia-noite
  - gaps entre ferramentas
  - timezone-aware
  - detached HEAD
  - fallback de branch
  - multiplos `USER_SETTINGS_CHANGE`

- `Epic 2`
  - modularizacao em pacote `tracker/`
  - versionamento de formato
  - renderers separados
  - logging e type hints
  - lookup table de modelos

- `Epic 3`
  - dataset de referencia
  - tendencia semanal
  - renderizacao Markdown, JSON e CSV

- `Epic 4`
  - datasets de anomalia
  - sessoes curtas
  - inconsistencias de modelos e sessoes
  - turnos por sessao
  - padroes de conversa

- `Epic 5`
  - Cursor como terceira fonte

- `Epic 6`
  - limitacoes upstream documentadas

## Itens abertos de maior impacto imediato

- `BKL-030` backfill de tokens legados do Claude Code
- `BKL-004` regex que trunca modelos com ponto
- `BKL-011` sessoes cruzando meia-noite
- `BKL-012` gap entre ferramentas descartado
- `BKL-028` leitura de JSONL sem tratamento por linha
- `BKL-029` `last_updated` semanticamente incorreto
- `BKL-010` detached HEAD como SHA
- `BKL-016` conversao errada de datetimes timezone-aware

## Regra de ouro para contexto barato

- Nao abrir `epics.md` para saber "o que esta aberto".
- Nao abrir backlog historico para entender arquitetura.
- Nao abrir specs arquivadas para reconstituir decisoes ja resumidas no kernel v2.

---
Autoria/Implementação: GPT-5 Codex

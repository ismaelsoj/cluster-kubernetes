---
title: 'Adotar Kong Gateway 3.14.0.3 nos artefatos ativos'
type: 'chore'
created: '2026-05-28'
baseline_commit: 'c5b6aa0'
status: 'done'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/distillate-v2/architecture-status.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O repositório ainda referencia a linha antiga do Kong DB-Less (`3.4.x` / `kong:3.4.2`) em artefatos ativos de arquitetura, contexto e story, mas a documentação oficial do Kong mostra que a release mais recente é `3.14.0.3`, publicada em `2026-05-25`, e que `3.14` é a LTS atual. Se essas referências permanecerem divergentes, a story 3.1 será implementada contra uma base desatualizada e com riscos de comportamento incorreto em relação às mudanças de default introduzidas na série `3.14`.

**Approach:** Atualizar apenas os artefatos vivos que orientam implementação e operação futura para apontar explicitamente para `3.14.0.3`, incorporando também os guardrails que ficaram mais importantes nessa série, como `tls_certificate_verify=on` por padrão e o default de rotas `https` no Kong 3.14. Preservar documentos históricos (`archive/`, `distillate/` legado e relatos retroativos) como registro do passado, sem “reescrever a história”.

## Boundaries & Constraints

**Always:** Confirmar tudo em documentação oficial do Kong; manter pt-BR; preservar a linha GitOps/DB-less/KIC já decidida; atualizar só artefatos ativos que guiam trabalho futuro; manter a story 3.1 coerente com a adoção de `3.14.0.3`; registrar claramente impactos de breaking/default changes da série `3.14`.

**Ask First:** Se a investigação mostrar necessidade de alterar mais do que documentação/spec ativa, como introduzir novos manifests operacionais, mudar topologia de deployment do Kong, trocar KIC por outro modelo, ou editar artefatos históricos para “uniformizar” versões passadas.

**Never:** Editar `_bmad-output/implementation-artifacts/archive/` ou `_bmad-output/distillate/` legado apenas para apagar referências antigas; alterar versões de ArgoCD/Keycloak sem evidência; inventar manifests do Kong que ainda não existem; mudar `k3d.yaml`, bootstrap ou política de sync waves como efeito colateral desta tarefa.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH | Artefatos ativos com referências a `3.4.x` e `kong:3.4.2` | Todos os documentos vivos passam a apontar para `3.14.0.3` e mencionam os defaults relevantes de `3.14` | N/A |
| HISTORICAL_REFERENCE | Referência antiga encontrada em `archive/` ou `distillate/` legado | O arquivo histórico é preservado; no máximo a spec/documentação ativa explica que o histórico permanece intocado | Não editar o histórico |
| NO_RUNTIME_MANIFEST | Não há manifestos reais do Kong ainda, só placeholders e a story 3.1 | A adoção acontece via contexto, arquitetura e story, preparando a implementação futura com a versão correta | Não fabricar deployment só para “ter onde trocar a tag” |

</frozen-after-approval>

## Code Map

- `_bmad-output/distillate-v2/architecture-status.md` -- resumo vivo da stack e do estado arquitetural carregado na entrada obrigatória do repositório.
- `_bmad-output/project-context.md` -- contexto persistente com versões, invariantes e guardrails operacionais para agentes.
- `_bmad-output/planning-artifacts/architecture.md` -- arquitetura detalhada ainda ativa, agora alinhada à linha `3.14 LTS` e aos defaults endurecidos do Kong 3.14.
- `_bmad-output/planning-artifacts/epics.md` -- origem da Story 3.1 e dos critérios de aceite atualizados para `kong:3.14.0.3`.
- `_bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` -- story pronta para dev que precisa passar a orientar a implementação contra `3.14.0.3`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/distillate-v2/architecture-status.md` -- atualizar a stack base de Kong para `3.14.0.3`/`3.14 LTS` e remover a âncora antiga `3.4.x` -- o companion é a porta de entrada de arquitetura do repositório.
- [x] `_bmad-output/project-context.md` -- ajustar a seção de stack para `3.14.0.3` e manter consistência com os padrões ativos de health/status/logs -- evita que agentes futuros implementem o gateway contra uma referência obsoleta.
- [x] `_bmad-output/planning-artifacts/architecture.md` -- substituir referências normativas a `3.4.x LTS` por `3.14.0.3`/`3.14 LTS` e registrar os defaults relevantes da série `3.14` (`tls_certificate_verify` e rotas HTTPS por padrão) -- essa é a base de decisão técnica longa do projeto.
- [x] `_bmad-output/planning-artifacts/epics.md` -- atualizar a Story 3.1 para usar `3.14.0.3` no AC e manter coerência com a LTS atual -- o backlog implementável precisa refletir a versão oficial adotada.
- [x] `_bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` -- revisar ACs, tasks, notas técnicas e validação manual para orientar a futura implementação do Kong em `3.14.0.3`, incluindo os defaults/breaking changes relevantes de `3.14` -- esta é a peça que mais diretamente dirige o próximo trabalho de dev.

**Acceptance Criteria:**
- Given os artefatos ativos do projeto, when a busca por referências normativas do Kong for executada, then não devem restar menções ativas a `3.4.x` ou `kong:3.4.2` fora de históricos preservados.
- Given a Story 3.1 pronta para desenvolvimento, when um agente futuro a usar como guia, then ela deve apontar explicitamente para `3.14.0.3` e alertar sobre os defaults importantes introduzidos em `3.14`.
- Given a documentação oficial do Kong 3.14, when a arquitetura do repositório for lida, then os riscos de `tls_certificate_verify=on` por padrão e de rotas `https` por padrão devem estar refletidos nos artefatos ativos onde isso influencia implementação futura.

## Spec Change Log

## Design Notes

A principal nuance aqui é que “adotar a última versão estável” não significa só trocar string de versão. A série `3.14` trouxe defaults que podem quebrar configurações DB-less futuras se a story permanecer ancorada na mentalidade de `3.4.x`, especialmente:

- `tls_certificate_verify` ligado por padrão em `3.14`, com impacto explícito em configurações DB-less que usem `tls_verify=false`.
- `Route protocols` com default `https`, o que afeta a forma como rotas e ingressos futuros devem ser modelados.

Como o repositório ainda não tem manifests reais do Kong, a adoção correta neste momento é atualizar os artefatos normativos que antecedem a implementação, e não criar código de runtime artificialmente.

## Verification

**Commands:**
- `rg -n "3\\.4\\.x|kong:3\\.4\\.2" _bmad-output/project-context.md _bmad-output/distillate-v2 _bmad-output/planning-artifacts _bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` -- expected: nenhum match nos artefatos ativos editados.
- `rg -n "3\\.14\\.0\\.3|3\\.14 LTS|tls_certificate_verify|https. por padrão|https por padrão" _bmad-output/project-context.md _bmad-output/distillate-v2/architecture-status.md _bmad-output/planning-artifacts/architecture.md _bmad-output/planning-artifacts/epics.md _bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` -- expected: referências novas presentes nos pontos normativos principais.
- `git diff -- _bmad-output/distillate-v2/architecture-status.md _bmad-output/project-context.md _bmad-output/planning-artifacts/architecture.md _bmad-output/planning-artifacts/epics.md _bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` -- expected: diff concentrado em atualização de versão e guardrails de 3.14, sem alterações colaterais em históricos.

## Suggested Review Order

1. [architecture-status.md](../distillate-v2/architecture-status.md#L8) -- confirme a versão-base da stack e o guardrail de defaults do Kong 3.14 em [L16](../distillate-v2/architecture-status.md#L16).
2. [project-context.md](../project-context.md#L22) -- valide a versão persistida no contexto do projeto e a regra operacional em [L95](../project-context.md#L95).
3. [architecture.md](../planning-artifacts/architecture.md#L140) -- revise a decisão normativa principal, o endurecimento de defaults em [L156](../planning-artifacts/architecture.md#L156) e a checagem de coerência em [L474](../planning-artifacts/architecture.md#L474).
4. [epics.md](../planning-artifacts/epics.md#L327) -- confira o ajuste do backlog implementável e o critério de aceite adicional em [L330](../planning-artifacts/epics.md#L330).
5. [3-1-manifestos-kustomize-kong-db-less.md](3-1-manifestos-kustomize-kong-db-less.md#L26) -- valide ACs, tasks e notas técnicas da story, incluindo [L30](3-1-manifestos-kustomize-kong-db-less.md#L30), [L42](3-1-manifestos-kustomize-kong-db-less.md#L42), [L74](3-1-manifestos-kustomize-kong-db-less.md#L74), [L148](3-1-manifestos-kustomize-kong-db-less.md#L148) e [L152](3-1-manifestos-kustomize-kong-db-less.md#L152).

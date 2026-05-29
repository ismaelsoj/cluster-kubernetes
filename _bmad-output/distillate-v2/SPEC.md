---
type: bmad-spec
slug: cluster-kubernetes-contexto-agente
companions:
  - implementation-rules.md
  - architecture-status.md
  - planning.md
  - deferred-work.md
sources:
  - ../distillate/_index.md
  - ../distillate/01-regras-implementacao.md
  - ../distillate/02-arquitetura-decisoes.md
  - ../distillate/03-epicos-stories-status.md
  - ../distillate/04-trabalho-diferido.md
---

# SPEC

## Why

O projeto principal já possui um distillate útil, mas a porta de entrada ainda empilha regras de implementação, arquitetura e roadmap na leitura inicial. Este kernel v2 reduz o contexto padrão para o mínimo confiável e empurra detalhes para companions por intenção de trabalho.

## Capabilities

- `CAP-1`
  - `intent`: Fornecer uma entrada única, curta e estável para agentes que atuam na infraestrutura GitOps principal.
  - `success`: O agente entende stack, invariantes, limites arquiteturais e rota de leitura sem abrir os artefatos longos na primeira passada.

- `CAP-2`
  - `intent`: Separar regras rígidas de implementação, estado arquitetural e planejamento ativo.
  - `success`: Implementação, revisão, arquitetura e planejamento carregam apenas o companion necessário.

- `CAP-3`
  - `intent`: Reduzir o custo de contexto nas tarefas operacionais mais comuns do repositório.
  - `success`: A maioria das tarefas de infra consegue começar lendo `SPEC.md` e no máximo um ou dois companions.

## Constraints

- Comunicação e documentação continuam obrigatoriamente em pt-BR.
- `.tracker/` permanece invisível para tarefas de infraestrutura Kubernetes, salvo solicitação explícita do usuário.
- A fonte de contexto do projeto principal passa a ser `_bmad-output/distillate-v2/`; `distillate/` antigo vira referência histórica.
- Não ler `_bmad-output/planning-artifacts/` nem `_bmad-output/implementation-artifacts/archive/` como caminho feliz de contexto.
- Todo artefato editado por IA deve registrar autoria do modelo.
- O workflow Git obrigatório do repositório continua valendo: sincronizar com `main`, trabalhar em branch descritiva e nunca fazer `git add` ou `git commit` sem autorização explícita.

## Non-goals

- Reescrever os artefatos de planejamento originais.
- Alterar decisões arquiteturais ou backlog nesta etapa.
- Substituir specs de histórias ou documentação detalhada de operação.

## Success signal

Um agente de infra consegue iniciar trabalho seguro no repositório lendo `SPEC.md` e apenas os companions necessários para sua tarefa. A abertura do distillate antigo completo e de artefatos longos de planejamento vira exceção, não padrão.

## Assumptions

- O objetivo desta iteração é reduzir tokens carregados no contexto, preservando os artefatos existentes como referência.

## Open Questions

- Nenhuma nesta iteração.

---
Autoria/Implementação: GPT-5 Codex

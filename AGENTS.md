# AGENTS.md — Regras Universais para Agentes de IA

## Idioma

- Comunicação e documentação em pt-BR.

## Porta de entrada obrigatória

- Leia primeiro `_bmad-output/distillate-v2/SPEC.md`.
- Carregue apenas os companions necessários:
  - `implementation-rules.md` para implementação e review
  - `architecture-status.md` para ADRs, segurança e topologia
  - `planning.md` para roadmap e próximo trabalho
  - `deferred-work.md` para riscos e diferidos

## Invariantes do repositório

- Projeto principal: GitOps para cluster Kubernetes local com k3d, ArgoCD, Kong, Keycloak e PostgreSQL.
- `.tracker/` é invisível para tarefas de infraestrutura Kubernetes, salvo solicitação explícita do usuário.
- Não usar `_bmad-output/implementation-artifacts/archive/` nem `_bmad-output/planning-artifacts/` como caminho feliz de contexto.
- Todo artefato editado por IA deve registrar `Autoria/Implementação: <modelo>`.
- Change Log de histórias em `_bmad-output/implementation-artifacts/` deve usar data/hora de Brasília no formato `AAAA-MM-DD HH:MM:SS-03:00`.

## Git

- Antes de desenvolver: `git pull origin main` e nova branch descritiva a partir de `main`.
- Commits diretos em `main` são proibidos.
- `git add` e `git commit` só com autorização explícita do usuário.

## Code Review

- Review estritamente propositivo.
- Registrar observações na história ou artefato relevante.
- Não aplicar alterações sugeridas sem aprovação explícita do usuário.

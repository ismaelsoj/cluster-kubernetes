# AGENTS.md — Regras Universais para Agentes de IA

> Este arquivo é lido automaticamente por Antigravity, Cursor, Claude Code e outros agentes compatíveis.
> Contém políticas de governança do repositório que TODO agente DEVE seguir, independentemente da ferramenta ou framework.

## Idioma

- Comunicação e documentação DEVEM ser em **pt-BR**.

## Contexto do Projeto

- Repositório GitOps para cluster Kubernetes local (k3d + ArgoCD + Kong + Keycloak).
- Stack e regras de implementação detalhadas em `_bmad-output/distillate/_index.md` — leia antes de implementar qualquer código.

## Git Workflow

- **Antes de iniciar qualquer desenvolvimento**, execute obrigatoriamente:
  1. `git pull origin main`
  2. Crie e mude para uma nova branch a partir de `main` com nome descritivo baseado na tarefa.
- Commits diretos na branch `main` são **ESTRITAMENTE PROIBIDOS**.

## Git Permissions

- A execução autônoma de `git add` ou `git commit` é **PROIBIDA**.
- Você **DEVE** solicitar e obter autorização explícita do usuário ANTES de executar esses comandos.

## Code Review

- O code review deve ser **estritamente propositivo**.
- Registre as observações diretamente na especificação da história ou artefato relevante.
- Sugira as alterações, mas **NUNCA** aplique-as sem aprovação explícita do usuário.
- Após aplicar alterações aprovadas, atualize a especificação marcando os itens como concluídos.

## Rastreabilidade de Autoria (LLM)

- Todo artefato gerado ou editado por IA DEVE registrar explicitamente qual modelo LLM executou a tarefa.
  - Formato: `Autoria/Implementação: <modelo>` no rodapé ou seção pertinente.
  - Em caso de revisão por outro agente: `Revisão: <modelo>` abaixo do autor original.
- O **Change Log** de todas as especificações de histórias (em `_bmad-output/implementation-artifacts/`) DEVE conter data e hora no fuso horário de Brasília (UTC-3), no formato `AAAA-MM-DD HH:MM:SS-03:00` (ex: `2026-05-22 22:38:49-03:00`).

## Isolamento de Domínios e Otimização de Contexto

- A pasta `.tracker/` é **invisível** para tarefas de infraestrutura Kubernetes. Agentes só devem acessá-la mediante solicitação explícita. Menção espontânea é violação de escopo semântico.
- A pasta `_bmad-output/implementation-artifacts/archive/` contém histórias concluídas. **NUNCA** leia ou vasculhe arquivos dentro desta pasta para buscar contexto de projeto.
- Evite ler os arquivos originais em `_bmad-output/planning-artifacts/`. Utilize sempre as versões otimizadas em `_bmad-output/distillate/` como sua fonte da verdade.

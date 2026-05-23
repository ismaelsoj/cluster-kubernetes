---
type: bmad-distillate
sources:
  - "../project-context.md"
  - "../planning-artifacts/prd.md"
  - "../planning-artifacts/architecture.md"
  - "../planning-artifacts/epics.md"
  - "../implementation-artifacts/sprint-status.yaml"
  - "../implementation-artifacts/deferred-work.md"
downstream_consumer: "dev-story, create-story, code-review"
created: "2026-05-22"
token_estimate: 8500
parts: 4
---

## Orientação

- Destilado de 6 documentos do projeto cluster-kubernetes: PRD, Arquitetura, Épicos, Project Context, Sprint Status e Trabalho Diferido
- Consumer: workflows de implementação (dev-story, create-story, code-review)
- Projeto: plataforma GitOps On-Premise (k3d + ArgoCD + Kong DB-Less + Keycloak + PostgreSQL) com foco Zero-Trust e DevEx "Fricção Zero"
- Status: Épico 1 concluído (5/5 stories done + retro); Épicos 2-4 em backlog
- Dependências lineares: É1→É2→É3→É4 (18 stories total)

## Manifesto de Seções

- `01-regras-implementacao.md` — Regras rígidas de nomenclatura, formato, labels, estrutura Kustomize e processo ArgoCD que TODO manifesto deve obedecer
- `02-arquitetura-decisoes.md` — ADRs, stack com versões, limites arquiteturais, fluxos de dados e padrões de segurança
- `03-epicos-stories-status.md` — Decomposição completa de épicos/stories com critérios de aceitação, FRs mapeados e status atual
- `04-trabalho-diferido.md` — Itens identificados em code reviews pendentes de resolução, agrupados por story destino

## Itens Cross-Cutting

- Segregação criptográfica Dev/Prod: Realms e chaves Keycloak locais DEVEM ser matematicamente distintas da Produção — tokens vazados de dev são rejeitados em prod
- Safe-Prune seletivo: `prune: false` para infra central (Kong, Keycloak, ArgoCD); `prune: true` para apps de negócio
- Descoberta automática de apps: `apps-app.yaml` usa glob `cluster/apps/*` + `CreateNamespace=true` — não registrar APIs manualmente
- Paridade local-produção: mesma topologia k3d/Kong/Keycloak; overlays diferenciam apenas configurações
- Logs JSON estruturado: obrigatório desde primeiro deploy em Kong e Keycloak
- Healthchecks públicos (FR24): `readinessProbe` + `livenessProbe` obrigatórios em TODO Deployment; endpoints não autenticados
- PriorityClasses: Kong e Keycloak com prioridade máxima (NFR-R01) — imunes a eviction

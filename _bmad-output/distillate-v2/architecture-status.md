# Arquitetura e Status

Use este companion para decisões arquiteturais, segurança, topologia e leitura rápida do estado atual do programa.

## Estado atual resumido

- Projeto: plataforma GitOps on-premise para cluster Kubernetes local com k3d, ArgoCD, Kong DB-Less, Keycloak e PostgreSQL.
- Stack base: k3d v5.8.3, ArgoCD v3.4.2, Kong DB-Less v3.4.x LTS, Keycloak 26.6.2, Kustomize v5.x, kube-linter, Conftest e GitHub Actions.
- Status: Épico 1 concluído; épicos 2 a 4 permanecem em backlog.
- Próximo marco funcional: Story 2.1, PostgreSQL em Wave 1 dentro de `keycloak-auth`.

## ADRs e limites load-bearing

- Kong é DB-Less e stateless para aderência total ao GitOps.
- Validação de JWT/JWKS acontece localmente no gateway, com cache para resiliência e baixa latência.
- Keycloak é o único emissor de tokens.
- ArgoCD lê apenas do Git; alterações manuais no cluster são proibidas, exceto bootstrap de secrets.
- Desenvolvedores de apps trabalham apenas em `/cluster/apps/<api>/` sobre boilerplates.
- Não usar Gateway API, Service Mesh ou cofres automatizados na fase atual.

## Segurança e confiabilidade

- Todo tráfego externo entra pelo Kong.
- Kong termina TLS antes do tráfego interno para os pods.
- Segregação criptográfica entre dev e produção é obrigatória.
- NetworkPolicies compensam temporariamente a ausência de service mesh.
- PriorityClass máxima para Kong e Keycloak é requisito de resiliência.
- Zero segredos em texto plano no Git.
- `prune: false` é regra para infra central; `prune: true` é regra para apps de negócio.

## NFRs que mais mudam decisões

- Latência de borda <= 20 ms.
- Setup local < 5 minutos via `make up`.
- Tráfego externo 100% TLS/HTTPS.
- Gateway deve operar >= 60 minutos via cache JWKS sem Keycloak.

## Topologia e recuperação

- Estrutura principal: `cluster/bootstrap/`, `cluster/infrastructure/`, `cluster/apps/` e `cluster/boilerplates/api-base-v1/`.
- Fluxo de dados: cliente externo -> Kong -> validacao JWKS local -> HTTP interno -> API; em deep security, oauth2-proxy sidecar reforca validacao local.
- Recuperacao parcial: restaurar componente e deixar o ArgoCD resincronizar.
- Recuperacao total: criar namespaces, injetar secrets, instalar ArgoCD, aplicar `root-app.yaml` e deixar as sync waves reassumirem.

---
Autoria/Implementação: GPT-5 Codex

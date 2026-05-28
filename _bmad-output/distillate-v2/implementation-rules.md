# Regras de Implementação

Use este companion para implementar ou revisar manifests, overlays, scripts e automações do projeto principal.

## Invariantes obrigatórios

- Nomes Kubernetes, diretórios e manifests em `kebab-case`.
- Padrão de nome: `<app>-<tipo>`.
- Labels obrigatórios: `app.kubernetes.io/name`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of=cluster-kubernetes`.
- `app.kubernetes.io/component` só pode ser `api`, `database`, `identity-provider`, `gateway` ou `worker`.
- YAML com 2 espaços, comentário inicial em pt-BR e tags Docker imutáveis; nunca `latest`.
- Todo componente segue `base/` + `overlays/local|homologacao|production`.
- Scripts ficam em `/scripts/`; documentação em `/docs/`.
- Boilerplates vivem em `/cluster/boilerplates/` com versionamento semântico e `CONTRACT.md`.
- `CONTRACT.md` do boilerplate precisa declarar ao menos `app-name`, `hostname`, `paths`, `rate-limit-per-minute` e `namespace`.
- Desenvolvedores operam em `/cluster/apps/<api>/`; não editam a base do boilerplate diretamente.
- Dependências internas, como PostgreSQL do Keycloak, ficam no namespace do serviço pai.

## Regras GitOps e ArgoCD

- `argocd.argoproj.io/sync-wave` é obrigatório em manifests de infraestrutura.
- Ordem: Wave 0 namespaces/secrets, Wave 1 PostgreSQL, Wave 2 Keycloak, Wave 3 Kong, Wave 4+ apps.
- `infra-app.yaml` usa `prune: false`.
- `apps-app.yaml` usa `prune: true`, `CreateNamespace=true` e glob `cluster/apps/*`.
- Não usar `ApplicationSets`; o padrão é App-of-Apps clássico.
- APIs de negócio não devem ser registradas manualmente no bootstrap; a descoberta é automática via glob.

## Validação e qualidade

- `kube-linter` e `conftest` são gate de `make up` e CI.
- `make up` deve falhar se houver violação de nomenclatura, labels, `latest` ou probes obrigatórios.
- `readinessProbe` e `livenessProbe` são obrigatórios nos Deployments.
- Kong e Keycloak devem manter logs JSON estruturados desde o primeiro deploy.

## Quando abrir mais contexto

- Abra `architecture-status.md` se a tarefa tocar segurança, topologia ou ADRs.
- Abra `planning.md` se a tarefa depender do épico ou da story atual.
- Abra `deferred-work.md` se a mudança estiver perto de um item já diferido.

---
Autoria/Implementação: GPT-5 Codex

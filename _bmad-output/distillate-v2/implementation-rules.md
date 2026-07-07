# Regras de Implementação

Use este companion para implementar ou revisar manifests, overlays, scripts e automações do projeto principal.

## Invariantes obrigatórios

- Nomes Kubernetes, diretórios e manifests em `kebab-case`.
- Padrão de nome: `<app>-<tipo>`.
- Labels obrigatórios: `app.kubernetes.io/name`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of=cluster-kubernetes`.
- `app.kubernetes.io/component` só pode ser `api`, `database`, `identity-provider`, `gateway`, `worker` ou `network`.
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

- `kube-linter` e `conftest` são gate de `make up` e CI. **Falha no lint bloqueia tudo.**
- `readinessProbe` e `livenessProbe` são obrigatórios nos Deployments.
- Kong e Keycloak devem manter logs JSON estruturados desde o primeiro deploy.

### Regras conftest (OPA — `policy/kebab-case.rego`)

- Todo `metadata.name` de recurso Kubernetes deve ser `kebab-case` (apenas `[a-z0-9-]`).
- Todo `metadata.namespace` deve ser `kebab-case`.
- `CustomResourceDefinition` é isento da verificação de nome (formato `<plural>.<group>` é obrigatório pela spec do k8s).
- Exceções permitidas: `default`, `system:serviceaccount:argocd:argocd-application-controller`, e nomes RBAC do MetalLB (`metallb-system:controller`, `metallb-system:speaker`).
- Para adicionar nova exceção de RBAC vendor, editar o conjunto `exceptions` em `policy/kebab-case.rego`.

### Regras kube-linter (`.kube-linter.yaml`)

Aplicadas a `Deployment`, `Service`, `StatefulSet` e `DaemonSet`:

| Check | Regra |
|-------|-------|
| `required-label-name` | `app.kubernetes.io/name` obrigatório |
| `required-label-component` | `app.kubernetes.io/component` ∈ `{api, database, identity-provider, gateway, worker, network}` |
| `required-label-part-of` | `app.kubernetes.io/part-of: cluster-kubernetes` fixo |
| `no-liveness-probe` | `livenessProbe` obrigatório em Deployments |
| `no-readiness-probe` | `readinessProbe` obrigatório em Deployments |
| `latest-tag` | Proibido em qualquer imagem |

### Padrão obrigatório para recursos vendor (manifests upstream via URL remota)

Quando um `kustomization.yaml` referencia um manifest externo via `resources: - https://...`, os recursos upstream frequentemente violam nossas regras (labels ausentes, hostNetwork, NET_RAW, etc.). O responsável pela inclusão **deve** neutralizar essas violações com patches kustomize no mesmo arquivo ou no overlay que referencia a base:

```yaml
patches:
  - patch: |-
      apiVersion: apps/v1
      kind: DaemonSet
      metadata:
        name: <nome-do-recurso>
        namespace: <namespace>
        annotations:
          ignore-check.kube-linter.io/host-network: "vendor — design upstream intencional"
          ignore-check.kube-linter.io/required-label-name: "recurso vendor upstream"
          ignore-check.kube-linter.io/required-label-component: "recurso vendor upstream"
          ignore-check.kube-linter.io/required-label-part-of: "recurso vendor upstream"
          # adicionar demais checks que o upstream viola
    target:
      kind: DaemonSet
      name: <nome-do-recurso>
      namespace: <namespace>
```

Referência de implementação: `cluster/infrastructure/metallb/base/kustomization.yaml`.

## Quando abrir mais contexto

- Abra `architecture-status.md` se a tarefa tocar segurança, topologia ou ADRs.
- Abra `planning.md` se a tarefa depender do épico ou da story atual.
- Abra `deferred-work.md` se a mudança estiver perto de um item já diferido.

---
Autoria/Implementação: GPT-5 Codex

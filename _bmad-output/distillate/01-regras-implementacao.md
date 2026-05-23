# Regras de Implementação — Destilado. Parte 1 de 4.

## Nomenclatura Kubernetes

- Namespaces, Deployments, Services, ConfigMaps, diretórios: SEMPRE `kebab-case`; NUNCA PascalCase/camelCase/snake_case
- Padrão: `<app>-<tipo>` (ex: `keycloak-deployment`, `kong-configmap`)
- Ancoragem: nome do recurso K8s DEVE derivar do nome do diretório em `/apps/` (dir `api-pedidos` → deployment `api-pedidos-deployment`, namespace `api-pedidos`)
- Labels obrigatórios em TODO recurso:
  - `app.kubernetes.io/name`: igual ao nome do diretório/app
  - `app.kubernetes.io/component`: valores permitidos: `api`, `database`, `identity-provider`, `gateway`, `worker`
  - `app.kubernetes.io/part-of`: fixo `cluster-kubernetes`
- Dependências internas (ex: PostgreSQL do Keycloak) ficam no namespace do serviço pai (`keycloak-auth`); apenas serviços independentes recebem namespaces próprios

## Formato YAML

- Indentação: SEMPRE 2 espaços; NUNCA tabs ou 4 espaços
- Cabeçalho obrigatório: todo YAML inicia com comentário descritivo em pt-BR (ex: `# Deployment principal do Keycloak - Identity Provider OIDC`)
- Tags Docker: SEMPRE tag explícita e imutável (ex: `keycloak:26.2.1`); NUNCA `latest`

## Estrutura Kustomize

- Todo componente DEVE seguir:
  ```
  /infrastructure/<componente>/
  ├── base/
  │   ├── kustomization.yaml
  │   └── <recurso>.yaml
  └── overlays/
      ├── local/
      ├── homologacao/
      └── production/
  ```
- NUNCA criar componente sem separação `base/` + `overlays/` com 3 ambientes
- Scripts Bash: exclusivamente em `/scripts/`; NUNCA na raiz
- Documentação: exclusivamente em `/docs/`; NUNCA em pastas de infraestrutura
- Boilerplates em `/cluster/boilerplates/` com versionamento semântico de pastas (`v1/`, `v2/`); atualizações da plataforma NÃO propagam automaticamente para APIs em produção

## Contrato do Boilerplate

- Todo Boilerplate DEVE conter `CONTRACT.md` com tabela: `Variável | Obrigatória | Valor Padrão | Descrição`
- Variáveis mínimas obrigatórias: `app-name`, `hostname`, `paths`, `rate-limit-per-minute`, `namespace`
- Desenvolvedores operam exclusivamente em `/cluster/apps/<sua-api>/` via overlay; NUNCA modificam Base diretamente
- Procedimento de escape: dev aciona equipe de Plataforma se Boilerplate insuficiente

## Processo ArgoCD (Sync Waves)

- Annotation obrigatória em todo manifesto de infraestrutura: `argocd.argoproj.io/sync-wave: "<número>"`
- Ordem estrita: Wave 0 (Namespaces/Secrets) → Wave 1 (PostgreSQL) → Wave 2 (Keycloak) → Wave 3 (Kong DB-Less) → Wave 4+ (Apps de negócio)
- `infra-app.yaml`: `prune: false` (Safe-Prune)
- `apps-app.yaml`: `prune: true` + `CreateNamespace=true` + glob `cluster/apps/*`
- NUNCA usar `ApplicationSets` — padrão é App-of-Apps clássico

## Validação Automatizada

- `kube-linter` + `conftest` (OPA) como pré-condição do `make up` e gate de CI
- Valida: kebab-case, labels obrigatórios, proibição `latest`, probes obrigatórios
- `make up` DEVE falhar se violações detectadas

## Rastreabilidade LLM

- Todo artefato gerado/editado por IA DEVE registrar: `Autoria/Implementação: <modelo>`
- Revisão por outro agente: `Revisão: <modelo>` abaixo do autor original

## Isolamento .tracker/

- Pasta `.tracker/` é invisível para tarefas de infraestrutura K8s; acesso apenas mediante solicitação explícita do desenvolvedor
- Menção espontânea em contexto de infra = violação de escopo semântico

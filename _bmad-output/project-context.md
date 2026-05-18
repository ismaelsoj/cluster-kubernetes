---
project_name: 'cluster-kubernetes'
user_name: 'Ismael'
date: '2026-05-13'
sections_completed: ['technology_stack', 'naming_conventions', 'file_structure', 'yaml_format', 'argocd_process', 'security_boundaries', 'critical_dont_do']
status: 'complete'
rule_count: 40
optimized_for_llm: true
---

# Contexto do Projeto para Agentes de IA

_Este arquivo contém regras críticas e padrões que agentes de IA devem seguir ao implementar código neste projeto. Foco nos detalhes não-óbvios que os agentes poderiam perder._

---

## Stack de Tecnologia e Versões

- **k3d** v5.8.3 — provisiona o cluster Kubernetes local via Docker
- **Kubernetes** (via k3d) — runtime de orquestração de contêineres
- **ArgoCD** v3.4.2 — operador GitOps (pull-based), padrão App-of-Apps
- **Kong DB-Less** v3.4.x LTS — API Gateway stateless, instalado via Kong Ingress Controller (KIC)
- **Keycloak** 26.2.1 — Identity Provider OIDC
- **PostgreSQL** (versão a fixar no overlay) — banco de estado exclusivo do Keycloak
- **Kustomize** v5.x (nativo no `kubectl`) — motor de templates YAML
- **kube-linter** & **Conftest (OPA)** (a configurar na Story 1.4) — validação automática estrutural, de segurança e de nomenclatura de manifestos YAML
- **GitHub Actions** (`actions/checkout@v4`) — pipeline de CI
- **Makefile + Bash** — orquestrador do ciclo de vida local do desenvolvedor

## Critical Implementation Rules

### Nomenclatura Kubernetes

- **Namespaces, Deployments, Services, ConfigMaps, diretórios:** SEMPRE `kebab-case`. Nunca PascalCase, camelCase ou snake_case.
- **Padrão de nome de recurso:** `<app>-<tipo>` (ex: `keycloak-deployment`, `kong-configmap`).
- **Ancoragem obrigatória:** o nome do recurso K8s DEVE derivar diretamente do nome do diretório em `/apps/`. Se o diretório é `api-pedidos`, o deployment é `api-pedidos-deployment` e o namespace é `api-pedidos`.
- **Labels obrigatórios em TODO recurso:**
  - `app.kubernetes.io/name`: igual ao nome do diretório/app
  - `app.kubernetes.io/component`: SOMENTE um desses valores: `api`, `database`, `identity-provider`, `gateway`, `worker`
  - `app.kubernetes.io/part-of`: fixo como `cluster-kubernetes` em todos os recursos do repositório
- **Namespaces de dependências:** dependências internas (ex: PostgreSQL do Keycloak) ficam no mesmo namespace do serviço pai (`keycloak-auth`). Apenas serviços independentes recebem namespaces próprios.

### Estrutura de Arquivos e Kustomize

- **Todo componente de infraestrutura** deve seguir obrigatoriamente a estrutura:
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
- **Nunca criar componente sem separação `base/` e `overlays/`** com os 3 ambientes (local, homologacao, production).
- **Scripts Bash** ficam exclusivamente em `/scripts/`. Nunca soltos na raiz do repositório.
- **Documentação** (contratos, guias, emergência) fica exclusivamente em `/docs/`.
- **Boilerplates** em `/cluster/boilerplates/` devem adotar versionamento semântico de pastas (`v1/`, `v2/`) — atualizações da plataforma NÃO propagam automaticamente para APIs em produção.
- **Todo Boilerplate** deve conter `CONTRACT.md` com tabela de colunas: `Variável | Obrigatória | Valor Padrão | Descrição`. Variáveis mínimas obrigatórias: `app-name`, `hostname`, `paths`, `rate-limit-per-minute`, `namespace`.
- **Desenvolvedores** operam exclusivamente em `/cluster/apps/<sua-api>/` via overlay do Kustomize. Nunca modificam a Base do Boilerplate diretamente.
- **`apps-app.yaml`** usa descoberta automática via glob (`path: cluster/apps/*`) — não registrar novas APIs manualmente.
- **Namespaces de aplicações de negócio** são criados automaticamente via `CreateNamespace=true` no ArgoCD — não editar `/infrastructure/namespaces/` para isso.

### Formato YAML

- **Indentação:** SEMPRE 2 espaços. Nunca tabs ou 4 espaços.
- **Cabeçalho obrigatório:** todo arquivo YAML deve iniciar com comentário descritivo em **pt-BR** (ex: `# Deployment principal do Keycloak - Identity Provider OIDC`).
- **Tags Docker:** SEMPRE tag explícita e imutável (ex: `keycloak:26.2.1`). Nunca `latest` em nenhum manifesto.

### Processo ArgoCD (Sync Waves)

- **Annotation obrigatória** em todo manifesto de infraestrutura: `argocd.argoproj.io/sync-wave: "<número>"`.
- **Ordem estrita de Sync Waves:**

  | Wave | Componente | Motivo |
  |------|-----------|--------|
  | `"0"` | Namespaces e Secrets | Pré-requisitos estruturais |
  | `"1"` | PostgreSQL | Dependência de estado do Keycloak |
  | `"2"` | Keycloak | Depende do banco operacional |
  | `"3"` | Kong DB-Less | Depende do JWKS endpoint do Keycloak |
  | `"4+"` | Aplicações de negócio | Dependem do Gateway e IAM |

- **Safe-Prune segregado:**
  - Infraestrutura central (Kong, Keycloak, ArgoCD): `prune: false` — gerenciado pelo `infra-app.yaml`.
  - Aplicações de negócio: `prune: true` — gerenciado pelo `apps-app.yaml`.
- **Healthchecks obrigatórios:** todo Deployment DEVE declarar `readinessProbe` e `livenessProbe`. Endpoints de healthcheck devem ser públicos (não autenticados).
- **Logs estruturados:** habilitar formato JSON nos componentes que suportam (Kong e Keycloak suportam nativamente) desde o primeiro deploy.

### Segurança e Limites Arquiteturais

- **Secrets nunca no Git:** credenciais (senhas, chaves) são injetadas manualmente no bootstrap do cluster. Nenhum Secret deve aparecer em nenhum manifesto versionado.
- **Segregação de ambientes obrigatória:** o k3d local DEVE operar com Realms e chaves de assinatura Keycloak matematicamente distintas da produção. Tokens gerados em dev são rejeitados em prod.
- **Tráfego externo:** entra exclusivamente pelo Kong (namespace `kong-gateway`). O Kong termina TLS e valida JWKS localmente antes de repassar ao Pod.
- **Validação JWKS descentralizada:** Kong valida tokens via cache local de chaves públicas (não por introspecção ativa no Keycloak). Cache TTL = 60 minutos.
- **Keycloak é o único emissor de tokens.** Nenhum outro componente emite ou assina JWTs.
- **PostgreSQL do Keycloak** é acessível somente dentro do namespace `keycloak-auth` (isolado por NetworkPolicy).
- **GitOps estrito:** o ArgoCD lê exclusivamente do repositório Git. Alterações manuais no cluster são proibidas, exceto Secrets no bootstrap inicial.
- **Ingress blindado:** o objeto `Ingress` pertence à Base Kustomize da plataforma. Desenvolvedores preenchem apenas variáveis via overlay — nunca manipulam a estrutura do Ingress diretamente.
- **Anotações do Kong via Boilerplate:** Rate Limiting e autenticação fluem exclusivamente através de `annotations` declaradas no `Ingress`. Nenhuma configuração dinâmica via Admin API do Kong.

### Regras Críticas — O Que NÃO Fazer

- **NÃO usar PascalCase, camelCase ou snake_case** em nomes de recursos ou diretórios Kubernetes.
- **NÃO criar recursos sem os labels** `app.kubernetes.io/name`, `app.kubernetes.io/component` e `app.kubernetes.io/part-of`.
- **NÃO usar `latest`** em nenhuma imagem Docker, em nenhuma circunstância.
- **NÃO criar componente sem separação `base/` e `overlays/`** com os 3 ambientes (local, homologacao, production).
- **NÃO usar indentação com tabs ou 4 espaços** em arquivos YAML.
- **NÃO criar arquivos YAML sem comentário descritivo inicial em pt-BR.**
- **NÃO modificar diretamente a Base do Boilerplate** sem autorização da equipe de Plataforma. Desenvolvedores usam apenas overlays.
- **NÃO omitir a annotation `argocd.argoproj.io/sync-wave`** em manifestos de infraestrutura.
- **NÃO omitir `readinessProbe` ou `livenessProbe`** em Deployments.
- **NÃO usar `ApplicationSets` do ArgoCD** — o padrão é App-of-Apps clássico (decidido como excessivamente complexo para o MVP).
- **NÃO criar scripts bash fora de `/scripts/`.**
- **NÃO misturar documentação técnica dentro de pastas de infraestrutura** — docs vão em `/docs/`.
- **NÃO aplicar `prune: false` a aplicações de negócio** — apenas à infraestrutura central. Apps usam `prune: true`.

---

## Diretrizes de Uso

**Para Agentes de IA:**

- Leia este arquivo antes de implementar qualquer código ou manifesto
- Siga TODAS as regras exatamente como documentadas
- Em caso de dúvida, prefira a opção mais restritiva
- Consulte `_bmad-output/planning-artifacts/architecture.md` para decisões arquiteturais completas

**Para Humanos:**

- Mantenha este arquivo focado nas necessidades dos agentes — lean e específico
- Atualize ao fixar versões que estão "a definir" (ArgoCD, PostgreSQL)
- Revise periodicamente para remover regras que se tornarem óbvias
- Ao adicionar nova restrição arquitetural, adicione aqui também

Última Atualização: 2026-05-18

# Arquitetura e Decisões — Destilado. Parte 2 de 4.

## Stack Tecnológico

- k3d v5.8.3: provisiona cluster K8s local via Docker
- Kubernetes via k3d: runtime de orquestração
- ArgoCD v3.4.2: operador GitOps pull-based; padrão App-of-Apps
- Kong DB-Less v3.4.x LTS: API Gateway stateless via Kong Ingress Controller (KIC)
- Keycloak 26.2.1: Identity Provider OIDC
- PostgreSQL (versão a fixar no overlay): banco exclusivo do Keycloak
- Kustomize v5.x (nativo kubectl): motor de templates
- kube-linter + Conftest (OPA): validação automática
- GitHub Actions (actions/checkout@v4): pipeline CI
- Makefile + Bash: orquestrador local

## ADRs Fundacionais

- Gateway DB-Less (Stateless): Kong DB-Less → conformidade total com GitOps; toda config de rotas/Rate Limits via Git+ArgoCD; rejeita APIs dinâmicas stateful em favor de imutabilidade
- Validação JWKS Local: cache JWKS no Kong em vez de Introspecção Ativa no Keycloak; sobrevivência do fluxo por 60min em queda do IDP (NFR-R02); latência sub-20ms (NFR-P01)
- Gestão Estática de Segredos: injeção manual no bootstrap; sem Vault na Fase 1
- Rejected: ApplicationSets do ArgoCD (complexo demais para MVP single-cluster)
- Rejected: Gateway API/HTTPRoute (adiado; Ingress clássico com anotações Kong para curva de aprendizado menor)
- Rejected: Service Mesh/mTLS interno (adiado Fase 3; compensado temporariamente por NetworkPolicies)
- Rejected: Cofres automatizados de segredos (adiado para simplificar Fase 1)

## Limites Arquiteturais

- Tráfego Norte-Sul: todo tráfego externo entra exclusivamente pelo Kong (`kong-gateway`); Kong termina TLS e valida JWKS antes de repassar ao Pod
- Identidade: Keycloak é único emissor de tokens; nenhum outro componente emite/assina JWTs; PostgreSQL acessível somente dentro de `keycloak-auth` (NetworkPolicy)
- GitOps: ArgoCD lê exclusivamente do Git; alterações manuais no cluster proibidas (exceto Secrets no bootstrap); `cluster/bootstrap/` é único ponto de entrada
- DevEx: desenvolvedores operam exclusivamente em `/cluster/apps/<api>/`; consomem Base de `/cluster/boilerplates/api-base-v1/` via Kustomize; preenchem variáveis do CONTRACT.md

## Fluxo de Dados

- Cliente Externo →(HTTPS)→ Kong Gateway →(validação JWKS cache local)→ HTTP interno → Pod API → valida JWT localmente (Deep Security via oauth2-proxy sidecar)
- Keycloak → refresh periódico → Cache JWKS do Kong (TTL ≥ 60min)

## Segurança e Hardening

- Contenção JWKS 60min: Rate Limits restritivos como barreira contra exfiltração durante janela de validade cega do cache
- NetworkPolicies: isolamento East-West entre namespaces (compensa ausência de mTLS interno)
- Segregação Dev/Prod: Realms e chaves de assinatura locais matematicamente distintas da Produção
- IP Whitelisting para API Keys de legados: explicitamente fora do escopo MVP (risco aceito)
- Criptografia: 100% tráfego externo sob TLS/HTTPS (NFR-S01); zero segredos em Git (NFR-S02)

## NFRs Chave

- NFR-P01: latência de borda ≤ 20ms (validação JWKS local)
- NFR-P02: setup local < 5min via `make up` (imagens cacheadas)
- NFR-S01: 100% tráfego externo TLS/HTTPS
- NFR-S02: zero segredos texto plano em Git
- NFR-R01: PriorityClass máxima para Kong e Keycloak (imunes a eviction)
- NFR-R02: Gateway opera ≥ 60min via cache JWKS sem Keycloak

## Estrutura de Diretórios

```
cluster-kubernetes/
├── Makefile, k3d.yaml, README.md
├── .github/workflows/lint.yml
├── scripts/ (cluster-up.sh, cluster-down.sh, generate-token.sh, lint.sh, status.sh, inject-secrets.sh)
├── docs/ (contrato-do-desenvolvedor.md, bootstrap-emergencia.md)
└── cluster/
    ├── bootstrap/ (root-app.yaml, infra-app.yaml, apps-app.yaml)
    ├── infrastructure/
    │   ├── namespaces/ (Wave 0)
    │   ├── keycloak-auth/ (Wave 1: Postgres + Wave 2: Keycloak + realm-config.json)
    │   ├── kong-gateway/ (Wave 3)
    │   └── network-policies/
    ├── apps/ (Wave 4+, descoberta automática via glob)
    └── boilerplates/api-base-v1/ (CONTRACT.md, base/, overlays/)
```

## Cenários de Recuperação

- Parcial (ArgoCD ativo, componente caído): restaurar componente → ArgoCD detecta divergência → resincroniza
- Total (cluster perdido): criar namespaces → injetar Secrets → instalar ArgoCD → aplicar root-app.yaml → ArgoCD assume via Sync Waves

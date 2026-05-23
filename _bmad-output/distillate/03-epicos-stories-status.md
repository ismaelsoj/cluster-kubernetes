# Épicos, Stories e Status — Destilado. Parte 3 de 4.

## Status Geral

- Total: 4 épicos, 18 stories
- Dependências lineares: É1→É2→É3→É4
- Épico 1: DONE (5/5 stories + retrospectiva concluída 2026-05-22)
- Épicos 2-4: backlog
- Próximo: Story 2.1 (PostgreSQL Wave 1)

## Cobertura

- 24/24 FRs mapeados; 6/6 NFRs cobertos
- Jornadas 1-2 do PRD cobertas; Jornada 3 (Legado ERP) → Pós-MVP

## Épico 1: Fundação do Repositório, Automação Local e Bootstrap GitOps — DONE

- 1.1 Scaffold Repositório + k3d.yaml: DONE — árvore de diretórios completa, `k3d.yaml` com limites de recursos, separação base/overlays, kebab-case
- 1.2 Makefile + Scripts Automação: DONE — `make up`/`make down`, cluster-up.sh/cluster-down.sh, setup < 5min (NFR-P02)
- 1.3 Bootstrap ArgoCD + App-of-Apps: DONE — ArgoCD operacional, root-app.yaml, infra-app (prune:false), apps-app (prune:true + CreateNamespace + glob), sync-waves corretos
- 1.4 Linter YAML + CI + README: DONE — kube-linter + conftest (OPA), make lint como pré-condição, lint.yml no GitHub Actions, README com pré-requisitos
- 1.5 Procedimento Secrets + Doc Emergência: DONE — inject-secrets.sh, bootstrap-emergencia.md (esqueleto para refinamento no É3)

## Épico 2: Identidade, Persistência e Recuperação de Desastres — BACKLOG

- 2.1 PostgreSQL (Wave 1): Baixa Complexidade — deploy GitOps em `keycloak-auth`, sync-wave:"1", tag imutável postgres:18.4, NetworkPolicy restringindo acesso, probes, labels, comentário pt-BR
- 2.2 Keycloak (Wave 2): Média — sync-wave:"2", tag keycloak:26.6.2, conectado ao PostgreSQL via Secret, PriorityClass máxima, healthcheck público, logs JSON, overlays 3 ambientes, Ingress local
- 2.3 Realm + Client M2M: Baixa — realm-config.json com chaves locais distintas de prod, Client client_credentials (FR06), TTL configurável (FR07), revogação manual (FR08), Event Listeners (FR09)
- 2.4 Backup/Restore PostgreSQL: Baixa — pg_dump/pg_restore testado (FR23), fixture de dados de teste documentado

## Épico 3: Gateway de Borda e Segurança Zero-Trust — BACKLOG

- 3.1 Kong DB-Less (Wave 3): Média — modo DB-Less via ConfigMap, tag kong:3.4.2, PriorityClass, NetworkPolicy, healthcheck público, logs JSON
- 3.2 TLS + JWKS + Rate Limit: Alta — HTTP→rejeita/redireciona HTTPS (FR11/NFR-S01); validação JWKS cache (FR12), latência <20ms (NFR-P01); Rate Limit default 100 req/min (FR15); cache JWKS TTL ≥60min (NFR-R02)
- 3.3 Script Token + Feedback Terminal: Baixa — generate-token.sh via curl ao Keycloak (FR04), status.sh com resumo formatado; validação: sem token→401, com Bearer→200
- 3.4 Refinamento Bootstrap Emergência: Baixa — atualizar bootstrap-emergencia.md com dados reais (nomes Secrets, comandos kubectl verificados, healthcheck endpoints)
- 🏁 Marco: Jornada 1 (Dev M2M Local) validável ao final deste épico

## Épico 4: Boilerplate, Habilitação Dev e Deep Security — BACKLOG

- 4.1 Base Kustomize Boilerplate + CONTRACT.md: Média — deployment/service/ingress blindado com anotações Kong (FR05), dev interage só via variáveis no Overlay, CONTRACT.md com tabela padronizada
- 4.2 Overlays + Rate Limiting + Bypass Swagger: Média — 3 overlays funcionais, Rate Limit customizável via anotação Kong (FR14), /swagger sem token em local/homologação (FR16), 401 em produção
- 4.3 API Teste End-to-End: Baixa — `cluster/apps/api-teste/` consumindo Base, ArgoCD detecta via glob, namespace automático, validação Jornada 1 completa
- 4.4 Sidecar oauth2-proxy Deep Security: Alta — pod com 2 containers (app + oauth2-proxy), fluxo Kong→Sidecar→App, validação JWT independente (FR17), extração claims como headers X-Auth-Request-* (FR19), Introspection Endpoint para revogação (FR18), fallback cache JWKS se Keycloak indisponível
- 4.5 Contrato do Desenvolvedor: Baixa — docs/contrato-do-desenvolvedor.md com visão geral, pré-requisitos, passo a passo Boilerplate, referência CONTRACT.md, teste local, fluxo segurança completo, procedimento de escape

## Mapa FR → Épico

- É1: FR01, FR02, FR03(parcial), FR20, FR21, FR22
- É2: FR06, FR07, FR08, FR09, FR23
- É3: FR04, FR10, FR11, FR12, FR13, FR15, FR24
- É4: FR03(completude), FR05, FR14, FR16, FR17, FR18, FR19

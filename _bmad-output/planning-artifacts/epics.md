---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# cluster-kubernetes - Decomposição de Épicos e Histórias

## Visão Geral

Este documento fornece a decomposição completa de épicos e histórias para o projeto cluster-kubernetes, transformando os requisitos do PRD e as decisões da Arquitetura em histórias implementáveis. Validado por 2 rodadas de Party Mode (6 agentes) e Tree of Thoughts.

## Inventário de Requisitos

### Requisitos Funcionais

- **FR01:** Provisionar cluster K8s local completo via `make up`.
- **FR02:** Destruir/resetar cluster local via `make down`.
- **FR03:** Paridade exata de topologia local-produção (Kong, Keycloak).
- **FR04:** Gerar e exibir Token M2M de Teste automaticamente no terminal.
- **FR05:** Instanciar nova API via Boilerplate YAML padronizado.
- **FR06:** Gerar credenciais M2M (Client Credentials) via Keycloak.
- **FR07:** Definir TTL estendido para tokens M2M na Fase 1.
- **FR08:** Revogar credenciais/Clients manualmente em emergência.
- **FR09:** Registrar logs nativos de emissão de tokens (auditoria básica).
- **FR10:** Interceptar todo tráfego HTTP/HTTPS de entrada do cluster.
- **FR11:** Forçar bloqueio de requisições HTTP inseguras na borda (HTTPS/TLS).
- **FR12:** Validar tokens OIDC localmente via JWKS cache.
- **FR13:** Repassar Token JWT original (Bearer) intacto para aplicação interna.
- **FR14:** Configurar Rate Limiting por API via configuração declarativa.
- **FR15:** Aplicar Rate Limit padrão restritivo automaticamente (Secure by Default).
- **FR16:** Isentar rotas `/swagger` de autenticação em ambientes Local/Homologação.
- **FR17:** Aplicação interna valida criptograficamente o Token JWT via Sidecar.
- **FR18:** Introspecção/Revogação ativa contra Keycloak para invalidar tokens em emergência.
- **FR19:** Aplicação extrai dados de identidade diretamente do payload JWT.
- **FR20:** ArgoCD sincroniza manifestos exclusivamente a partir do Git.
- **FR21:** Safe-Prune inibe deleção automática de manifestos críticos.
- **FR22:** SRE injeta Secrets manualmente no cluster (sem versionar no Git).
- **FR23:** SRE restaura identidades via backups estáticos do PostgreSQL.
- **FR24:** Gateway e Identidade expõem healthchecks públicos não autenticados.

### Requisitos Não-Funcionais

- **NFR-P01:** Latência de borda ≤ 20ms.
- **NFR-P02:** Setup local completo < 5 minutos.
- **NFR-S01:** 100% tráfego externo sob TLS/HTTPS.
- **NFR-S02:** Zero segredos em texto plano nos repositórios Git.
- **NFR-R01:** Pods críticos (Kong, Keycloak) com PriorityClass máxima.
- **NFR-R02:** Gateway opera ≥ 60 minutos via cache JWKS em caso de queda do Keycloak.

### Requisitos Adicionais (Arquitetura)

- **Starter:** App-of-Apps GitOps + k3d Makefile. Story 0 = Scaffold.
- **Kustomize v5.x:** Separação `base/` + `overlays/` (local, homologacao, production).
- **Sync Waves:** Wave 0→1→2→3→4+.
- **NetworkPolicies:** Isolamento East-West entre namespaces.
- **Segregação Dev/Prod:** Realms e chaves criptográficas distintas.
- **Linter:** `kube-linter` como pré-condição do `make up` e gate de CI.
- **Logs JSON:** Kong e Keycloak desde o primeiro deploy.
- **CONTRACT.md:** Documentação formal de variáveis do Boilerplate.
- **Tags imutáveis:** Proibido `latest`.
- **Labels obrigatórios:** `app.kubernetes.io/name`, `component`, `part-of: cluster-kubernetes`.
- **Nomenclatura `kebab-case`:** Universal.
- **Comentários pt-BR:** Todo YAML inicia com bloco descritivo.
- **PriorityClasses:** Kong e Keycloak com prioridade máxima.
- **Safe-Prune seletivo:** `prune: false` infra, `prune: true` apps.
- **Descoberta automática:** `apps-app.yaml` via glob `cluster/apps/*`.
- **Sidecar JWT:** `oauth2-proxy` — consistente com Security Glue, sem conflito com Linkerd (Fase 3).

### Requisitos de Design UX

N/A — Plataforma Backend/Infraestrutura.

### Rastreabilidade: Jornada 3 (Legado ERP)

A Jornada 3 do PRD está **explicitamente fora do escopo** — endereçada no Pós-MVP (Fase 2).

### Mapa de Cobertura de FRs

| FR | Épico | Descrição |
|----|-------|-----------|
| FR01 | É1 | Provisionar cluster local via `make up` |
| FR02 | É1 | Destruir cluster local via `make down` |
| FR03 | É1+É4 | Paridade local-produção |
| FR04 | É3 | Token M2M automático no terminal |
| FR05 | É4 | Boilerplate YAML para novas APIs |
| FR06 | É2 | Gerar credenciais M2M |
| FR07 | É2 | TTL estendido para tokens |
| FR08 | É2 | Revogar credenciais em emergência |
| FR09 | É2 | Logs nativos de auditoria |
| FR10 | É3 | Interceptar todo tráfego de entrada |
| FR11 | É3 | Forçar HTTPS/TLS na borda |
| FR12 | É3 | Validação JWKS local |
| FR13 | É3 | Repasse JWT para aplicação |
| FR14 | É4 | Rate Limiting customizável |
| FR15 | É3 | Rate Limit padrão |
| FR16 | É4 | Bypass Swagger por ambiente |
| FR17 | É4 | Validação JWT via Sidecar oauth2-proxy |
| FR18 | É4 | Introspecção de emergência |
| FR19 | É4 | Extração de identidade do JWT |
| FR20 | É1 | GitOps via ArgoCD |
| FR21 | É1 | Safe-Prune |
| FR22 | É1 | Injeção manual de Secrets |
| FR23 | É2 | Restauração via backup PostgreSQL |
| FR24 | É3 | Healthchecks públicos |

**Cobertura: 24/24 FRs | 6/6 NFRs | Jornadas 1-2 cobertas | Jornada 3 → Pós-MVP**

## Lista de Épicos

- **Épico 1:** Fundação do Repositório, Automação Local e Bootstrap GitOps (5 stories)
- **Épico 2:** Identidade, Persistência e Recuperação de Desastres (4 stories)
- **Épico 3:** Gateway de Borda e Segurança Zero-Trust (4 stories)
- **Épico 4:** Boilerplate, Habilitação do Desenvolvedor e Deep Security (5 stories)

**Total: 18 stories | Dependências: É1→É2→É3→É4**

---

## Épico 1: Fundação do Repositório, Automação Local e Bootstrap GitOps

O Engenheiro de Plataforma possui o repositório GitOps completo, provisiona/destrói cluster k3d com comando único, ArgoCD operacional com Safe-Prune, Secrets documentados e validação via linter.

### Story 1.1: Scaffold do Repositório e Configuração k3d

**Complexidade:** Média Complexidade

Como um Engenheiro de Plataforma,
Eu quero criar a estrutura completa de diretórios do repositório GitOps e o arquivo `k3d.yaml`,
Para que a fundação esteja estabelecida com limites de recursos definidos.

**Critérios de Aceitação:**

**Dado** que o repositório está vazio
**Quando** a story for implementada
**Então** a árvore de diretórios completa deve existir conforme a Arquitetura (`cluster/bootstrap/`, `cluster/infrastructure/`, `cluster/apps/`, `cluster/boilerplates/`, `scripts/`, `docs/`)
**E** o `k3d.yaml` deve existir com limites severos de CPU/Memória
**E** cada diretório de infraestrutura deve possuir separação `base/` + `overlays/` (local, homologacao, production)
**E** nomenclatura `kebab-case` em todos os diretórios

### Story 1.2: Makefile e Scripts de Automação Local

**Complexidade:** Média Complexidade

Como um Desenvolvedor,
Eu quero provisionar e destruir o cluster k3d com `make up` / `make down` (nativamente no macOS/Linux ou via WSL2 no Windows),
Para que eu trabalhe com a infraestrutura sem conhecer os detalhes do Kubernetes e com atrito zero.

**Critérios de Aceitação:**

**Dado** que o repositório possui a estrutura (Story 1.1)
**Quando** `make up` for executado (seja no terminal Unix nativo ou no shell do WSL2 no Windows)
**Então** `scripts/cluster-up.sh` deve provisionar o cluster k3d conforme `k3d.yaml`
**E** o cluster deve estar acessível via `kubectl`

**Dado** que o cluster está em execução
**Quando** `make down` for executado (no terminal Unix ou via WSL2 no Windows)
**Então** `scripts/cluster-down.sh` deve destruir completamente o cluster sem resíduos

**Dado** imagens Docker cacheadas
**Quando** `make up` for executado
**Então** provisionamento completo em < 5 minutos (NFR-P02)

### Story 1.3: Bootstrap ArgoCD e Manifestos App-of-Apps

**Complexidade:** Média Complexidade

Como um Engenheiro de Plataforma,
Eu quero que o ArgoCD seja instalado automaticamente e aplique manifestos a partir do Git,
Para que a infraestrutura seja governada por GitOps com proteção contra deleção acidental.

**Critérios de Aceitação:**

**Dado** que o cluster k3d está em execução (Story 1.2)
**Quando** `cluster-up.sh` concluir a instalação do ArgoCD
**Então** o ArgoCD deve estar operacional e `root-app.yaml` aplicado automaticamente

**Dado** que o `root-app.yaml` foi aplicado
**Quando** o ArgoCD sincronizar
**Então** `infra-app.yaml` com `prune: false` (FR21) e `apps-app.yaml` com `prune: true` + `CreateNamespace=true` + glob `cluster/apps/*` devem ser detectados
**E** todos os recursos devem possuir `sync-wave` correto (Wave 0 para namespaces)
**E** nenhum segredo em texto plano nos manifestos (NFR-S02)

### Story 1.4: Linter YAML, Pipeline CI e README

**Complexidade:** Média Complexidade

Como um Engenheiro de Plataforma,
Eu quero validação automática de todos os manifestos,
Para que erros de nomenclatura, labels ausentes ou tags `latest` sejam detectados antes do deploy.

**Critérios de Aceitação:**

**Dado** `scripts/lint.sh` configurado com `kube-linter` e `conftest` (OPA)
**Quando** `make lint` ou `make up` executado
**Então** valida: `kebab-case` (via Conftest), labels `app.kubernetes.io/*`, proibição `latest` e probes obrigatórios (via kube-linter)
**E** `make up` falha se violações em qualquer validador forem detectadas

**Dado** `.github/workflows/lint.yml` existe
**Quando** commit enviado
**Então** CI executa mesma validação como gate de qualidade

**Dado** `README.md` na raiz
**Quando** lido por novo membro
**Então** lista pré-requisitos (Docker, kubectl, k3d), comando `make up` e link para Contrato do Desenvolvedor

### Story 1.5: Procedimento de Secrets e Documentação de Emergência

**Complexidade:** Baixa Complexidade

Como um SRE,
Eu quero procedimento documentado para injetar Secrets e guia de recuperação,
Para que eu reconstrua a infraestrutura sem depender de conhecimento tácito.

**Critérios de Aceitação:**

**Dado** cluster em execução
**Quando** SRE seguir procedimento de injeção
**Então** Secrets criados nos namespaces corretos via `kubectl create secret` sem valores no Git (FR22, NFR-S02)

**Dado** `docs/bootstrap-emergencia.md`
**Quando** lido por SRE
**Então** contém sequência: criar namespaces → injetar Secrets → instalar ArgoCD → aplicar root-app.yaml
**E** é esqueleto inicial com placeholders (refinado no Épico 3)

---

## Épico 2: Identidade, Persistência e Recuperação de Desastres (Keycloak + PostgreSQL)

Identity Provider operacional com PriorityClass máxima, tokens M2M Client Credentials com TTL configurável, logs de auditoria e backup/restore testado.

### Story 2.1: Manifestos Kustomize do PostgreSQL (Wave 1)

**Complexidade:** Baixa Complexidade

Como um Engenheiro de Plataforma,
Eu quero o PostgreSQL deployado via GitOps no namespace `keycloak-auth`,
Para que o Keycloak tenha repositório de estado isolado por NetworkPolicies.

**Critérios de Aceitação:**

**Dado** ArgoCD operacional (Épico 1)
**Quando** ArgoCD sincronizar `cluster/infrastructure/keycloak-auth/`
**Então** PostgreSQL provisionado com `sync-wave: "1"`, tag imutável (ex: `postgres:16.3`), labels obrigatórios
**E** `readinessProbe`/`livenessProbe` configurados
**E** NetworkPolicy restringe acesso ao PostgreSQL a pods dentro de `keycloak-auth`
**E** YAML inicia com comentário pt-BR

### Story 2.2: Manifestos Kustomize do Keycloak (Wave 2)

**Complexidade:** Média Complexidade

Como um Engenheiro de Plataforma,
Eu quero o Keycloak deployado via GitOps conectado ao PostgreSQL,
Para que a plataforma tenha Identity Provider centralizado com prioridade máxima.

**Critérios de Aceitação:**

**Dado** PostgreSQL operacional (Story 2.1)
**Quando** ArgoCD sincronizar manifestos do Keycloak
**Então** Keycloak provisionado com `sync-wave: "2"`, tag imutável (ex: `keycloak:26.2.1`), conectado ao PostgreSQL via Secret
**E** PriorityClass máxima associada (NFR-R01)
**E** healthcheck público (FR24), logs JSON estruturado
**E** overlays para 3 ambientes, acessível via Ingress local

### Story 2.3: Configuração do Realm e Client M2M

**Complexidade:** Baixa Complexidade

Como um Administrador da Plataforma,
Eu quero Realm pré-configurado com Client M2M,
Para que eu emita tokens de longo TTL sem configuração manual repetitiva.

**Critérios de Aceitação:**

**Dado** Keycloak operacional (Story 2.2)
**Quando** `realm-config.json` importado
**Então** Realm com chaves de assinatura locais distintas da Produção, Client `client_credentials` configurado (FR06)
**E** TTL estendido configurável (FR07), revogação manual possível (FR08)
**E** Event Listeners registram emissão de tokens (FR09)
**E** `curl` contra endpoint de token retorna JWT válido (validação precoce)

### Story 2.4: Procedimento de Backup/Restore do PostgreSQL

**Complexidade:** Baixa Complexidade

Como um SRE,
Eu quero procedimento testado de backup e restauração do banco do Keycloak,
Para que eu recupere identidades em caso de desastre.

**Critérios de Aceitação:**

**Dado** PostgreSQL com dados do Realm (Story 2.3)
**Quando** `pg_dump` executado
**Então** backup completo gerado externamente ao cluster

**Dado** backup externo existe e banco vazio/corrompido
**Quando** `pg_restore` executado
**Então** banco restaurado com Realms/Clients intactos (FR23), Keycloak volta a emitir tokens
**E** fixture de dados de teste documentado para reprodutibilidade

---

## Épico 3: Gateway de Borda e Segurança Zero-Trust (Kong DB-Less)

Todo tráfego interceptado pelo Kong com TLS, JWKS, Rate Limit default e PriorityClass. Gateway sobrevive 60min sem Keycloak. Dev recebe token no terminal.

**🏁 Marco: Jornada 1 (Dev M2M Local) completamente validável ao final deste épico.**

### Story 3.1: Manifestos Kustomize do Kong DB-Less (Wave 3)

**Complexidade:** Média Complexidade

Como um Engenheiro de Plataforma,
Eu quero o Kong deployado em modo DB-Less via GitOps, interceptando todo tráfego de entrada,
Para que exista ponto único de controle com prioridade máxima.

**Critérios de Aceitação:**

**Dado** Keycloak operacional (Épico 2)
**Quando** ArgoCD sincronizar `cluster/infrastructure/kong-gateway/`
**Então** Kong provisionado com `sync-wave: "3"`, modo DB-Less via ConfigMap, tag imutável `kong:3.14.0.3`
**E** PriorityClass máxima (NFR-R01), NetworkPolicy, healthcheck público (FR24), logs JSON
**E** labels obrigatórios, overlays para 3 ambientes
**E** configuração compatível com os defaults da série 3.14, incluindo `tls_certificate_verify` ativo e ausência de dependência em rotas HTTP implícitas

### Story 3.2: TLS, Validação JWKS e Rate Limit Default

**Complexidade:** Alta Complexidade

Como um Engenheiro de Plataforma,
Eu quero TLS na borda, validação JWKS local e Rate Limit conservador por padrão,
Para que requisições sem token sejam bloqueadas e o Gateway sobreviva a quedas do Keycloak.

**Critérios de Aceitação:**

**Dado** Kong operacional (Story 3.1)
**Quando** requisição HTTP (porta 80) chegar
**Então** Kong rejeita/redireciona para HTTPS (FR11, NFR-S01)

**Dado** requisição HTTPS com JWT válido
**Quando** Kong processar
**Então** validação via cache JWKS (FR12), latência < 20ms (NFR-P01), token repassado intacto no header Bearer (FR13)

**Dado** nenhum Rate Limit explícito configurado
**Quando** requisição chegar
**Então** limite conservador 100 req/min aplicado automaticamente (FR15)

**Dado** TTL do cache JWKS inspecionado
**Quando** verificado
**Então** valor ≥ 60 minutos (NFR-R02)

### Story 3.3: Script de Token e Feedback Estruturado do Terminal

**Complexidade:** Baixa Complexidade

Como um Desenvolvedor,
Eu quero token M2M funcional e resumo de status no terminal após `make up`,
Para que eu teste minha API imediatamente.

**Critérios de Aceitação:**

**Dado** cluster completo (Kong + Keycloak + Postgres)
**Quando** `make up` ou `make token` executado
**Então** `generate-token.sh` solicita token ao Keycloak via `curl` e exibe no terminal (FR04)

**Dado** token gerado
**Quando** `status.sh` executado
**Então** imprime resumo formatado: status componentes, URLs locais, token pronto para copiar

**Dado** token utilizado
**Quando** `curl` sem token → `401 Unauthorized`
**E** `curl` com Bearer → `200 OK` (Jornada 1 — "O Teste Frio")

### Story 3.4: Refinamento do Bootstrap de Emergência

**Complexidade:** Baixa Complexidade

Como um SRE,
Eu quero documentação de recuperação com dados reais da infraestrutura completa,
Para que eu reconstrua a plataforma do zero com comandos verificados.

**Critérios de Aceitação:**

**Dado** `docs/bootstrap-emergencia.md` (esqueleto do Épico 1)
**Quando** atualizado com dados reais
**Então** contém sequência completa com nomes exatos de Secrets, comandos `kubectl` verificados, endpoints de healthcheck reais
**E** documenta recuperação parcial vs. reconstrução total

---

## Épico 4: Boilerplate, Habilitação do Desenvolvedor e Deep Security (DevEx)

Dev deploya APIs de ponta a ponta via Boilerplate padronizado com validação JWT interna via Sidecar oauth2-proxy.

### Story 4.1: Base Kustomize do Boilerplate e CONTRACT.md

**Complexidade:** Média Complexidade

Como um Desenvolvedor,
Eu quero template padronizado com documentação clara das variáveis,
Para que eu instancie uma API sem entender a estrutura interna do Ingress.

**Critérios de Aceitação:**

**Dado** `cluster/boilerplates/api-base-v1/`
**Quando** Base Kustomize criada
**Então** contém `kustomization.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml` (blindado) com anotações Kong (FR05)
**E** dev interage apenas com variáveis no Overlay

**Dado** `CONTRACT.md` no diretório
**Quando** lido
**Então** tabela com colunas `Variável | Obrigatória | Valor Padrão | Descrição`
**E** variáveis mínimas: `app-name`, `hostname`, `paths`, `rate-limit-per-minute` (default conservador), `namespace`

**Dado** templates inspecionados pelo linter
**Quando** validados
**Então** labels obrigatórios, probes, tag imutável, comentários pt-BR presentes

### Story 4.2: Overlays por Ambiente, Rate Limiting e Bypass de Swagger

**Complexidade:** Média Complexidade

Como um Desenvolvedor,
Eu quero configurar minha API para diferentes ambientes com Rate Limit personalizável,
Para que eu tenha controle granular sem comprometer segurança em produção.

**Critérios de Aceitação:**

**Dado** Base Kustomize (Story 4.1)
**Quando** overlays criados
**Então** 3 overlays funcionais: `local/`, `homologacao/`, `production/`

**Dado** dev altera `rate-limit-per-minute` no overlay
**Quando** aplicado
**Então** anotação Kong reflete novo valor (FR14)

**Dado** rota `/swagger` acessada em local/homologação
**Quando** requisição chega ao Kong
**Então** acesso sem token (FR16)

**Dado** rota `/swagger` em produção
**Quando** requisição chega
**Então** `401 Unauthorized` — sem bypass

**Dado** paridade verificada
**Quando** local comparado com production
**Então** topologia idêntica, apenas configurações diferem (FR03 completude)

### Story 4.3: API de Teste e Homologação End-to-End

**Complexidade:** Baixa Complexidade

Como um Engenheiro de Plataforma,
Eu quero deployar API de teste usando o Boilerplate para validar o fluxo completo,
Para que eu confirme que o template funciona antes de abrir para as equipes.

**Critérios de Aceitação:**

**Dado** Boilerplate e overlays (Stories 4.1, 4.2)
**Quando** `cluster/apps/api-teste/` criado consumindo Base via Kustomize
**Então** dev preenche apenas variáveis do CONTRACT.md

**Dado** ArgoCD detecta via glob
**Quando** sincronizar
**Então** API deployada com namespace criado automaticamente, Kong roteando, Rate Limit ativo

**Dado** API operacional
**Quando** Jornada 1 executada
**Então** sem token → `401`, com Bearer → `200 OK`, onboarding < 1 hora

*⚠️ Checkpoint: "Boilerplate funcional — aguardando camada de segurança interna"*

### Story 4.4: Sidecar oauth2-proxy para Deep Security

**Complexidade:** Alta Complexidade

Como um Engenheiro de Plataforma,
Eu quero Sidecar oauth2-proxy em cada pod de API, validando JWT e fazendo introspecção,
Para que a segurança Zero-Trust seja garantida em profundidade.

**Critérios de Aceitação:**

**Dado** API de teste deployada (Story 4.3)
**Quando** Sidecar adicionado à Base Kustomize
**Então** pod com 2 containers (app + oauth2-proxy com tag imutável), fluxo: Kong → Sidecar → App

**Dado** Sidecar interceptando
**Quando** JWT válido chegar
**Então** valida assinatura independentemente do Kong (FR17), extrai claims como headers `X-Auth-Request-*` (FR19)

**Dado** Client revogado no Keycloak (FR08)
**Quando** token revogado chegar
**Então** Sidecar consulta Introspection Endpoint e bloqueia (FR18)

**Dado** Keycloak indisponível
**Quando** introspecção falhar
**Então** Sidecar faz fallback para cache JWKS local

### Story 4.5: Contrato do Desenvolvedor

**Complexidade:** Baixa Complexidade

Como um Desenvolvedor recém-chegado,
Eu quero documentação centralizada sobre como deployar minha API,
Para que eu seja produtivo sem depender de suporte da equipe de Plataforma.

**Critérios de Aceitação:**

**Dado** `docs/contrato-do-desenvolvedor.md` criado
**Quando** lido por novo dev
**Então** contém: visão geral, pré-requisitos, uso do Boilerplate (passo a passo), referência CONTRACT.md, teste local (`make up` → token → curl), deploy via Git
**E** documenta fluxo de segurança completo: TLS (Kong) + JWKS (Kong) + Sidecar oauth2-proxy + Rate Limit
**E** lista anotações/variáveis Kustomize homologadas
**E** inclui procedimento de escape (Boilerplate insuficiente → acionar Plataforma)

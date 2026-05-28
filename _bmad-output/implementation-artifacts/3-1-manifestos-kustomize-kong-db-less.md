---
baseline_commit: c5b6aa0
---

CRITICAL REQUIREMENT [COMPLEXITY]: Voce DEVE definir explicitamente o nivel de complexidade da tarefa nas linhas iniciais de TODA especificacao de historia. NUNCA omita esta classificacao.

# Story 3.1: Manifestos Kustomize do Kong DB-Less (Wave 3)

**Status:** review
**Complexidade:** Média Complexidade

## Story Foundation

**User Story:** Como um Engenheiro de Plataforma, quero o Kong deployado em modo DB-Less via GitOps, interceptando todo trafego de entrada, para que exista ponto unico de controle com prioridade maxima.

**Valor de Negocio:** Esta story abre o marco funcional do Epico 3 e prepara a borda unica pela qual o cluster local passara a expor Keycloak e, depois, as APIs de negocio. Sem ela, as stories 3.2 a 4.5 nao conseguem usar o padrao de Ingress blindado definido na arquitetura.

**Dependencias Confirmadas:**

- O Epico 2 esta concluido no `sprint-status`, portanto PostgreSQL, Keycloak e o endpoint JWKS ja existem no cluster alvo.
- `cluster/infrastructure/kong-gateway/` ja existe com `base/` e `overlays/`, mas a base ainda esta vazia e precisa ser preenchida nesta story.
- O bootstrap local ja desabilita Traefik e expõe `8080:80` e `8443:443` no `k3d.yaml`; o Kong deve encaixar nessa topologia sem mudar o bootstrap.

**Acceptance Criteria:**

- **AC1:** Dado Keycloak operacional, quando o ArgoCD sincronizar `cluster/infrastructure/kong-gateway/`, então o Kong deve ser provisionado na Wave 3 dentro do namespace `kong-gateway`, com imagem pinada em tag imutável `kong:3.14.0.3`, labels obrigatórios e overlays `local`, `homologacao` e `production`.
- **AC2:** Dado o Deployment do Kong em execução, quando o container for inspecionado, então o runtime deve operar em modo DB-less (`database=off`) e consumir configuração declarativa via ConfigMap/GitOps, sem depender de configuração mutável via Admin API ou estado em banco.
- **AC3:** Dado o gateway ativo, quando os manifests forem verificados, então devem existir PriorityClass máxima, NetworkPolicy explícita, healthchecks públicos não autenticados e logs estruturados desde o primeiro deploy.
- **AC4:** Dado o componente renderizado por Kustomize, quando `kubectl kustomize` for executado para os três overlays, então o render deve concluir sem erro e manter a estrutura canônica do projeto.
- **AC5:** Dado o gateway configurado para a série `3.14`, quando a configuração declarativa for revisada, então ela não deve depender de `tls_verify=false` nem de protocolos HTTP implícitos que entrem em conflito com os defaults mais rígidos de `3.14`.

## Tasks / Subtasks

- [x] Preencher a base do Kong em `cluster/infrastructure/kong-gateway/base/` (AC1, AC2, AC3, AC5)
  - [x] Atualizar `kustomization.yaml` para declarar `namespace: kong-gateway` e listar todos os recursos da Wave 3
  - [x] Criar `kong-deployment.yaml`
  - [x] Criar `kong-service.yaml`
  - [x] Criar `kong-configmap.yaml`
  - [x] Criar `kong-priorityclass.yaml`
  - [x] Criar `kong-networkpolicy.yaml`
- [x] Configurar o runtime do Kong para DB-less e observabilidade basica (AC2, AC3, AC5)
  - [x] Fixar a imagem em `kong:3.14.0.3`, alinhada com a LTS ativa adotada pelo repositório
  - [x] Declarar `KONG_DATABASE=off` e montar ConfigMap com a configuração necessária para boot DB-less
  - [x] Habilitar `status_listen` em porta dedicada para probes Kubernetes, usando `/status` e `/status/ready`
  - [x] Garantir logs em `stdout/stderr` com formato estruturado, sem expor o Admin API publicamente
  - [x] Modelar a configuração já compatível com os defaults de `3.14`, sem depender de `tls_verify=false` nem de rotas HTTP implícitas
- [x] Expor o tráfego de borda de forma compatível com a topologia atual do cluster (AC1, AC3)
  - [x] Publicar portas de proxy compatíveis com o balanceador já mapeado em `k3d.yaml`
  - [x] Preservar o papel do Kong como ponto único de entrada, sem mexer em `k3d.yaml` nem reativar Traefik
  - [x] Criar NetworkPolicy minimamente permissiva e compatível com o acesso ao JWKS do Keycloak nas stories seguintes
- [x] Garantir consistência GitOps/Kustomize por ambiente (AC1, AC4)
  - [x] Manter `overlays/local`, `overlays/homologacao` e `overlays/production` apontando para `../../base`, a menos que um patch real de ambiente seja indispensável
  - [x] Validar `kubectl kustomize` para cada overlay antes de encerrar a story
- [x] Registrar rastreabilidade e validação manual no artefato final (AC1, AC2, AC3, AC4)
  - [x] Atualizar a `File List` com todos os arquivos novos e alterados
  - [x] Preencher `Completion Notes List` com a decisão final de deployment adotada
  - [x] Registrar `Autoria/Implementação` em cada manifesto criado

## Dev Notes

### Contexto do Epico

- O Epico 3 prepara a borda Zero-Trust do cluster. Esta story sobe apenas a fundação do gateway.
- TLS estrito, validação JWKS, rate limit default e roteamento funcional pertencem principalmente à Story 3.2. Não puxar esse escopo para dentro da 3.1 sem evidência técnica forte.
- O marco do epico é tornar a Jornada 1 validável ao final do Epico 3; esta story deve preparar a base para isso, não entregar o fluxo completo sozinha.

### Guardrails Arquiteturais Obrigatórios

- O namespace do componente é `kong-gateway`; não criar namespace novo nem mover o gateway para `argocd` ou `keycloak-auth`.
- Todo manifesto de infraestrutura deve ter `argocd.argoproj.io/sync-wave: "3"` e os labels `app.kubernetes.io/name`, `app.kubernetes.io/component=gateway` e `app.kubernetes.io/part-of=cluster-kubernetes`.
- O projeto continua em `Kustomize base/ + overlays/local|homologacao|production`; não introduzir Helm chart, ApplicationSet, Gateway API ou Service Mesh nesta story.
- A fonte de verdade permanece no Git e nos objetos Kubernetes. Não usar Admin API do Kong como caminho principal de configuração nem introduzir banco para o gateway.
- O `infra-app.yaml` já aponta para `cluster/infrastructure` com `prune: false`; esta story não deve alterar `cluster/bootstrap/infra-app.yaml` nem o fluxo do `root-app`.
- A série `3.14` endurece defaults sensíveis: `tls_certificate_verify` vem habilitado por padrão e rotas novas não devem depender de `http` implícito. A implementação precisa assumir esses defaults explicitamente.
- PriorityClass máxima atende o AC, mas não provará "imunidade a eviction" sozinha. O trabalho diferido já registra que PDB/QoS podem ser necessários no futuro; não prometer além disso no texto final da implementação.

### Arquivos Que Precisam Ser Lidos/Preservados

**UPDATE obrigatórios**

- `cluster/infrastructure/kong-gateway/base/kustomization.yaml`
  - **Estado atual:** base vazia com `resources: []`, reservada explicitamente para a Story 3.1.
  - **Esta story muda:** namespace, lista de recursos e organização da Wave 3.
  - **Preservar:** cabeçalho em pt-BR, nome do diretório `kong-gateway` e o papel desta pasta como base compartilhada.

**Arquivos existentes para preservar, mesmo se não mudarem**

- `cluster/infrastructure/kong-gateway/overlays/local/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/homologacao/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/production/kustomization.yaml`
  - **Estado atual:** overlays mínimos apontando para `../../base`.
  - **Preservar:** simplicidade do overlay enquanto não houver necessidade real de patch por ambiente.

- `cluster/infrastructure/kustomization.yaml`
  - **Estado atual:** agrega `namespaces/base`, `keycloak-auth/overlays/local` e `kong-gateway/overlays/local`.
  - **Esta story provavelmente não muda:** a ordem já está correta para o ambiente local.
  - **Preservar:** ordem namespaces -> keycloak -> kong. Só editar se um problema de render ou dependência realmente exigir.

- `cluster/bootstrap/infra-app.yaml`
  - **Estado atual:** ArgoCD lê `cluster/infrastructure` com `prune: false`.
  - **Preservar:** comportamento Safe-Prune e `targetRevision: main`.
  - **Não fazer:** trocar o path, o prune ou a política de sync por causa do Kong.

- `k3d.yaml`
  - **Estado atual:** Traefik desabilitado, `8080:80` e `8443:443` expostos no load balancer.
  - **Preservar:** topologia de portas e o fato de o Kong assumir a borda após a Wave 3.
  - **Não fazer:** adicionar portas novas no host para contornar erro de manifesto do Kong.

- `scripts/cluster-up.sh`
  - **Estado atual:** `make up` cria o cluster, injeta secrets, instala ArgoCD e aplica os Apps monitorando a branch local.
  - **Preservar:** fluxo idempotente atual.
  - **Não fazer:** editar o script para "compensar" falha do Kong sem provar que a origem do problema está no bootstrap.

### Estrutura de Arquivos Esperada

```text
cluster/infrastructure/kong-gateway/
├── base/
│   ├── kustomization.yaml            # UPDATE
│   ├── kong-configmap.yaml           # NEW
│   ├── kong-deployment.yaml          # NEW
│   ├── kong-networkpolicy.yaml       # NEW
│   ├── kong-priorityclass.yaml       # NEW
│   └── kong-service.yaml             # NEW
└── overlays/
    ├── local/kustomization.yaml
    ├── homologacao/kustomization.yaml
    └── production/kustomization.yaml
```

### Padroes de Implementacao Recomendados

- Reutilizar o estilo dos manifests de `cluster/infrastructure/keycloak-auth/base/`: comentarios descritivos em pt-BR, 2 espacos, labels oficiais e `sync-wave` no `metadata.annotations`.
- Se o deployment escolhido incluir Kong Ingress Controller, usar uma topologia suportada e documentar claramente no story diff. Evitar o modelo sidecar tradicional depreciado nas docs atuais do Kong.
- O status listener do Kong precisa ser configurado explicitamente para probes Kubernetes. O default oficial é local-only; sem isso, `readinessProbe` e `livenessProbe` falham.
- Em DB-less, o readiness do Kong depende de config valida carregada. Não concluir a story com um deployment "subindo" mas preso em `NotReady`.
- Não expor a Admin API do Kong publicamente. Se precisar dela para depuração local, restrinja a loopback/cluster-internal e documente a escolha no artefato.
- Esta story nao deve criar regras de negócio, `Ingress` de app, plugin de rate limit, redirect HTTP->HTTPS ou validação JWKS final. Esses comportamentos são da Story 3.2.

### Git Intelligence e Padroes Recentes do Projeto

- Os commits recentes mostram reforço de validação manual, clareza operacional e endurecimento pós-review. A implementação do Kong deve seguir o mesmo padrão: comandos reprodutíveis, sem alegações vagas de "funciona".
- O Epico 2 consolidou o uso de `set -euo pipefail` em scripts e manifests com autoria LLM registrada. A story 3.1 deve manter a mesma rastreabilidade.
- O padrão mais seguro observado nas stories 2.x é preservar o bootstrap existente e concentrar a mudança no diretório do componente. Use isso aqui também.

### Informacoes Tecnicas Atuais Relevantes

- Em **28 de maio de 2026**, o changelog oficial do Kong Gateway lista `3.14.0.3` como a release mais recente, publicada em **25 de maio de 2026**, e a política oficial de suporte mantém `3.14 LTS` como a LTS mais nova da série 3.x.
- A documentação oficial do Kong confirma que DB-less em Kubernetes pode rodar com ou sem Kong Ingress Controller. Quando há controller, o servidor da API do Kubernetes vira a fonte de verdade das configurações do gateway.
- A documentação oficial do Kong indica que o `status_listen` é a API correta para health e métricas não sensíveis. O endpoint `/status/ready` exige `status_listen` habilitado e retorna `200` em DB-less apenas quando existe config válida e não vazia.
- A documentação oficial do KIC mantém `Ingress` suportado e informa que o `ingress class` default do controller é `kong` quando nada é configurado. Isso é relevante para não quebrar as stories futuras que usarão Ingress blindado.
- A documentação oficial de breaking changes do Kong 3.14 registra `tls_certificate_verify=on` por padrão e mudança do default de protocolos de rotas para `https`; a configuração declarativa desta story deve nascer compatível com isso.

## Plano de Validação Manual

**1. Validar lint e render Kustomize antes de subir cluster:**
```bash
make lint

kubectl kustomize cluster/infrastructure/kong-gateway/overlays/local >/tmp/kong-local.yaml
kubectl kustomize cluster/infrastructure/kong-gateway/overlays/homologacao >/tmp/kong-homologacao.yaml
kubectl kustomize cluster/infrastructure/kong-gateway/overlays/production >/tmp/kong-production.yaml
```
**Esperado:** todos os comandos retornam `0`; os arquivos renderizados contêm `Deployment`, `Service`, `ConfigMap`, `PriorityClass` e `NetworkPolicy` do Kong.

**2. Subir o cluster completo via fluxo GitOps padrão:**
```bash
make down
make up
```
**Esperado:** bootstrap concluído sem intervenção manual extra; ArgoCD sobe e o namespace `kong-gateway` passa a ter recursos do Kong.

**3. Verificar recursos básicos do gateway:**
```bash
kubectl get all -n kong-gateway
kubectl get priorityclass kong-critical
kubectl get networkpolicy -n kong-gateway
```
**Esperado:** Deployment/Pod/Service do Kong presentes, `PriorityClass` existente e ao menos uma `NetworkPolicy` aplicada no namespace.

**4. Confirmar variáveis e modo DB-less no pod:**
```bash
kubectl exec -n kong-gateway deploy/kong-deployment -- printenv | grep '^KONG_DATABASE=off$'
kubectl exec -n kong-gateway deploy/kong-deployment -- printenv | grep '^KONG_STATUS_LISTEN='
```
**Esperado:** `KONG_DATABASE=off` visível e `KONG_STATUS_LISTEN` configurado para a porta de health definida na implementação.

**5. Validar liveness/readiness do Kong pela Status API:**
```bash
kubectl port-forward -n kong-gateway deploy/kong-deployment 8100:8100 >/tmp/kong-status.log 2>&1 &
PF_PID=$!
sleep 3

if ! kill -0 "$PF_PID" 2>/dev/null; then
  cat /tmp/kong-status.log
  exit 1
fi

curl -i http://localhost:8100/status
curl -i http://localhost:8100/status/ready

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
```
**Esperado:** ambos os endpoints respondem `HTTP/1.1 200 OK`. Se `/status/ready` retornar `503`, a config DB-less carregada ainda não está válida ou pronta.

**6. Confirmar exposição das portas de borda sem alterar o bootstrap:**
```bash
kubectl get svc -n kong-gateway kong-service -o yaml | grep -E 'port: 80|port: 443'
kubectl get pods -n kong-gateway -l app.kubernetes.io/name=kong -o jsonpath='{.items[0].spec.priorityClassName}'; echo
```
**Esperado:** serviço publica portas de proxy compatíveis com `80`/`443` e o pod usa a `PriorityClass` definida.

**7. Inspecionar logs estruturados:**
```bash
kubectl logs -n kong-gateway deploy/kong-deployment --tail=20
```
**Esperado:** saída em `stdout/stderr` sem erro de boot; o formato deve ser estruturado o suficiente para consumo operacional e não depender de arquivos locais dentro do container.

## References

- `_bmad-output/planning-artifacts/epics.md` - secao `Epico 3 > Story 3.1`
- `_bmad-output/planning-artifacts/architecture.md` - secoes de `Decisoes Arquiteturais Centrais`, `Padroes de Processo`, `Mapeamento de Requisitos para Componentes` e `Estrutura Completa de Diretorios`
- `_bmad-output/project-context.md` - regras criticas de nomenclatura, labels, sync waves, healthchecks e GitOps
- `cluster/infrastructure/kong-gateway/base/kustomization.yaml`
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`
- `cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml`
- `cluster/infrastructure/keycloak-auth/base/postgresql-networkpolicy.yaml`
- `cluster/infrastructure/kustomization.yaml`
- `cluster/bootstrap/infra-app.yaml`
- `scripts/cluster-up.sh`
- `k3d.yaml`
- `docs/runbook-operacoes.md`
- Kong Docs - Version support policy: https://developer.konghq.com/gateway/version-support-policy/
- Kong Docs - Changelog: https://developer.konghq.com/gateway/changelog/
- Kong Docs - DB-less mode: https://developer.konghq.com/gateway/db-less-mode/
- Kong Docs - Breaking changes: https://developer.konghq.com/gateway/breaking-changes/
- Kong Docs - Configuration reference (`status_listen`): https://developer.konghq.com/gateway/configuration/
- Kong Docs - Health check probes: https://developer.konghq.com/gateway/traffic-control/health-check-probes/
- Kong Docs - KIC Ingress and ingress class: https://developer.konghq.com/kubernetes-ingress-controller/ingress/

## Project Context Reference

- **Namespace do componente:** `kong-gateway`
- **Wave esperada:** `3`
- **Diretorio de implementacao:** `cluster/infrastructure/kong-gateway/`
- **Dependencia anterior:** `cluster/infrastructure/keycloak-auth/`
- **Bootstrap local:** `scripts/cluster-up.sh` + `cluster/bootstrap/*.yaml`
- **Portas do host ja reservadas pelo cluster:** `8080 -> 80` e `8443 -> 443`
- **Regra de autoria LLM:** todo arquivo editado deve registrar `Autoria/Implementação: <modelo>`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

Contexto carregado a partir de `SPEC.md`, `implementation-rules.md`, `architecture-status.md`, `_bmad-output/project-context.md`, manifests existentes do `keycloak-auth`, `sprint-status.yaml` e documentacao oficial do Kong para DB-less, `status_listen`, readiness e modo read-only.

### Implementation Plan

- Preencher a base do `kong-gateway` com manifests Wave 3 e manter os overlays apontando para `../../base`.
- Subir o runtime do Kong em modo DB-less com `ConfigMap` declarativo, `status_listen` dedicado e `Admin API` desabilitada.
- Endurecer o container com root filesystem somente leitura, `KONG_PREFIX=/var/run/kong` e volumes efemeros para `prefix` e `/tmp`.
- Validar o componente com `kubectl kustomize` nos tres overlays e com a suite completa do repositório via `make lint`.

### Completion Notes List

- Base `cluster/infrastructure/kong-gateway/base/` preenchida com `kustomization`, `ConfigMap`, `Deployment`, `Service`, `PriorityClass` e `NetworkPolicy`, todos na Wave 3 e com labels obrigatorios.
- Runtime do Kong fixado em `kong:3.14.0.3`, com `KONG_DATABASE=off`, `KONG_DECLARATIVE_CONFIG`, `KONG_STATUS_LISTEN`, `KONG_ADMIN_LISTEN=off` e logs de acesso em JSON via `stdout`.
- Deployment endurecido com `readOnlyRootFilesystem: true`, `KONG_PREFIX=/var/run/kong`, volumes `emptyDir` para `/var/run/kong` e `/tmp`, e probes em `/status` e `/status/ready`.
- Configuracao declarativa inicial mantida compatível com os defaults da serie `3.14`, usando rota `keycloak.local` com `protocols: [http, https]`, sem `tls_verify=false` e sem dependencia de configuracao mutavel via Admin API.
- `kubectl kustomize` validado com sucesso para `overlays/local`, `overlays/homologacao` e `overlays/production`, e a suite `make lint` passou integralmente (Conftest + kube-linter).
- As validacoes de runtime em cluster permanecem descritas no `Plano de Validação Manual` e nao foram executadas neste turno.

### File List

- `_bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` - UPDATE
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kustomization.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-configmap.yaml` - NEW
- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml` - NEW
- `cluster/infrastructure/kong-gateway/base/kong-networkpolicy.yaml` - NEW
- `cluster/infrastructure/kong-gateway/base/kong-priorityclass.yaml` - NEW
- `cluster/infrastructure/kong-gateway/base/kong-service.yaml` - NEW

## Change Log

- `2026-05-28 14:49:31-03:00`: Story criada pelo workflow `bmad-create-story`, com contexto tecnico detalhado para implementacao do Kong DB-Less na Wave 3. Status definido como `ready-for-dev`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-28 15:47:58-03:00`: Implementacao concluida com manifests base do Kong DB-Less, rota declarativa inicial para `keycloak.local`, hardening do container em modo read-only e validacoes `kubectl kustomize` + `make lint`. Status atualizado para `review`. Autoria/Implementação: GPT-5 Codex.

---
Autoria/Implementação: GPT-5 Codex

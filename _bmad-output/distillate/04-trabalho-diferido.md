# Trabalho Diferido — Destilado. Parte 4 de 4.

## Diferido para Story 2.x+ (Infra/Security)

- [inject-secrets.sh:38,50] Fallback de geração de senha com ~64 bits entropia vs 128 bits do openssl; afeta containers Alpine/minimais; harmonizar quando sistema de secrets centralizado (Story 3.4+)
- [keycloak-priorityclass.yaml:13] PriorityClass não garante "imunidade a eviction"; avaliar em hardening futuro se a story deve exigir apenas prioridade alta ou também QoS Guaranteed/PDB/recursos (`requests == limits`)

## Diferido para Cross-Story/Repo

- Makefile sem `.DEFAULT_GOAL` — `make` puro executa `up` acidentalmente; definir `.DEFAULT_GOAL := help`
- Makefile sem alvo `help` para descoberta
- Repo sem `.gitignore` — kubeconfig, logs, artefatos podem ser commitados
- Repo sem `.gitattributes` — clones Windows corrompem shebang `*.sh` com `core.autocrlf=true`
- README sem link para architecture.md na seção Documentação
- Sem ADR formalizando convenção de idiomas (PT-BR docs/comentários + EN nomes técnicos + `homologacao` sem cedilha)

## Diferido para Hardening do Lint (Story futura)

- [policy/kebab-case.rego:9] `kebab_case_pattern` rejeita nomes com ponto — operadores como cert-manager geram recursos com `.` (ex: `cert-manager.io`); causará falsos positivos; adicionar exceções por prefixo/sufixo
- Output vazio de `kustomize build` (exit 0, 0 bytes) indistinguível de stub intencional; guard `total_manifests > 0` mitiga no agregado mas não reporta qual diretório falhou

## Diferido para .tracker/ (Fora do escopo infra)

- Detached HEAD capturado como SHA de branch; sessões cruzando meia-noite; Antigravity change events sem `active_model`; regex `(.*?)\.` trunca modelos com ponto no nome; `re.search` captura apenas primeiro `<USER_SETTINGS_CHANGE>` por linha JSON; `-\d{8}\b` pode comer sufixos numéricos não-data; inconsistência de padrão de guarda de tabelas vazias

## Deferido de: code review de story-3.1 (2026-07-06)

- [kong-deployment.yaml:104-107] `kong-tls-secret` referenciado sem `optional: true`; deploy trava em ContainerCreating se secret ausente e GitOps não consegue self-heal — endurecer no fluxo secrets central
- MetalLB adicionado durante code review anterior sem sub-story formal (justificado só em Change Log); formalizar retroativamente como sub-story ou nota arquitetural em `architecture-status.md`
- [cluster/infrastructure/kustomization.yaml:10-13] Aplica overlays `local` incondicionalmente (metallb + oauth2-proxy + keycloak + kong); quando `infra-app-{env}.yaml` de homologacao/production materializar, migrar para roots separados por ambiente
- [kong-deployment.yaml:44-49] QoS Burstable (requests≠limits) sob PriorityClass `kong-critical=1100000`; kubelet evictar por QoS ignora PriorityClass (só afeta scheduler); considerar `requests==limits` + PDB (similar ao ponto já registrado para keycloak-priorityclass.yaml:13)
- [kong-declarative-config.yaml:19-24] Rate-limit global `policy: local minute:100` amplifica DoS via 404 (requests inexistentes consomem quota); mitigar com response error handlers ou remoção do plugin global se permanecer após review 3.2
- [kong-declarative-config.yaml:44-49] Rota `/.well-known` casa qualquer OIDC well-known do Keycloak, incluindo outros realms — restringir path após hardening 3.2
- [kong-deployment.yaml:39] `readOnlyRootFilesystem: true` com Kong Gateway pode falhar em `mkdir /var/lib/kong` em builds específicas; adicionar monitoring/alerta em CrashLoop com mensagem "read-only file system"
- [kong-deployment.yaml:63-70] `startupProbe` failureThreshold 24 × 5s = 120s pode estourar em cold pull da imagem `kong/kong-gateway:3.14.0.3` (~500MB) em k3d; considerar pre-pull hook via `k3d image import` no bootstrap ou aumentar timeout
- [kong-deployment.yaml:26] `imagePullPolicy: IfNotPresent` sem digest sha256 permite cache poisoning silencioso via `k3d image import` local; adicionar `@sha256:...` para pin criptográfico
- [kong-configmap.yaml] `KONG_HOSTNAME` não definido — Kong usa hostname do pod em `X-Forwarded-Host` de respostas de erro; observabilidade/UX
- [metallb/overlays/local/l2advertisement.yaml] Sem `nodeSelectors`/`interfaces` — em k3d multi-node (server + agent), VIP flappa 30s em restart de node eleito
- [k3d.yaml + kong-service.yaml] k3d-serverlb (portas 80:30080, 443:30443) + MetalLB VIP `172.18.0.200` provocam dois caminhos de acesso (localhost vs IP MetalLB); rotas com `hosts: [localhost, keycloak.local]` retornam 404 no caminho pelo IP MetalLB. Documentar no runbook operacional
- [kong-declarative-config.yaml:19-24] Rate-limit `policy: local` mantém counter por worker; escalar Kong (`replicas>1`) multiplica o limite efetivo; migrar para `redis`/`cluster` ao introduzir HA
- [kong-networkpolicy.yaml:22-29] Ingress NP sem `from:` funciona hoje via SNAT do NodePort do k3d-loadbalancer; qualquer endurecimento futuro com `from: ipBlock` quebra silenciosamente; documentar contrato

## Itens Resolvidos (Implementados)

- ~~Docker fallback sensível ao diretório~~ → implementado com `$(git rev-parse --show-toplevel)`
- ~~Mensagem de erro genérica com diretórios de scan ausentes~~ → implementado com validação explícita de existência
- ~~Instalar conftest nativamente no GitHub Actions~~ → implementado a pedido do dev
- ~~kebab-case.rego colon-check excessivamente amplo~~ → descartado (política real usa lista estrita)

Revisão: GPT-5.5

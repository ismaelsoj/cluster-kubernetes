---
baseline_commit: d7d2d4d
---

CRITICAL REQUIREMENT [COMPLEXITY]: Voce DEVE definir explicitamente o nivel de complexidade da tarefa nas linhas iniciais de TODA especificacao de historia. NUNCA omita esta classificacao.

# Story 3.2: TLS, Validação JWKS e Rate Limit Default

**Status:** in-progress
**Complexidade:** Alta Complexidade

## Story Foundation

**User Story:** Como um Engenheiro de Plataforma, quero TLS na borda, validação JWKS local e Rate Limit conservador por padrão, para que requisições sem token sejam bloqueadas e o Gateway sobreviva a quedas do Keycloak.

**Valor de Negocio:** Esta story transforma a fundação do Kong entregue na Story 3.1 em uma borda segura de fato. Ela fecha os requisitos centrais do Épico 3 para tráfego HTTPS, validação local de tokens emitidos pelo Keycloak, contenção por rate limit e operação resiliente durante indisponibilidade temporária do IdP.

**Dependencias Confirmadas:**

- Story 3.1 concluída e validada em cluster: Kong DB-Less roda em `kong-gateway`, imagem `kong/kong-gateway:3.14.0.3`, `KONG_DATABASE=off`, MetalLB local entrega `EXTERNAL-IP`, `/status/ready` responde `ready` e `make lint` passou.
- Keycloak 26.6.2 já existe em `keycloak-auth`, com realm `cluster-local`, client `m2m-client`, `accessTokenLifespan` de 3600s no realm e service account local configurada.
- O PRD exige solução 100% Open-Source: `Kong DB-Less + OAuth2-Proxy`, sem licenças Enterprise. Não usar plugins Kong `openid-connect` ou `jwt-signer` como caminho feliz.
- `scripts/inject-secrets.sh` já cria namespaces `keycloak-auth` e `kong-gateway`, mas hoje injeta apenas secrets do Keycloak/PostgreSQL. TLS do Kong precisa entrar nesse fluxo sem gravar chave privada no Git.
- O bootstrap local expõe `80` e `443` no load balancer do k3d. Para que `localhost` chegue ao `kong-service` com ServiceLB desabilitado e MetalLB ativo, o caminho local usa NodePorts fixos `30080` e `30443` por baixo, sem criar portas paralelas para o usuário.

**Acceptance Criteria:**

- **AC1:** Dado Kong operacional, quando uma requisição HTTP chegar pela porta 80, então o gateway deve rejeitar ou redirecionar para HTTPS sem encaminhar tráfego inseguro ao upstream.
- **AC2:** Dado requisição HTTPS com JWT válido emitido pelo Keycloak, quando a cadeia de borda processar a chamada, então a validação deve ocorrer por componente Open-Source integrado ao Kong, preferencialmente OAuth2-Proxy com OIDC/JWKS, mantendo latência adicional alvo menor que 20ms e repassando `Authorization: Bearer <token>` intacto ao upstream quando a validação permitir.
- **AC3:** Dado uma requisição sem JWT, com JWT inválido, expirado ou com `iss` incompatível, quando ela atingir rota protegida, então a cadeia Kong + componente OSS de autenticação deve bloquear antes do upstream com resposta não-2xx apropriada.
- **AC4:** Dado nenhum Rate Limit explícito por rota/app, quando uma requisição chegar, então o limite default conservador de `100 req/min` deve ser aplicado automaticamente.
- **AC5:** Dado TTL do cache JWKS inspecionado, quando a configuração do plugin/validador for revisada, então o valor efetivo deve ser `>= 3600s` para sustentar a sobrevivência mínima de 60 minutos sem Keycloak.
- **AC6:** Dado cluster inexistente, quando `make down && make up` executado, então o fluxo completo funciona sem intervenção manual além das entradas já previstas para bootstrap local.

## Tasks / Subtasks

- [ ] Configurar TLS de borda sem segredos no Git (AC1, AC2, AC6)
  - [ ] Atualizar `scripts/inject-secrets.sh` para criar/atualizar Secret TLS `kong-tls-secret` em `kong-gateway`, preferindo valores de `.env` quando existirem e gerando certificado local automaticamente quando ausentes
  - [ ] Corrigir a lógica `--skip-if-exists` para não sair cedo se apenas os secrets do Keycloak existirem; ela deve considerar todos os secrets obrigatórios do bootstrap atual
  - [ ] Montar `kong-tls-secret` no Deployment do Kong como volume read-only, sem expor chave privada em ConfigMap, log, story ou manifesto versionado
  - [ ] Adicionar `KONG_SSL_CERT` e `KONG_SSL_CERT_KEY` em `kong-configmap.yaml` apontando para arquivos montados do Secret
- [ ] Separar rotas/protocolos declarativos do Kong (AC1, AC2, AC3)
  - [ ] Atualizar `kong-declarative-config.yaml` para não manter a rota principal com `protocols: [http, https]` como caminho feliz
  - [ ] Criar comportamento explícito para HTTP na porta 80: rejeição segura ou redirect permanente para HTTPS; aceitar como válido `308/301` com `Location` HTTPS ou rejeição clara como `426 Upgrade Required`
  - [ ] Manter endpoints públicos necessários do Keycloak sem autenticação de borda quando forem indispensáveis para OIDC, como discovery, JWKS e token endpoint
  - [ ] Aplicar validação JWT/JWKS somente às rotas protegidas, evitando bloquear o endpoint usado para obter o próprio token
- [ ] Implementar validação JWKS real, não simulada (AC2, AC3, AC5)
  - [ ] Implementar o caminho gratuito previsto no PRD: Kong DB-Less na borda + OAuth2-Proxy OSS para OIDC/JWKS, sem depender de plugins Enterprise do Kong
  - [ ] Configurar OAuth2-Proxy com provider `keycloak-oidc`, `oidc-issuer-url` do realm `cluster-local` e validação de Bearer tokens quando aplicável ao fluxo M2M
  - [ ] Não usar os plugins Kong `openid-connect` ou `jwt-signer`: a documentação oficial atual marca ambos como `Enterprise only`
  - [ ] Não usar o plugin OSS `jwt` como substituto para JWKS dinâmico do Keycloak se isso exigir duplicar chaves públicas em `jwt_secrets` ou quebrar rotação/cache JWKS
  - [ ] Se OAuth2-Proxy não satisfizer tecnicamente o AC de M2M/JWKS com cache local, interromper e abrir `correct-course`; não mascarar com validação parcial
  - [ ] Alinhar `issuer`, `jwks_uri`/discovery e `iss` real dos tokens do Keycloak; se necessário, ajustar hostname/proxy headers do Keycloak para emitir tokens com issuer externo estável
  - [ ] Garantir que falha temporária do Keycloak não derrube validação de tokens já verificáveis enquanto o cache JWKS válido existir
- [ ] Aplicar Rate Limit default conservador (AC4)
  - [ ] Configurar plugin `rate-limiting` com `minute: 100` e `policy: local` para DB-Less/single-replica local
  - [ ] Documentar no artefato da implementação que `policy: local` é aceitável para o MVP local com 1 réplica, mas não é contador global em múltiplos pods; Redis fica fora do escopo atual
  - [ ] Garantir que o rate limit não bloqueie discovery/JWKS/token de forma que inviabilize validação e geração de token local
- [ ] Preservar compatibilidade com Story 3.1 e bootstrap GitOps (AC1, AC6)
  - [ ] Não reintroduzir Admin API pública nem banco para Kong
  - [ ] Preservar `KONG_NGINX_WORKER_PROCESSES=auto` na base e patch `"1"` apenas no overlay `local`
  - [ ] Preservar MetalLB local e `Service` LoadBalancer com portas 80/443
  - [ ] Manter `sync-wave: "3"`, labels obrigatórios e autoria LLM em todos os artefatos editados
- [ ] Atualizar documentação operacional mínima (AC1, AC2, AC3)
  - [ ] Atualizar `docs/runbook-operacoes.md` para trocar o acesso pós-Kong para HTTPS local em `https://localhost`, incluindo observação sobre certificado local/self-signed quando aplicável
  - [ ] Documentar comandos para validar HTTP bloqueado, HTTPS funcionando, JWT válido aceito, JWT ausente/inválido bloqueado e rate limit retornando `429`
- [ ] Executar validações automatizadas e manuais (AC1-AC6)
  - [ ] Rodar `make lint`
  - [ ] Rodar `kubectl kustomize` para `local`, `homologacao` e `production`
  - [ ] Rodar validação completa `make down && make up`
  - [ ] Validar respostas HTTP/HTTPS/JWT/rate limit em cluster local e registrar resultados no `Dev Agent Record`

### Review Findings

> Code review adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor) executado em 2026-05-29 contra `main` (`d7d2d4d..fc8e440`). Revisão: claude-opus-4-7.

**Decisões necessárias (resolver antes dos patches):**

- [x] [Review][Patch aplicado] AC4 — Rate limit não era default global, só protegia `/protected` — **Aplicado (2026-05-29):** adicionado plugin `rate-limiting` **global** (`minute:100`, `policy:local`) no nível raiz do `kong-declarative-config.yaml` (default automático para toda requisição, fiel ao AC4); override por rota em `/protected` mantido como demonstração do padrão (precedência por rota sobrepõe o global). `make lint` 4806/4806 OPA. Decisão original era opção 2, ampliada para global a pedido do usuário (per-path continua customizável via plugin por rota).
- [ ] [Review][Decision→Validar] AC5 — TTL do cache JWKS >= 3600s não configurado nem comprovado — `oauth2-proxy-configmap.yaml` não declara TTL/refresh de JWKS; o go-oidc renova de forma reativa (por `kid` desconhecido / `Cache-Control` do `/certs`). O passo 11 só provou ~10s, não 60 min. **Resolvido (2026-05-29, party mode): opção 2.** Rotação de chave do realm é **manual no MVP** → `kid` estável → o cache de chave pública em memória valida tokens offline por toda a vida deles (tokens vivem no máximo `accessTokenLifespan=3600s`), o que satisfaz o AC5 pelo mecanismo real (não por um TTL fixo). **AC5 segue NÃO comprovado** até o teste de queda longa (passo 11 revisado) que o Ismael rodará offline. Backlog: evoluir rotação de chave. NÃO abrir correct-course agora.
- [x] [Review][Decision→Resolvido] AC6 — Bootstrap `make down && make up` — **Resolvido (2026-05-29): o usuário confirmou que validou o fluxo completo end-to-end; faltava apenas registrar explicitamente no Dev Agent Record.** Não é mais um achado aberto.
- [ ] [Review][Decision→Backlog] Divergência arquitetural — OAuth2-Proxy é proxy intermediário (`OAUTH2_PROXY_UPSTREAMS`), não validação local/sidecar no gateway. **Resolvido (2026-05-29, party mode): opção (b)** — alvo é migrar para **forward-auth** (Kong consulta o `/auth` do OAuth2-Proxy só para decisão 200/401 e faz o proxy direto ao upstream real), mantendo o Kong como autoridade de borda e tirando o OAuth2-Proxy do caminho de dados. Upstream-proxy atual **aceito como interino** para o MVP (rota de prova = userinfo; sem API de negócio até o Épico 4). Migração registrada em deferred-work com gatilho no Épico 4. Pendências de validação do AC2: medir latência adicional < 20ms e explicar `userinfo=200` com `PASS_AUTHORIZATION_HEADER=false` (investigação registrada).

**Patches (correção objetiva):**

- [x] [Review][Patch aplicado] Pre-flight de portas obsoleto após mudança para 80/443 [scripts/cluster-up.sh:57] — **Aplicado (2026-05-29):** `for port in 8080 8443` → `for port in 80 443`, alinhado ao mapeamento do `k3d.yaml`. `bash -n` OK.

**Deferidos (documentados em deferred-work.md):**

- [x] [Review][Defer] Overlays homologacao/production herdam config local-only e a OPA fixa `https://localhost` globalmente [policy/kong-edge-security.rego:199-231] — deferido, fora de escopo do MVP local
- [x] [Review][Defer] Guardrails OPA por matching de string literal são frágeis/vacuos [policy/kong-edge-security.rego:115,157] — deferido, não bloqueia
- [x] [Review][Defer] `OAUTH2_PROXY_TRUSTED_PROXY_IPS` confia em toda RFC1918 [oauth2-proxy-configmap.yaml:42] — deferido, aceitável no MVP local
- [x] [Review][Defer] Certificado TLS rotaciona a cada `make up` sem reload do Kong [scripts/inject-secrets.sh:187] — deferido, baixo impacto
- [x] [Review][Defer] Flag `INSECURE_OIDC_ALLOW_UNVERIFIED_EMAIL=true` tornado obrigatório pela OPA [policy/kong-edge-security.rego:217] — deferido, defensável para M2M
- [x] [Review][Defer] Requisições por host != localhost/keycloak.local retornam 404 em vez de 426/redirect — deferido, AC1 ainda satisfeito (sem encaminhamento inseguro)
- [x] [Review][Defer] Latência adicional < 20ms (AC2) não medida — deferido, alvo a validar
- [x] [Review][Defer] `client_secret` de dev (`dev-m2m-local-secret`) versionado [realm-config.json] — deferido, pré-existente em `main` (fixture local)

**Dispensados (5):** bloqueio HTTP cobre todos os paths via prefixo `/` (rotas OIDC são HTTPS-only, então HTTP só casa a rota `426`); Authorization Bearer chega ao upstream (userinfo 200 em runtime contradiz a leitura dos flags `PASS_AUTHORIZATION_HEADER`); NetworkPolicy egress 8080 casa a porta do pod pós-DNAT; fallback `random_b64`/`printf %b` de baixíssima probabilidade; `SCOPE openid` irrelevante no fluxo Bearer M2M.

## Dev Notes

### Contexto do Epico

- O Épico 3 entrega a borda Zero-Trust: TLS, JWKS, rate limit default e feedback para o dev obter token.
- Esta story é o ponto de maior risco técnico do épico porque cruza criptografia, proxy reverso, issuer OIDC, plugin Kong e bootstrap de secrets.
- Story 3.3 deve melhorar o script de token e feedback terminal, mas esta story precisa deixar o caminho técnico seguro validável sem depender de configuração manual escondida.

### Guardrails Arquiteturais Obrigatórios

- Kong permanece DB-Less e stateless. Toda configuração de rotas, serviços e plugins deve vir de Git/Kustomize, exceto material sensível injetado como Secret no cluster.
- A solução de autenticação deve permanecer gratuita/Open-Source. O PRD nomeia explicitamente `Kong DB-Less + OAuth2-Proxy`; portanto, plugins Kong `openid-connect`, `jwt-signer` ou outros marcados como Enterprise only estão fora do caminho feliz.
- Zero segredos no Git. Certificado público pode aparecer em logs/comandos se necessário, mas chave privada nunca deve aparecer em manifesto versionado, story, `ConfigMap`, output de validação ou commit.
- A validação JWKS deve ser local/cached na cadeia de borda Open-Source, não introspecção ativa a cada request no Keycloak.
- TTL/cache JWKS deve ficar alinhado com o objetivo de sobrevivência `>= 60 minutos` e com o realm `accessTokenLifespan = 3600`.
- Keycloak é o único emissor de tokens. Não criar emissor alternativo, token assinado pelo Kong ou segredo JWT paralelo para satisfazer teste.
- Todo tráfego externo entra pelo Kong; não contornar a borda com port-forward como prova final de aceite, exceto para depuração.
- Não introduzir Gateway API, Service Mesh, Helm, ApplicationSet, Redis ou Vault nesta story sem decisão explícita posterior.

### Arquivos Que Precisam Ser Lidos/Preservados

**UPDATE obrigatórios**

- `cluster/infrastructure/kong-gateway/base/kong-declarative-config.yaml`
  - **Estado atual:** define `_format_version: "3.0"`, service `keycloak-service` e rota `keycloak-route` com `protocols: [http, https]`.
  - **Esta story muda:** rotas/protocolos, plugins de TLS/JWKS/rate limit e separação entre endpoints públicos OIDC e rotas protegidas.
  - **Preservar:** DB-Less declarativo, upstream interno `keycloak-service.keycloak-auth.svc.cluster.local`, ausência de `tls_verify=false` e autoria.

- `cluster/infrastructure/kong-gateway/base/kong-configmap.yaml`
  - **Estado atual:** env vars runtime do Kong, `KONG_DATABASE=off`, `KONG_DECLARATIVE_CONFIG`, `KONG_ADMIN_LISTEN=off`, `KONG_PROXY_LISTEN` com HTTP/HTTPS e logs JSON.
  - **Esta story muda:** adicionar paths de certificado TLS montado e eventuais env vars indispensáveis para plugin/cache.
  - **Preservar:** Admin API off, logs JSON, `KONG_NGINX_WORKER_PROCESSES=auto` na base e configuração compatível com read-only filesystem.

- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml`
  - **Estado atual:** monta config declarativa, `emptyDir` para prefix/tmp, probes em `8100`, securityContext non-root/read-only e imagem `kong/kong-gateway:3.14.0.3`.
  - **Esta story muda:** montar `kong-tls-secret` read-only e talvez ajustar probes/env/volumes para plugin escolhido.
  - **Preservar:** imagem validada, recursos, probes, read-only filesystem, PriorityClass e sem Admin API pública.

- `cluster/infrastructure/kong-gateway/base/kong-networkpolicy.yaml`
  - **Estado atual:** ingress permite 8000/8443/8100; egress permite DNS e Keycloak pod na porta 8080.
  - **Esta story muda:** só ajustar se o mecanismo JWKS/discovery exigir egress adicional comprovado.
  - **Preservar:** egress mínimo, acesso ao Keycloak e bloqueio implícito de destinos não necessários.

- `scripts/inject-secrets.sh`
  - **Estado atual:** cria namespaces `keycloak-auth` e `kong-gateway`; injeta `keycloak-db-secret` e `keycloak-admin-secret`; `--skip-if-exists` sai se apenas `keycloak-db-secret` existe.
  - **Esta story muda:** gerar/injetar `kong-tls-secret`, persistir variáveis locais seguras em `.env` quando necessário e corrigir skip parcial.
  - **Preservar:** `set -euo pipefail`, uso de `.env`, prompts interativos seguros, `chmod 600`, idempotência via `kubectl apply`.

- `docs/runbook-operacoes.md`
  - **Estado anterior:** orientava acesso pós-Kong via `http://keycloak.local:8080`.
  - **Esta story muda:** documentar HTTPS local em `https://localhost`, teste de certificado local, token/JWKS/rate limit e comportamento esperado em `http://localhost`.
  - **Preservar:** comandos existentes de Keycloak/PostgreSQL que continuam válidos para depuração interna.

**Arquivos existentes para preservar, mesmo se não mudarem**

- `cluster/infrastructure/kong-gateway/base/kong-service.yaml`
  - **Preservar:** `type: LoadBalancer`, portas `80` e `443`, `appProtocol` correto e labels.

- `cluster/infrastructure/kong-gateway/overlays/local/kustomization.yaml`
  - **Preservar:** patch local de `KONG_NGINX_WORKER_PROCESSES: "1"` por OOMKilled no k3d. Se o arquivo for editado, adicionar/atualizar `Autoria/Implementação`.

- `cluster/infrastructure/kong-gateway/overlays/homologacao/kustomization.yaml`
- `cluster/infrastructure/kong-gateway/overlays/production/kustomization.yaml`
  - **Preservar:** overlays simples apontando para `../../base`, salvo necessidade real de TLS/cert/hostname por ambiente.

- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`
  - **Estado atual:** `KC_HTTP_ENABLED=true`, `KC_HOSTNAME_STRICT=false`, `KC_PROXY_HEADERS=xforwarded`.
  - **Possível mudança:** ajustar hostname externo/headers apenas se necessário para corrigir issuer OIDC e discovery via Kong.
  - **Preservar:** Keycloak atrás de edge TLS, HTTP interno na porta 8080, logs JSON e health na porta 9000.

- `cluster/infrastructure/keycloak-auth/base/realm-config.json`
  - **Estado atual:** realm `cluster-local`, `accessTokenLifespan: 3600`, client `m2m-client`.
  - **Preservar:** TTL de 3600s como base do requisito de cache JWKS. Não aumentar o token para mascarar falha de cache.

- `scripts/cluster-up.sh`
  - **Preservar:** chama `inject-secrets.sh` antes do ArgoCD e usa branch local no bootstrap. Editar só se a injeção TLS provar necessidade no fluxo.

### Estrutura de Arquivos Esperada

```text
cluster/infrastructure/kong-gateway/
├── base/
│   ├── kong-configmap.yaml              # UPDATE
│   ├── kong-declarative-config.yaml     # UPDATE
│   ├── kong-deployment.yaml             # UPDATE
│   ├── kong-networkpolicy.yaml          # UPDATE se necessário
│   ├── kong-priorityclass.yaml          # preservar
│   ├── kong-service.yaml                # preservar
│   └── kustomization.yaml               # UPDATE se novos manifests forem criados
└── overlays/
    ├── local/kustomization.yaml         # preservar patch de worker local
    ├── homologacao/kustomization.yaml
    └── production/kustomization.yaml

scripts/
└── inject-secrets.sh                    # UPDATE para kong-tls-secret

docs/
└── runbook-operacoes.md                 # UPDATE validação HTTPS/JWT/rate limit
```

**Possível novo componente OSS se a implementação optar por validação de borda nesta story**

```text
cluster/infrastructure/oauth2-proxy/
├── base/
│   ├── kustomization.yaml
│   ├── oauth2-proxy-configmap.yaml
│   ├── oauth2-proxy-deployment.yaml
│   ├── oauth2-proxy-service.yaml
│   └── oauth2-proxy-networkpolicy.yaml
└── overlays/
    ├── local/kustomization.yaml
    ├── homologacao/kustomization.yaml
    └── production/kustomization.yaml
```

### Padroes de Implementacao Recomendados

- Preferir `kong-tls-secret` criado por `kubectl create secret tls ... --dry-run=client -o yaml | kubectl apply -f -`.
- Para ambiente local, aceitar certificado self-signed gerado automaticamente, desde que a chave fique apenas em `.env`/arquivo local ignorado ou pipe seguro para `kubectl`; se arquivos temporários forem necessários, usar `/tmp` e limpar ao final.
- O teste de HTTPS local pode usar `curl -k` por certificado local self-signed, mas a implementação não deve depender de `tls_verify=false` no Kong.
- Modelar HTTP inseguro como rota separada de rejeição/redirect. Não deixar `protocols: [http, https]` na rota protegida principal.
- Manter `Authorization` intacto. Não trocar Bearer token por header proprietário nesta story.
- Se OAuth2-Proxy for introduzido agora, manter imagem com tag imutável, manifests em `base/ + overlays/local|homologacao|production`, labels obrigatórios, probes e NetworkPolicy explícita.
- Configurar OAuth2-Proxy para Keycloak OIDC usando `provider=keycloak-oidc`, issuer do realm local e validação de tokens Bearer quando aplicável. Validar em documentação/runtime se o cache/JWKS atende o requisito de 60 minutos antes de marcar AC5 como concluído.
- Não adicionar Redis para rate limit nesta story. Como o Deployment atual é `replicas: 1`, `policy: local` atende o MVP; documentar que escala horizontal exige Redis depois.

### Previous Story Intelligence

- A imagem `kong:3.14.0.3` falhou; a imagem validada é `kong/kong-gateway:3.14.0.3`.
- `KONG_NGINX_WORKER_PROCESSES=auto` causou `OOMKilled` no k3d; a correção validada é manter `auto` na base e patch `"1"` apenas no overlay local.
- MetalLB v0.16.0 foi adicionado para resolver `Service LoadBalancer` em `<pending>` no k3d. Não remover ou contornar com NodePort.
- A Story 3.1 separou `kong-configmap.yaml` de `kong-declarative-config.yaml`; preservar essa separação para não voltar a misturar env vars e config DB-Less.
- `make lint` passou após exceções documentadas para CRDs/recursos vendor do MetalLB. Se novos recursos vendor entrarem, aplicar o padrão de patches/justificativas em vez de afrouxar políticas globais.

### Git Intelligence e Padroes Recentes do Projeto

- `d7d2d4d` finalizou e validou a Story 3.1, alterando apenas o artefato de story.
- `ba87866` aplicou code review da Story 3.1 e tocou os manifests reais do Kong/MetalLB; esse commit consolidou a separação de config, PriorityClass e workaround local.
- `262ed19` reforçou o linter após inclusão do MetalLB; novas violações devem ser tratadas por exceção específica e justificada, não por remoção de gates.
- O padrão recente é registrar evidência operacional concreta no `Completion Notes List`, com comandos e resultados, em vez de afirmar genericamente que o cluster funciona.

### Informacoes Tecnicas Atuais Relevantes

- Kong Gateway 3.14 LTS continua sendo a linha ativa adotada pelo projeto; `3.14.0.3` foi mantida como imagem validada na Story 3.1.
- A documentação oficial do Kong informa que os plugins `openid-connect` e `jwt-signer` são Enterprise only. Eles não atendem à restrição de custo/licença do PRD.
- A documentação oficial do Kong informa que o plugin JWT OSS valida JWTs com credenciais de Consumer (`jwt_secrets`) e não substitui automaticamente discovery/JWKS OIDC do Keycloak. Usá-lo duplicando chave pública seria regressão contra rotação JWKS.
- A documentação oficial do Rate Limiting recomenda `local` ou Redis em KIC/DB-Less; `cluster` depende de datastore e não serve para Kong DB-Less. `local` tem impacto baixo, mas contadores divergem com múltiplos pods.
- A documentação oficial do Keycloak 26 recomenda hostname explícito ou proxy headers corretos atrás de TLS edge. Misconfiguração de hostname/headers pode gerar issuer (`iss`) divergente e quebrar validação OIDC.
- A documentação oficial do OAuth2-Proxy possui provider `keycloak-oidc` e opções de validação para Bearer tokens/JWTs; a implementação deve validar essas opções contra o fluxo M2M do projeto antes de considerar JWKS concluído.

## Plano de Validação Manual

**1. Validar render e lint antes do cluster:**

```bash
make lint

kubectl kustomize cluster/infrastructure/kong-gateway/overlays/local >/tmp/kong-local.yaml
kubectl kustomize cluster/infrastructure/kong-gateway/overlays/homologacao >/tmp/kong-homologacao.yaml
kubectl kustomize cluster/infrastructure/kong-gateway/overlays/production >/tmp/kong-production.yaml
```

**Esperado:** comandos retornam `0`; renders contêm TLS mount/env, config declarativa com plugins/rotas esperadas e nenhum Secret com chave privada versionado.

**2. Validar bootstrap completo do zero:**

```bash
make down
make up
```

**Esperado:** fluxo conclui sem intervenção manual extra; `kong-tls-secret`, `oauth2-proxy-secret`, `keycloak-db-secret` e `keycloak-admin-secret` existem nos namespaces corretos; ArgoCD sincroniza infraestrutura.

**3. Verificar TLS secret e montagem no Kong sem imprimir chave privada:**

```bash
kubectl get secret kong-tls-secret -n kong-gateway -o jsonpath='{.type}'; echo
kubectl get pod -n kong-gateway -l app.kubernetes.io/name=kong -o jsonpath='{.items[0].spec.volumes[*].name}'; echo
kubectl exec -n kong-gateway deploy/kong-deployment -- test -r /etc/kong/tls/tls.crt
kubectl exec -n kong-gateway deploy/kong-deployment -- test -r /etc/kong/tls/tls.key
```

**Esperado:** tipo `kubernetes.io/tls`; volume TLS presente; arquivos legíveis pelo container; nenhum comando imprime `tls.key`.

**4. Validar exposição localhost para o Kong:**

```bash
kubectl get svc kong-service -n kong-gateway \
  -o jsonpath='{range .spec.ports[*]}{.name}{"="}{.nodePort}{"\n"}{end}'
```

**Esperado:** `proxy-http=30080` e `proxy-https=30443`, alinhados aos mapeamentos `80:30080` e `443:30443` do `k3d.yaml`.

**5. Validar HTTP inseguro bloqueado ou redirecionado:**

```bash
curl -i http://localhost/
```

**Esperado:** resposta não encaminha conteúdo normal do Keycloak por HTTP. Aceitável: `301/308` para HTTPS ou `426/403` explícito.

**6. Validar HTTPS na borda:**

```bash
curl -k -i https://localhost/realms/cluster-local/.well-known/openid-configuration
```

**Esperado:** `HTTP/2 200` ou `HTTP/1.1 200`; discovery OIDC responde via Kong HTTPS; issuer/discovery são coerentes com a configuração de validação.

**7. Obter token M2M pelo caminho compatível com issuer esperado:**

```bash
TOKEN="$(
  curl -ksf -X POST https://localhost/realms/cluster-local/protocol/openid-connect/token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'grant_type=client_credentials' \
    -d 'client_id=m2m-client' \
    -d 'client_secret=dev-m2m-local-secret' \
    --data-urlencode 'scope=openid profile email' \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

python3 - <<'PY' "$TOKEN"
import base64, json, sys
payload = sys.argv[1].split('.')[1] + '=='
claims = json.loads(base64.urlsafe_b64decode(payload))
print("iss=" + claims["iss"])
print("scope=" + claims.get("scope", ""))
PY
```

**Esperado:** token gerado; `iss` impresso bate com issuer aceito pelo plugin JWKS/OIDC do Kong; `scope` contém `openid`.

**8. Validar OAuth2-Proxy antes da rota protegida:**

```bash
kubectl rollout status deployment/oauth2-proxy-deployment \
  -n kong-gateway \
  --timeout=180s

kubectl get endpoints oauth2-proxy-service -n kong-gateway

kubectl logs -n kong-gateway deploy/oauth2-proxy-deployment --tail=50
```

**Esperado:** rollout concluído, endpoint do Service preenchido na porta `4180` e logs sem `invalid configuration` ou erro de `cookie_secret`.

```bash
kubectl port-forward svc/oauth2-proxy-service -n kong-gateway 4180:4180 \
  >/tmp/oauth2-proxy-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

curl -sf http://localhost:4180/ping
curl -sf http://localhost:4180/ready

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
```

**Esperado:** `/ping` e `/ready` retornam sucesso HTTP.

**9. Validar rota protegida com e sem token:**

A rota protegida de prova é o `userinfo` do Keycloak atrás do prefixo `/protected` do Kong:

```bash
curl -k -i https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo

curl -k -i https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer ${TOKEN}"
```

**Esperado:** sem token retorna `401/403` do Kong antes do upstream; com token válido não é bloqueado pelo Kong e preserva `Authorization: Bearer`.

**10. Validar rate limit default:**

```bash
for i in $(seq 1 105); do
  curl -ks -o /tmp/kong-rl-body.txt -w "%{http_code}\n" \
    https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo \
    -H "Authorization: Bearer ${TOKEN}"
done | tail -10
```

**Esperado:** após aproximadamente 100 requests na janela de 1 minuto, alguma resposta retorna `429 Too Many Requests` e headers de rate limit aparecem quando suportados pelo plugin.

**11. Validar sobrevivência do cache JWKS (teste de queda longa — rodar offline):**

Use `/oauth2/auth` para esta prova. A rota `/protected/.../userinfo` depende do Keycloak como upstream e retorna `502 Bad Gateway` quando o Keycloak está em `replicas=0`, mesmo com a validação JWT/JWKS já tendo passado.

> **Nota de método (code review 2026-05-29):** o teste anterior só derrubava o Keycloak por `sleep 10` (10s), o que não prova os 60 min do AC5. Com rotação de chave **manual** (MVP), o `kid` é estável e o cache de chave pública do go-oidc valida tokens offline por toda a vida deles. Como `accessTokenLifespan=3600s`, um token vive no máximo 60 min — então o `exp` do token e a janela do AC5 coincidem. Por isso o teste valida que um token emitido ANTES da queda continua sendo validado offline, sem round-trip ao Keycloak, por toda a sua validade. Aos ~3600s o `401` passa a ser do `exp` do token (não do cache) — isso é esperado, não falha de cache.

**11a. Capturar o input que decide o TTL (header `Cache-Control` do `/certs`):**

```bash
curl -k -sI https://localhost/realms/cluster-local/protocol/openid-connect/certs | grep -i '^cache-control'
```

**Esperado:** registrar o `max-age` retornado pelo Keycloak 26. Não bloqueia o AC (a sobrevivência vem do `kid` estável + cache em memória), mas documenta o comportamento real.

**11b. Teste de sobrevivência com token pré-emitido (loop ~55 min):**

```bash
# TOKEN deve ter sido obtido no passo 7 e estar fresco (exp ~3600s à frente).
curl -k -i https://localhost/oauth2/auth -H "Authorization: Bearer ${TOKEN}"   # popula o cache → 202

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=0

for minute in 1 15 30 45 55; do
  sleep 60 # repetir até atingir cada marco; ajuste conforme preferir (cron/at)
  code="$(curl -k -s -o /dev/null -w '%{http_code}' \
    https://localhost/oauth2/auth -H "Authorization: Bearer ${TOKEN}")"
  echo "t+? min (marco ${minute}): HTTP ${code}"
done

# Opcional: confirmar que NÃO houve refetch de JWKS durante a queda
kubectl logs -n kong-gateway deploy/oauth2-proxy-deployment --since=60m | grep -i 'jwks\|keys\|fetch' || echo "sem refetch de JWKS nos logs"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=1
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth
```

**Esperado:** com o Keycloak em `replicas=0`, todas as chamadas de `/oauth2/auth` com o mesmo token (dentro do `exp`) retornam `202 Accepted` com `gap-auth: service-account-m2m-client`, e os logs do OAuth2-Proxy NÃO registram refetch de JWKS durante a janela. Isso prova validação offline pelo cache em memória. AC5 só vira `done` após este teste passar.

## References

- `_bmad-output/distillate-v2/SPEC.md` - porta obrigatória e limites do repositório.
- `_bmad-output/distillate-v2/implementation-rules.md` - labels, sync waves, YAML, lint, vendor patches e GitOps.
- `_bmad-output/distillate-v2/architecture-status.md` - Kong DB-Less 3.14 LTS, JWKS local, TLS e NFRs.
- `_bmad-output/distillate-v2/planning.md` - Story 3.2 como próximo item do Épico 3.
- `_bmad-output/distillate-v2/deferred-work.md` - riscos diferidos próximos ao bootstrap e resiliência.
- `_bmad-output/project-context.md` - regras persistentes de stack, secrets, autoria e isolamento.
- `_bmad-output/planning-artifacts/prd.md` - requisito de custo/licença: `Kong DB-Less + OAuth2-Proxy`, 100% Open-Source.
- `_bmad-output/planning-artifacts/epics.md` - seção `Épico 3 > Story 3.2`.
- `_bmad-output/planning-artifacts/architecture.md` - ADRs de Gateway DB-Less, JWKS local, TLS, rate limit e limites de tráfego.
- `_bmad-output/implementation-artifacts/3-1-manifestos-kustomize-kong-db-less.md` - aprendizados e estado validado da story anterior.
- `cluster/infrastructure/kong-gateway/base/kong-declarative-config.yaml`
- `cluster/infrastructure/kong-gateway/base/kong-configmap.yaml`
- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml`
- `cluster/infrastructure/kong-gateway/base/kong-networkpolicy.yaml`
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`
- `cluster/infrastructure/keycloak-auth/base/realm-config.json`
- `scripts/inject-secrets.sh`
- `scripts/cluster-up.sh`
- `docs/runbook-operacoes.md`
- Kong Docs - OpenID Connect plugin: https://developer.konghq.com/plugins/openid-connect/
- Kong Docs - JWT plugin: https://developer.konghq.com/plugins/jwt/
- Kong Docs - JWT Signer plugin: https://developer.konghq.com/plugins/jwt-signer/
- Kong Docs - Rate Limiting plugin: https://developer.konghq.com/plugins/rate-limiting/
- Kong Docs - KIC Rate Limiting: https://developer.konghq.com/kubernetes-ingress-controller/get-started/rate-limiting/
- Kong Docs - Version support policy: https://developer.konghq.com/gateway/version-support-policy/
- OAuth2-Proxy Docs - Keycloak OIDC provider: https://oauth2-proxy.github.io/oauth2-proxy/configuration/providers/keycloak_oidc/
- OAuth2-Proxy Docs - configuration overview: https://oauth2-proxy.github.io/oauth2-proxy/7.5.x/configuration/overview/
- Keycloak Docs - Configuring the hostname v2: https://www.keycloak.org/server/hostname
- Keycloak Docs - Reverse proxy: https://www.keycloak.org/server/reverseproxy

## Project Context Reference

- **Namespace do gateway:** `kong-gateway`
- **Namespace do IdP:** `keycloak-auth`
- **Wave esperada do Kong:** `3`
- **Imagem validada do Kong:** `kong/kong-gateway:3.14.0.3`
- **Realm local:** `cluster-local`
- **Client M2M local:** `m2m-client`
- **TTL token/JWKS alvo:** `3600s`
- **Portas host k3d:** `80 -> 30080 -> Kong HTTP`, `443 -> 30443 -> Kong HTTPS`
- **Regra de autoria LLM:** todo arquivo editado deve registrar `Autoria/Implementação: <modelo>`

## Questões e Riscos Salvos para o Dev Agent

- **Plugin/licença Kong:** não usar `openid-connect` nem `jwt-signer` do Kong no caminho feliz; ambos são Enterprise only na documentação oficial atual. A solução gratuita planejada é `Kong DB-Less + OAuth2-Proxy`.
- **Issuer Keycloak:** validar o `iss` real emitido quando o token é obtido via Kong HTTPS. Divergência de issuer é bug de configuração, não detalhe cosmético.
- **Rota protegida para teste:** como ainda não existe API de negócio do Épico 4, a implementação deve definir explicitamente qual rota protegida será usada para provar validação JWT sem bloquear endpoints públicos necessários do Keycloak.
- **TLS local:** cert-manager não é obrigatório para HTTPS local; `kong-tls-secret` pode ser criado diretamente via `kubectl create secret tls` a partir de certificado self-signed gerado no bootstrap.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

Contexto carregado a partir de `SPEC.md`, companions `implementation-rules.md`, `architecture-status.md`, `planning.md`, `deferred-work.md`, `project-context.md`, sprint status, story 3.1, manifests atuais do Kong/Keycloak, scripts de bootstrap e documentação oficial Kong/Keycloak para OIDC/JWKS, rate limiting, TLS/hostname e reverse proxy.

- `make lint` falhou no RED com a nova política `policy/kong-edge-security.rego`, validando ausência inicial de TLS mount/env, rota HTTP bloqueada, rota protegida, OAuth2-Proxy e rate limit default.
- `make lint` passou no GREEN com 3382/3382 checks OPA e 0 erros no kube-linter após implementação.
- `kubectl kustomize` passou para `kong-gateway`, `oauth2-proxy` e `keycloak-auth` nos overlays `local`, `homologacao` e `production`.
- `make down` e `make up` executaram com sucesso; bootstrap criou `kong-tls-secret` e `oauth2-proxy-secret` em `kong-gateway`.
- Validação runtime HTTP/HTTPS/JWT/rate limit bloqueada no ArgoCD: `targetRevision: story/3-2-context` não existe no remoto, então `root-app`/`infra-app` ficaram `Unknown` com erro `unable to resolve 'story/3-2-context' to a commit SHA`.
- Investigação runtime posterior confirmou que `localhost:8080/8443` não chegava ao Kong porque o `serverlb` do k3d encaminhava para portas de nó `80/443`, enquanto o `kong-service` estava exposto via MetalLB. Correção inicial aplicada com NodePorts fixos `30080/30443`; ajuste posterior mudou o caminho feliz para portas padrão do host `80/443`.
- OAuth2-Proxy validado após correção do `cookie_secret`: `rollout status` concluído, endpoint `oauth2-proxy-service` preenchido na porta `4180`, logs sem erro de `cookie_secret`, `/ping` e `/ready` retornando `HTTP 200`.
- Ajuste para portas padrão validado estaticamente: `bash -n scripts/inject-secrets.sh` passou; `kubectl kustomize` passou para `kong-gateway`, `oauth2-proxy` e `keycloak-auth` nos overlays `local`, `homologacao` e `production`; `make lint` passou com 4450/4450 checks OPA e 0 erros kube-linter.
- Falha runtime do passo 9 investigada: OAuth2-Proxy retornava `403` com log `email in id_token () isn't verified` para token M2M. Correção aplicada para usar `preferred_username` como claim de identidade e permitir email não verificado no fluxo M2M, mantendo validação por issuer/audience/assinatura. `kubectl kustomize` passou para os overlays do OAuth2-Proxy e `make lint` passou com 4806/4806 checks OPA e 0 erros kube-linter.
- Segundo `403` do passo 9 validado como resposta do `userinfo` por escopo ausente: token antigo tinha `scope=email profile`; comando corrigido com `scope=openid profile email` gerou token com `scope=openid email profile` e `curl` na rota protegida retornou `HTTP 200`.
- Retorno `502` do passo 11 diagnosticado como teste incorreto: `/protected/.../userinfo` valida o token, mas depois precisa do upstream Keycloak. Com Keycloak em `replicas=0`, o probe correto de cache JWKS é `/oauth2/auth`, que retornou `HTTP 202` antes da queda e `HTTP 202` durante a queda; Keycloak voltou com rollout concluído.

### Completion Notes List

- Implementado bootstrap idempotente de `kong-tls-secret` e `oauth2-proxy-secret` em `scripts/inject-secrets.sh`, incluindo correção de `--skip-if-exists` para considerar todos os secrets obrigatórios atuais.
- Kong configurado com certificado TLS montado via Secret, `KONG_SSL_CERT`/`KONG_SSL_CERT_KEY`, rota HTTP explícita com `426`, rotas OIDC públicas somente HTTPS, rota protegida `/protected` via OAuth2-Proxy e plugin `rate-limiting` com `minute: 100` e `policy: local`.
- Adicionado componente `cluster/infrastructure/oauth2-proxy/` com base e overlays `local`, `homologacao` e `production`, usando imagem oficial `quay.io/oauth2-proxy/oauth2-proxy:v7.15.2`, probes, NetworkPolicy e segredos via `oauth2-proxy-secret`.
- Keycloak ajustado para issuer HTTPS local estável (`https://localhost`) e client M2M alinhado ao TTL de 3600s com audience `m2m-client`.
- Runbook atualizado com comandos de validação para HTTP bloqueado, HTTPS, token M2M, rota protegida, rate limit e cache JWKS.
- Exposição local ajustada para os comandos de aceite em `localhost` e `localhost:443`: `k3d.yaml` encaminha host `80/443` para NodePorts fixos e `kong-service` declara `nodePort: 30080/30443`.
- Guardrails OPA atualizados para proteger `localhost` como host local principal, issuer externo `https://localhost` no Keycloak/OAuth2-Proxy e redirect `https://localhost/oauth2/callback`.
- Geração do `cookie_secret` do OAuth2-Proxy corrigida para produzir segredo literal de 32 bytes aceito pelo proxy; `--skip-if-exists` agora deixa de pular quando o Secret existente tem cookie inválido.
- OAuth2-Proxy ajustado para tokens M2M de service account: `OAUTH2_PROXY_OIDC_EMAIL_CLAIM=preferred_username` e `OAUTH2_PROXY_INSECURE_OIDC_ALLOW_UNVERIFIED_EMAIL=true`.
- Story permanece `in-progress` até autorização explícita para publicar commit/push ou outro caminho GitOps que permita o ArgoCD sincronizar os manifests e validar `localhost` com a topologia nova após recriação do cluster.

### File List

- `_bmad-output/implementation-artifacts/3-2-tls-validacao-jwks-rate-limit-default.md` - NEW
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - UPDATE
- `_bmad-output/implementation-artifacts/investigations/investigacao-kong-localhost-tls-resposta-vazia.md` - NEW
- `_bmad-output/implementation-artifacts/investigations/oauth2-proxy-userinfo-403-investigation.md` - NEW
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` - UPDATE
- `cluster/infrastructure/keycloak-auth/base/realm-config.json` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-configmap.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-declarative-config.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-networkpolicy.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-service.yaml` - UPDATE
- `cluster/infrastructure/kustomization.yaml` - UPDATE
- `cluster/infrastructure/oauth2-proxy/base/kustomization.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-configmap.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-deployment.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-service.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-networkpolicy.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/overlays/local/kustomization.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/overlays/homologacao/kustomization.yaml` - NEW
- `cluster/infrastructure/oauth2-proxy/overlays/production/kustomization.yaml` - NEW
- `docs/runbook-operacoes.md` - UPDATE
- `k3d.yaml` - UPDATE
- `policy/kong-edge-security.rego` - NEW
- `scripts/inject-secrets.sh` - UPDATE

## Change Log

- `2026-05-29 00:17:06-03:00`: Story criada pelo workflow `bmad-create-story`, com contexto técnico detalhado para TLS de borda, validação JWKS/cache, rate limit default e bootstrap de secrets. Status definido como `ready-for-dev`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 00:41:26-03:00`: Correção pós-validação de licenciamento: story alinhada ao PRD 100% Open-Source (`Kong DB-Less + OAuth2-Proxy`), removendo plugins Kong `openid-connect`/`jwt-signer` Enterprise do caminho feliz; adicionada nota de que cert-manager não é obrigatório para TLS local. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 01:01:44-03:00`: Implementação em andamento: TLS de borda, OAuth2-Proxy OSS, validação JWKS via `oidc-jwks-url`, rate limit default, política OPA de borda e runbook operacional adicionados. Validações estáticas passaram; validação runtime aguarda publicação da branch `story/3-2-context` para o ArgoCD sincronizar via GitOps. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 08:23:00-03:00`: Correções pós-investigação: `localhost:8080/8443` ajustado para alcançar Kong via NodePorts fixos `30080/30443`; geração e validação do `cookie_secret` do OAuth2-Proxy corrigidas; plano manual e runbook passaram a validar explicitamente OAuth2-Proxy (`rollout`, endpoints, logs, `/ping` e `/ready`). `make lint` passou 3738/3738 OPA + 0 kube-linter; OAuth2-Proxy validado em cluster após reinjeção do Secret. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 08:41:09-03:00`: Ajuste solicitado para usar `localhost` nas portas padrão: `k3d.yaml` mapeia `80:30080` e `443:30443`, Kong aceita `localhost` e `keycloak.local`, Keycloak/OAuth2-Proxy usam issuer externo `https://localhost`, e runbook/plano manual passaram a validar `http://localhost` e `https://localhost`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 08:57:11-03:00`: Plano manual corrigido para substituir placeholders de rota pela rota protegida concreta `https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 09:04:02-03:00`: Correção do `403` no passo 9: OAuth2-Proxy passou a usar `preferred_username` como claim de identidade e permitir email não verificado no fluxo M2M de service account; investigação registrada em `investigations/oauth2-proxy-userinfo-403-investigation.md`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 09:16:47-03:00`: Correção do segundo `403` do passo 9: o `userinfo` do Keycloak retornava `insufficient_scope` porque o token M2M era emitido com `scope=email profile`; comando de obtenção do token passou a solicitar `scope=openid profile email` e a imprimir o scope para validação explícita. Validação runtime com token novo retornou `HTTP 200` na rota protegida. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 09:23:05-03:00`: Correção do passo 11: teste de sobrevivência do cache JWKS deixou de usar `/protected/.../userinfo`, pois essa rota depende do Keycloak como upstream e retorna `502` quando o Keycloak está parado; o probe correto passou a ser `/oauth2/auth`, esperado `202 Accepted` com `gap-auth`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 09:24:35-03:00`: Validação runtime do passo 11 corrigido: `/oauth2/auth` retornou `202` antes da queda e `202` com Keycloak em `replicas=0`; Keycloak restaurado para `replicas=1` com rollout concluído. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 10:54:18-03:00`: Code review adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor) executado contra `main` (`d7d2d4d..fc8e440`). 4 decision-needed, 1 patch, 8 defer, 5 dispensados. **Decisões:** D1 (AC4) → patch aplicado como plugin `rate-limiting` global + override por rota; D2 (AC5) → opção 2 (party mode): rotação de chave manual sustenta o cache offline, mas AC5 segue não comprovado até teste de queda longa (passo 11 revisado, rodado offline pelo usuário); D3 (AC6) → resolvido (usuário confirmou validação end-to-end); D4 (topologia) → opção (b) party mode: migrar para forward-auth registrado em deferred-work, upstream-proxy atual aceito como interino. **Patches aplicados:** rate-limiting global em `kong-declarative-config.yaml` e correção do pre-flight de portas (`80/443`) em `cluster-up.sh`. `make lint` 4806/4806 OPA + 0 kube-linter. Pendências para `done`: validar AC5 (teste offline 61 min), medir latência AC2 < 20ms e explicar passthrough do `Authorization` (userinfo=200 com `PASS_AUTHORIZATION_HEADER=false`). Story permanece `in-progress`. Revisão: claude-opus-4-7.

---
Autoria/Implementação: GPT-5 Codex
Revisão: claude-opus-4-7

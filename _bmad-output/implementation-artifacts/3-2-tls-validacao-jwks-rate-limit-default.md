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
- O bootstrap local expõe `8080 -> 80` e `8443 -> 443` no load balancer do k3d. A story deve usar essa topologia, não criar portas paralelas.

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
  - [ ] Atualizar `docs/runbook-operacoes.md` para trocar o acesso pós-Kong de `http://keycloak.local:8080` para HTTPS local em `https://keycloak.local:8443`, incluindo observação sobre certificado local/self-signed quando aplicável
  - [ ] Documentar comandos para validar HTTP bloqueado, HTTPS funcionando, JWT válido aceito, JWT ausente/inválido bloqueado e rate limit retornando `429`
- [ ] Executar validações automatizadas e manuais (AC1-AC6)
  - [ ] Rodar `make lint`
  - [ ] Rodar `kubectl kustomize` para `local`, `homologacao` e `production`
  - [ ] Rodar validação completa `make down && make up`
  - [ ] Validar respostas HTTP/HTTPS/JWT/rate limit em cluster local e registrar resultados no `Dev Agent Record`

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
  - **Estado atual:** orienta acesso pós-Kong via `http://keycloak.local:8080`.
  - **Esta story muda:** documentar HTTPS na porta `8443`, teste de certificado local, token/JWKS/rate limit e comportamento esperado na porta 8080.
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

**Esperado:** fluxo conclui sem intervenção manual extra; `kong-tls-secret`, `keycloak-db-secret` e `keycloak-admin-secret` existem nos namespaces corretos; ArgoCD sincroniza infraestrutura.

**3. Verificar TLS secret e montagem no Kong sem imprimir chave privada:**

```bash
kubectl get secret kong-tls-secret -n kong-gateway -o jsonpath='{.type}'; echo
kubectl get pod -n kong-gateway -l app.kubernetes.io/name=kong -o jsonpath='{.items[0].spec.volumes[*].name}'; echo
kubectl exec -n kong-gateway deploy/kong-deployment -- test -r /etc/kong/tls/tls.crt
kubectl exec -n kong-gateway deploy/kong-deployment -- test -r /etc/kong/tls/tls.key
```

**Esperado:** tipo `kubernetes.io/tls`; volume TLS presente; arquivos legíveis pelo container; nenhum comando imprime `tls.key`.

**4. Validar HTTP inseguro bloqueado ou redirecionado:**

```bash
curl -i -H 'Host: keycloak.local' http://localhost:8080/
```

**Esperado:** resposta não encaminha conteúdo normal do Keycloak por HTTP. Aceitável: `301/308` para HTTPS ou `426/403` explícito.

**5. Validar HTTPS na borda:**

```bash
curl -k -i -H 'Host: keycloak.local' https://localhost:8443/realms/cluster-local/.well-known/openid-configuration
```

**Esperado:** `HTTP/2 200` ou `HTTP/1.1 200`; discovery OIDC responde via Kong HTTPS; issuer/discovery são coerentes com a configuração de validação.

**6. Obter token M2M pelo caminho compatível com issuer esperado:**

```bash
TOKEN="$(
  curl -ksf -X POST https://keycloak.local:8443/realms/cluster-local/protocol/openid-connect/token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret' \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

python3 - <<'PY' "$TOKEN"
import base64, json, sys
payload = sys.argv[1].split('.')[1] + '=='
print(json.loads(base64.urlsafe_b64decode(payload))["iss"])
PY
```

**Esperado:** token gerado; `iss` impresso bate com issuer aceito pelo plugin JWKS/OIDC do Kong.

**7. Validar rota protegida com e sem token:**

```bash
curl -k -i https://keycloak.local:8443/<rota-protegida-definida-na-implementacao>

curl -k -i https://keycloak.local:8443/<rota-protegida-definida-na-implementacao> \
  -H "Authorization: Bearer ${TOKEN}"
```

**Esperado:** sem token retorna `401/403` do Kong antes do upstream; com token válido não é bloqueado pelo Kong e preserva `Authorization: Bearer`.

**8. Validar rate limit default:**

```bash
for i in $(seq 1 105); do
  curl -ks -o /tmp/kong-rl-body.txt -w "%{http_code}\n" \
    https://keycloak.local:8443/<rota-com-rate-limit-definida-na-implementacao> \
    -H "Authorization: Bearer ${TOKEN}"
done | tail -10
```

**Esperado:** após aproximadamente 100 requests na janela de 1 minuto, alguma resposta retorna `429 Too Many Requests` e headers de rate limit aparecem quando suportados pelo plugin.

**9. Validar sobrevivência do cache JWKS:**

```bash
kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=0
sleep 10

curl -k -i https://keycloak.local:8443/<rota-protegida-definida-na-implementacao> \
  -H "Authorization: Bearer ${TOKEN}"

kubectl scale deployment/keycloak-deployment -n keycloak-auth --replicas=1
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth
```

**Esperado:** token previamente validável continua aceito enquanto cache JWKS estiver válido; Keycloak volta a `Ready` ao final.

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
- **Portas host k3d:** `8080 -> 80`, `8443 -> 443`
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

### Completion Notes List

- Implementado bootstrap idempotente de `kong-tls-secret` e `oauth2-proxy-secret` em `scripts/inject-secrets.sh`, incluindo correção de `--skip-if-exists` para considerar todos os secrets obrigatórios atuais.
- Kong configurado com certificado TLS montado via Secret, `KONG_SSL_CERT`/`KONG_SSL_CERT_KEY`, rota HTTP explícita com `426`, rotas OIDC públicas somente HTTPS, rota protegida `/protected` via OAuth2-Proxy e plugin `rate-limiting` com `minute: 100` e `policy: local`.
- Adicionado componente `cluster/infrastructure/oauth2-proxy/` com base e overlays `local`, `homologacao` e `production`, usando imagem oficial `quay.io/oauth2-proxy/oauth2-proxy:v7.15.2`, probes, NetworkPolicy e segredos via `oauth2-proxy-secret`.
- Keycloak ajustado para issuer HTTPS local estável (`https://keycloak.local:8443`) e client M2M alinhado ao TTL de 3600s com audience `m2m-client`.
- Runbook atualizado com comandos de validação para HTTP bloqueado, HTTPS, token M2M, rota protegida, rate limit e cache JWKS.
- Story permanece `in-progress` até autorização explícita para publicar a branch/commit ou outro caminho GitOps que permita o ArgoCD sincronizar os manifests para validação runtime.

### File List

- `_bmad-output/implementation-artifacts/3-2-tls-validacao-jwks-rate-limit-default.md` - NEW
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - UPDATE
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` - UPDATE
- `cluster/infrastructure/keycloak-auth/base/realm-config.json` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-configmap.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-declarative-config.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml` - UPDATE
- `cluster/infrastructure/kong-gateway/base/kong-networkpolicy.yaml` - UPDATE
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
- `policy/kong-edge-security.rego` - NEW
- `scripts/inject-secrets.sh` - UPDATE

## Change Log

- `2026-05-29 00:17:06-03:00`: Story criada pelo workflow `bmad-create-story`, com contexto técnico detalhado para TLS de borda, validação JWKS/cache, rate limit default e bootstrap de secrets. Status definido como `ready-for-dev`. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 00:41:26-03:00`: Correção pós-validação de licenciamento: story alinhada ao PRD 100% Open-Source (`Kong DB-Less + OAuth2-Proxy`), removendo plugins Kong `openid-connect`/`jwt-signer` Enterprise do caminho feliz; adicionada nota de que cert-manager não é obrigatório para TLS local. Autoria/Implementação: GPT-5 Codex.
- `2026-05-29 01:01:44-03:00`: Implementação em andamento: TLS de borda, OAuth2-Proxy OSS, validação JWKS via `oidc-jwks-url`, rate limit default, política OPA de borda e runbook operacional adicionados. Validações estáticas passaram; validação runtime aguarda publicação da branch `story/3-2-context` para o ArgoCD sincronizar via GitOps. Autoria/Implementação: GPT-5 Codex.

---
Autoria/Implementação: GPT-5 Codex

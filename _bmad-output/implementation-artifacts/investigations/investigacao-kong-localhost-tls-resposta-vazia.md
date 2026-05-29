# Investigação: Kong localhost TLS resposta vazia

## Resumo de Passagem

1. **O que aconteceu.** Confirmado: `localhost:8080` retorna `curl: (52) Empty reply from server` e `localhost:8443` retorna `curl: (35) SSL_ERROR_SYSCALL`, enquanto o próprio Kong está saudável e responde corretamente pelo IP MetalLB `172.18.0.200`.
2. **Estado do caso.** Ativo: a causa do problema em `localhost` foi deduzida como incompatibilidade de topologia: o `serverlb` do k3d encaminha as portas do host para as portas dos nós, não para o IP LoadBalancer do MetalLB. O defeito separado do OAuth2-Proxy foi corrigido ao gerar `cookie_secret` com tamanho literal aceito.
3. **Próxima ação necessária.** Recriar o cluster com o `k3d.yaml` atualizado para portas padrão (`80:30080` e `443:30443`) e repetir a validação runtime por `http://localhost` e `https://localhost`.

## Informações do Caso

| Campo | Valor |
| ----- | ----- |
| Ticket | N/A |
| Data de abertura | 2026-05-29 |
| Status | Ativo |
| Sistema | Cluster k3d `cluster-kubernetes`, Kong Gateway 3.14.0.3 DB-Less, IP externo MetalLB `172.18.0.200`; topologia corrigida pretendida: host `80 -> nodePort 30080` e host `443 -> nodePort 30443` no `serverlb` do k3d |
| Fontes de evidência | Erros de `curl` relatados pelo usuário, reprodução local com `curl`, `kubectl get pods/svc/endpoints`, logs do Kong, logs do OAuth2-Proxy, configuração nginx do `serverlb` k3d e verificações Docker/k3d |

## Declaração do Problema

O usuário observou:

- `curl -i -H 'Host: keycloak.local' http://localhost:8080/` retornou `curl: (52) Empty reply from server`.
- `curl -k -i -H 'Host: keycloak.local' https://localhost:8443/realms/cluster-local/.well-known/openid-configuration` retornou `curl: (35) LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to localhost:8443`.

Essas saídas não satisfazem os AC1/AC2 da Story 3.2 porque são falhas de transporte, não respostas HTTP explícitas do gateway.

## Inventário de Evidências

| Fonte | Status | Observações |
| ----- | ------ | ----------- |
| Saídas de `curl` do usuário | Disponível | O mesmo padrão de falha foi reproduzido com `curl` local fora do sandbox. |
| Estado dos pods do cluster | Disponível | Kong `1/1 Running`; OAuth2-Proxy `CrashLoopBackOff`; Keycloak e PostgreSQL `Running`. |
| Estado de Services/endpoints | Disponível | `kong-service` tem `EXTERNAL-IP 172.18.0.200` e endpoints `10.42.0.10:8000,10.42.0.10:8443`; `oauth2-proxy-service` não tem endpoints prontos enquanto o pod quebra. |
| Logs do Kong | Disponível | Kong informa configuração declarativa carregada de `/kong/declarative/kong.yml` e nginx saudável. |
| Logs do OAuth2-Proxy | Disponível | Startup falha com a mensagem literal: `cookie_secret must be 16, 24, or 32 bytes ... but is 44 bytes`. |
| Configuração do `serverlb` k3d | Disponível | O stream nginx encaminha as portas do host `80/443` para os nós k3d nas portas `80/443`, não para `172.18.0.200`. |
| Teste direto via MetalLB | Disponível | A partir do container `serverlb` do k3d, HTTP para `172.18.0.200` retorna `426`; discovery HTTPS retorna `HTTP/2 200`. |

## Backlog da Investigação

| # | Caminho a explorar | Prioridade | Status | Observações |
| - | ------------------ | ---------- | ------ | ----------- |
| 1 | Decidir exposição local suportada: manter IP MetalLB ou mapear portas do host k3d para NodePorts fixos | Alta | Aberto | Necessário para validar os comandos de aceite com `localhost:8080/8443`. |
| 2 | Corrigir geração do `cookie_secret` do OAuth2-Proxy para produzir segredo aceito de 16/24/32 bytes | Alta | Aberto | Necessário antes da validação da rota protegida. |
| 3 | Reexecutar `curl` pelo host após corrigir a exposição | Alta | Aberto | Confirma AC1/AC2 pelos comandos documentados. |
| 4 | Reexecutar verificações de token/JWT/rate limit após OAuth2-Proxy iniciar | Alta | Aberto | Confirma AC2/AC3/AC4. |

## Linha do Tempo

| Hora | Evento | Fonte | Confiança |
| ---- | ------ | ----- | --------- |
| 2026-05-29 11:00:03 UTC | Kong carregou a configuração declarativa e iniciou worker | `kubectl logs -n kong-gateway deploy/kong-deployment` | Confirmado |
| 2026-05-29 11:03:03 UTC | OAuth2-Proxy falhou no startup por tamanho inválido do cookie secret | `kubectl logs -n kong-gateway deploy/oauth2-proxy-deployment` | Confirmado |
| 2026-05-29, durante a investigação | `curl` no host para `localhost:8080/8443` reproduziu erros de transporte | comandos locais de `curl` | Confirmado |
| 2026-05-29, durante a investigação | Teste direto no IP MetalLB retornou o comportamento esperado do gateway | `docker exec k3d-cluster-kubernetes-serverlb curl ... 172.18.0.200` | Confirmado |

## Achados Confirmados

### Achado 1: O caminho `localhost` não chega ao Kong pelo IP LoadBalancer pretendido

**Evidência:** a configuração do `serverlb` do k3d encaminha `listen 80` para `k3d-cluster-kubernetes-agent-0:80` e `k3d-cluster-kubernetes-server-0:80`; `listen 443` segue o mesmo padrão para a porta `443`.

**Detalhe:** `kong-service` está exposto pelo MetalLB em `172.18.0.200`, com NodePorts `30829/31551`, enquanto o mapeamento do host no `serverlb` k3d aponta para as portas dos nós `80/443`. As falhas observadas em `localhost` acontecem antes de o Kong conseguir produzir uma resposta HTTP válida.

### Achado 2: A configuração do Kong foi carregada e responde corretamente via IP MetalLB

**Evidência:** log do Kong: `declarative config loaded from /kong/declarative/kong.yml`; `curl` direto do container `serverlb` para `http://172.18.0.200/` retorna `HTTP/1.1 426`; discovery HTTPS direto retorna `HTTP/2 200`.

**Detalhe:** isso refuta a hipótese de que a rota `426` ou a montagem do certificado TLS estejam totalmente quebradas. O gateway funciona no caminho LoadBalancer alcançável dentro da rede Docker.

### Achado 3: OAuth2-Proxy não inicia com o cookie secret gerado atualmente

**Evidência:** log do OAuth2-Proxy: `cookie_secret must be 16, 24, or 32 bytes to create an AES cipher, but is 44 bytes`.

**Detalhe:** `scripts/inject-secrets.sh` gera hoje `random_b64 32`, que resulta em uma string base64 de 44 caracteres. O OAuth2-Proxy exige um segredo de tamanho aceito para criar o cipher AES.

## Conclusões Deduzidas

### Dedução 1: As falhas de `curl` em localhost são incompatibilidade de topologia, não falha de rota do Kong

**Baseada em:** Achados 1 e 2.

**Raciocínio:** se o Kong fosse o componente que estivesse falhando, o tráfego direto para o IP LoadBalancer dele também falharia. Em vez disso, o caminho direto pelo MetalLB produz HTTP/TLS esperado, enquanto `localhost` passa pelo `serverlb` k3d para portas de nó `80/443` que não estão conectadas ao IP MetalLB.

**Conclusão:** o caminho documentado `localhost:8080/8443` não é equivalente, hoje, ao caminho real de exposição do `kong-service`.

### Dedução 2: A validação de rota protegida não pode passar até o OAuth2-Proxy iniciar

**Baseada em:** Achado 3 e ausência de endpoints no `oauth2-proxy-service`.

**Raciocínio:** Kong consegue rotear `/protected` para `oauth2-proxy-service`, mas esse Service não tem endpoints prontos enquanto o Deployment está quebrando.

**Conclusão:** as validações runtime de JWT/JWKS e rate limit estão bloqueadas pelo defeito no segredo do OAuth2-Proxy, mesmo após corrigir a exposição por `localhost`.

## Hipóteses

### Hipótese 1: NodePorts fixos mais mapeamento k3d fariam os comandos `localhost` funcionarem

**Status:** Aberta

**Teoria:** fixar `nodePort` em `kong-service` e atualizar `k3d.yaml` para mapear `8080/8443` para esses NodePorts, em vez de mapear para as portas de nó `80/443`.

**Indicadores de apoio:** a configuração atual do `serverlb` prova que ele encaminha para portas de nó; `kong-service` já tem endpoints funcionando e NodePorts dinâmicos.

**Confirmaria:** após a alteração de topologia, `curl http://localhost:8080/` retornaria `426` e o discovery HTTPS retornaria `200`.

**Refutaria:** `localhost` continuaria falhando mesmo com o caminho NodePort direto funcionando.

**Resolução:** Aberta.

## Evidências Ausentes

| Lacuna | Impacto | Como obter |
| ------ | ------- | ---------- |
| Decisão se o projeto prefere validação por IP MetalLB ou por `localhost` | Define a direção da correção | Decisão de produto/arquitetura na Story 3.2 ou confirmação do usuário |
| Resultado runtime após corrigir o segredo do OAuth2-Proxy | Confirma a rota JWT/JWKS | Ajustar geração do segredo, reinjetar Secret e reiniciar o Deployment |

## Rastreamento no Código/Fonte

| Elemento | Detalhe |
| -------- | ------- |
| Origem do erro | Caminho `localhost`: `k3d.yaml` mapeia portas do host para `serverlb` `80/443`; configuração do `serverlb` encaminha para nós em `80/443`. |
| Gatilho | Usuário executa `curl` contra `localhost:8080` ou `localhost:8443`. |
| Condição | Kong está exposto pelo MetalLB em `172.18.0.200`, não pelas portas de nó `80/443`; OAuth2-Proxy também quebra por segredo de cookie inválido. |
| Arquivos relacionados | `k3d.yaml`, `cluster/infrastructure/kong-gateway/base/kong-service.yaml`, `scripts/inject-secrets.sh`, `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-deployment.yaml`. |

## Conclusão

**Confiança:** Alta

Causa raiz confirmada para as duas falhas de `curl`: as portas `localhost` documentadas não estão conectadas ao Service LoadBalancer do Kong na topologia atual k3d + MetalLB. Segundo defeito confirmado: OAuth2-Proxy está fora do ar porque o segredo de cookie gerado tem tamanho inválido.

## Próximos Passos Recomendados

### Direção de correção

1. Escolher e implementar um modelo de exposição local:
   - Preferível para os comandos de aceite atuais: NodePorts fixos em `kong-service` mais mapeamentos em `k3d.yaml` de `8080/8443` para esses NodePorts.
   - Alternativa: atualizar docs/testes para usar `172.18.0.200` a partir de um contexto na rede Docker, mas isso é pior para a experiência local do desenvolvedor.
2. Gerar um `cookie_secret` aceito pelo OAuth2-Proxy em vez de uma string base64 de 44 bytes.

### Diagnóstico

Depois das correções:

```bash
curl -i http://localhost/
curl -k -i https://localhost/realms/cluster-local/.well-known/openid-configuration
kubectl get endpoints -n kong-gateway oauth2-proxy-service
```

## Plano de Reprodução

1. Garantir que o cluster atual está no ar.
2. Executar `curl -i -H 'Host: keycloak.local' http://localhost:8080/`: observar resposta vazia.
3. Executar `curl -k -i -H 'Host: keycloak.local' https://localhost:8443/...`: observar erro SSL syscall.
4. Executar testes diretos no IP MetalLB a partir de `k3d-cluster-kubernetes-serverlb`: observar `426` e `200` esperados.

## Achados Laterais

- Confirmado: `oauth2-proxy-service` não tem endpoints enquanto o Deployment quebra; a validação de rota protegida está bloqueada independentemente do problema de exposição por `localhost`.

## Acompanhamento: 2026-05-29

### Novas Evidências

- `k3d.yaml` foi inicialmente ajustado para mapear `8080:30080` e `8443:30443`.
- `kong-service` foi ajustado com NodePorts fixos `30080` para HTTP e `30443` para HTTPS.
- `scripts/inject-secrets.sh --skip-if-exists` detectou o `cookie_secret` inválido existente, regenerou o valor e atualizou `oauth2-proxy-secret`.
- `kubectl rollout status deployment/oauth2-proxy-deployment -n kong-gateway --timeout=180s` concluiu com sucesso após reinício do Deployment.
- `kubectl get endpoints oauth2-proxy-service -n kong-gateway` mostrou endpoint preenchido em `10.42.0.11:4180`.
- `/ping` e `/ready` do OAuth2-Proxy responderam `HTTP/1.1 200 OK` via port-forward.
- `make lint` passou com 3738/3738 checks OPA e 0 erros kube-linter.

### Achados Adicionais

- Confirmado: o defeito de `cookie_secret` foi corrigido no cluster atual.
- Confirmado: o guardrail OPA agora cobre os NodePorts fixos necessários para o caminho `localhost`.

### Hipóteses Atualizadas

#### Hipótese 1: NodePorts fixos mais mapeamento k3d fariam os comandos `localhost` funcionarem

**Status:** Parcialmente confirmada

**Resolução parcial:** manifests e `k3d.yaml` foram ajustados e passaram no lint. A confirmação completa exige recriar o cluster com o novo `k3d.yaml` e deixar o ArgoCD aplicar a versão commitada da branch.

### Mudanças no Backlog

| # | Caminho a explorar | Prioridade | Status | Observações |
| - | ------------------ | ---------- | ------ | ----------- |
| 1 | Recriar cluster com novo `k3d.yaml` e branch publicada | Alta | Aberto | Necessário para confirmar `localhost` e `localhost:443` no caminho real. |
| 2 | Reexecutar validações HTTP/HTTPS/JWT/rate limit completas | Alta | Aberto | Depende de commit/push ou outro caminho GitOps aprovado. |

### Conclusão Atualizada

**Confiança:** Alta

A causa original foi corrigida nos manifests e no bootstrap de secrets, mas a validação final de `localhost` ainda depende de recriação do cluster com o `k3d.yaml` novo e sincronização GitOps da branch publicada.

## Acompanhamento: 2026-05-29 08:41:09-03:00

### Decisão de Exposição Local

- O caminho feliz solicitado passou a ser `http://localhost` e `https://localhost`, usando as portas padrão do host.
- `keycloak.local` permanece como alias de compatibilidade nas rotas do Kong, mas deixou de ser necessário para os comandos principais de validação manual.

### Mudanças Aplicadas nos Artefatos

- `k3d.yaml` passou a mapear `80:30080` e `443:30443`.
- `kong-declarative-config.yaml` passou a aceitar `localhost` e `keycloak.local` nas rotas HTTP, OIDC públicas, callback OAuth2 e rota protegida.
- `keycloak-deployment.yaml` passou a declarar `KC_HOSTNAME=https://localhost`, estabilizando o issuer externo esperado dos tokens.
- `oauth2-proxy-configmap.yaml` passou a usar `https://localhost/realms/cluster-local` como issuer externo, mantendo JWKS/token/userinfo internos por Service Kubernetes.
- `docs/runbook-operacoes.md` e a story passaram a documentar validação por `http://localhost` e `https://localhost`.

### Estado Atual

**Confiança:** Alta para correção estática; pendente de validação runtime.

A confirmação final ainda exige recriar o cluster, porque mudanças em `k3d.yaml` só entram em vigor na criação do cluster. Como o ArgoCD consome Git remoto, a validação completa também depende de publicar a branch ou usar outro caminho GitOps explicitamente aprovado.

---
Autoria/Implementação: GPT-5 Codex

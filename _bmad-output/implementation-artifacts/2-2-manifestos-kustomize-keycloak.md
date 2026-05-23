CRITICAL REQUIREMENT [COMPLEXITY]: Você DEVE definir explicitamente o nível de complexidade da tarefa nas linhas iniciais de TODA especificação de história. NUNCA omita esta classificação.

# Story 2.2: manifestos-kustomize-keycloak

**Status:** review
**Complexidade:** Média Complexidade

## Story Foundation

**User Story:** Como desenvolvedor da plataforma, quero implantar o Keycloak via GitOps na onda 2, conectado ao PostgreSQL existente, para fornecer o Identity Provider OIDC do cluster com segurança, observabilidade e alta disponibilidade.

**Acceptance Criteria:**
- Dado que o cluster está operando, quando o ArgoCD processar a Wave 2, então o Deployment do Keycloak (tag imutável `keycloak:26.6.2`) deve ser provisionado no namespace `keycloak-auth`.
- Dado que o Keycloak depende do banco de dados, quando o container iniciar, então ele deve conectar-se com sucesso ao PostgreSQL através do serviço interno e credenciais injetadas via secret `keycloak-db-secret`.
- Dado o requisito de alta prioridade (NFR-R01), quando o pod do Keycloak for criado, então ele deve estar associado a uma PriorityClass de prioridade máxima (imune a eviction).
- Dado os requisitos de observabilidade, quando o Keycloak gerar logs, então eles devem estar formatados em JSON (`KC_LOG_CONSOLE_OUTPUT=json`) e possuir healthchecks públicos (`/health/ready`, `/health/live`) habilitados (`KC_HEALTH_ENABLED=true`).
- Dado o fluxo externo, quando houver acesso, então um Ingress local deve rotear o tráfego adequadamente para o Keycloak.
- Dado os padrões de conformidade do repositório, quando passarem pelo lint, então os manifestos devem conter os labels obrigatórios, anotações de sync-wave ("2"), formato kebab-case e comentário em pt-BR.

## Developer Context & Technical Requirements

**Arquitetura:**
- O deploy deve ocorrer no namespace `keycloak-auth`, conectando-se ao serviço `postgresql-service` configurado na história 2.1.
- Estrutura Kustomize base:
  ```text
  cluster/infrastructure/keycloak-auth/
  ├── base/
  │   ├── keycloak-deployment.yaml
  │   ├── keycloak-service.yaml
  │   ├── keycloak-ingress.yaml
  │   ├── keycloak-priorityclass.yaml
  │   └── kustomization.yaml (atualizado)
  └── overlays/
      ├── local/
      ├── homologacao/
      └── production/
  ```

**Requisitos Específicos do Keycloak 26.6.2:**
- Imagem: `quay.io/keycloak/keycloak:26.6.2` (NUNCA latest).
- Variáveis de ambiente requeridas para conectar ao banco de dados:
  - `KC_DB=postgres`
  - `KC_DB_URL=jdbc:postgresql://postgresql-service.keycloak-auth.svc.cluster.local:5432/keycloak`
  - `KC_DB_USERNAME` e `KC_DB_PASSWORD` devem ser lidas das chaves `database-user` e `database-password` do secret `keycloak-db-secret`.
- Variáveis de inicialização/operacionais (Quarkus distribution):
  - Iniciar com o comando nativo `start` ou `start-dev` (para local). Se usar `start` para produção (segurança forte), defina variáveis mandatórias como `KC_HOSTNAME_STRICT=false` (em dev/test) ou configure hosts corretamente, e `KC_PROXY_HEADERS=xforwarded` para o Kong. O MVP requer proxy no edge.
  - Habilitar health probes com `KC_HEALTH_ENABLED=true` e `KC_METRICS_ENABLED=true`. Usar endpoints HTTP: `http://localhost:8080/health/ready` e `http://localhost:8080/health/live`.
  - Habilitar log estruturado: `KC_LOG_CONSOLE_OUTPUT=json`.
  - Definir `KEYCLOAK_ADMIN` e `KEYCLOAK_ADMIN_PASSWORD` se apropriado (poderá ser injetado via secret ou configurado no entrypoint). No MVP o foco é injetar a senha de banco; o user root admin pode ser lido de secrets caso o `inject-secrets.sh` provedencie ou ser estipulado provisoriamente.

**Regras Kustomize e K8s (01-regras-implementacao.md):**
- Labels OBRIGATÓRIOS: 
  - `app.kubernetes.io/name: keycloak`
  - `app.kubernetes.io/component: identity-provider`
  - `app.kubernetes.io/part-of: cluster-kubernetes`
- Cabeçalho OBRIGATÓRIO em pt-BR em todo YAML.
- Sync Wave: anotação obrigatória `argocd.argoproj.io/sync-wave: "2"` em todos os manifestos do Keycloak (Deployment, Service, Ingress, PriorityClass).
- PriorityClass: recurso non-namespaced (cluster-scoped), mas faz parte deste pacote para deploy do Keycloak. Deve prever preemption e alto valor (ex: 1000000).

## Previous Story Intelligence
Da Story 2.1 (PostgreSQL) aprendemos:
- É essencial adicionar as labels corretamente no pod: `app.kubernetes.io/name: keycloak` e `app.kubernetes.io/component: identity-provider`. O PostgreSQL foi configurado com uma NetworkPolicy que restringe acesso *apenas* a pods com esses dois labels no namespace `keycloak-auth`. Um label faltante causará timeout de conexão ("connection refused").
- A validação de Linting via `make lint` é rigorosa. O Deployment do Keycloak deve possuir configuration de security context adequado (non-root se possível, readonly root filesystem se aplicável com mapeamento de emptyDirs no `/opt/keycloak/data` e `/tmp`) e especificar adequadamente Requests e Limits (memória para Java Quarkus).

## Latest Tech Information
Para o Keycloak 26+ em container:
- A execução acontece sobre Quarkus (a era WildFly acabou). O entrypoint lida diretamente com os argumentos como `./kc.sh start`.
- Usar `/opt/keycloak/bin/kc.sh start` com os parâmetros apropriados. 
- Porta padrão HTTP exposta é a `8080`.
- Certifique-se que o usuário runAsNonRoot do Keycloak (UID 1000) possua acesso aos volumes necessários.

## Project Context Reference
- A porta interna que o Keycloak expõe é a `8080` (HTTP). O SSL/TLS é encerrado na borda pelo Kong DB-less na Wave 3 (NFR-S01).
- Arquivos de infra-app continuam com `prune: false`.
- O `kustomization.yaml` em `cluster/infrastructure/keycloak-auth/base/` precisa ser atualizado agregando os manifestos criados sem remover os do Postgres.

## Plano de Validação Manual

**1. Validação de Sintaxe (Linting):**
- Executar `make lint` na raiz do projeto.
- **Resultado Esperado:** Nenhuma violação apontada pelo conftest e kube-linter.

**2. Provisionamento e Sync:**
- Executar `make up`.
- **Resultado Esperado:** O ArgoCD detecta as mudanças e inicia a onda 2. Os pods do Keycloak são provisionados no namespace `keycloak-auth` após o PostgreSQL iniciar e se tornar Ready.

**3. Validação dos Recursos e Health:**
- Executar `kubectl get pods -l app.kubernetes.io/name=keycloak -n keycloak-auth`
- **Resultado Esperado:** O pod atinge status `Running` e `Ready 1/1`. As probes em `/health/live` e `/health/ready` não entram em loop de falha.
- Checar PriorityClass: `kubectl get pod <nome-do-pod> -n keycloak-auth -o jsonpath='{.spec.priorityClassName}'`
- **Resultado Esperado:** Deve exibir o nome do PriorityClass configurado.

**4. Verificação de Conectividade e Observabilidade:**
- Verificar logs do Keycloak: `kubectl logs -l app.kubernetes.io/name=keycloak -n keycloak-auth`
- **Resultado Esperado:** Logs puramente formatados em JSON (`{"timestamp":"...", "message":"..."}`). Nenhum erro de timeout no banco de dados demonstrando que a NetworkPolicy permite o tráfego adequadamente.

**5. Validação Ingress/Network:**
- Executar `kubectl get ingress -n keycloak-auth`. Acessar localmente o domínio correspondente no `/` para verificar o painel web ou o healthcheck pelo ingress.
- **Resultado Esperado:** Retorno HTTP 200 via navegador ou curl.

## Tasks/Subtasks

- [x] Implementar PriorityClass (`cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml`)
- [x] Implementar os manifestos do Keycloak
  - [x] Criar `keycloak-deployment.yaml` configurado (tag imutável, secrets para Postgres, logs em JSON, health enabled, labels exatos).
  - [x] Adicionar livenessProbe e readinessProbe adequados para Keycloak Quartus (`/health/live`, `/health/ready`).
  - [x] Garantir securityContext e resources declarados.
  - [x] Criar `keycloak-service.yaml` com sync-wave "2".
  - [x] Criar `keycloak-ingress.yaml` com sync-wave "2" (com regras de roteamento HTTP básicas caso Kong ainda não esteja operando TLS; focar na compatibilidade padrão para k3d Ingress temporário ou preparado para a futura integração).
- [x] Atualizar o arquivo `kustomization.yaml` na base (`cluster/infrastructure/keycloak-auth/base/kustomization.yaml`) adicionando os manifestos criados.

## Dev Agent Record

### Plano de Implementação
1. PriorityClass `keycloak-critical` (valor 1000000, PreemptLowerPriority) — cluster-scoped, wave "2"
2. Deployment com imagem `quay.io/keycloak/keycloak:26.6.2`, modo `start`, HTTP habilitado, variáveis KC_* injetadas via env/secret, securityContext non-root (UID 1000) com `readOnlyRootFilesystem: true` e emptyDirs em `/opt/keycloak/data` e `/tmp`; probes HTTP em `/health/live` e `/health/ready`
3. Service ClusterIP expondo porta 80 → 8080
4. Ingress via Traefik para host `keycloak.local` (temporário até Kong Wave 3)
5. Atualização do `kustomization.yaml` base preservando recursos do PostgreSQL

### Notas de Conclusão
- Todos os 4 manifestos criados + kustomization.yaml atualizado
- `make lint` passou: 92 testes conftest (OPA) + kube-linter — 0 falhas, 0 warnings
- Labels obrigatórios (`name`, `component`, `identity-provider`, `part-of`) presentes no Deployment e Service (checados pelo kube-linter) e no PriorityClass/Ingress por consistência
- Labels exatos no pod template garantem compatibilidade com a NetworkPolicy do PostgreSQL da Story 2.1
- `KC_HTTP_ENABLED=true` + `KC_HOSTNAME_STRICT=false` + `KC_PROXY_HEADERS=xforwarded` permitem operação em HTTP por trás do Kong
- Credenciais admin injetadas via `keycloak-admin-secret` (criado pelo `inject-secrets.sh`)

### Lista de Arquivos
- `cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/keycloak-service.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/keycloak-ingress.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml` (atualizado)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (atualizado)

### Autoria
Implementação: claude-sonnet-4-6

## Change Log
- `2026-05-23 00:05:00-03:00`: Especificação de história gerada, incluindo regras do BMad, restrições arquiteturais Zero-Trust e dependências documentadas para a configuração nativa GitOps.
- `2026-05-23 00:09:00-03:00`: Atualização da versão do Keycloak de 26.2.1 para a última versão estável 26.6.2.
- `2026-05-23 00:00:00-03:00`: Implementação concluída — 4 manifestos Keycloak criados, kustomization.yaml atualizado, make lint 0 falhas. Status: review.

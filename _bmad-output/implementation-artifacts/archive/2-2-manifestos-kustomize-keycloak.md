CRITICAL REQUIREMENT [COMPLEXITY]: Você DEVE definir explicitamente o nível de complexidade da tarefa nas linhas iniciais de TODA especificação de história. NUNCA omita esta classificação.

# Story 2.2: manifestos-kustomize-keycloak

**Status:** done
**Complexidade:** Média Complexidade

## Story Foundation

**User Story:** Como desenvolvedor da plataforma, quero implantar o Keycloak via GitOps na onda 2, conectado ao PostgreSQL existente, para fornecer o Identity Provider OIDC do cluster com segurança, observabilidade e alta disponibilidade.

**Acceptance Criteria:**
- Dado que o cluster está operando, quando o ArgoCD processar a Wave 2, então o Deployment do Keycloak (tag imutável `keycloak:26.6.2`) deve ser provisionado no namespace `keycloak-auth`.
- Dado que o Keycloak depende do banco de dados, quando o container iniciar, então ele deve conectar-se com sucesso ao PostgreSQL através do serviço interno e credenciais injetadas via secret `keycloak-db-secret`.
- Dado o requisito de alta prioridade (NFR-R01), quando o pod do Keycloak for criado, então ele deve estar associado a uma PriorityClass de prioridade máxima (imune a eviction).
- Dado os requisitos de observabilidade, quando o Keycloak gerar logs, então eles devem estar formatados em JSON (`KC_LOG_CONSOLE_OUTPUT=json`) e possuir healthchecks internos (`/health/ready`, `/health/live`) habilitados (`KC_HEALTH_ENABLED=true`) na management port `9000`.
- Dado o fluxo local antes da Wave 3, quando houver necessidade de acesso ao Keycloak, então o procedimento operacional deve usar port-forward até o Kong assumir o roteamento de borda.
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
  - Habilitar health probes com `KC_HEALTH_ENABLED=true` e `KC_METRICS_ENABLED=true`. Usar endpoints internos na management port: `http://localhost:9000/health/ready` e `http://localhost:9000/health/live`.
  - Habilitar log estruturado: `KC_LOG_CONSOLE_OUTPUT=json`.
  - Definir `KC_BOOTSTRAP_ADMIN_USERNAME` e `KC_BOOTSTRAP_ADMIN_PASSWORD` a partir do secret `keycloak-admin-secret`. No MVP o foco é injetar a senha de banco e as credenciais bootstrap do console administrativo via `inject-secrets.sh`.

**Regras Kustomize e K8s (01-regras-implementacao.md):**
- Labels OBRIGATÓRIOS: 
  - `app.kubernetes.io/name: keycloak`
  - `app.kubernetes.io/component: identity-provider`
  - `app.kubernetes.io/part-of: cluster-kubernetes`
- Cabeçalho OBRIGATÓRIO em pt-BR em todo YAML.
- Sync Wave: anotação obrigatória `argocd.argoproj.io/sync-wave: "2"` em todos os manifestos do Keycloak (Deployment, Service, PriorityClass).
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
- Antes da Wave 3, o acesso local ao Keycloak deve ser feito por port-forward; não há Ingress funcional porque Traefik está desabilitado no k3d.
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
- **Resultado Esperado:** Logs puramente formatados em JSON (`{"timestamp":"...", "message":"..."}`). Nenhum erro de timeout no banco de dados e nenhum aviso de variáveis administrativas depreciadas (`KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`).

**5. Validação de Acesso Local Pré-Kong:**
- Executar `kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80` e acessar `http://localhost:8090`.
- **Resultado Esperado:** O painel web do Keycloak responde via navegador ou curl. Healthchecks permanecem internos na porta management `9000`.

**6. Validação de Login Administrativo:**
- Obter as credenciais bootstrap a partir do Secret:
  ```bash
  ADMIN_USERNAME="$(kubectl get secret keycloak-admin-secret -n keycloak-auth \
    -o jsonpath='{.data.admin-username}' | base64 -d)"

  ADMIN_PASSWORD="$(kubectl get secret keycloak-admin-secret -n keycloak-auth \
    -o jsonpath='{.data.admin-password}' | base64 -d)"

  printf 'Usuário admin: %s\n' "${ADMIN_USERNAME}"
  printf 'Senha admin: %s\n' "${ADMIN_PASSWORD}"
  ```
- Com o port-forward ativo, acessar `http://localhost:8090/admin` e autenticar com o usuário e senha exibidos.
- **Resultado Esperado:** Login administrativo concluído com sucesso sem expor credenciais em arquivos versionados.

## Tasks/Subtasks

- [x] Implementar PriorityClass (`cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml`)
- [x] Implementar os manifestos do Keycloak
  - [x] Criar `keycloak-deployment.yaml` configurado (tag imutável, secrets para Postgres, logs em JSON, health enabled, labels exatos).
  - [x] Adicionar livenessProbe e readinessProbe adequados para Keycloak Quartus (`/health/live`, `/health/ready`).
  - [x] Garantir securityContext e resources declarados.
  - [x] Criar `keycloak-service.yaml` com sync-wave "2".
  - [x] Documentar acesso local por port-forward até o Kong assumir o roteamento de borda na Wave 3.
- [x] Atualizar o arquivo `kustomization.yaml` na base (`cluster/infrastructure/keycloak-auth/base/kustomization.yaml`) adicionando os manifestos criados.

### Review Findings

- [x] [Review][Patch] Remover/deferir o Ingress da Wave 2 e ajustar story/runbook para port-forward até Kong [cluster/infrastructure/keycloak-auth/base/keycloak-ingress.yaml:15]
- [x] [Review][Patch] Manter health interno na management port `9000` e ajustar story/runbook para não prometer health público via Service/Ingress [cluster/infrastructure/keycloak-auth/base/keycloak-service.yaml:18]
- [x] [Review][Defer] PriorityClass não garante a "imunidade a eviction" declarada no AC [cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml:13] — deferred, motivo: Não tenho condições técnicas de tomar essa decisão agora.
- [x] [Review][Patch] Adicionar `startupProbe` para evitar restart prematuro no bootstrap do Keycloak [cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml:99]
- [x] [Review][Patch] Corrigir rastreabilidade LLM dos artefatos novos sem autoria [docs/runbook-operacoes.md:1; CLAUDE.md:1]
- [x] [Review][Patch] Reordenar ou corrigir timestamps cronológicos do Change Log da story [_bmad-output/implementation-artifacts/2-2-manifestos-kustomize-keycloak.md:140]

## Dev Agent Record

### Plano de Implementação
1. PriorityClass `keycloak-critical` (valor 1000000, PreemptLowerPriority) — cluster-scoped, wave "2"
2. Deployment com imagem `quay.io/keycloak/keycloak:26.6.2`, modo `start`, HTTP habilitado, variáveis KC_* injetadas via env/secret, securityContext non-root (UID 1000) com `readOnlyRootFilesystem: true` e emptyDirs em `/opt/keycloak/data` e `/tmp`; probes HTTP em `/health/live` e `/health/ready` na management port `9000`
3. Service ClusterIP expondo porta 80 → 8080
4. Acesso local por port-forward até Kong assumir o roteamento de borda na Wave 3
5. Atualização do `kustomization.yaml` base preservando recursos do PostgreSQL

### Notas de Conclusão
- Todos os 3 manifestos do Keycloak criados + kustomization.yaml atualizado
- `make lint` passou: 82 testes conftest (OPA) + kube-linter — 0 falhas, 0 warnings
- Labels obrigatórios (`name`, `component`, `identity-provider`, `part-of`) presentes no Deployment e Service (checados pelo kube-linter) e no PriorityClass por consistência
- Labels exatos no pod template garantem compatibilidade com a NetworkPolicy do PostgreSQL da Story 2.1
- `KC_HTTP_ENABLED=true` + `KC_HOSTNAME_STRICT=false` + `KC_PROXY_HEADERS=xforwarded` permitem operação em HTTP por trás do Kong
- Credenciais bootstrap admin injetadas via `keycloak-admin-secret` (criado pelo `inject-secrets.sh`) usando variáveis `KC_BOOTSTRAP_ADMIN_USERNAME` e `KC_BOOTSTRAP_ADMIN_PASSWORD`

### Lista de Arquivos
- `cluster/infrastructure/keycloak-auth/base/keycloak-priorityclass.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/keycloak-service.yaml` (novo)
- `cluster/infrastructure/keycloak-auth/base/kustomization.yaml` (atualizado)
- `docs/runbook-operacoes.md` (atualizado)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (atualizado)

### Autoria
Implementação: claude-sonnet-4-6
Revisão: GPT-5.5

## Change Log
- `2026-05-27 14:54:49-03:00`: Story testada e concluída pelo usuário; status atualizado para `done` e sprint status sincronizado.
- `2026-05-27 14:41:47-03:00`: Ajuste pós-validação — variáveis administrativas depreciadas do Keycloak substituídas por `KC_BOOTSTRAP_ADMIN_USERNAME`/`KC_BOOTSTRAP_ADMIN_PASSWORD`; Plano de Validação Manual recebeu passo para obter credenciais do Secret e validar login no console.
- `2026-05-27 14:10:44-03:00`: Patches do code review aplicados — Ingress da Wave 2 removido, health interno em `9000` documentado, `startupProbe` adicionado, autoria LLM registrada em artefatos novos e Change Log reordenado.
- `2026-05-27 14:03:07-03:00`: Decisões do code review registradas — Ingress removido/deferido até Kong; health mantido interno na management port 9000; hardening de eviction/PriorityClass diferido por insuficiência técnica para decisão agora.
- `2026-05-27 14:03:07-03:00`: Code review executado contra `main`; achados registrados na seção Review Findings. Status permanece review até decisão/aplicação dos patches.
- `2026-05-23 00:09:00-03:00`: Atualização da versão do Keycloak de 26.2.1 para a última versão estável 26.6.2.
- `2026-05-23 00:05:00-03:00`: Especificação de história gerada, incluindo regras do BMad, restrições arquiteturais Zero-Trust e dependências documentadas para a configuração nativa GitOps.
- `2026-05-23 00:00:00-03:00`: Implementação concluída — manifestos Keycloak criados, kustomization.yaml atualizado, make lint 0 falhas. Status: review.

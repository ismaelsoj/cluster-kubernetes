---
baseline_commit: 3f1d89d879c64e22ad1b7675b08587a37c7a5a1b
---

CRITICAL REQUIREMENT [COMPLEXITY]: Voce DEVE definir explicitamente o nivel de complexidade da tarefa nas linhas iniciais de TODA especificacao de historia. NUNCA omita esta classificacao.

# Story 3.4: Refinamento do Bootstrap de Emergencia

**Status:** done
**Complexidade:** Baixa Complexidade

## Story Foundation

**User Story:** Como um SRE, quero documentacao de recuperacao com dados reais da infraestrutura completa, para que eu reconstrua a plataforma do zero com comandos verificados.

**Valor de Negocio:** Esta story fecha a Jornada 2 do PRD no ponto mais sensivel para operacao: recuperar a fundacao GitOps sem depender de memoria tribal. O ganho principal nao e criar novos componentes, e sim transformar o esqueleto de `docs/bootstrap-emergencia.md` em um procedimento confiavel, coerente com os manifests, scripts e testes reais ja validados nos Epicos 1, 2 e 3.

**Classificacao de Escopo:** Story majoritariamente documental, com validacao operacional obrigatoria. O caminho feliz esperado e atualizar `docs/bootstrap-emergencia.md`; qualquer ajuste em scripts so deve acontecer se a documentacao nao puder refletir com honestidade o comportamento real atual.

**Dependencias Confirmadas:**

- Story 1.5 criou o esqueleto inicial de `docs/bootstrap-emergencia.md`, mas ele ainda preserva placeholders e instrucoes parciais.
- Story 2.4 consolidou backup e restore do PostgreSQL do Keycloak, incluindo os scripts `scripts/pg-backup.sh` e `scripts/pg-restore.sh`.
- Story 3.2 estabilizou a topologia de borda local em `https://localhost`, os secrets de TLS/OAuth2-Proxy, os endpoints de health e o comportamento correto do teste offline em `/oauth2/auth`.
- Story 3.3 refinou `scripts/cluster-up.sh`, `scripts/inject-secrets.sh`, `docs/runbook-operacoes.md` e o resumo operacional do terminal; esses artefatos agora sao a fonte mais fiel do bootstrap real.
- O `sprint-status.yaml` marca `3-4-refinamento-bootstrap-emergencia` como backlog e o Epico 3 como `in-progress`; esta criacao de contexto promove a story para `ready-for-dev`.

## Acceptance Criteria

- **AC1:** Dado `docs/bootstrap-emergencia.md` ainda em estado de esqueleto, quando a story for implementada, entao o documento deve refletir a topologia real atual do projeto, com nomes exatos de namespaces, `Applications`, `Deployments`, `Services`, `Secrets`, rotas e endpoints usados na recuperacao.
- **AC2:** Dado um cenario de reconstrucao total do cluster, quando o SRE seguir o guia, entao a sequencia operacional deve ficar explicita e verificavel: criar cluster, garantir namespaces, injetar secrets obrigatorios, instalar ArgoCD, aplicar bootstrap GitOps e confirmar readiness dos componentes centrais.
- **AC3:** Dado um cenario de falha parcial, quando apenas um subconjunto da plataforma estiver degradado, entao o guia deve separar claramente recuperacao parcial vs. reconstruicao total, incluindo quando usar `argocd app sync`, quando usar restore do PostgreSQL e quando reexecutar scripts de bootstrap.
- **AC4:** Dado o procedimento de restore do PostgreSQL/Keycloak, quando o runbook for refinado, entao os comandos de pausa de auto-heal, restore, validacao pos-restore e reativacao do auto-heal devem estar corretos, consistentes com `root-app`, `infra-app`, `scripts/pg-restore.sh` e os fixtures locais efetivamente usados hoje.
- **AC5:** Dado que healthchecks e probes reais ja existem na plataforma, quando o documento for atualizado, entao ele deve listar endpoints e comandos de verificacao que batam com a implementacao atual, incluindo ArgoCD, Keycloak, Kong e OAuth2-Proxy, sem inventar portas, paths ou comportamentos nao validados.
- **AC6:** Dado que ha informacoes sobre recovery espalhadas entre `docs/bootstrap-emergencia.md`, `docs/runbook-operacoes.md`, `scripts/cluster-up.sh` e as historias 2.4/3.2/3.3, quando a story for concluida, entao o caminho feliz de emergencia deve ficar coerente entre esses artefatos, com divergencias removidas ou explicitamente justificadas.

## Tasks / Subtasks

- [x] Refinar `docs/bootstrap-emergencia.md` com o bootstrap real da plataforma (AC1, AC2, AC5)
  - [x] Substituir o framing de "esqueleto com placeholders" por um runbook operacional de verdade, preservando o aviso de zero segredos no Git.
  - [x] Confirmar e documentar os nomes exatos usados hoje: `argocd`, `keycloak-auth`, `kong-gateway`, `root-app`, `infra-app`, `apps-app`, `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret`, `oauth2-proxy-secret`.
  - [x] Registrar a ordem real de bootstrap: cluster -> namespaces/secrets -> ArgoCD -> App-of-Apps -> readiness da plataforma.
  - [x] Explicar com clareza o papel do override de `targetRevision` para branch local, alinhado ao comportamento atual de `scripts/cluster-up.sh`.
- [x] Separar recuperacao total vs. recuperacao parcial de forma objetiva (AC2, AC3)
  - [x] Criar seccoes distintas para reconstruir do zero e para recuperar servicos ja existentes no cluster.
  - [x] Incluir sinais de decisao do operador: quando basta `argocd app sync`, quando reexecutar `make secrets`/`scripts/inject-secrets.sh`, quando usar restore de banco e quando destruir/recriar o cluster.
  - [x] Preservar a regra GitOps: mudancas manuais no cluster so sao aceitaveis para bootstrap de secrets e procedimentos de recuperacao explicitamente previstos.
- [x] Consolidar o restore do PostgreSQL/Keycloak em um fluxo coerente (AC3, AC4)
  - [x] Validar se `root-app` e `infra-app` devem ser ambos ajustados em todos os passos de freeze/unfreeze de auto-heal; se sim, padronizar isso no documento.
  - [x] Garantir que os comandos de backup, restore e validacao pos-restore batam com `scripts/pg-backup.sh`, `scripts/pg-restore.sh` e com o fixture local `m2m-client`.
  - [x] Documentar explicitamente que `dev-m2m-local-secret` e fixture de desenvolvimento local, nao padrao para outros ambientes.
- [x] Atualizar os checks de saude e validacao final do runbook (AC5, AC6)
  - [x] Usar endpoints reais do projeto: Keycloak em `:9000/health/*`, Kong em `/status` e `/status/ready`, OAuth2-Proxy em `/ping` e `/ready`, e o fluxo externo em `https://localhost`.
  - [x] Diferenciar probes internos de Kubernetes de validacoes externas de jornada operacional.
  - [x] Incluir comandos de verificacao final que provem plataforma funcional apos recovery, inclusive emissao de token e teste protegido quando isso fizer sentido.
- [x] Harmonizar a documentacao adjacente e registrar evidencias (AC6)
  - [x] Revisar `docs/runbook-operacoes.md` apenas se necessario para evitar contradicao com o bootstrap de emergencia.
  - [x] Registrar no artefato da historia quais arquivos foram comparados e quais divergencias foram resolvidas.
  - [x] Executar a validacao manual documentada e registrar evidencias concretas no `Dev Agent Record`.

### Review Findings

- [x] [Review][Decision] Secao 5.4: manter check interno direto ao Keycloak (porta 80 via `keycloak-service`) como validacao especifica do restore; secao 6.2 continua como validacao final da plataforma com `make token` — nota explicativa adicionada na 5.4 [docs/bootstrap-emergencia.md:secao 5.4]

- [x] [Review][Patch] Padronizar `localhost` em todos os pontos — todos os enderecos internos agora usam `localhost` (incluindo secao 2 e secao 6.1) [docs/bootstrap-emergencia.md]
- [x] [Review][Patch] `runbook-operacoes.md` caminho simples de restore sem reativacao do auto-heal — reativacao de `root-app` e `infra-app` adicionada apos `pg-restore.sh` [docs/runbook-operacoes.md]
- [x] [Review][Patch] Atribuicao `GPT-5 Codex` — `Revisao: claude-sonnet-4-6` adicionado como rodape nos dois documentos [docs/bootstrap-emergencia.md, docs/runbook-operacoes.md]
- [x] [Review][Patch] Secao 6.4 sem safety guard — aviso `[!WARNING]` adicionado com instrucao de recuperacao manual do Keycloak [docs/bootstrap-emergencia.md:secao 6.4]
- [x] [Review][Patch] Narrativa de Sync Waves ausente — descricao das waves adicionada no Passo 5 (Wave 1=PostgreSQL, Wave 2=Keycloak, Wave 3=Kong/OAuth2-Proxy) [docs/bootstrap-emergencia.md]
- [x] [Review][Patch] Tabela de inventario sem Services — `postgresql-service`, `keycloak-service`, `kong-service`, `oauth2-proxy-service` adicionados [docs/bootstrap-emergencia.md:secao 2]
- [x] [Review][Patch] Secao 4.1 sync duplo redundante — primeiro `argocd app sync infra-app --force` removido, mantido apenas `argocd app sync root-app infra-app apps-app --force` [docs/bootstrap-emergencia.md:secao 4.1]

- [x] [Review][Defer] Token extraction via `awk -F=` poderia truncar se token contivesse `=` — irrelevante para JWTs (base64url sem padding), valido como principio geral [docs/bootstrap-emergencia.md:secao 6.3] — deferred, pre-existing
- [x] [Review][Defer] `pg_restore --clean --if-exists` sem `--dbname` explicito no script — comportamento do script, nao do documento [scripts/pg-restore.sh] — deferred, pre-existing
- [x] [Review][Defer] `argocd app sync` pressupoe contexto CLI pre-autenticado — cenario real em bootstrap do zero; cobre gap operacional fora do escopo desta story [docs/bootstrap-emergencia.md:secao 4.1] — deferred, pre-existing
- [x] [Review][Defer] Procedimento manual de branch override (passo 4) nao tem verificacao de remote-existence — doc ja menciona fallback para `main`; complexidade do script fora do escopo [docs/bootstrap-emergencia.md:secao 3.2] — deferred, pre-existing

## Dev Notes

### Contexto do Epico

- O Epico 3 entrega a operacao de borda Zero-Trust completa no ambiente local. A story 3.4 fecha o lado SRE da mesma jornada: como reconstruir essa fundacao sem depender de tentativa e erro.
- A implementacao nao deve "redesenhar" o bootstrap. Ela deve espelhar o comportamento real ja consolidado nas stories 1.5, 2.4, 3.2 e 3.3.
- O resultado esperado nao e uma documentacao generica de Kubernetes; e um guia cirurgico para esta topologia especifica (`k3d + ArgoCD + Keycloak + PostgreSQL + Kong + OAuth2-Proxy`).

### Guardrails Arquiteturais Obrigatorios

- Preservar a ordem de Sync Waves e a narrativa correspondente no runbook: PostgreSQL Wave 1, Keycloak Wave 2, Kong/OAuth2-Proxy Wave 3.
- Nao documentar segredos em texto plano nem sugerir salvar valores sensiveis no Git. O bootstrap de secrets continua manual/externo por design.
- O caminho feliz externo continua sendo `https://localhost`; o guia nao deve reintroduzir `localhost:8080/8443` como principal nem depender de acesso direto ao Service interno do Keycloak para validacoes de plataforma.
- Diferenciar validacao de token pela borda (`https://localhost/...`) de verificacoes internas de manutencao via `kubectl port-forward`.
- Nao inverter a autoridade operacional dos artefatos: `scripts/cluster-up.sh` e `scripts/inject-secrets.sh` definem o comportamento do bootstrap automatizado; `docs/bootstrap-emergencia.md` deve explica-lo, nao contradize-lo.
- Se a story exigir tocar `scripts/cluster-up.sh` ou `scripts/inject-secrets.sh`, isso precisa ser motivado por divergencia real entre comportamento e documentacao. Evitar scope creep em scripts sem ganho concreto de recovery.
- Preservar o Safe-Prune da infra central: `infra-app` com `prune: false`; nao documentar comandos que enfraquecam essa protecao sem motivo.

### Arquivos Que Precisam Ser Lidos/Preservados

**UPDATE obrigatorio**

- `docs/bootstrap-emergencia.md`
  - **Estado atual:** mistura esqueleto antigo com trechos reais de restore, mas ainda nao esta consolidado como runbook unico e coerente.
  - **Esta story muda:** transforma o documento em guia operacional verificavel para recuperacao total e parcial.
  - **Preservar:** foco em pt-BR, zero segredos no Git, reconstruicao por GitOps e rastreabilidade da fixture local.

**Arquivos existentes para ler completamente antes de editar**

- `scripts/cluster-up.sh`
  - **Estado atual:** cria/reconcilia cluster, injeta secrets, instala ArgoCD, aplica `root-app`/`infra-app`/`apps-app` com override de branch e aguarda readiness de Keycloak, Kong e OAuth2-Proxy.
  - **O que pode impactar a story:** a documentacao precisa refletir esta ordem e os nomes reais dos componentes.
  - **Preservar:** idempotencia, override de `targetRevision` e codigos de saida honestos.

- `scripts/inject-secrets.sh`
  - **Estado atual:** garante namespaces e cria/atualiza `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret` e `oauth2-proxy-secret`.
  - **O que pode impactar a story:** os nomes exatos e o comportamento de `make secrets`/`.env` precisam aparecer corretamente no guia.
  - **Preservar:** injeção manual/externa de segredos, sem versionamento.

- `docs/runbook-operacoes.md`
  - **Estado atual:** concentra troubleshooting, token, teste protegido e restore do PostgreSQL, com partes que se sobrepoem ao bootstrap de emergencia.
  - **O que pode impactar a story:** remover contradicoes e decidir o que fica como referencia primaria vs. complementar.
  - **Preservar:** comandos de validacao em runtime ja homologados nas stories 3.2 e 3.3.

- `cluster/bootstrap/root-app.yaml`
  - **Estado atual:** `Application` raiz com `targetRevision: main`, override em runtime por `cluster-up.sh` e `selfHeal: true`.
  - **O que pode impactar a story:** o guia deve explicar corretamente quando aplicar com `sed` e quando o script ja faz isso.
  - **Preservar:** semantica App-of-Apps e labels atuais.

- `cluster/bootstrap/infra-app.yaml`
  - **Estado atual:** `Application` de infraestrutura com `prune: false` e `selfHeal: true`.
  - **O que pode impactar a story:** passos de freeze/unfreeze durante restore e a narrativa de Safe-Prune.
  - **Preservar:** protecao da fundacao critica.

- `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`
  - **Estado atual:** health/metrics em porta de management `9000`, `KC_HOSTNAME=https://localhost`, bootstrap admin por Secret.
  - **O que pode impactar a story:** endpoints e probes reais do Keycloak.
  - **Preservar:** management port `9000`, readiness/liveness e issuer HTTPS local.

- `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml`
  - **Estado atual:** probes em `/status` e `/status/ready` na porta 8100, TLS por `kong-tls-secret`.
  - **O que pode impactar a story:** checks de health reais do gateway.
  - **Preservar:** DB-less, status API e secret TLS atual.

- `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-deployment.yaml`
  - **Estado atual:** liveness em `/ping`, readiness em `/ready`, secret `oauth2-proxy-secret`.
  - **O que pode impactar a story:** checks de saude reais do validador JWT/JWKS.
  - **Preservar:** comportamento atual dos endpoints e integracao via Secret.

### Estrutura de Arquivos Esperada

```text
docs/
├── bootstrap-emergencia.md      # UPDATE obrigatorio
└── runbook-operacoes.md         # UPDATE opcional se houver contradicao

scripts/
├── cluster-up.sh                # READ COMPLETO; UPDATE apenas se necessario
├── inject-secrets.sh            # READ COMPLETO; UPDATE apenas se necessario
├── pg-backup.sh                 # READ se precisar alinhar comandos
└── pg-restore.sh                # READ se precisar alinhar comandos

cluster/bootstrap/
├── root-app.yaml                # READ COMPLETO
└── infra-app.yaml               # READ COMPLETO
```

### Estado Atual a Preservar no Sistema

- `root-app`, `infra-app` e `apps-app` sao os nomes canonicos das `Applications` ArgoCD.
- `keycloak-auth` e `kong-gateway` sao namespaces obrigatorios antes da injecao de secrets.
- O bootstrap automatizado usa `kubectl apply --server-side=true --force-conflicts` para instalar ArgoCD `v3.4.2`.
- O guia atual de restore ja usa freeze/unfreeze de auto-heal, mas ha historico recente de divergencia sobre quando patchar tambem o `root-app`; a implementacao desta story deve resolver isso explicitamente.
- O fluxo de validacao pos-restore usa `m2m-client` e o token endpoint do realm `cluster-local`; esse fixture e aceito apenas para ambiente local.

### Padroes de Implementacao Recomendados

- Tratar `docs/bootstrap-emergencia.md` como runbook principal de desastre e `docs/runbook-operacoes.md` como complemento operacional. Se os dois mantiverem o mesmo procedimento, manter o texto curto e referencial para evitar drift futuro.
- Preferir comandos idempotentes (`kubectl apply`, `kubectl create namespace --dry-run=client -o yaml | kubectl apply -f -`) quando a recuperacao puder ser reexecutada.
- Quando o procedimento tiver precondicoes fortes, registra-las antes do bloco de comandos. Isso evita que o operador execute patches ou restores na ordem errada.
- Em validacoes finais, separar:
  - saude interna do cluster (`kubectl get`, probes, rollout);
  - saude da borda (`https://localhost`, discovery, token);
  - recuperacao de identidade (`pg_restore`, token M2M pos-restore).
- Nao duplicar manualmente listas de nomes/paths se o script ja os define de forma clara; onde possivel, documentar o nome canonico exatamente como aparece no repositrio.

### Previous Story Intelligence

- A Story 3.3 consolidou `make status` e `make token` como caminho feliz para operadores e desenvolvedores; a 3.4 deve reutilizar esse fluxo como validacao final de recovery, nao criar um roteiro paralelo.
- O code review da 3.3 deixou um diferido relevante: `docs/runbook-operacoes.md` perdeu uma instrucao do `root-app` sem explicacao clara. Esta story e o lugar natural para corrigir ou justificar isso.
- A Story 3.2 confirmou que a topologia correta de borda para validacao externa e `https://localhost`, e que o teste de sobrevivencia offline usa `/oauth2/auth`, nao `/protected/.../userinfo`.
- A Story 3.2 tambem confirmou os endpoints de health reais: Keycloak na porta `9000`, Kong em `/status` e `/status/ready`, OAuth2-Proxy em `/ping` e `/ready`.
- A fixture local `dev-m2m-local-secret` permaneceu deliberadamente versionada para ambiente dev. A documentacao precisa tratá-la como fixture controlada, nao como padrao de seguranca.

### Git Intelligence e Padroes Recentes do Projeto

- `46a43e6 feat: implementa story 3.3 token e feedback terminal`
  - Arquivos relevantes: `docs/runbook-operacoes.md`, `scripts/cluster-up.sh`, `scripts/generate-token.sh`, `scripts/status.sh`, `scripts/token-helpers.sh`.
  - Insight: o bootstrap e a operacao local recentes ficaram concentrados em scripts e runbook; a story 3.4 deve partir desses artefatos como fonte primaria.
- `fa10a9a code review da história 3.2.`
  - Arquivos relevantes: `cluster/infrastructure/kong-gateway/base/kong-declarative-config.yaml`, `scripts/cluster-up.sh`, `deferred-work.md`.
  - Insight: ajustes de bootstrap e documentacao costumam nascer de validacao runtime real; evitar especulacao e registrar evidencias.
- `484f799 finalização da história com a validação pelo opus dos últimos critérios de aceite pendentes`
  - Arquivos relevantes: `3-2-tls-validacao-jwks-rate-limit-default.md`, `deferred-work.md`.
  - Insight: recovery e bootstrap estao ligados a itens diferidos de rate limit, auto-heal e prova offline; a story 3.4 deve mencionar esses limites sem tentar resolvelos todos.

### Informacoes Tecnicas Atuais Relevantes

- A documentacao oficial do Argo CD 3.4 continua recomendando `kubectl apply --server-side --force-conflicts` para instalar `install.yaml`, justamente porque alguns CRDs excedem o limite de annotations do apply client-side. Isso confirma que o procedimento atual do projeto para instalar `v3.4.2` esta alinhado com a recomendacao oficial. Fonte oficial: Argo CD Installation e Getting Started 3.4.
- A documentacao oficial do Keycloak 26.6.2 confirma que os health endpoints ficam na porta de management `9000` por padrao quando health/metrics estao habilitados, e que o endpoint de token do fluxo `client_credentials` continua sendo `/realms/{realm}/protocol/openid-connect/token`. Tambem confirma que esse fluxo nao retorna refresh token por padrao. Fonte oficial: Keycloak Management Interface, Health Checks e Server Administration Guide.
- A documentacao oficial do Kong Gateway 3.14 indica que `/status/ready` responde `200` quando a configuracao valida foi carregada e o gateway esta pronto para trafego; isso combina com os probes atuais do `kong-deployment`. Fonte oficial: Kong Health Check Probes.
- A documentacao oficial do OAuth2-Proxy 7.15.x mantem `/ping` e `/ready` como endpoints padrao de health, `api_routes` retornando `401` quando nao autenticadas e `403` para JWT invalido quando `bearer_token_login_fallback=false`. Isso sustenta a documentacao atual do fluxo protegido e os checks do deployment. Fonte oficial: OAuth2-Proxy Overview e Behaviour 7.15.x.

### Projeto Contexto de Referencia

- Regras permanentes carregadas do `project-context.md`: nomes em `kebab-case`, GitOps estrito, nenhum segredo versionado, docs em pt-BR e nada de acoplamento com `.tracker/`.
- Companions utilizados nesta story: `planning.md`, `architecture-status.md`, `implementation-rules.md` e `deferred-work.md`.
- UX nao se aplica: plataforma backend/infra sem artefato UX associado.

## Plano de Validacao Manual

**1. Validar a sequencia de bootstrap do documento contra o comportamento real atual**

```bash
sed -n '1,260p' docs/bootstrap-emergencia.md
sed -n '1,260p' scripts/cluster-up.sh
sed -n '1,260p' scripts/inject-secrets.sh
```

Esperado: a ordem documentada bate com a ordem real dos scripts; nomes de namespaces, secrets e applications estao consistentes.

**2. Validar a reinstalacao idempotente dos secrets obrigatorios**

```bash
make secrets
kubectl get secrets -n keycloak-auth
kubectl get secrets -n kong-gateway
```

Esperado: existem `keycloak-db-secret`, `keycloak-admin-secret`, `kong-tls-secret` e `oauth2-proxy-secret`, sem necessidade de salvar valores no Git.

**3. Validar a instalacao e estado do ArgoCD**

```bash
kubectl get ns argocd
kubectl get deploy -n argocd
kubectl wait --for=condition=Available -n argocd --timeout=180s deployment/argocd-server
kubectl get applications -n argocd
```

Esperado: namespace `argocd` presente, `argocd-server` disponivel, e as applications `root-app`, `infra-app` e `apps-app` visiveis.

**4. Validar os healthchecks reais dos componentes centrais**

```bash
kubectl exec -n keycloak-auth deploy/keycloak-deployment -- curl -sf http://localhost:9000/health/ready
kubectl exec -n kong-gateway deploy/kong-deployment -- curl -sf http://localhost:8100/status/ready
kubectl exec -n kong-gateway deploy/oauth2-proxy-deployment -- curl -sf http://localhost:4180/ready
```

Esperado: os tres comandos retornam sucesso HTTP.

**5. Validar o fluxo externo minimo pos-bootstrap**

```bash
curl -k -sf https://localhost/realms/cluster-local/.well-known/openid-configuration >/tmp/oidc.json
bash scripts/generate-token.sh
```

Esperado: discovery OIDC acessivel via Kong HTTPS e token M2M gerado com sucesso.

**6. Validar o caminho de restore documentado**

```bash
./scripts/pg-backup.sh
kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":false}}}}'
kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'
```

Esperado: backup gerado e `selfHeal` temporariamente desativado conforme o procedimento final documentado.

**7. Validar o retorno ao estado operacional**

```bash
make status
```

Esperado: resumo operacional indica cluster acessivel, componentes centrais prontos, URLs corretas e orientacao final coerente com o bootstrap de emergencia.

## Story Completion Status

- Status alvo para criacao do contexto: `ready-for-dev`
- Nota de conclusao desta etapa: `Ultimate context engine analysis completed - comprehensive developer guide created`

## Change Log

- 2026-05-29 15:17:22-03:00 | Story criada pelo workflow `bmad-create-story`, com contexto tecnico detalhado para consolidar o bootstrap de emergencia, restore e validacoes reais da fundacao GitOps. Status definido como `ready-for-dev`. | Autoria/Implementacao: GPT-5 Codex
- 2026-05-29 15:29:57-03:00 | Runbook de bootstrap de emergencia consolidado com reconstrucao total, recuperacao parcial, restore coerente de PostgreSQL/Keycloak, ajustes de contradicao em `docs/runbook-operacoes.md` e evidencias reais de validacao operacional registradas. Status atualizado para `review`. | Autoria/Implementacao: GPT-5 Codex

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `git pull origin main` executado com sucesso antes da implementacao: repositorio ja estava atualizado em relacao a `origin/main`.
- `git diff --check` executado com sucesso apos as edicoes, sem erros de whitespace ou conflitos estruturais.
- `kubectl get nodes` confirmou cluster local acessivel com `2/2 Ready`.
- `kubectl get applications -n argocd` confirmou `root-app`, `infra-app` e `apps-app` em `Synced` e `Healthy`.
- `make status` confirmou `argocd`, `keycloak-auth`, `kong-gateway` e `oauth2-proxy` como `Ready`, com emissao de token M2M funcional.
- `curl -k -sf https://localhost/realms/cluster-local/.well-known/openid-configuration` respondeu com discovery OIDC acessivel pela borda HTTPS local.
- Validacao da rota protegida: sem token retornou `401`; com token emitido por `scripts/generate-token.sh` retornou `200`.
- Healthchecks internos validados por `kubectl port-forward` + `curl` no host:
  - Keycloak `http://127.0.0.1:19000/health/ready` retornou JSON `UP`.
  - Kong `http://127.0.0.1:18100/status/ready` retornou `{"message":"ready"}`.
  - OAuth2-Proxy `http://127.0.0.1:14180/ready` retornou `OK`.
- Divergencia identificada durante a validacao: os containers atuais nao possuem `curl`, entao os checks internos documentados foram ajustados para `kubectl port-forward` + `curl`, que e o caminho realmente executavel no ambiente atual.

### Implementation Plan

- Reescrever `docs/bootstrap-emergencia.md` como runbook principal, alinhado aos scripts e manifests atuais.
- Corrigir divergencias reais com `docs/runbook-operacoes.md`, em especial o freeze/unfreeze de `root-app` e `infra-app`.
- Validar a coerencia final com `scripts/cluster-up.sh`, `scripts/inject-secrets.sh`, `scripts/pg-backup.sh`, `scripts/pg-restore.sh` e checks operacionais disponiveis no ambiente.

### Completion Notes List

- `docs/bootstrap-emergencia.md` foi reescrito como runbook principal de desastre, substituindo o framing de esqueleto por procedimentos verificaveis para reconstrucao total, recuperacao parcial, restore do PostgreSQL/Keycloak e validacao final.
- O bootstrap manual passou a refletir fielmente `scripts/cluster-up.sh`: aplicacao de `root-app`, `infra-app` e `apps-app` com override de `targetRevision`, e nao apenas do `root-app`.
- O fluxo de restore foi consolidado com congelamento e reativacao coerentes de `root-app` e `infra-app`, em linha com `scripts/pg-restore.sh` e com a protecao `prune` atual.
- `docs/runbook-operacoes.md` foi ajustado apenas onde havia contradicao real: agora aponta para `docs/bootstrap-emergencia.md` como runbook principal de desastre e voltou a incluir o freeze de `root-app` no restore.
- Os checks de saude internos passaram a usar `kubectl port-forward` + `curl` no host, porque a validacao real mostrou que as imagens atuais nao incluem `curl` para `kubectl exec`.
- Arquivos comparados na implementacao: `docs/bootstrap-emergencia.md`, `docs/runbook-operacoes.md`, `scripts/cluster-up.sh`, `scripts/inject-secrets.sh`, `scripts/pg-backup.sh`, `scripts/pg-restore.sh`, `cluster/bootstrap/root-app.yaml`, `cluster/bootstrap/infra-app.yaml`, `cluster/bootstrap/apps-app.yaml`, `cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml`, `cluster/infrastructure/kong-gateway/base/kong-deployment.yaml` e `cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-deployment.yaml`.

### File List

- `_bmad-output/implementation-artifacts/3-4-refinamento-bootstrap-emergencia.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `docs/bootstrap-emergencia.md`
- `docs/runbook-operacoes.md`

## References

- [Source: _bmad-output/planning-artifacts/epics.md#epico-3]
- [Source: _bmad-output/planning-artifacts/prd.md#jornada-2-engenheiro-de-plataforma-e-sre-cenario-de-desastre]
- [Source: _bmad-output/planning-artifacts/architecture.md#infraestrutura-e-implantacao]
- [Source: _bmad-output/project-context.md]
- [Source: _bmad-output/distillate-v2/implementation-rules.md]
- [Source: _bmad-output/distillate-v2/architecture-status.md]
- [Source: _bmad-output/distillate-v2/planning.md]
- [Source: _bmad-output/distillate-v2/deferred-work.md]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md]
- [Source: _bmad-output/implementation-artifacts/3-2-tls-validacao-jwks-rate-limit-default.md]
- [Source: _bmad-output/implementation-artifacts/3-3-script-token-feedback-terminal.md]
- [Source: docs/bootstrap-emergencia.md]
- [Source: docs/runbook-operacoes.md]
- [Source: scripts/cluster-up.sh]
- [Source: scripts/inject-secrets.sh]
- [Source: cluster/bootstrap/root-app.yaml]
- [Source: cluster/bootstrap/infra-app.yaml]
- [Source: cluster/infrastructure/keycloak-auth/base/keycloak-deployment.yaml]
- [Source: cluster/infrastructure/kong-gateway/base/kong-deployment.yaml]
- [Source: cluster/infrastructure/oauth2-proxy/base/oauth2-proxy-deployment.yaml]
- [Source: https://argo-cd.readthedocs.io/en/release-3.4/operator-manual/installation/]
- [Source: https://github.com/argoproj/argo-cd/blob/master/docs/getting_started.md]
- [Source: https://www.keycloak.org/observability/health]
- [Source: https://www.keycloak.org/server/management-interface]
- [Source: https://www.keycloak.org/docs/latest/server_admin/]
- [Source: https://docs.konghq.com/gateway/latest/production/monitoring/healthcheck-probes/]
- [Source: https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview/]
- [Source: https://oauth2-proxy.github.io/oauth2-proxy/behaviour/]

Autoria/Implementacao: GPT-5 Codex

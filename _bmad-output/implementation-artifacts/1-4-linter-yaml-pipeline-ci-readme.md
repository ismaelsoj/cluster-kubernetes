# Story 1.4: Linter YAML, Pipeline CI e README

Status: done

<!-- Note: A validação é opcional. Execute validate-create-story para checagem de qualidade antes do dev-story. -->

## Story

Como um Engenheiro de Plataforma,
Eu quero a validação automática de todos os manifestos e documentação clara de onboarding,
Para que erros de nomenclatura, labels ausentes, tags `latest` ou violações de segurança sejam detectados de forma precoce (localmente e na esteira) e novos membros se integrem sem atrito.

## Acceptance Criteria

1. **[LINT-SCRIPT-IMPLEMENTATION]** Dado que o script `scripts/lint.sh` está configurado para usar `kube-linter` e `kustomize`, quando executado (tanto de forma avulsa pelo `make lint` quanto pelo `make up`), então ele deve validar de forma recursiva todos os recursos gerados pelo `kustomize build` nos diretórios do cluster (incluindo `cluster/bootstrap/` e `cluster/infrastructure/`). A validação deve garantir de forma rígida:
   - **Nomenclatura Kubernetes**: Recursos e namespaces em `kebab-case` (`kebab-case-names-only`).
   - **Labels Obrigatórios**: Presença dos labels `app.kubernetes.io/name` (combinando com o app/componente), `app.kubernetes.io/component` (restrito aos valores: `api`, `database`, `identity-provider`, `gateway`, `worker`), e `app.kubernetes.io/part-of` (fixo como `cluster-kubernetes`).
   - **Proibição de Tags Imutáveis**: Nenhuma imagem Docker pode usar a tag `:latest` (FR20 / NFR-S02).
   - **Probes de Resiliência**: Presença obrigatória de `readinessProbe` e `livenessProbe` em Deployments (infraestrutura e stubs).
   - **Prevenção de Falso Verde ("Falso Positivo")**: O script deve executar o `kustomize build` e garantir que o número de manifestos gerados é superior a 0 (`manifest count > 0`) antes de passar no teste, para evitar que diretórios vazios ou bases com `resources: []` passem com falso verde.
   - **Fallback Zero-Friction (Docker)**: Se a ferramenta `kube-linter` não estiver instalada localmente no host do desenvolvedor, o script deve fazer fallback automático e transparente para rodar o linter via Docker usando a imagem estável e imutável `stackrox/kube-linter:v0.8.3` (ou versão superior estável de forma imutável, ex: `v0.8.3`), garantindo o princípio de atrito zero.
   - **Escape Hatch (SKIP_LINT)**: Implementar suporte à variável de ambiente `SKIP_LINT=1`. Se estiver setada como `1`, o script exibe um aviso em português e sai imediatamente com exit `0`, permitindo o bypass em situações de depuração extrema.

2. **[MAKE-UP-INTEGRATION]** Dado que o Makefile possui o alvo `lint` chamando `scripts/lint.sh`, quando o desenvolvedor executa `make up`, então o target `lint` deve ser disparado como pré-condição obrigatória. Se qualquer violação for detectada na validação e a variável `SKIP_LINT` não for `1`, o processo `make up` deve falhar imediatamente (exit code não nulo) no console com erro compreensível em português, impedindo que manifestos errados cheguem ao cluster local.

3. **[CI-PIPELINE]** Dado o repositório git versionado no GitHub, quando novos commits forem enviados (push) para qualquer branch ou Pull Requests forem abertos contra a branch `main`, então o workflow do GitHub Actions em `.github/workflows/lint.yml` deve rodar o mesmo `kube-linter` sobre todos os manifestos YAML como um gate de qualidade mandatório. O workflow deve incorporar as seguintes regras de hardening e resiliência (conforme triagem diferida da Story 1.1):
   - **Suporte a Branches com Barras**: Configurar o gatilho `push: branches: ["**"]` (glob de duas estrelas `**` para casar caminhos com separadores de barras `/`, como `feature/1-2-cluster`, que o glob `*` simples ignora).
   - **Princípio do Menor Privilégio (Least Privilege)**: Declarar explicitamente no workflow o bloco `permissions: contents: read` para garantir o acesso estritamente necessário.
   - **Hardening de Supply Chain**: Usar a ação `actions/checkout` fixada por commit SHA (ex: `actions/checkout@692973e3d937129bcbf40652eb9f2f61becf33db` # v4.1.7 ou similar) e desativar explicitamente a persistência de credenciais do Git no runner via `persist-credentials: false`.
   - **Prevenção de Jobs Concorrentes**: Adicionar um grupo de `concurrency` baseado no workflow e branch para abortar automaticamente runs concorrentes pendentes na mesma branch quando um novo commit for enviado.
   - **Timeout de Segurança**: Definir um limite rígido de tempo de execução (`timeout-minutes: 10` ou similar) no job de lint para mitigar runners travados infinitamente em caso de erro na ferramenta de análise.

4. **[README-ONBOARDING]** Dado que um novo desenvolvedor ou SRE clona o repositório, quando ele ler o arquivo `README.md` na raiz do projeto, então o documento deve conter instruções claras de onboarding pt-BR de atrito zero que listam detalhadamente os pré-requisitos necessários (Docker, kubectl, k3d, make, e WSL2 se no Windows), o comando rápido para inicialização e teste (`make up`), comandos do Makefile suportados em formato de tabela, e links diretos explícitos para o Contrato do Desenvolvedor (`docs/contrato-do-desenvolvedor.md`), para o Bootstrap de Emergência (`docs/bootstrap-emergencia.md`) e para a Decisão de Arquitetura (`_bmad-output/planning-artifacts/architecture.md`).

5. **[HYGIENE-AND-CROSS-CUTTING]** Dado a hygiene geral do repositório, quando as alterações da Story 1.4 forem commitadas, então devem ser sanados os itens cross-cutting diferidos na Story 1.1:
   - **Higiene do Git (.gitignore)**: Criar o `.gitignore` na raiz do projeto contendo exclusões padrão do ecossistema Kubernetes local e desenvolvimento (kubeconfigs temporários, `.kube`, chaves locais, dumps `.sql`, logs, diretórios temporários).
   - **Higiene Windows (.gitattributes)**: Criar o `.gitattributes` na raiz do projeto contendo regras estritas para forçar finais de linha LF (`* text eol=lf`) nos arquivos shell `*.sh` e `Makefile`, garantindo compatibilidade total no Windows/WSL2 e prevenindo erros clássicos no Windows/WSL2 causados pela conversão de final de linha CRLF (`\r\n`), bem como garantir que o bit de execução dos scripts em `/scripts/*.sh` seja mantido no Git.

## Tasks / Subtasks

- [x] **Tarefa 1: Implementar o script `scripts/lint.sh` completo** (AC: #1)
  - [x] Adicionar suporte à verificação e bypass imediato se `SKIP_LINT=1` estiver setada no topo do script.
  - [x] Implementar a lógica de busca local do binário `kube-linter`.
  - [x] Se `kube-linter` não for encontrado no PATH, implementar o fallback transparente via Docker:
    - [x] Rodar container `docker run --rm -v "$(pwd):/dir" stackrox/kube-linter:v0.8.3 lint /dir/cluster/` (com fallback para v0.8.3 estável e imutável).
  - [x] Garantir que o linter valide manifestos gerados pelo `kustomize build` para todas as pastas de infraestrutura (`cluster/infrastructure/namespaces`, `cluster/infrastructure/keycloak-auth`, `cluster/infrastructure/kong-gateway`, etc.).
  - [x] Adicionar guarda anti-"Falso Verde": ler o output do `kustomize build` e garantir que o número de manifestos compilados é maior que 0 (`grep -c "kind:"` ou similar). Abortar com erro se 0 objetos forem encontrados para lint.
  - [x] Garantir que o script retorne exit code não nulo se violações de nomenclatura, labels ausentes, tags `:latest` ou falta de probes forem detectadas.

- [x] **Tarefa 2: Integrar o Linter no Makefile e Validar Localmente** (AC: #2)
  - [x] Garantir que o Makefile declare os targets `.PHONY: lint` e `up: lint` de forma robusta e idempotente.
  - [x] Adicionar um target de escape no Makefile (ex: `make up-force` que roda `SKIP_LINT=1 make up`) para dar flexibilidade ao desenvolvedor.
  - [x] Criar um manifesto temporário inválido (ex: com tag `latest` ou com nome do namespace em `PascalCase` ou sem probes) no diretório de infraestrutura ou apps e validar se `make up` e `make lint` bloqueiam o provisionamento local imediatamente e reportam o erro. Deletar o manifesto de teste após a validação.

- [x] **Tarefa 3: Implementar o workflow de CI em `.github/workflows/lint.yml`** (AC: #3)
  - [x] Atualizar `.github/workflows/lint.yml` com a automação real de lint.
  - [x] Usar Gatilho `push: branches: ["**"]` para suportar corretamente branches com barras de separação.
  - [x] Declarar bloco `permissions: contents: read` para Least Privilege.
  - [x] Pinar `actions/checkout` por SHA de commit estável (`actions/checkout@692973e3d937129bcbf40652eb9f2f61becf33db` # v4.1.7) com `persist-credentials: false`.
  - [x] Integrar a execução do kube-linter na esteira de CI executando a esteira de lint unificada do repositório local.
  - [x] Adicionar o bloco de `concurrency` para cancelar execuções concorrentes na mesma branch/workflow.
  - [x] Configurar `timeout-minutes: 10` (ou similar de segurança) no job do runner do GitHub.

- [x] **Tarefa 4: Atualizar e Enriquecer o `README.md`** (AC: #4)
  - [x] Revisar o `README.md` mantendo as instruções em português e o guia para WSL2 no Windows.
  - [x] Adicionar na tabela de comandos Makefile os alvos `make lint`, `make status` e `make up-force` na íntegra.
  - [x] Incluir hiperlinks diretos explícitos para o Contrato do Desenvolvedor (`docs/contrato-do-desenvolvedor.md`), para o Bootstrap de Emergência (`docs/bootstrap-emergencia.md`) e para a Decisão de Arquitetura (`_bmad-output/planning-artifacts/architecture.md`).

- [x] **Tarefa 5: Implementar a Hygiene de Repositório (.gitignore, .gitattributes, migração de Kustomize)** (AC: #5)
  - [x] Criar o `.gitignore` na raiz do repositório contendo exclusões padrão do ecossistema Kubernetes local e desenvolvimento.
  - [x] Criar o `.gitattributes` na raiz para forçar finais de linha LF (`* text eol=lf`) nos arquivos shell `*.sh` e `Makefile`, garantindo compatibilidade total no Windows/WSL2 e preservando permissões de execução (+x).
  - [x] Migrar em todos os manifestos de stubs Kustomize a diretiva obsoleta `apiVersion: kustomize.config.k8s.io/v1beta1` para `apiVersion: kustomize.config.k8s.io/v1` para evitar avisos futuros de obsolescência das novas versões. *Nota: Revertido para v1beta1 devido à restrição estrita do compilador local kubectl kustomize v1.34.1 que crasheia em v1.*iVersion: kustomize.config.k8s.io/v1beta1` para `apiVersion: kustomize.config.k8s.io/v1` para evitar avisos futuros de obsolescência das novas versões.

## Dev Notes

### Padrões e Regras Críticas do `kube-linter` e `Kustomize`

- **Prevenção de Falso Verde (Recurso Vazio)**: Em kustomize v5+, bases sem resources (`resources: []` ou apenas diretórios vazios) geram 0 bytes de manifestos. O `kube-linter` avalia 0 bytes e diz "0 violations", o que é um falso positivo (falso verde). O script `lint.sh` deve contar os objetos utilizando uma lógica como `grep -c "kind:"` ou similar sobre o output consolidado antes de submetê-lo ao `kube-linter`, abortando imediatamente com erro se o compilado estiver vazio.
- **Pinning de Versões**: Em conformidade absoluta com o "Secure by Default" e "Tags Imutáveis", o `kube-linter` utilizado na esteira de CI ou via Docker local deve ter sua tag/versão estritamente pinada (ex: `stackrox/kube-linter:v0.8.3` e `actions/checkout@692973e3d937129bcbf40652eb9f2f61becf33db`).
- **Segurança da Supply Chain (GitHub Actions)**: Pinar por SHA previne ataques de supply chain caso tags de major version (como `@v4`) sejam sequestradas ou modificadas na marketplace do GitHub. A desativação de persist-credentials impede que scripts arbitrários roubem o token de acesso GitHub injetado implicitamente no runner.

### Aprendizados das Stories Anteriores (Story 1.3)

Durante a implementação da Story 1.3, enfrentamos 4 incidentes críticos de conciliação do ArgoCD local devido a drift de branch e conflito de CRDs gigantes:
1. **CRD gigantesco do ArgoCD (`applicationsets`)**: o `kubectl apply` normal falhava por estourar o limite de 256KB da annotation de last-applied-configuration. A solução adotada foi mudar a instalação no `cluster-up.sh` para usar server-side apply:
   `kubectl apply --server-side=true --force-conflicts -n argocd -f <manifest-url>`
   Essa abordagem deve ser mantida, e manifestos gigantescos futuros devem ser aplicados dessa mesma forma.
2. **Drift de Branch Local (`ARGO_TARGET_BRANCH`)**: Para evitar que o ArgoCD sobrescreva as configurações locais apontando para `main` (branch canônica) em vez de branches de desenvolvimento local, o script `cluster-up.sh` foi refatorado para usar `sed` e substituir `targetRevision: main` pela branch local nos 3 manifestos de bootstrap (`root-app`, `infra-app` e `apps-app`).
3. **Respeito a Ignore Differences**: Foi necessária a adição de `RespectIgnoreDifferences=true` e `ignoreDifferences` no `root-app.yaml` para impedir o auto-heal de reverter os targetRevision dos apps filhos para a branch principal.
4. **Bootstrap Out-of-band**: Para eliminar um `OutOfSync` cosmético infinito, o `root-app.yaml` foi excluído do auto-gerenciamento do GitOps. Ele é aplicado exclusivamente via `cluster-up.sh` e gerenciado fora da esteira regular do ArgoCD.

Qualquer manifesto modificado nesta Story deve respeitar rigorosamente essas diretrizes funcionais e arquiteturais.

### Project Structure Notes

- **Nomenclatura Kubernetes**: A convenção universal é `kebab-case` para tudo (namespaces, diretórios, deploy, configs).
- **Comentários pt-BR**: O cabeçalho dos novos manifestos e arquivos criados nesta Story deve obrigatoriamente possuir comentário inicial descritivo em português.
- **Localização de Arquivos**: O script de linter deve residir exclusivamente em `scripts/lint.sh` e o workflow em `.github/workflows/lint.yml`.

### References

- [Regras de Formatação e Padrões de YAML](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/project-context.md#yaml-format)
- [Regras de Linter YAML e Tags Imutáveis](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/project-context.md#regras-críticas--o-que-não-fazer)
- [Diretrizes de Automação de Ciclo de Vida](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/planning-artifacts/architecture.md#integração-de-workflow-de-desenvolvimento)
- [BDD da Story 1.4](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/planning-artifacts/epics.md#story-14-linter-yaml-pipeline-ci-readme)
- [Itens Diferidos para a Story 1.4](file:///Users/ismael/git/cluster-kubernetes/_bmad-output/implementation-artifacts/deferred-work.md#diferido-para-story-14-linter-real--ci-hardening)

## Dev Agent Record

### Agent Model Used

gemini-3-flash (via /bmad-create-story)

### Debug Log References

### Completion Notes List

### File List

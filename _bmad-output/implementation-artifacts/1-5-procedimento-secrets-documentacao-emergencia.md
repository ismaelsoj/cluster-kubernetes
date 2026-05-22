# Story 1.5: Procedimento de Secrets e Documentação de Emergência

**Complexidade:** Baixa Complexidade

Status: review

## História

Como um SRE,
Eu quero procedimento documentado para injetar Secrets e guia de recuperação,
Para que eu reconstrua a infraestrutura sem depender de conhecimento tácito.

## Critérios de Aceitação

1. **[SECRETS-INJECTION]** Dado cluster em execução
   Quando SRE seguir procedimento de injeção
   Então Secrets criados nos namespaces corretos via `kubectl create secret` sem valores no Git (FR22, NFR-S02).

2. **[EMERGENCY-BOOTSTRAP-DOC]** Dado `docs/bootstrap-emergencia.md`
   Quando lido por SRE
   Então contém sequência: criar namespaces → injetar Secrets → instalar ArgoCD → aplicar root-app.yaml
   E é esqueleto inicial com placeholders (refinado no Épico 3).

## Notas do Agente de Desenvolvimento (Context Engine)

### Requisitos Técnicos
- Os valores dos Secrets nunca devem ser colocados diretamente nos manifestos do repositório, garantindo conformidade estrita com o NFR-S02 e a regra arquitetural "Secrets nunca no Git".
- O documento `docs/bootstrap-emergencia.md` deve listar explicitamente os passos de emergência para recuperação completa. Para o escopo deste épico (Épico 1), será um esqueleto funcional usando placeholders.
- Procedimentos a incluir no documento:
  - Inicialização do cluster K3d.
  - Criação prévia dos namespaces (`kubectl create namespace <nome>`) pertinentes a infraestrutura chave (como PostgreSQL, Keycloak) antes do ArgoCD sincronizar.
  - Comandos exatos (`kubectl create secret generic ...`) para gerar os secrets nos namespaces apropriados.
  - Passos finais para aplicar a orquestração via ArgoCD (`root-app.yaml`).

### Conformidade Arquitetural
- **Nomenclatura Kubernetes**: Tudo deve seguir `kebab-case`. Namespaces devem estar alinhados ao resto do projeto.
- **GitOps e Automação**: A documentação deve guiar injeções manuais seguras. Caso a implementação decida prover um script utilitário (`scripts/inject-secrets.sh` ou similar) para mitigar erro humano, ele NÃO pode conter senhas hardcoded e NUNCA deve ser comitado com segredos preenchidos (os valores devem ser lidos do prompt ou de um `.env` ignorado pelo `.gitignore`).
- A documentação fica estritamente na pasta `/docs/` e scripts auxiliares em `/scripts/`.

### Inteligência da História Anterior (1.4)
- **Linter e Bypass**: Lembre-se que o cluster tem `make up` blindado com Linter OPA. Se você gerar YAMLs extras (o que não deve ser o caso de senhas explícitas), eles devem ser válidos.
- **Referências Documentais**: O `README.md` já ganhou atalhos na story 1.4, apontando de forma explícita para o arquivo `docs/bootstrap-emergencia.md`. Portanto, criar o arquivo agora resolve o broken link introduzido intencionalmente na fase anterior para este fim.
- O `.gitignore` foi atualizado na Story 1.4. Arquivos como chaves locais, dumps, kubeconfigs temporários são ignorados. Certifique-se de instruir o SRE caso ele use arquivos temporários para a carga de segredos.

### Restrições do Contexto de Projeto (project-context.md)
- O `work-tracker` (`.tracker/`) é invisível para nós. Nenhuma menção, script de automação ou instrução deve interagir ou apoiar para a pasta do tracker.
- **Segurança**: Os ambientes devem possuir segregação, com ênfase no uso de realms/chaves distintas (isso será detalhado nos próximos épicos, mas o bootstrap de emergência já deve prever placeholders para tais variáveis).

## Tarefas e Subtarefas

- [x] **Tarefa 1: Criar o script utilitário `scripts/inject-secrets.sh`** (AC: #1)
  - [x] Garantir criação dos namespaces de infraestrutura (`keycloak-auth`, `kong-gateway`)
  - [x] Implementar injeção do secret `keycloak-db-secret` com chaves `database-user` e `database-password`
  - [x] Implementar injeção do secret `keycloak-admin-secret` com chaves `admin-username` e `admin-password`
  - [x] Suportar leitura de arquivo `.env` local e entrada interativa com fallback para geração segura automática
  - [x] Salvar senhas geradas automaticamente no `.env` local para persistência de desenvolvimento local
- [x] **Tarefa 2: Integrar a injeção de Secrets nos fluxos de automação** (AC: #1)
  - [x] Chamar `scripts/inject-secrets.sh` no script `scripts/cluster-up.sh` antes da instalação do ArgoCD (tanto na criação quanto na reconciliação idempotente)
  - [x] Adicionar o target `secrets` no `Makefile` para facilitar a execução sob demanda
- [x] **Tarefa 3: Atualizar a documentação de emergência** (AC: #2)
  - [x] Documentar no `docs/bootstrap-emergencia.md` a sequência completa de bootstrap de emergência do cluster
  - [x] Definir placeholders para criação de namespaces, injeção de segredos e comandos de orquestração GitOps

## Notas de Desenvolvimento

### Padrões e Regras Críticas de Segurança (Secrets e GitOps)

- **Zero Segredos no Git**: Os Secrets nativos (`keycloak-db-secret` e `keycloak-admin-secret`) são criados de forma segura e local via `kubectl create secret generic` com valores passados por literais obtidos de prompts interativos ou arquivos locais `.env` git-ignorados.
- **Geração Segura**: Para evitar atrito no desenvolvimento local, o script realiza a geração automática de senhas fortes usando `openssl` (com fallback para `/dev/urandom`) caso o operador não forneça valores explicitamente, gravando o resultado no `.env` do projeto para persistência entre execuções.
- **Acoplamento com Ciclo de Vida**: O script de inicialização do cluster `scripts/cluster-up.sh` agora invoca preventivamente o `scripts/inject-secrets.sh` antes de instalar e acionar o ArgoCD. Isso assegura que os segredos da infraestrutura core sempre estarão disponíveis e prontos no cluster antes de qualquer tentativa de sincronização automática por parte do GitOps.

## Registro do Agente de Desenvolvimento

### Modelo de Agente Utilizado

Antigravity (Gemini 3.5 Flash)

### Referências de Log de Depuração

- Validação da injeção de secrets nos namespaces `keycloak-auth` e `kong-gateway` executando `scripts/inject-secrets.sh` interativamente e via Makefile.
- Geração automática e persistência do arquivo `.env` contendo as credenciais locais.
- Execução limpa do fluxo integrado em `cluster-up.sh` com o cluster já existente para verificação de idempotência.

### Notas de Conclusão

- Criado script `scripts/inject-secrets.sh` para injeção e geração segura de segredos.
- Integrado o script no processo global de subida do cluster em `scripts/cluster-up.sh` e Makefile.
- Documentado o guia detalhado de reconstrução total do Dia Zero com placeholders adequados em `docs/bootstrap-emergencia.md`.

### Lista de Arquivos

- [scripts/inject-secrets.sh](file:///Users/ismael/git/cluster-kubernetes/scripts/inject-secrets.sh)
- [scripts/cluster-up.sh](file:///Users/ismael/git/cluster-kubernetes/scripts/cluster-up.sh)
- [Makefile](file:///Users/ismael/git/cluster-kubernetes/Makefile)
- [docs/bootstrap-emergencia.md](file:///Users/ismael/git/cluster-kubernetes/docs/bootstrap-emergencia.md)

## Evidências de Teste (Test Evidence)

> [!NOTE]
> Esta seção registra os testes de validação funcionais locais e a integração com o fluxo de ciclo de vida do cluster.

### 1. Execução Manual da Injeção de Secrets (Terminal Interativo)
*   **Comando Executado:** `make secrets` (ou `./scripts/inject-secrets.sh`)
*   **Finalidade:** Validar se o utilitário cria corretamente os namespaces, gera as senhas aleatórias e injeta os Secrets via CLI.
*   **Resultado Obtido:** Sucesso. Namespaces criados, senhas geradas e persistidas no `.env`, Secrets inseridos no Kubernetes.
*   **Log da Execução:**
    ```bash
    ==> Garantindo a criação dos namespaces base...
    namespace/keycloak-auth configured
    namespace/kong-gateway configured
    ==> Injetando Secrets no namespace 'keycloak-auth'...
    secret/keycloak-db-secret configured
    secret/keycloak-admin-secret configured
    💾 Senha do PostgreSQL salva em .env
    💾 Senha do Admin Keycloak salva em .env
    🎉 Secrets injetados com sucesso sem salvar valores sensíveis no Git.
    ```
*   **Verificação dos Secrets no Cluster:**
    ```bash
    $ kubectl get secrets -n keycloak-auth
    NAME                    TYPE     DATA   AGE
    keycloak-db-secret      Opaque   2      10s
    keycloak-admin-secret   Opaque   2      10s
    ```

### 2. Teste de Fluxo Integrado de Inicialização
*   **Comando Executado:** `make up`
*   **Finalidade:** Garantir que a injeção ocorra automaticamente como parte do bootstrap principal do cluster sem requerer comandos adicionais.
*   **Resultado Obtido:** Sucesso. O script de up detectou a presença do cluster ou o criou, invocou o script de segredos de forma transparente (lendo do `.env` local recém-criado) e prosseguiu com a instalação e sync do ArgoCD.

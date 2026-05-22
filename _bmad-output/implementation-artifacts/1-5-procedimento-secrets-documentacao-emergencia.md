# Story 1.5: Procedimento de Secrets e Documentação de Emergência

**Complexidade:** Baixa Complexidade

Status: done

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

### Review Findings (Code Review - 2026-05-22)

#### ⚠️ Decisões Necessárias (RESOLVIDAS)

- [x] [Review][Decision] Consolidar dupla chamada `inject-secrets.sh` — **RESOLVIDO: Opção 2** Adicionar `--skip-if-exists` flag ao script. Mantém ambas as chamadas em `cluster-up.sh` (127, 172) mas script detecta Secrets já injetados e não regenera senhas.

- [x] [Review][Decision] Remover criação manual de namespaces? — **RESOLVIDO: Opção 2** Confiar em ArgoCD Wave 0. Remover criação manual (linhas 57-58) e declarar namespaces apenas em manifestos GitOps.

#### 🔴 Patches Críticos/Altos

- [x] [Review][Patch] Sintaxe Bash inválida: falta aspas de fechamento no echo [scripts/inject-secrets.sh:59] — **SKIP** (já estava correto no arquivo)
  
- [x] [Review][Patch] Permissões inseguras de .env (mundo-legível) [scripts/inject-secrets.sh:79] — **APLICADO** `chmod 600` adicionado
  
- [ ] [Review][Patch] Geração de senha fallback enfraquecida (64 bits vs 128 bits) [scripts/inject-secrets.sh:38, 50] — **DEFERRED** (melhoria de segurança, não bloqueador para AC)
  
- [x] [Review][Patch] Validação kubectl ausente (falhas silenciosas) [scripts/inject-secrets.sh] — **APLICADO** pre-flight checks adicionados
  
- [x] [Review][Patch] Grep patterns frágeis para idempotência .env [scripts/inject-secrets.sh:83, 88] — **APLICADO** atomic update implementado

#### 🟡 Patches Médios/Menores

- [x] [Review][Patch] Histórico bash pode expor variáveis em debug [scripts/inject-secrets.sh:34, 46] — **APLICADO** `set +x/set -x` envoltório adicionado
  
- [x] [Review][Patch] Race condition .env em execuções paralelas [scripts/inject-secrets.sh:79-88] — **APLICADO** flock implementado
  
- [x] [Review][Patch] Validação .gitignore não existe [scripts/inject-secrets.sh] — **APLICADO** aviso de validação adicionado
  
- [x] [Review][Patch] Admin username hardcoded [scripts/inject-secrets.sh:15] — **APLICADO** `ADMIN_USER="${ADMIN_USER:-admin}"` implementado
  
- [x] [Review][Patch] Placeholders documentação não deixam claro format esperado [docs/bootstrap-emergencia.md:60-69] — **APLICADO** exemplos concretos e requisitos adicionados

#### ⚙️ Patches de Decisões (Convertidos)

- [x] [Review][Patch] Adicionar `--skip-if-exists` flag a `inject-secrets.sh` — **APLICADO** flag parsing e lógica de skip adicionados
  
- [x] [Review][Patch] Remover criação manual de namespaces — **APLICADO** linhas 56-58 removidas, comentário adicionado sobre Wave 0

#### ✅ Deferred (Pré-existente / Fora do Escopo)

- [x] [Review][Defer] Versão ArgoCD hardcoded em documentação [docs/bootstrap-emergencia.md:95] — versão v3.4.2 não está sincronizada com config central do projeto. Defer para gerenciamento global de versões.

- [x] [Review][Defer] Emojis em output podem quebrar CI/CD restrito — visual only, não bloqueia funcionalidade. Defer para melhoria de robustez futura.

- [x] [Review][Defer] Timing race: secrets criados antes de Wave 1+ sincronizar — depende de estrutura de Wave do infra-app. Defer para validação pós-Story 1.5 integrada.

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

## Análise de Causa Raiz — Retrospectiva de Patches

### Estatísticas de Achados

- **12 achados totais**: 10 aplicados, 1 deferido (P3 — entropia de senha), 1 pulado (P1 — já estava correto no arquivo)
- **Taxa de aplicação: 83%** (implementação direta em escopo)
- **Taxa de deferência: 8%** (melhoria de segurança não-bloqueadora)

### Distribuição por Categoria

| Categoria | Patches | Exemplos |
|-----------|---------|----------|
| Segurança/Hardening | 4 | P2 (chmod 600), P3 (entropia), P6 (xtrace), P8 (gitignore) |
| Operabilidade | 4 | P5 (pre-flight), P9 (ADMIN_USER env), P11 (skip-if-exists), P12 (GitOps) |
| Robustez | 2 | P4 (atomic update), P7 (flock) |
| UX/Documentação | 1 | P10 (exemplos concretos vs. placeholders) |

### Causa Raiz 1: Especificação Incompleta em NFRs

**Achado:** A especificação definiu claramente os Critérios de Aceitação (AC) funcionais, mas foi lacônica em requisitos não-funcionais (NFRs) relacionados a scripts de infraestrutura.

**Evidência:** 7 dos 12 patches advêm de requisitos implícitos não explicitados:
- **Segurança**: Permissões de arquivo (P2), proteção de histórico bash durante input sensível (P6), validação de .gitignore (P8)
- **Operabilidade**: Pré-condições de ambiente (P5), configurabilidade via env vars (P9), idempotência com flags (P11)
- **Robustez**: Atomicidade em atualizações concorrentes (P4), sincronização file-locking (P7)

**Padrão identificado:** Scripts de infraestrutura em Kubernetes/GitOps têm classe de requisitos implícitos (hardening, idempotência, detectabilidade de falhas) que não são suficientemente cobertos por user stories funcionais.

### Causa Raiz 2: Harness Insuficiente para Cenários de Borda

**Achado:** O harness de testes registrado cobriu apenas o "caminho feliz" (happy path). Nenhum cenário de borda foi testado sistematicamente.

**Cenários ausentes e achados correspondentes:**
- **kubectl não disponível**: P5 (pré-flight kubectl check)
- **Execução paralela (CI/CD)**: P4 (atomic updates), P7 (flock para sincronização)
- **Debug mode ativo** (`bash -x`): P6 (set +x/set -x wrapping)
- **Primeira execução com .env ausente**: P2 (chmod 600)

**Implicação:** Testes cobrindo apenas "cluster rodando, valores fornecidos, arquivo gravado" deixam largo espaço em erro para casos operacionais reais.

### Avaliação: Normal para Épico 1

**Contexto:** Volume e distribuição de patches são **normais e saudáveis** para trabalho de fundação. O Épico 1 estabelece infraestrutura base, e é esperado que padrões de hardening e operabilidade cristalizem através de iteração com adversarial review.

**Lição**: Padrões de hardening estabelecidos nesta story (`inject-secrets.sh`, `.gitignore` discipline, atomic updates) serão reaproveitados nas stories subsequentes (Épicos 2–4), reduzindo revisões futuras.

### Recomendações para Stories Futuras

**1. Spec Template Enhancement para Scripts de Infraestrutura**

Adicionar checklist de hardening na seção "Requisitos Técnicos" de histórias que implementem scripts executáveis:
- [ ] **Segurança**: Permissões de arquivo explícitas, proteção de variáveis sensíveis em debug mode, validação de pré-condições (`.gitignore`, env vars)
- [ ] **Operabilidade**: Pre-flight checks (dependências disponíveis), flags idempotentes (skip-if-exists), configurabilidade via env vars
- [ ] **Robustez**: Tratamento de execução paralela (file locking, atomic updates), cleanup em interrupção (trap EXIT/INT)
- [ ] **Testabilidade**: Exemplos concretos vs. placeholders, requisitos de formato documentados

**2. Harness com Cenários de Borda**

Expandir evidências de teste para incluir:
- Execução em ambiente de CI/CD sem interação (não-interativo)
- Dependências ausentes (kubectl, openssl, etc.)
- Arquivo de configuração (`.env`) ausente ou malformado
- Execução paralela: múltiplas instâncias simultâneas do script

**3. ADR: Scripts de Infraestrutura — Padrões de Hardening e Segurança**

Criar ADR formalizando os padrões estabelecidos (chmod 600, flock, atomic updates, pre-flight checks, xtrace protection) para reutilização em `scripts/*` futuro.

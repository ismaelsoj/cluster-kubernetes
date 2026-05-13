---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
releaseMode: phased
inputDocuments:
  - _bmad-output/planning-artifacts/research/technical-local-kubernetes-cluster-kong-keycloak-research-2026-05-11.md
workflowType: 'prd'
classification:
  projectType: Plataforma de Infraestrutura e Integração (API Gateway & Identity Management)
  domain: Platform Engineering / SecOps / Cloud-Native
  complexity: Alta
  projectContext: Greenfield On-Premise
---

# Documento de Requisitos do Produto (PRD) - cluster-kubernetes

**Autor:** Ismael
**Data:** 2026-05-11

## Resumo Executivo (Executive Summary)

A plataforma tem como visão estabelecer uma Infraestrutura de Integrações On-Premise segura, previsível e escalável, projetada para garantir que todas as APIs corporativas sejam roteadas por um Gateway único (Kong) e protegidas nativamente por autenticação OIDC (Keycloak). A plataforma soluciona o desafio crítico de gerenciar o perímetro de segurança sob um modelo "Zero-Trust" sem asfixiar a produtividade das equipes de negócio. Através de uma fundação imutável baseada em GitOps (ArgoCD), o projeto estabelece uma fundação resiliente para integrações, mantendo a integridade da autenticação sem abrir exceções arquiteturais para sistemas legados cruzados.

### O que Torna Isso Especial (What Makes This Special)

O principal diferencial da plataforma é o equilíbrio absoluto entre resiliência operacional e paridade de ambientes. Operacionalmente, a escolha consciente por um Gateway *Stateless* (Kong DB-Less com OAuth2-Proxy) extirpa o risco de operar e manter múltiplos bancos de dados Stateful num datacenter físico. Para a Experiência do Desenvolvedor (DevEx), o produto se destaca pela garantia de paridade local: através da automação via scripts `k3d` e do uso de repositórios de Boilerplates validados, as equipes de desenvolvimento conseguem subir, testar e debugar o fluxo completo de segurança (incluindo OIDC) em suas próprias máquinas de forma idêntica à produção On-Premise. Isso oculta a complexidade árdua do Kubernetes e viabiliza a geração de código assistida por Inteligência Artificial (BMad) com atrito quase nulo.

## Classificação do Projeto (Project Classification)

- **Tipo de Projeto:** Plataforma de Infraestrutura e Integração (API Gateway & Gestão de Identidade) focada na entrega da fundação técnica na v1, alavancada por Boilerplates e fluxos de trabalho assistidos por IA.
- **Domínio:** Platform Engineering / SecOps / Cloud-Native (On-Premise) aderente aos princípios Zero-Trust (validação JWT interna) com planos explícitos de contingência para Segredos K8s manuais.
- **Complexidade:** Alta na infraestrutura base. Riscos mitigados pela exigência de automação de terminal (comando único `make up`) e diretrizes de infraestrutura críticas: Configuração obrigatória de Edge Proxy, QoS estrito de Recursos e versão Imutável de Tags Docker.
- **Contexto do Projeto:** Greenfield On-Premise (Servidores Físicos). O projeto seguirá um roteiro tático em 4 fases interconectadas: (1) Fundação Local e Gestão de Segredos Manuais; (2) GitOps da Tríade Base (Postgres, Keycloak, Kong DB-Less) com governança "Safe-Prune" e rotina de Backups; (3) Integração Security Glue (OAuth2-Proxy e SSO no ArgoCD); e (4) Habilitação do Desenvolvedor através de Boilerplates padronizados.

## Critérios de Sucesso (Success Criteria)

### Sucesso do Usuário (Desenvolvedores)

- **Fricção Zero Local:** Um desenvolvedor consegue subir o ambiente completo (`k3d`, Kong, Keycloak, Postgres) em sua máquina com um único comando (ex: `make up`) em menos de 5 minutos, garantindo paridade total com a produção.
- **Integração Descomplicada:** Desenvolvedores conseguem publicar uma nova API de negócios em produção utilizando apenas os *Boilerplates YAML* fornecidos, sem precisar de suporte da equipe de Plataforma para debugar fluxos OIDC/OAuth2.

### Sucesso do Negócio (Business Success)

- **Segurança de Perímetro Unificada:** 100% das novas APIs roteadas pela plataforma exigem autenticação centralizada no Keycloak (Zero-Trust), eliminando "rotas fantasmas" sem proteção.
- **Otimização de Custos de Licença:** O projeto entrega as capacidades de um API Gateway corporativo com OIDC mantendo-se 100% Open-Source (Kong DB-Less + OAuth2-Proxy), sem necessidade de licenças Enterprise.
- **Governança Segura On-Premise:** O modelo GitOps (ArgoCD *Pull-based*) opera sem a necessidade de abrir portas de firewall de entrada no datacenter corporativo.

### Sucesso Técnico (Technical Success)

- **Resiliência Stateless:** O API Gateway (Kong) opera exclusivamente em modo DB-Less (Stateless), garantindo escalabilidade instantânea e reduzindo os bancos de dados Stateful da infraestrutura base para apenas um (PostgreSQL do Keycloak).
- **Proteção contra Desastres:** Implementação comprovada de diretrizes de sobrevivência, incluindo "Safe-Prune" no ArgoCD e rotinas automáticas de backup externo para o banco de dados da identidade.
- **Previsibilidade de Recursos:** 100% dos manifestos de infraestrutura e boilerplates possuem Resource Quotas (Limites de CPU/Memória) rígidos e tags de versão Docker imutáveis (proibido o uso da tag `latest`).

### Resultados Mensuráveis (Measurable Outcomes)

- **Tempo de Setup Local (MTTS):** Reduzido para < 5 minutos via scripts de automação.
- **Tempo de Onboarding de Nova API:** < 1 hora de esforço para um desenvolvedor utilizando os Boilerplates.
- **Disponibilidade da Identidade:** RTO (Recovery Time Objective) do banco do Keycloak e dos *Secrets* testado e documentado para cenários de queda do servidor.

## Escopo do Produto (Product Scope)

### MVP - Produto Mínimo Viável (Fase 1)

O escopo essencial para provar o valor e estabelecer a fundação técnica:
- Automação do ambiente local (`k3d up/down`).
- Deploy manual de Secrets base no cluster On-Premise.
- Deploy GitOps da Tríade de Infraestrutura (Postgres, Keycloak Oficial, Kong DB-Less) via ArgoCD.
- Interceptação de Segurança (Security Glue) via OAuth2-Proxy validando tokens OIDC.
- Criação e homologação do primeiro repositório de *Boilerplates YAML* com uma API de teste.

### Funcionalidades de Crescimento (Pós-MVP)

O que torna o projeto pronto para escalar o uso na empresa:
- Pipelines de CI (GitHub Actions) integradas para construir imagens das APIs e atualizar as tags no repositório GitOps automaticamente.
- Desenvolvimento de Middlewares ou sidecars dedicados para permitir a autenticação segura de sistemas legados de fábrica (que não suportam OIDC nativamente).
- Deploy de pilha de Observabilidade mínima (Prometheus/Grafana) lendo as métricas `/metrics` do Kong e Keycloak.

### Visão de Futuro (Vision)

A evolução máxima da Plataforma (O "Sonho"):
- Implementação de um Portal de Desenvolvedor (ex: Backstage) oferecendo uma abstração *Self-Service* visual, escondendo completamente os YAMLs e o ArgoCD.
- Implementação de Service Mesh (ex: Linkerd) para controle granular de tráfego interno (East-West).
- Centralização avançada de Logs via OpenSearch para auditoria unificada de toda a empresa.

## Jornadas de Usuário (User Journeys)

### Jornada 1: O Desenvolvedor de Aplicações (Validação M2M Local)
**Personagem:** Lucas (Dev Backend)
**Situação:** A equipe de Lucas desenvolveu um novo microsserviço de relatórios financeiros e precisa testá-lo protegido antes de mandar pra produção.
**A Jornada:**
1. **Setup:** Lucas roda `make up` em sua máquina. O cluster `k3d` sobe idêntico à produção, com o Kong e o Keycloak prontos, e o terminal imprime automaticamente um Token de Teste válido.
2. **Ação:** Ele adapta o *Boilerplate YAML* para a sua nova rota `/relatorios`.
3. **Clímax (O Teste Frio):** Lucas usa o Postman para disparar contra sua API local **sem informar o token**. Imediatamente, ele recebe um duro `401 Unauthorized` da infraestrutura. Satisfeito, ele repete a chamada, desta vez injetando o Token Bearer gerado pelo script. O tráfego flui e a API responde 200 OK.
4. **Resolução:** Com o bloqueio e a liberação validados localmente, ele commita o YAML. O ArgoCD implanta na produção. Em seguida, ele apenas aciona o Admin do Keycloak da empresa para que gere o Token de Aplicação oficial de produção e o entregue ao sistema cliente.

### Jornada 2: Engenheiro de Plataforma e SRE (Cenário de Desastre)
**Personagem:** Ismael (SRE/Arquiteto da Plataforma)
**Situação:** Sexta-feira, 22h. Um problema de hardware no Datacenter corrompe o disco local onde o banco de dados do Keycloak (PostgreSQL) estava rodando. Toda a autenticação da empresa cai.
**A Jornada:**
1. **O Impacto:** Sem banco de dados, o Keycloak quebra. O OAuth2-Proxy no Kong, sem ter a quem perguntar, barra 100% do tráfego das APIs. O alerta dispara.
2. **Contenção Segura:** Ismael não precisa se preocupar com o ArgoCD "deletando" coisas por pânico, pois a governança de *Safe-Prune* desativou deleções automáticas na fundação.
3. **Clímax (Recuperação):** Ele acessa o cofre de senhas corporativo seguro e copia as credenciais manuais (Secrets). Como a política de Backup Externo noturno estava ativa, Ismael restaura o estado do banco de dados no K8s.
4. **Resolução:** O Keycloak volta à vida, o ArgoCD garante que os manifestos do Kong estão perfeitos, e o tráfego volta a fluir em segurança. A fundação imutável salvou o fim de semana.

### Jornada 3: O Sistema Legado Cru (O Desafio de Integração Pós-Token)
**Personagem:** Robô do ERP de Fábrica
**Situação:** Um sistema antigo da fábrica, que não suporta a gestão de tokens dinâmicos (OIDC), precisa enviar notas para a nova API.
**A Jornada:**
1. **A Barreira:** O Robô tenta enviar os dados e recebe 401 Unauthorized, pois não consegue injetar o cabeçalho Bearer OIDC.
2. **O Ponto de Contato:** Eles acionam Ismael para pedir que "remova a segurança dessa rota".
3. **Clímax (Solução):** Ismael recusa baixar a régua Zero-Trust. Em vez disso, a plataforma provê um *Middleware de Integração* ou ativa um plugin específico no Kong para aquela rota, que traduz uma API Key estática do Robô para um Token de Aplicação válido por trás dos panos.
4. **Resolução:** O legado passa a enviar seus dados, a auditoria central do Keycloak registra o tráfego, e o bloqueio OIDC continua blindando a borda contra invasores.

### Resumo de Requisitos de Jornada (Journey Requirements Summary)
- O ambiente local (`Makefile`) deve gerar o Realm, o Client de teste e extrair o Token Bearer via `curl`, devolvendo-o diretamente no console.
- A arquitetura necessita focar primariamente na emissão e validação de tokens `Client Credentials` (M2M) em vez de fluxos `Authorization Code` com telas de login.
- A plataforma deve suportar plugins/middlewares de tradução de autenticação na borda (no Kong) para viabilizar sistemas legados sem quebrar o modelo Zero-Trust.

## Requisitos Específicos de Domínio (Domain-Specific Requirements)

### Conformidade e Regulação (Compliance & Regulatory)
- **Governança Pragmática de Acesso:** Sem *over-engineering*. O sistema usará os logs básicos e nativos do Keycloak (que já vêm embutidos) para fins de *troubleshooting* das emissões de token. Auditorias formais complexas (como aderência a ISO/SOC2) estão **fora do escopo** para evitar overhead de desenvolvimento e manutenção na V1.
- **Gestão de Segredos:** Devido à política estrita do GitOps (onde tudo no Git é texto plano), é terminantemente proibido versionar senhas. Segredos devem ser geridos manualmente e injetados diretamente no cluster.

### Restrições Técnicas (Technical Constraints)
- **Criptografia e Assinatura:** Todos os tokens (JWT) devem trafegar exclusivamente sobre HTTPS/TLS (terminação no Kong) e o Gateway deve validar a assinatura criptográfica do Keycloak antes de repassar o tráfego interno.
- **Alta Disponibilidade e Cota:** O Gateway e a Identidade são o coração do tráfego. As cotas de consumo de CPU/Memória (QoS) do Kong devem ter alta prioridade de agendamento no Kubernetes (PriorityClasses) para evitar paralisações no servidor On-Premise.

### Requisitos de Integração (Integration Requirements)
- **Padronização M2M:** A infraestrutura deve forçar o padrão OIDC *Client Credentials* para comunicação *Server-to-Server*.
- **Observabilidade Passiva:** A arquitetura deve expor portas de métricas padronizadas (`/metrics` no formato Prometheus) para que ferramentas de monitoramento futuras consigam ler o estado da rede facilmente.

### Mitigação de Riscos (Risk Mitigations)
- **Risco de Lockout Global:** Se o Identity Provider cair, toda a empresa para. *Mitigação:* Isolar o banco de dados do Keycloak com políticas agressivas de backup externo e proibir o ArgoCD de fazer `prune` (deleção) dos manifestos base do Ingress.

## Requisitos Técnicos da Plataforma (Platform-Specific Technical Requirements)

### Arquitetura de Autenticação (Auth Model)
- **Ciclo de Vida (MVP):** Emissão de tokens `Client Credentials` M2M com ciclo de vida (TTL) longo (ex: 1 ano), gerenciados pelo administrador do Keycloak. O objetivo é remover o atrito inicial de testes e integrações.
- **Backlog de Inovação:** Pesquisa e implementação de uma rotina de expiração curta com rotação automatizada de credenciais M2M.

### Política de Proteção de Tráfego (Rate Limits)
- **Gestão Descentralizada (*Secure by Default*):** O Gateway não imporá um estrangulamento global na borda. A proteção de *Rate Limiting* será delegada para cada aplicação. No entanto, para evitar erros humanos, o *Boilerplate YAML* base da plataforma virá obrigatoriamente com um limite conservador pré-configurado (ex: 100 req/min). Se o desenvolvedor não alterar nada, a infraestrutura já nasce protegida contra picos e abusos.

### Tratamento de Erros (Error Handling)
- **Bloqueio Limpo (MVP):** Requisições barradas pelo Gateway (por falta de autenticação OIDC ou estouro de cota) retornarão respostas HTTP padrão "cruas" (como `401 Unauthorized` ou `429 Too Many Requests`). O mapeamento para uma formatação corporativa padronizada de JSON de erro foi movido para o backlog.

### Especificação de Contratos (API Docs)
- **Padrão OpenAPI:** Todas as integrações utilizarão o padrão OpenAPI.
- **Bypass de Documentação por Ambiente:** O Gateway (Kong) será configurado para abrir exceção na regra de autenticação (Zero-Trust) especificamente para rotas de documentação (ex: `/swagger`, `/docs`), **mas apenas nos ambientes Local e de Homologação**, facilitando a descoberta por outros times. Em **Produção**, esse *bypass* não existirá, mantendo os contratos estruturais protegidos de acessos não autenticados.

## Escopo do Projeto e Desenvolvimento em Fases (Project Scoping & Phased Development)

### Estratégia e Filosofia do MVP
**Abordagem do MVP:** Plataforma de Fundação (Platform MVP). O objetivo é garantir que 1 API possa ser desenvolvida, testada localmente e implantada em produção através da esteira 100% segura, provando a viabilidade técnica do Kong + Keycloak + ArgoCD. Focaremos em estabilidade tática, adiando complexidades.
**Requisitos de Recursos (Time):** Pelo menos 1 Engenheiro de Plataforma Sênior (para setup Kubernetes/GitOps) e 1 Desenvolvedor para testar a integração inicial. A operação inicial será suportada pelo próprio administrador da plataforma.

### Escopo do MVP (Fase 1)
**Jornadas Core Suportadas:**
- Desenvolvedor testando API localmente com Automação M2M.
- Engenheiro (SRE) recuperando a infraestrutura em caso de desastres.

**Capacidades Críticas (Must-Haves da V1):**
- Cluster `k3d` automatizado gerando token de teste no terminal.
- Deploy GitOps On-Premise blindado pelo ArgoCD.
- Interceptação de tráfego com Kong + OAuth2-Proxy.
- Keycloak configurado para emitir Tokens *Client Credentials* de longo TTL.
- Repositório base com *Boilerplate YAML* contendo limite conservador de tráfego (Rate Limit default) e exceção de Swagger para ambientes não produtivos.

### Roadmap de Crescimento (Post-MVP)
**Fase 2 (Adoção Corporativa & Legados):**
- Implementação de Middlewares/Plugins no Kong para traduzir autenticação estática de sistemas Legados ERP (resolvendo a Jornada 3).
- Implementação da stack de Observabilidade (Prometheus/Grafana) conectada às rotas `/metrics`.
- Integração de CI (GitHub Actions) para automação de build e substituição de tags no ArgoCD.

**Fase 3 (Visão Expandida / "O Sonho"):**
- Portal de Desenvolvedor visual (Backstage).
- Rotação automatizada de curto prazo para credenciais M2M.
- Implementação de Service Mesh (Linkerd) para controle granular de tráfego.

### Estratégia de Mitigação de Riscos
- **Risco Técnico (Divergência de Ambientes):** *Mitigação:* Uso estrito do mesmo `k3d` base e dependência absoluta do repositório GitOps via ArgoCD para aplicar manifestos, evitando configurações manuais não rastreáveis.
- **Risco de Adoção (Fricção do Desenvolvedor):** *Mitigação:* Script de automação injetando o Token diretamente no terminal.
- **Risco de Recursos (Silo de Conhecimento):** *Mitigação:* O GitOps serve nativamente como "Documentação Executável".

## Requisitos Funcionais (Functional Requirements)

### 1. Gestão do Ambiente Local (Local DevEx)
- **FR01:** O Desenvolvedor deve ser capaz de provisionar um cluster Kubernetes local completo via comando único de automação (`make up`).
- **FR02:** O Desenvolvedor deve ser capaz de destruir completamente e resetar o cluster local para o seu estado original limpo via comando único (`make down`).
- **FR03:** O Sistema Local deve espelhar a exata topologia de infraestrutura da Produção (Kong, Keycloak).
- **FR04:** O Sistema Local deve gerar e apresentar automaticamente um Token M2M de Teste válido diretamente no terminal após o provisionamento.
- **FR05:** O Desenvolvedor deve ser capaz de instanciar uma nova API utilizando um modelo padronizado (*Boilerplate YAML*) fornecido pela plataforma.

### 2. Gerenciamento de Identidade e Acesso (IAM)
- **FR06:** O Administrador da Plataforma deve ser capaz de gerar credenciais de acesso *Machine-to-Machine* (Client Credentials).
- **FR07:** O Administrador da Plataforma deve ser capaz de definir um Tempo de Vida (TTL) estendido para os tokens M2M gerados na Fase 1.
- **FR08:** O Administrador da Plataforma deve ser capaz de revogar credenciais ou *Clients* manualmente em caráter de emergência.
- **FR09:** O Sistema de Identidade deve registrar logs nativos de emissão de tokens para fins de auditoria básica e *troubleshooting*.

### 3. Governança de Tráfego e API Gateway
- **FR10:** O Sistema de Gateway deve interceptar todo o tráfego HTTP/HTTPS de entrada do cluster.
- **FR11:** O Sistema de Gateway deve forçar o bloqueio ou redirecionamento de todas as requisições HTTP inseguras na borda, aceitando o tráfego de tokens exclusivamente através de canais criptografados (HTTPS/TLS).
- **FR12:** O Sistema de Gateway deve validar tokens OIDC localmente na borda utilizando chaves criptográficas em cache (JWKS), bloqueando acessos não autenticados sem depender do banco do Keycloak a cada requisição.
- **FR13:** O Sistema de Gateway deve repassar o Token JWT bruto original no cabeçalho (ex: `Authorization: Bearer`) intacto para a aplicação interna.
- **FR14:** O Desenvolvedor deve ser capaz de configurar o limite de taxa de requisições (*Rate Limiting*) específico para sua API via configuração declarativa.
- **FR15:** O Sistema de Gateway deve aplicar um limite de taxa padrão restritivo automaticamente caso o desenvolvedor não especifique um limite explícito (*Secure by Default*).
- **FR16:** O Sistema de Gateway é capaz de isentar rotas públicas pré-determinadas (ex: `/swagger`) da obrigatoriedade de Token de Autenticação exclusivamente em ambientes Locais/Homologação.

### 4. Zero-Trust na Camada de Aplicação (API Layer)
- **FR17:** O Sistema de Aplicação Interna (através da base do *Boilerplate*) deve interceptar a requisição e realizar sua própria validação criptográfica do Token JWT.
- **FR18:** O Sistema de Aplicação Interna ou o Gateway deve realizar consultas ativas de Introspecção/Revogação (Introspection Endpoint) contra o Keycloak para invalidar instantaneamente tokens revogados manualmente em emergências, sobrepondo-se ao cache local de assinaturas.
- **FR19:** O Sistema de Aplicação Interna deve extrair e ler de forma independente os dados de identidade diretamente do payload do JWT validado.

### 5. Operações Contínuas e Recuperação (SRE & GitOps)
- **FR20:** O Sistema de Deploy Contínuo (ArgoCD) deve aplicar e sincronizar manifestos de roteamento e infraestrutura exclusivamente a partir de um repositório Git.
- **FR21:** O Engenheiro de Plataforma (SRE) deve ser capaz de inibir a exclusão automatizada (*Safe-Prune*) de manifestos críticos de Ingress/Gateway para evitar apagões por falha humana no repositório.
- **FR22:** O Engenheiro de Plataforma (SRE) deve ser capaz de injetar *Secrets* sensíveis da plataforma manualmente no cluster, sem versioná-los no Git.
- **FR23:** O Engenheiro de Plataforma (SRE) deve ser capaz de restaurar o estado operacional das identidades utilizando backups estáticos do Banco de Dados externo (PostgreSQL).
- **FR24:** O Sistema de Gateway e o Sistema de Identidade devem expor rotas de *healthcheck* públicas (não autenticadas) para viabilizar o automonitoramento de vida e disponibilidade pelo próprio cluster Kubernetes.

## Requisitos Não-Funcionais (Non-Functional Requirements)

### Desempenho (Performance)
- **NFR-P01 (Latência de Borda):** A interceptação de segurança do Gateway (validação local do JWT e roteamento) deve adicionar, no máximo, **20ms** de latência de rede à requisição original da API em condições normais de operação.
- **NFR-P02 (DevEx / Tempo de Setup):** O provisionamento completo do ambiente local pelo desenvolvedor (execução do `make up`), assumindo que as imagens Docker já estejam cacheadas localmente na máquina, deve ser concluído e entregar o token em **menos de 5 minutos**.

### Segurança (Security)
- **NFR-S01 (Criptografia Restrita):** 100% do tráfego externo gerenciado pelo Gateway deve ser forçado a operar sob criptografia (TLS/HTTPS), rejeitando e bloqueando ativamente conexões planas (HTTP porta 80) na borda.
- **NFR-S02 (Vazamento Zero no GitOps):** Os repositórios Git que armazenam os manifestos de infraestrutura devem possuir 0% de tolerância para segredos em texto plano (senhas, private keys), sendo compulsoriamente injetados no cluster de forma externa/manual.

### Confiabilidade e Resiliência (Reliability)
- **NFR-R01 (Imunidade a Eviction):** Os *Pods* críticos da fundação (Kong e Keycloak) devem possuir a classificação máxima de prioridade no Kubernetes (*PriorityClass*). O Kubelet jamais poderá desalocar a infraestrutura para dar espaço a uma aplicação de negócio por falta de recursos (OOM).
- **NFR-R02 (Sobrevivência de Borda):** O Gateway deve garantir o roteamento ininterrupto de requisições que possuam tokens válidos (validação via cache JWKS) por pelo menos **60 minutos (1 hora)** em caso de indisponibilidade total e queda repentina do Keycloak, provendo uma janela de recuperação segura para o SRE.

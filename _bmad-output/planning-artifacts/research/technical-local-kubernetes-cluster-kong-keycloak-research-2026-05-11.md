---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Cluster Kubernetes Local com Kong e Keycloak para Plataforma de Integrações'
research_goals: 'Montar um ambiente local de Kubernetes com Kong como proxy reverso único e Keycloak para autenticação e gestão de identidade, avaliando ferramentas de cluster local (ex: kind) e planejando a transição para CI/CD em homologação/produção.'
user_name: 'Ismael'
date: '2026-05-11'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-11
**Author:** Ismael
**Research Type:** technical

---

## Resumo Executivo (Executive Summary)

A presente pesquisa técnica consolida a arquitetura e o planejamento de infraestrutura para uma Plataforma de Integrações robusta, operando num modelo de implantação contínua e segura desde o ambiente de desenvolvimento local (`k3d`) até o deploy on-premise (bare-metal/VMs). A arquitetura converge três pilares principais: **Governança GitOps** (através do ArgoCD, eliminando exposição de firewalls e comandos imperativos), **Identidade Centralizada** (utilizando a distribuição oficial do Keycloak baseada em Quarkus atuando como IdP) e **Roteamento Ágil** (Kong Ingress Controller operando em modo DB-less).

Para a segurança de acesso a rotas sensíveis, padronizamos a delegação de autorização do Kong Ingress para um componente interceptador (OAuth2-Proxy), que força a autenticação no Keycloak antes do tráfego tocar os microsserviços de negócio. O gerenciamento de credenciais utilizará recursos nativos do Kubernetes (criados manualmente) para manter o repositório GitOps higienizado. A escalabilidade e observabilidade foram priorizadas com recomendações rígidas de limites de recursos (QoS) e intenção futura do uso de OpenSearch.

**Principais Descobertas e Recomendações Estratégicas:**
- **Deploy On-Premise Seguro (Pull-based):** A combinação de GitHub Actions (para CI) com ArgoCD (para CD) resolve a exposição de segurança no on-premise e protege os manifestos Kubeconfig.
- **Isolamento da Responsabilidade de Identidade:** O Keycloak Oficial atuará estritamente como IdP e emissor de tokens OIDC, enquanto a complexidade de interceptação de rede fica no proxy de borda.
- **Paridade Local-Produção:** A adoção do k3d garante paridade local imediata com a produção on-premise, facilitando testes end-to-end de Ingress e Segurança no computador do desenvolvedor.

---

## Índice Analítico (Table of Contents)

1. [Visão Geral da Pesquisa](#visão-geral-da-pesquisa-research-overview)
2. [Análise da Stack Tecnológica](#análise-da-stack-tecnológica-technology-stack-analysis)
3. [Análise dos Padrões de Integração](#análise-dos-padrões-de-integração-integration-patterns-analysis)
4. [Análise de Padrões Arquiteturais](#análise-de-padrões-arquiteturais-architectural-patterns-and-design)
5. [Pesquisa de Implementação e Adoção Tecnológica](#pesquisa-de-implementação-e-adoção-tecnológica-implementation-approaches-and-technology-adoption)
6. [Recomendações Técnicas e Roadmap](#recomendações-técnicas)

---

## Visão Geral da Pesquisa (Research Overview)

### Confirmação do Escopo da Pesquisa Técnica

**Tópico da Pesquisa:** Cluster Kubernetes Local com Kong e Keycloak para Plataforma de Integrações
**Objetivos da Pesquisa:** Montar um ambiente local de Kubernetes com Kong como proxy reverso único e Keycloak para autenticação e gestão de identidade, avaliando ferramentas de cluster local (ex: kind) e planejando a transição para CI/CD em homologação/produção.

**Escopo da Pesquisa Técnica:**

- Análise de Arquitetura - padrões de design, frameworks, arquitetura do sistema
- Abordagens de Implementação - metodologias de desenvolvimento, padrões de codificação
- Stack Tecnológica - linguagens, ferramentas, plataformas
- Padrões de Integração - APIs, protocolos, interoperabilidade
- Considerações de Desempenho - escalabilidade, otimização, padrões

**Metodologia de Pesquisa:**

- Dados atuais da web com rigorosa verificação de fontes
- Validação em múltiplas fontes para afirmações técnicas críticas
- Níveis de confiança para informações incertas
- Cobertura técnica abrangente com insights específicos de arquitetura

**Escopo Confirmado em:** 2026-05-11

---

## Análise da Stack Tecnológica (Technology Stack Analysis)

### Linguagens de Programação e Configuração

A stack para este ambiente baseia-se fortemente em linguagens e formatos voltados para infraestrutura como código (IaC) e GitOps, essenciais para a transição do ambiente local para produção.
_Linguagens Principais: YAML (para manifestos Kubernetes, Helm e Kustomize), HCL (Terraform, caso adote IaC para o provisionamento do cluster base) e Bash/Shell (para automações locais temporárias)._
_Linguagens Emergentes: CUE e Jsonnet estão ganhando adoção para configuração avançada e validação de manifestos._
_Evolução da Linguagem: Forte movimento saindo de scripts imperativos (Bash) para declarações puras (YAML/GitOps) para garantir a reprodutibilidade dos clusters._
_Características de Desempenho: YAML e Kustomize são processados instantaneamente sem overhead de execução._
_Fonte: Conhecimento consolidado da indústria sobre infraestrutura Cloud-Native._

### Frameworks de Desenvolvimento e Bibliotecas

O empacotamento das aplicações (Kong e Keycloak) será o foco principal das ferramentas de gerenciamento de pacotes do Kubernetes.
_Principais Frameworks: Helm (padrão de fato da indústria para deploy do Kong e Keycloak via Helm Charts oficiais) e Kustomize (ótimo para sobrepor configurações específicas por ambiente - local, dev, prod)._
_Micro-frameworks: Plugins comunitários do Kong (ex: `revomatico/kong-oidc` para Kong Open-Source) ou padrões OIDC nativos caso utilize o Kong Enterprise._
_Tendências de Evolução: Adoção do Helm Charts em conjunto com Kustomize (renderização via Helm, patch final via Kustomize) tem se tornado a prática recomendada._
_Maturidade do Ecossistema: Helm possui uma adoção gigantesca, com repositórios oficiais mantidos tanto pela KongHQ quanto pela Bitnami/Keycloak._
_Fonte: [Pesquisa Web e Melhores Práticas de GitOps](https://argoproj.github.io/argo-cd/user-guide/kustomize/)_

### Tecnologias de Banco de Dados e Armazenamento

Kong e Keycloak são stateful em suas instalações tradicionais, o que requer planejamento cuidadoso de armazenamento no Kubernetes local e de produção.
_Bancos de Dados Relacionais: PostgreSQL é a recomendação oficial e absoluta tanto para o Kong quanto para o Keycloak. Ele lidará com as rotas/plugins do Kong e os usuários/realms do Keycloak._
_Armazenamento Persistente: Necessidade de Persistent Volume Claims (PVCs) para o PostgreSQL para sobreviver a restarts dos pods._
_Modos de Implantação: Forte tendência para usar o Kong no modo **DB-less (Declarative)** via DB-less / Ingress Controller, o que remove a necessidade do Postgres para o Kong e facilita o GitOps. O Keycloak, no entanto, sempre necessitará do Postgres._
_Maturidade: Operadores como CloudNativePG (cnpg) ou Percona Operator são recomendados para gerenciar o Postgres em produção._
_Fonte: [Pesquisa na Documentação do Keycloak e Kong e Tendências de Armazenamento](https://dev.to)_

### Ferramentas e Plataformas de Desenvolvimento

A avaliação da ferramenta de Kubernetes local é uma das principais decisões arquiteturais deste momento.
_Ferramentas Principais (Comparativo Local):_ 
1. **k3d:** Utiliza o k3s dentro do Docker. Extremamente leve, sobe em segundos, tem excelente suporte nativo a Ingress e provisionamento de LoadBalancer local. É frequentemente superior para simular ambientes complexos localmente.
2. **kind (Kubernetes in Docker):** Padrão oficial do Kubernetes SIGs. É muito robusto e excelente para CI/CD (ex: rodar testes dentro do GitHub Actions), porém é um pouco mais pesado que o k3d e gerenciar Ingress/Port-forwarding localmente requer um pouco mais de configuração manual.
3. **minikube:** Tradicional, mas consome mais recursos, operando muitas vezes via máquina virtual (dependendo do driver). Considerado pesado para a necessidade moderna.
_Recomendação Inicial:_ **k3d** é ligeiramente mais vantajoso para o fluxo de desenvolvimento local de APIs com Kong devido ao fácil gerenciamento de portas e extrema leveza.
_Fonte: Avaliação de Ferramentas de Cluster Local da Web._

### Infraestrutura em Nuvem e Implantação

Para transição do ambiente local para homologação e produção, ferramentas de CI/CD baseadas no modelo GitOps são obrigatórias.
_Plataformas Principais:_ **GitHub Actions** ou **GitLab CI** para Integração Contínua (Build das imagens dos microsserviços, testes, linting).
_Tecnologias de Containers e Orquestração:_ O Kubernetes será a infraestrutura base, podendo rodar em EKS (AWS), AKS (Azure) ou GKE (GCP) no futuro.
_Plataformas GitOps:_ **ArgoCD** ou **FluxCD**. ArgoCD é amplamente recomendado por possuir uma interface visual (UI) poderosa para debug, o que ajuda muito times em transição. Eles monitoram o repositório Git e aplicam o estado no cluster automaticamente, removendo a necessidade de scripts imperativos (como `kubectl apply` ou bash scripts locais).
_Fonte: [Adoção do ArgoCD e GitOps](https://sealos.io, https://semaphore.io)_

### Tendências de Adoção Tecnológica

_Padrões de Migração:_ Saída de pipelines de CI que fazem deploy direto (push) para o cluster (`kubectl apply` no Jenkins/Actions) para um modelo de pull via GitOps (onde o cluster "puxa" a configuração do Git).
_Tecnologias Emergentes:_ Uso do Kong Ingress Controller com CRDs (Custom Resource Definitions) como `KongPlugin` ao invés das antigas anotações no recurso Ingress do Kubernetes, e a transição para a nova Gateway API do Kubernetes.
_Tecnologias Legadas:_ Scripts bash complexos para setup local e CI estão sendo massivamente abandonados em favor do ArgoCD / k3d e configuração puramente declarativa.
_Padrões de Integração OIDC:_ Integração de Kong Open Source com Keycloak via plugins OIDC (ex: `revomatico/kong-oidc`) para forçar o redirecionamento ao Login público do Keycloak para rotas protegidas.
_Fonte: [Tendências de Arquitetura Cloud-Native e KongHQ](https://medium.com)_

---

## Análise dos Padrões de Integração (Integration Patterns Analysis)

### Padrões de Design de API e Interceptação de Tráfego

Com base no seu direcionamento, o projeto utilizará estritamente a **distribuição oficial do Keycloak** (baseada em Quarkus), seguindo a documentação oficial para Kubernetes.
_Interceptação de Tráfego e Autenticação:_ O Keycloak oficial atua puramente como um Provedor de Identidade (IdP) e Servidor de Autorização. Ele não atua nativamente como um *Reverse Proxy* para interceptar tráfego de outras aplicações. Para que o tráfego não autenticado seja barrado e redirecionado para a tela de login do Keycloak, o padrão arquitetural exige que o **API Gateway (Kong)** ou um sidecar proxy faça essa interceptação no Ingress e delegue a verificação para o Keycloak (usando o protocolo OIDC).
_Ecossistema:_ A RedHat chegou a manter um proxy reverso oficial (Keycloak Gatekeeper), mas ele foi descontinuado pois a fundação decidiu focar apenas no core do Keycloak. Portanto, a integração segura recomendada é manter o Keycloak Oficial gerenciando os usuários, e configurar o Kong Ingress para validar os tokens emitidos por ele.

### Protocolos de Comunicação

_Comunicação HTTP/HTTPS:_ Todo o tráfego externo passa exclusivamente pelo Kong atuando como Ingress Controller via HTTPS (terminação SSL). O tráfego interno entre Kong, Keycloak e os microsserviços pode trafegar sem criptografia (HTTP) no ambiente local, isolado pela rede do Kubernetes.
_Protocolo de Identidade:_ O **OpenID Connect (OIDC)** é o protocolo central de comunicação para a autenticação, suportando nativamente os fluxos de login por interface e validação de tokens JWT.

### Abordagens de Interoperabilidade e Implantação (On-Premise)

A decisão entre usar apenas o GitHub Actions (Push) vs adotar o ArgoCD (Pull) é crucial para um ambiente **On-Premise**:
_Integração Ponto-a-Ponto (GitHub Actions + kubectl apply):_
Esta abordagem usa o modelo **Push**. O servidor do GitHub precisa enviar o comando diretamente para o seu cluster. **O grande problema on-premise:** Você teria que abrir portas de entrada no firewall da sua rede local/servidor para a internet, e salvar a chave administrativa (Kubeconfig) no GitHub. A única forma segura de contornar isso é mantendo e configurando _Self-Hosted Runners_ (servidores do GitHub Actions rodando dentro da sua própria rede), o que também traz manutenção pesada.
_GitOps (ArgoCD):_
Esta abordagem usa o modelo **Pull**. O ArgoCD é instalado _dentro_ do seu cluster e faz conexões de _saída_ (outbound) para ler o GitHub. **A grande vantagem on-premise:** Você não precisa abrir nenhuma porta de firewall de entrada e nenhuma credencial sensível do seu servidor sai da sua máquina local ou do servidor da empresa. O ArgoCD se atualiza sozinho de forma muito mais segura. A curva de aprendizado inicial se paga rapidamente pela paz de espírito de rede que ele traz.
_Fonte: [Comparativo Push vs Pull em ambientes privados](https://portainer.io)_

### Padrões de Integração de Microsserviços

_Padrão API Gateway:_ O Kong atua interceptando as chamadas e lidando com preocupações transversais (autenticação, rate limiting).
_Service Discovery:_ Resolução de serviços baseada inteiramente no DNS interno nativo do Kubernetes (CoreDNS), eliminando a necessidade de ferramentas externas tipo Eureka ou Consul.

### Padrões de Segurança de Integração

_SSO e Delegação:_ Autenticação de administradores via OAuth 2.0 (Authorization Code Flow) utilizando o Keycloak.
_Acesso de Microsserviços (M2M):_ No momento futuro onde microsserviços usarão o Keycloak para se comunicar via API Keys, o padrão OIDC "Client Credentials Grant" será o utilizado para que um serviço gere um token para acessar outro.

---

## Análise de Padrões Arquiteturais (Architectural Patterns and Design)

### Padrões de Arquitetura de Sistema (System Architecture Patterns)

A arquitetura do cluster será baseada no padrão de **Gateway Centralizado (Shared Gateway Pattern)**.
_Padrão de Arquitetura:_ O Kong Ingress Controller servirá como o ponto de entrada central (Edge Gateway) controlando o tráfego "North-South" (externo para interno). Ele fará o roteamento de borda e o descarregamento de TLS (TLS termination). Em conjunto, usaremos o padrão de **Delegação de Identidade** para o Keycloak.
_Trade-offs:_ A centralização do tráfego no Kong e da autenticação no Keycloak cria pontos únicos de falha, exigindo foco máximo na escalabilidade destes dois componentes. A vantagem é que os microsserviços ficam completamente agnósticos a regras complexas de roteamento e telas de login.

### Princípios de Design e Melhores Práticas

_Separação de Interesses (Separation of Concerns):_ A infraestrutura (Kong/Keycloak) será gerida separadamente das aplicações de negócio. 
_Namespaces de Isolamento:_
- `ingress-system`: Kong Gateway
- `iam-system` ou `keycloak`: Keycloak Oficial e Postgres do Keycloak
- `argocd`: ArgoCD (GitOps)
- `apps`: Microsserviços e APIs.
_Configuração como Código (Declarative Design):_ Todos os recursos seguirão uma abordagem estritamente declarativa via YAML, rejeitando comandos imperativos.

### Padrões de Escalabilidade e Desempenho

_Kong (DB-less):_ A recomendação absoluta para a arquitetura de desempenho e escalabilidade do Kong no Kubernetes moderno é operar no modo **DB-less** via Ingress Controller. As regras vivem apenas na memória dos Pods e no etcd do Kubernetes, o que permite o Kong escalar horizontalmente (HPA) instantaneamente sem gargalos de banco de dados.
_Keycloak (Alta Disponibilidade):_ O Keycloak escala através da tecnologia Infinispan (cache distribuído). Para ambientes on-premise críticos, requer no mínimo 2 réplicas e afinidade de nós (Node Affinity/Anti-affinity) para não rodar todos os pods no mesmo servidor físico.

### Padrões de Integração e Comunicação

_Gateway API vs Ingress API:_ Historicamente o Kong usa o recurso `Ingress` padrão. A arquitetura moderna aponta para a adoção da nova **Gateway API** do Kubernetes. Se o cluster suportar, adotar CRDs como `HTTPRoute` permitirá separar o gerenciamento da infraestrutura (Platform Team) do gerenciamento de rotas dos desenvolvedores.
_Sidecar Proxy (Tráfego Interno):_ Se a plataforma de integrações exigir controle complexo do tráfego interno (East-West) no futuro on-premise, um Service Mesh (como Linkerd ou Kong Mesh) poderá ser avaliado. Por enquanto, a comunicação interna se dará via Kubernetes DNS.

### Padrões de Arquitetura de Segurança

_Padrão OAuth2 Reverse Proxy:_ A implementação técnica da segurança se dará pelo deploy de um componente **OAuth2-Proxy** configurado para proteger as rotas da plataforma de integrações, interceptando requisições, executando o fluxo Authorization Code com o Keycloak, e passando o token seguro via Header HTTP para os microsserviços da retaguarda.
_TLS Termination:_ O Kong encerra a conexão segura e trafega internamente em texto puro (ou mTLS caso configurado).
_Gestão de Segredos:_ Por decisão arquitetural atual, não serão utilizados gerenciadores complexos como SOPS, Vault ou Sealed Secrets. O projeto utilizará **Secrets nativos do Kubernetes** (`Opaque`). 
**Atenção ao GitOps:** Como senhas não devem ir para o repositório Git em base64, esses Secrets deverão ser criados manualmente no cluster (via linha de comando) fora do fluxo do ArgoCD. As aplicações e deployments simplesmente referenciarão o nome desses Secrets pré-existentes.

### Padrões de Arquitetura de Dados

_Banco de Dados do Identity Provider:_ O PostgreSQL (banco obrigatório do Keycloak) deve rodar sob um padrão de **StatefulSet** amarrado a um Persistent Volume Claim (PVC) atrelado ao Storage Class local. Diferente do Kong DB-less, o Keycloak requer consistência estrita ACID para senhas e configurações.

### Arquitetura de Implantação e Operações

_Cluster Local para Produção:_ A arquitetura de implantação foi decidida:
1. **Local (Desenvolvedor):** `k3d` subindo Kong, Keycloak e a aplicação localmente de forma ultra-rápida.
2. **On-Premise (Servidores Reais):** Provisionamento do Kubernetes puro, utilizando ArgoCD (GitOps Pull-based) para aplicar as configurações em segurança sem abrir o firewall.
3. **CI (Continuous Integration):** GitHub Actions irá rodar testes, realizar o build da imagem Docker do seu microsserviço e realizar o `git push` atualizando a tag da imagem no repositório de manifestos.

---

## Pesquisa de Implementação e Adoção Tecnológica (Implementation Approaches and Technology Adoption)

### Estratégias de Adoção de Tecnologia
_Migração Gradual vs Inicial:_ Como o ambiente será desenvolvido do zero partindo do local (k3d) para os servidores físicos on-premise, a adoção tecnológica será "Big Bang" para a infraestrutura base (Kubernetes), mas gradual para as aplicações de negócios.
_Gerenciamento de Segredos:_ Adoção simplificada inicial com criação manual de `Secret` nativo no cluster, postergando o uso de Sealed Secrets para reduzir o atrito de engenharia, conforme decisão técnica prévia.

### Fluxos de Trabalho de Desenvolvimento e Ferramentas
_CI/CD (Integração e Implantação Contínua):_ 
- **GitHub Actions (CI):** Focado puramente em integração. Vai rodar lint, testes unitários, build da imagem Docker, gerar a tag semântica, publicar no container registry, e, em seguida, fazer um *commit automático* no repositório de manifestos (GitOps Repo) com a nova tag.
- **ArgoCD (CD):** Focado puramente em deployment. Vai escutar o repositório GitOps e, assim que a tag for atualizada pelo GitHub Actions, fará o pull e aplicará a nova imagem no cluster on-premise de forma ultra segura.

### Testes e Garantia de Qualidade
_Paridade de Ambientes:_ Validação garantida através da replicação exata da infraestrutura local via `k3d`. O desenvolvedor deve levantar o Kong, Keycloak e a aplicação localmente utilizando os exatos mesmos Helm Charts/Manifestos que o ArgoCD aplicará em produção.

### Práticas de Implantação e Operações
_Observabilidade (Monitoramento):_ O Kong Open-Source permite o uso de plugins para expor métricas na rota `/metrics`. O Keycloak (Quarkus) moderno expõe as mesmas métricas nativamente no endpoint `/metrics`. Para a operação on-premise ser cega, é fundamental no futuro um deploy de um *Prometheus Operator* para ler esses dados.
_Práticas de Log:_ Uso padronizado de logs em texto puro via `stdout/stderr` (melhor prática para containers), recolhidos nativamente pelas engines do Kubernetes. Como **intenção futura**, a arquitetura prevê a adoção do **OpenSearch** (ou outra stack open-source similar como Loki/EFK) para coletar, centralizar e indexar os logs de todos os nós do cluster, infraestrutura (Kong/Keycloak) e das aplicações de negócio.
### Organização de Equipe e Habilidades
_Mindset GitOps:_ O modelo ArgoCD exigirá que a equipe de operação abandone o mindset de "acessar a máquina (SSH) e rodar comandos" para o de "fazer um pull request com a mudança desejada". Modificações nos fluxos do Kong Ingress ou configuração do Keycloak só acontecem via commit em manifestos Git.

### Otimização de Custos e Gestão de Recursos
_Infraestrutura On-Premise:_ Não haverá custos elásticos de Cloud Provider, logo o desperdício significa exaustão da máquina física. Deve-se aplicar **Resource Requests e Limits** (`CPU` e `Memory`) de forma rigorosa nos namespaces do Keycloak, Postgres e Kong, para garantir que não sufoquem os microsserviços em picos de tráfego.

### Avaliação e Mitigação de Riscos
_Falha de Banco de Dados:_ Se o Postgres falhar, o Keycloak cai e paralisa novos logins. Mitigação: Implementação baseada em `StatefulSet` robusta ou operada via um Operator (ex: CloudNativePG) com rotina de backups para volumes locais externos.

## Recomendações Técnicas

### Roadmap de Implementação Sugerido
1. Inicializar o cluster local via `k3d`.
2. Instalar ArgoCD para governança GitOps desde o "Dia 1".
3. Deploy manual dos Kubernetes Secrets de bancos de dados no cluster para manter a segurança do Git.
4. Deploy declarativo via ArgoCD do PostgreSQL, Keycloak (Oficial) e Kong Ingress Controller.
5. Configuração do OAuth2-Proxy interligando as rotas protegidas do Kong com a tela de login do Keycloak.
6. Pipeline GitHub Actions gerando as imagens dos seus microsserviços e atuando como um "atualizador" do repositório GitOps.

### Recomendações Finais da Stack
- Cluster Kubernetes Local: **k3d**
- Identidade/SSO: **Keycloak Oficial (Quarkus)**
- Interceptação de Tráfego OIDC: **OAuth2-Proxy**
- API Gateway / Ingress: **Kong Open-Source (modo DB-Less)**
- Delivery / GitOps: **ArgoCD**

---

*Data de Conclusão da Pesquisa: 2026-05-11*
*Esta pesquisa técnica consolidada serve como referência autoritativa para o design e implementação do seu cluster local e produção on-premise.*

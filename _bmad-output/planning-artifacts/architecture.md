---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/research/technical-local-kubernetes-cluster-kong-keycloak-research-2026-05-11.md
workflowType: 'architecture'
project_name: 'cluster-kubernetes'
user_name: 'Ismael'
date: '2026-05-12'
lastStep: 8
status: 'complete'
completedAt: '2026-05-12'
---

# Documento de Decisão de Arquitetura

_Este documento é construído de forma colaborativa por meio da descoberta passo a passo. As seções são anexadas à medida que trabalhamos em cada decisão arquitetural juntos._

## Análise de Contexto do Projeto

### Visão Geral dos Requisitos

**Requisitos Funcionais:**
O projeto foca na construção de uma Plataforma de Integração robusta composta por 24 requisitos funcionais divididos em 5 pilares:
1. **Local DevEx:** Setup 1-click via `k3d` com paridade de produção e geração automática de token de teste.
2. **IAM:** Geração de M2M Client Credentials com longo TTL via Keycloak.
3. **Gateway e Tráfego:** Kong DB-less atuando como interceptador seguro com validação local de JWKS, "Secure by Default" Rate Limiting e HTTPS estrito.
4. **Zero-Trust:** Aplicações clientes precisam realizar validação criptográfica própria do token JWT (Deep Security).
5. **SRE e GitOps:** Implantação 100% via ArgoCD, gestão manual de *secrets* no cluster, e resiliência via backup de banco e *Safe-Prune*.

**Requisitos Não-Funcionais:**
- **Performance:** Latência adicionada pela borda inferior a 20ms; Tempo de setup local inferior a 5 minutos.
- **Segurança:** Uso mandatório de criptografia (TLS/HTTPS); Proibição absoluta de vazamento de segredos no Git.
- **Confiabilidade:** Componentes-chave (Kong, Keycloak) com prioridade máxima de agendamento (imunidade a *eviction*); Sobrevivência autônoma da borda via cache JWKS por 60 minutos durante quedas de IDP (exige sincronização entre o TTL do Token e o TTL do cache JWKS).
- **Consumo de Recursos (Footprint):** O ambiente local (`k3d`) deve possuir restrições severas e otimizações de uso de memória/CPU para garantir viabilidade de execução em notebooks corporativos restritos.

**Escala e Complexidade:**
O projeto possui alta complexidade de infraestrutura, com foco em resiliência e abstração de dificuldades operacionais para os desenvolvedores.
- Domínio primário: Platform Engineering / Cloud-Native (On-Premise)
- Nível de complexidade: Alta
- Componentes arquiteturais estimados: 4 (ArgoCD, Kong, Keycloak, PostgreSQL), além do framework local (`k3d`) e repositório de Boilerplates.

### Restrições Técnicas e Dependências

- Implantação em Datacenter físico (On-Premise) sem aberturas de firewall externas para *Push* (justificando o ArgoCD).
- Segredos (Senhas, Chaves) não podem ser inseridos nos repositórios Git, sendo injetados manualmente de forma estática no *bootstrap* (rotinas de rotação contínua de segredos estão explicitamente fora do escopo atual).
- Keycloak depende de um banco PostgreSQL externo para armazenar estado, que deve possuir estratégias de backup rotineiras e restauração testadas.
- Necessidade de acomodar sistemas legados (fábrica) que não "entendem" OIDC.

### Preocupações Transversais Identificadas (Cross-Cutting Concerns)

- **Paridade de Ambientes:** Garantir que as configurações do Kong e do Keycloak sejam espelhadas localmente para permitir testes precisos.
- **Resiliência e Recuperação de Desastres (DR):** Prevenção de auto-deleção no ArgoCD e garantia de operação continuada em cenários degradados. No entanto, a regra de "Safe-Prune" (`prune: false`) será aplicada **exclusivamente** à infraestrutura central (Namespaces do Kong, Keycloak e ArgoCD). Aplicações de negócios deverão permitir deleção automática (`prune: true`) para manter a higiene do cluster e evitar recursos zumbis.
- **Gestão de Identidade Padronizada (Zero-Trust):** Eliminar exceções pontuais de segurança através de uma governança rígida e universal. Para não destruir a experiência do desenvolvedor ("Fricção Zero"), a validação JWT não deve ser imposta às bibliotecas de negócios sem que a plataforma forneça abstrações prontas (SDKs ou Sidecars injetados via Boilerplate).
- **Estratégia de Integração de Legados:** Definição clara de como o Kong traduzirá requisições de sistemas antigos (API Keys) sem comprometer o isolamento Zero-Trust da infraestrutura.
- **Gerenciamento do Ciclo de Vida dos Boilerplates:** Utilização de bases versionadas (ex: Kustomize ou Helm) para os templates YAML, mitigando o risco de deriva de configuração (*drift*) no longo prazo.

### Decisões Arquiteturais Fundacionais (ADRs)

- **Gateway DB-Less (Stateless):** O uso do Kong DB-Less foi cristalizado para garantir conformidade total com GitOps. Toda configuração de rotas ou Rate Limits passa pelo repositório Git via ArgoCD, rejeitando a flexibilidade de APIs dinâmicas stateful em favor da previsibilidade e imutabilidade.
- **Validação JWKS Local (Borda Stateless):** A validação de tokens OIDC será baseada em cache JWKS no Kong em vez de Introspecção Ativa no Keycloak. Isso garante a sobrevivência do fluxo de dados por 60 minutos caso a Identidade sofra queda (resiliência de negócio), mantendo a latência na borda estritamente abaixo de 20ms.
- **Gestão Estática de Segredos:** Devido à necessidade pragmática de simplificar a Fase 1 e evitar componentes extras de infraestrutura (como Vaults), foi ratificada a injeção manual e estática de segredos no *bootstrap* do cluster.

### Ações de Mitigação e Hardening de Segurança

- **Contenção da Janela JWKS (60m):** Os *Rate Limits* do Gateway devem ser configurados de forma restritiva o suficiente para atuar como barreira de contenção contra a exfiltração em massa de dados caso um token seja roubado e abusado durante o período de validade cega do cache JWKS.
- **Isolamento de Tráfego Interno (East-West):** Para compensar a ausência de mTLS interno (adiado para a Fase 3), o projeto deve utilizar `NetworkPolicies` fundamentais do Kubernetes para isolar Namespaces e impedir interceptações laterais de rede na comunicação em texto claro entre o Gateway e os Pods.
- **Segregação Criptográfica Dev/Prod:** Os ambientes de desenvolvimento local (`k3d`) devem obrigatoriamente operar com Realms e chaves de assinatura locais matematicamente distintas do cluster de Produção. Isso assegura que o vazamento de um token gerado durante o desenvolvimento (ex: via GitHub) seja sumariamente rejeitado pelo Gateway de produção.
- *Nota sobre Sistemas Legados:* A proteção via lista de IPs permitidos (IP Whitelisting) para API Keys estáticas está explicitamente fora do escopo do MVP, consistindo em um risco técnico aceito provisoriamente em prol da velocidade de integração.

## Avaliação de Templates de Inicialização (Starter Templates)

### Domínio Tecnológico Principal

Infraestrutura e Platform Engineering (Kubernetes, GitOps, API Gateway, IAM) baseados nos requisitos do projeto.

### Opções de Starter Avaliadas

1. **Padrão "App of Apps" (ArgoCD)**: Estrutura clássica com um `root-app` apontando para manifestos de aplicações filhas. Excelente para ambientes controlados e On-Premise, fornecendo uma ordem de dependência clara.
2. **ApplicationSets (ArgoCD)**: Padrão moderno mais avançado usando geradores dinâmicos. Avaliado como excessivamente complexo e prematuro para a Fase 1 (MVP) focada em um único cluster de produção.

### Starter Selecionado: App-of-Apps GitOps + k3d Makefile

**Justificativa para Seleção:**
Fornece o equilíbrio perfeito entre a imutabilidade estrita exigida pelo PRD e a simplicidade de automação local. A estrutura permite aplicar as políticas de mitigação de desastres (Safe-Prune) de forma isolada na fundação (Kong/Keycloak), garantindo ao mesmo tempo que o desenvolvedor tenha "Fricção Zero" localmente.

**Comando de Inicialização:**

```bash
# Como se trata de infraestrutura GitOps, não há um 'create-app' CLI oficial.
# O projeto será inicializado estabelecendo o esqueleto do repositório:
mkdir -p cluster/{bootstrap,infrastructure,apps,boilerplates}
touch Makefile
```

**Decisões Arquiteturais Fornecidas pelo Starter:**

**Linguagem & Runtime:**
Arquivos declarativos YAML orquestrados pelo Kubelet (Kubernetes) e executados localmente via `k3d`. Automação de terminal apoiada em `Bash` e `Makefile` (executados nativamente no macOS/Linux e obrigatoriamente sob o ambiente **WSL2** no Windows).

**Solução de Estilização:**
N/A (Plataforma Backend/Infra).

**Ferramentas de Build:**
`Makefile` atuando como orquestrador do ciclo de vida local do desenvolvedor (`make up`, `make down`, `make token`).

**Framework de Teste:**
Validação contínua através de scripts acoplados ao `Makefile` que gerarão um Token M2M real consultando o Keycloak imediatamente após a subida da infraestrutura.

**Organização de Código:**
- `/cluster/bootstrap/`: Manifesto raiz ("Root") do ArgoCD.
- `/cluster/infrastructure/`: Manifestos do Kong DB-less, PostgreSQL e Keycloak.
- `/cluster/apps/`: Repositório de destino para as APIs da equipe de negócios.
- `/cluster/boilerplates/`: Bases estruturadas (Kustomize/Helm) para padronizar novas APIs.

**Experiência de Desenvolvimento:**
"Fricção Zero": O desenvolvedor executa exclusivamente `make up` (nativamente ou sob WSL2). O Makefile sobe o cluster k3d vazio, instala o ArgoCD e aplica o `bootstrap/`. O ArgoCD, a partir daí, sincroniza a infraestrutura inteira em cascata.

**Nota:** A inicialização do projeto estabelecendo esta estrutura de pastas e o `Makefile` base deve ser a primeira história de implementação.

## Decisões Arquiteturais Centrais

### Análise de Prioridade das Decisões

**Decisões Críticas (Bloqueiam a Implementação):**
- **Padrão de Roteamento de Borda:** Objeto `Ingress` (Kubernetes padrão com anotações do Kong).
- **Estrutura de Automação Local:** Topologia declarada via arquivo `k3d.yaml`, orquestrado via `Makefile`.
- **Padrão do Repositório GitOps:** Padrão clássico de raiz única *App-of-Apps* (ArgoCD).

**Decisões Importantes (Moldam a Arquitetura):**
- **Motor de Templates (Boilerplates):** *Kustomize* (v5.x nativo do kubectl).
- **Mecanismo de Interceptação Zero-Trust:** Kong operando em modo DB-Less (`3.14.0.3`, linha `3.14 LTS`) via Kong Ingress Controller.
- **Fonte de Identidade OIDC:** Keycloak hospedado com estado isolado no PostgreSQL.

**Decisões Adiadas (Post-MVP / Backlog Futuro):**
- **Gateway API (HTTPRoute):** A transição do objeto *Ingress* clássico para as CRDs modernas do *Gateway API* foi adicionada ao Backlog Futuro. A decisão de adiamento foca em garantir baixa curva de aprendizado inicial e adoção ágil no MVP.
- **Service Mesh interno (mTLS):** Adiado para a Fase 3 (interceptação lateral mitigada temporariamente com NetworkPolicies).
- **Cofres de Segredos Automatizados:** Adiado (adoção de injeção manual estática para reduzir atrito da fundação).

### Arquitetura de Dados

- **Repositório de Identidades:** O estado reside de forma exclusiva e isolada no banco PostgreSQL que atende o Keycloak. Depende de processo rigoroso de backup sistêmico.

### Autenticação e Segurança

- **Padrão M2M OIDC:** Fluxo estrito via *Client Credentials* de longo tempo de vida (TTL) para a Fase 1.
- **Validação JWKS Descentralizada:** Para manter a latência de rede sub-20ms e preencher a resiliência de queda temporal (sobrevivência de 60m), toda tokenização M2M passará por verificação local criptográfica de cache JWKS no Gateway Kong.
- **Defaults endurecidos do Kong 3.14:** A linha `3.14` habilita `tls_certificate_verify` por padrão e passa a privilegiar rotas HTTPS por default. Os manifestos e configurações declarativas do gateway devem refletir isso explicitamente para evitar boot inválido ou comportamento implícito divergente.

### Padrões de API e Comunicação

- **Roteamento Declarativo Universal:** Uso estrito e universal de objetos `Ingress` padrão. Regras de *Rate Limiting* (padrão conservador automático) e Autenticação fluem exclusivamente através de definições nas Anotações (`annotations`) declaradas pelo time de negócio via *Boilerplate*.
- **Blindagem do Ingress (Abstração):** O objeto `Ingress` pertence exclusivamente à *Base* do Kustomize mantida pela equipe de Plataforma. Os desenvolvedores clientes injetam apenas propriedades vitais (como `hostname`, `paths` e parâmetros de Rate Limit) por meio de variáveis no *Overlay*, sem nunca manipular a estrutura do Ingress diretamente. Essa blindagem isola o legado e viabiliza a migração futura para o *Gateway API* sem impacto nos repositórios das equipes.
- **Flexibilidade Legada:** *Plugins* instalados na camada do Gateway abstrairão o *handshake* engessado de sistemas legados de fábrica via conversão de chaves simples (API Keys).
- **Contrato do Desenvolvedor:** A plataforma deve manter uma documentação centralizada e versionada ("Contrato do Desenvolvedor") listando explicitamente quais parâmetros, variáveis do Kustomize e anotações do Kong são oficialmente homologados e suportados. Este contrato serve como a referência canônica para onboarding de novas equipes.

### Arquitetura Frontend

- *N/A (O escopo do projeto é uma plataforma Backend/Infraestrutura).*

### Infraestrutura e Implantação

- **Provisionamento Efêmero (DevEx):** Ambientes locais idênticos em infraestrutura instanciados via *wrapper* (`make up`). O manifesto subjacente `k3d.yaml` garantirá a imutabilidade limitando estritamente consumo de CPU/Memória (*Footprint*) para notebooks corporativos.
- **Árvore Estrutural do Repositório:** Divisão entre manifesto-raiz (`/bootstrap`), fundação (`/infrastructure`) e camada cliente (`/apps`).
- **Herança de Kustomize:** As APIs das equipes clientes derivarão suas propriedades consumindo configurações declaradas nas Bases do Kustomize residindo em `/boilerplates`.
- **Versionamento Semântico de Boilerplates:** As Bases Kustomize em `/boilerplates` devem adotar versionamento semântico estrito (ex: pastas `v1/`, `v2/` ou consumo via tags Git remotas). Atualizações da plataforma (como a adição de uma nova anotação obrigatória de segurança) não devem propagar-se automaticamente para APIs em produção, protegendo o *uptime* das equipes de negócio.

### Análise de Impacto das Decisões

**Sequência Lógica de Implementação:**
1. Criar o orquestrador `Makefile` acoplado ao arquivo declarativo base `k3d.yaml` contendo limites severos de recursos.
2. Elaborar a árvore de diretórios do repositório Git obedecendo ao padrão *App-of-Apps* e aplicar o manifesto "Root" do ArgoCD.
3. Estruturar as definições Kustomize da *Infraestrutura Core* (Keycloak, Postgres, Kong DB-Less).
4. Implementar a primeira "Base" Kustomize no diretório `/boilerplates`, testando o mapeamento do `Ingress` clássico apontado para a infraestrutura.

**Dependências Cruzadas (Cross-Component):**
- A funcionalidade e usabilidade das bases `Kustomize` (DevEx) são fundamentalmente acopladas às convenções fixadas para uso da classe de `Ingress` do Kong.
- O modelo de automação local baseada em `Makefile` requer sincronia irrestrita com o `k3d.yaml`; se houver modificações drásticas em topologia local, os *scripts bash* associados podem falhar.
- A blindagem do `Ingress` na Base Kustomize é pré-requisito técnico para a migração futura ao *Gateway API* sem impacto nos repositórios das equipes.

## Padrões de Implementação e Regras de Consistência

### Pontos de Conflito Potenciais Identificados

**4** categorias principais onde agentes de IA poderiam tomar decisões divergentes: Nomenclatura, Estrutura, Formato e Processo.

### Padrões de Nomenclatura

**Nomenclatura Kubernetes:**
- **Namespaces:** DEVE usar `kebab-case` (ex: `kong-gateway`, `keycloak-auth`, `api-pedidos`). NÃO DEVE usar PascalCase, camelCase ou snake_case.
- **Recursos (Deployments, Services, ConfigMaps):** DEVE seguir o padrão `<app>-<tipo>` em `kebab-case` (ex: `keycloak-deployment`, `kong-configmap`).
- **Ancoragem do Nome:** O nome do recurso Kubernetes DEVE derivar diretamente do nome do diretório correspondente em `/apps/`. Se o diretório é `api-pedidos`, o deployment é `api-pedidos-deployment` e o namespace é `api-pedidos`.
- **Labels:** DEVE incluir obrigatoriamente os labels recomendados oficiais em todo recurso:
  - `app.kubernetes.io/name`: DEVE corresponder ao nome do diretório/app.
  - `app.kubernetes.io/component`: DEVE usar um dos valores controlados: `api`, `database`, `identity-provider`, `gateway`, `worker`.
  - `app.kubernetes.io/part-of`: DEVE ser fixo como `cluster-kubernetes` para todos os recursos do repositório.
- **Diretórios Kustomize:** DEVE usar `kebab-case` para todas as pastas (ex: `/infrastructure/kong-gateway/`).
- **Namespaces para Dependências:** Dependências internas de um serviço (ex: PostgreSQL do Keycloak) DEVEM residir no mesmo namespace do serviço pai (ex: `keycloak-auth`). Apenas serviços independentes recebem namespaces próprios.

### Padrões de Estrutura

**Organização do Projeto:**
- Scripts auxiliares (bash) DEVEM residir exclusivamente em `/scripts/`, sendo chamados pelo `Makefile`. NÃO DEVE haver scripts bash soltos na raiz do repositório.
- Documentação do "Contrato do Desenvolvedor" e guias de onboarding DEVEM residir em `/docs/`.
- O repositório DEVE conter um `README.md` na raiz documentando pré-requisitos de sistema (Docker, kubectl, k3d, make, e WSL2 se no Windows), o comando de entrada (`make up`) e um link para o Contrato do Desenvolvedor em `/docs/`.
- NÃO DEVE haver documentação técnica misturada dentro das pastas de infraestrutura.

**Estrutura Kustomize:**
- Cada componente DEVE seguir a estrutura com separação entre `base/` e `overlays/` para os 3 ambientes:
  ```
  /infrastructure/<componente>/
  ├── base/
  │   ├── kustomization.yaml
  │   ├── deployment.yaml
  │   └── service.yaml
  └── overlays/
      ├── local/           # k3d na máquina do desenvolvedor
      ├── homologacao/     # servidor de testes no datacenter
      └── production/      # servidor de produção no datacenter
  ```
- NÃO DEVE existir componente sem essa separação `base/` e `overlays/`.

**Contrato de Interface do Boilerplate:**
- Toda Base Kustomize em `/boilerplates` DEVE conter um arquivo `CONTRACT.md` documentando as variáveis expostas para os Overlays dos desenvolvedores.
- O `CONTRACT.md` DEVE usar o formato de tabela markdown padronizado com as colunas: `Variável`, `Obrigatória`, `Valor Padrão`, `Descrição`.
- Variáveis mínimas obrigatórias que toda Base de Boilerplate DEVE expor: `app-name`, `hostname`, `paths`, `rate-limit-per-minute` (com valor padrão conservador), `namespace`.
- O `CONTRACT.md` DEVE distinguir claramente entre variáveis obrigatórias e opcionais.

**Procedimento de Escape do Boilerplate:**
- Quando o Boilerplate padrão não cobrir o caso de uso do desenvolvedor, ele DEVE abrir uma solicitação formal à equipe de Plataforma.
- O desenvolvedor NÃO DEVE modificar a Base diretamente.
- A equipe de Plataforma avalia se o caso justifica extensão da Base existente ou criação de um Boilerplate especializado.

### Padrões de Formato

**YAML:**
- DEVE usar indentação de **2 espaços**. NÃO DEVE usar tabs ou 4 espaços.
- Todo recurso Kubernetes DEVE iniciar com um bloco de comentário descritivo em **pt-BR** (ex: `# Deployment principal do Keycloak - Identity Provider OIDC`).

**Imagens Docker:**
- DEVE usar sempre tag explícita e imutável (ex: `keycloak:26.2.1`).
- NÃO DEVE usar a tag `latest` em nenhum manifesto, em nenhuma circunstância.

**Exemplo de Referência:**
```yaml
# Deployment principal do Keycloak - Identity Provider OIDC
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak-deployment
  namespace: keycloak-auth
  labels:
    app.kubernetes.io/name: keycloak
    app.kubernetes.io/component: identity-provider
    app.kubernetes.io/part-of: cluster-kubernetes
  annotations:
    argocd.argoproj.io/sync-wave: "2"
```

### Padrões de Processo

**Ordem de Sync Waves (ArgoCD):**
DEVE respeitar estritamente a seguinte ordem de sincronização. Todo manifesto de infraestrutura DEVE conter explicitamente a annotation `argocd.argoproj.io/sync-wave` com o valor numérico correspondente:

| Wave | Componente | Justificativa |
|------|-----------|---------------|
| 0 | Namespaces e Secrets | Pré-requisitos estruturais |
| 1 | PostgreSQL | Dependência de estado do Keycloak |
| 2 | Keycloak | Depende do banco estar operacional |
| 3 | Kong DB-Less | Depende do JWKS endpoint do Keycloak |
| 4+ | Aplicações de negócio | Dependem do Gateway e IAM |

**Sequência de Bootstrap Manual (Dia Zero / Emergência):**
Para reconstrução do cluster a partir do zero, DEVE seguir esta ordem:
1. Criar namespaces base.
2. Injetar Secrets manualmente (credenciais do Keycloak, PostgreSQL).
3. Instalar o ArgoCD.
4. Aplicar o manifesto Root App — a partir daqui o ArgoCD assume via Sync Waves.

**Healthchecks:**
- Todo recurso de infraestrutura DEVE declarar `readinessProbe` e `livenessProbe`.
- Endpoints de healthcheck DEVEM ser públicos (não autenticados), conforme FR24.
- Os Boilerplates de aplicações de negócio também DEVEM incluir probes de saúde nos templates padrão.

**Logs:**
- DEVE usar formato JSON estruturado sempre que o componente suportar (Kong e Keycloak suportam nativamente).
- Esta configuração DEVE ser habilitada desde o primeiro deploy.

**Validação Automatizada (Linter):**
- O repositório DEVE incluir validações automatizadas de manifestos YAML através do `kube-linter` (para boas práticas e segurança) e do `Conftest` baseado em Open Policy Agent - OPA (para regras estruturais e de nomenclatura, como o padrão kebab-case).
- O `Makefile` DEVE executar o linter como pré-condição obrigatória antes de aplicar manifestos no cluster local via `make up`.
- O pipeline de CI DEVE executar a mesma validação como gate de qualidade.

**Feedback do `make up`:**
- O script de automação DEVE imprimir ao final da execução um resumo estruturado contendo: status de cada componente (up/down), URL de acesso local e o token M2M de teste gerado.

**Visibilidade Operacional:**
- O Dashboard do ArgoCD é a interface oficial de visibilidade da plataforma, acessível para verificação de estado e conformidade das APIs implantadas.

### Escopo de Aplicação dos Padrões

**Regras que se aplicam SOMENTE à infraestrutura da plataforma (Kong, Keycloak, PostgreSQL, ArgoCD):**
- Sync Waves com annotations explícitas.
- Sequência de Bootstrap Manual.
- Safe-Prune desativado (`prune: false`).

**Regras que se aplicam TAMBÉM aos Boilerplates das equipes clientes:**
- Nomenclatura `kebab-case` e labels obrigatórios.
- Tags Docker imutáveis (proibido `latest`).
- Estrutura `base/` + `overlays/` (local, homologação, produção).
- Healthchecks (`readinessProbe` e `livenessProbe`).
- Comentários descritivos em pt-BR.
- Prune automático habilitado (`prune: true`).

### Diretrizes de Aplicação (Enforcement)

**Todo Agente de IA DEVE:**
1. Usar `kebab-case` para toda nomenclatura Kubernetes (namespaces, recursos, diretórios).
2. Derivar o nome do recurso K8s diretamente do nome do diretório em `/apps/`.
3. Respeitar a estrutura `base/` + `overlays/` (local, homologação, produção) do Kustomize para cada componente.
4. Declarar labels oficiais (`app.kubernetes.io/*`) em todo recurso, usando o vocabulário controlado para `component`.
5. Fixar o label `app.kubernetes.io/part-of` como `cluster-kubernetes`.
6. Iniciar todo arquivo YAML com comentário descritivo em pt-BR.
7. Especificar tags Docker imutáveis com versão explícita.
8. Incluir a annotation `argocd.argoproj.io/sync-wave` em todo manifesto de infraestrutura.
9. Declarar `readinessProbe` e `livenessProbe` em todo Deployment.
10. Emitir logs em JSON estruturado quando suportado pelo componente.
11. Executar o linter YAML como pré-condição do `make up`.

**Todo Agente de IA NÃO DEVE:**
1. Usar PascalCase, camelCase ou snake_case em nomes de recursos ou diretórios Kubernetes.
2. Criar recursos sem os labels oficiais `app.kubernetes.io/*`.
3. Usar a tag `latest` em imagens Docker.
4. Criar componentes sem separação `base/` e `overlays/`.
5. Usar indentação com tabs ou 4 espaços em arquivos YAML.
6. Criar arquivos YAML sem comentário descritivo inicial em pt-BR.
7. Modificar diretamente a Base do Boilerplate sem autorização da equipe de Plataforma.

## Estrutura do Projeto e Limites Arquiteturais

### Mapeamento de Requisitos para Componentes

| Categoria FR | Diretório Principal | Componentes |
|---|---|---|
| FR01-FR05 (Local DevEx) | `/`, `/scripts/` | `Makefile`, `k3d.yaml`, scripts |
| FR06-FR09 (IAM) | `/cluster/infrastructure/keycloak-auth/` | Keycloak + PostgreSQL |
| FR10-FR16 (Gateway) | `/cluster/infrastructure/kong-gateway/` | Kong DB-Less |
| FR17-FR19 (Zero-Trust) | `/cluster/boilerplates/` | Base Kustomize com JWT |
| FR20-FR24 (SRE/GitOps) | `/cluster/bootstrap/` | Root App ArgoCD |

### Estrutura Completa de Diretórios

```
cluster-kubernetes/
├── README.md
├── Makefile
├── k3d.yaml
├── .github/workflows/
│   └── lint.yml
├── scripts/
│   ├── cluster-up.sh
│   ├── cluster-down.sh
│   ├── generate-token.sh
│   ├── lint.sh
│   └── status.sh
├── docs/
│   ├── contrato-do-desenvolvedor.md
│   └── bootstrap-emergencia.md
└── cluster/
    ├── bootstrap/
    │   ├── root-app.yaml             # App-of-Apps pai
    │   ├── infra-app.yaml            # Filho: infraestrutura (prune: false)
    │   └── apps-app.yaml             # Filho: aplicações (prune: true, CreateNamespace=true)
    ├── infrastructure/
    │   ├── namespaces/               # Wave 0 (somente namespaces de infraestrutura)
    │   │   └── base/
    │   │       ├── kustomization.yaml
    │   │       └── namespaces.yaml
    │   ├── keycloak-auth/            # Wave 1 (Postgres) + Wave 2 (Keycloak)
    │   │   ├── base/
    │   │   │   ├── kustomization.yaml
    │   │   │   ├── postgres-deployment.yaml
    │   │   │   ├── postgres-service.yaml
    │   │   │   ├── keycloak-deployment.yaml
    │   │   │   ├── keycloak-service.yaml
    │   │   │   ├── keycloak-ingress.yaml
    │   │   │   └── realm-config.json     # Realm, Client e políticas de auditoria
    │   │   └── overlays/{local,homologacao,production}/
    │   ├── kong-gateway/             # Wave 3
    │   │   ├── base/
    │   │   │   ├── kustomization.yaml
    │   │   │   ├── kong-deployment.yaml
    │   │   │   ├── kong-service.yaml
    │   │   │   └── kong-configmap.yaml
    │   │   └── overlays/{local,homologacao,production}/
    │   └── network-policies/
    │       └── base/
    │           ├── kustomization.yaml
    │           └── isolation-policies.yaml
    ├── apps/                         # Wave 4+ (criados pelas equipes)
    └── boilerplates/
        └── api-base-v1/
            ├── CONTRACT.md
            ├── base/
            │   ├── kustomization.yaml
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   └── ingress.yaml          # Blindado: dev preenche variáveis
            └── overlays/{local,homologacao,production}/
```

**Nota sobre `overlays/`:** Cada overlay (`local`, `homologacao`, `production`) contém um `kustomization.yaml` com patches específicos do ambiente (imagens, réplicas, limites de recursos, variáveis). Namespaces de aplicações de negócio são criados automaticamente via `CreateNamespace=true` no ArgoCD, sem exigir edição em `/infrastructure/namespaces/`.

### Limites Arquiteturais

**Limite de Tráfego (Norte-Sul):**
- Todo tráfego externo entra exclusivamente pelo Kong (namespace `kong-gateway`).
- O Kong termina TLS e valida JWKS localmente antes de repassar ao Pod interno.

**Limite de Identidade:**
- O Keycloak é o único emissor de tokens. Nenhum outro componente emite ou assina JWTs.
- O PostgreSQL do Keycloak é acessível somente dentro do namespace `keycloak-auth` (isolado por NetworkPolicy).

**Limite de Configuração (GitOps):**
- O ArgoCD lê exclusivamente do repositório Git. Nenhuma alteração manual no cluster é aceita (exceto Secrets no bootstrap).
- O diretório `cluster/bootstrap/` é o único ponto de entrada do ArgoCD no repositório.
- O `infra-app.yaml` governa a infraestrutura com `prune: false` (Safe-Prune).
- O `apps-app.yaml` governa as aplicações de negócio com `prune: true` (higiene automática).

**Limite do Desenvolvedor (DevEx):**
- Desenvolvedores operam exclusivamente dentro de `/cluster/apps/<sua-api>/`.
- Consomem a Base de `/cluster/boilerplates/api-base-v1/` via referência Kustomize.
- Preenchem variáveis conforme o `CONTRACT.md`. Caso excedam o escopo, acionam a equipe de Plataforma.

### Fluxo de Dados

```
[Cliente Externo]
       │ HTTPS
       ▼
[Kong Gateway] ──validação JWKS──> [Cache Local de Chaves Públicas]
       │                                    ▲
       │ HTTP interno                       │ refresh periódico
       ▼                                    │
[Pod da API de Negócio] ◄──── [Keycloak] ◄──── [PostgreSQL]
       │
       └── valida JWT localmente (Deep Security via SDK/Sidecar)
```

### Integração de Workflow de Desenvolvimento

**Fluxo de Desenvolvimento Local:**
`make up` → lint.sh (validação) → cluster-up.sh (k3d + ArgoCD) → status.sh (resumo + token)

**Fluxo de Deploy (Produção/Homologação):**
Commit no Git → CI (lint.yml) → ArgoCD detecta mudança (pull) → Sync automático respeitando Waves

**Fluxo de Emergência (Dia Zero):**
Criar namespaces → Injetar Secrets → Instalar ArgoCD → Aplicar root-app.yaml → ArgoCD assume

## Resultados da Validação da Arquitetura

### Validação de Coerência

**Compatibilidade de Decisões:**
Todas as decisões tecnológicas funcionam em conjunto sem conflitos. Kong DB-Less (`3.14.0.3`, linha `3.14 LTS`) recebe configurações declarativas via Kustomize, alinhado ao ArgoCD. O Keycloak emite tokens validados localmente pelo Kong via JWKS. O k3d (v5.8.3) suporta o arquivo `k3d.yaml` declarativo. Nenhuma incompatibilidade detectada, desde que a configuração do gateway respeite os defaults mais rígidos introduzidos em `3.14`.

**Consistência de Padrões:**
Os padrões de nomenclatura (`kebab-case`), labels (`app.kubernetes.io/*` com vocabulário controlado), estrutura (`base/overlays` com 3 ambientes) e processo (Sync Waves com annotations explícitas) são aplicados uniformemente. A distinção de escopo (plataforma vs. negócio) está explícita na seção de Enforcement.

**Alinhamento Estrutural:**
A árvore de diretórios reflete diretamente as decisões arquiteturais. O bootstrap granular (3 manifestos) separa as políticas de prune. Os 3 overlays cobrem os 3 ambientes. O `CONTRACT.md` formaliza a abstração do Ingress blindado.

### Cobertura de Requisitos Funcionais

| FR | Descrição | Cobertura Arquitetural | Status |
|---|---|---|---|
| FR01 | `make up` provisiona cluster | `Makefile` + `k3d.yaml` + `/scripts/cluster-up.sh` | Coberto |
| FR02 | `make down` destrói cluster | `Makefile` + `/scripts/cluster-down.sh` | Coberto |
| FR03 | Paridade local-produção | `k3d.yaml` + overlays Kustomize | Coberto |
| FR04 | Token automático no terminal | `/scripts/generate-token.sh` + `status.sh` | Coberto |
| FR05 | Boilerplate YAML para APIs | `/cluster/boilerplates/api-base-v1/` + `CONTRACT.md` | Coberto |
| FR06-FR08 | Gestão de credenciais M2M | `keycloak-auth/` + `realm-config.json` | Coberto |
| FR09 | Logs de auditoria de tokens | `realm-config.json` (config versionada) | Coberto |
| FR10-FR11 | Interceptação e HTTPS | `kong-gateway/` + Ingress blindado na Base | Coberto |
| FR12 | Validação JWKS local | ADR: Validação JWKS Descentralizada | Coberto |
| FR13 | Repasse JWT ao Pod | Configuração Kong DB-Less | Coberto |
| FR14-FR15 | Rate Limiting | Anotações no Ingress via Boilerplate (default conservador) | Coberto |
| FR16 | Bypass Swagger (Local/Homologação) | Overlays `local/` e `homologacao/` | Coberto |
| FR17-FR19 | Deep Security (validação JWT) | Boilerplate com SDK/Sidecar (abstração para dev) | Coberto |
| FR20 | GitOps via ArgoCD | `bootstrap/root-app.yaml` → `infra-app` + `apps-app` | Coberto |
| FR21 | Safe-Prune | `infra-app.yaml` com `prune: false` | Coberto |
| FR22 | Secrets manuais | Sequência de Bootstrap + `docs/bootstrap-emergencia.md` | Coberto |
| FR23 | Restauração de backups | Documentado como processo operacional | Coberto |
| FR24 | Healthchecks públicos | Padrão: `readinessProbe`/`livenessProbe` obrigatórios | Coberto |

### Cobertura de Requisitos Não-Funcionais

| NFR | Cobertura | Status |
|---|---|---|
| Latência < 20ms | ADR: Validação JWKS local (sem introspecção) | Coberto |
| Setup < 5min | `make up` automatizado + footprint limitado | Coberto |
| TLS/HTTPS | Kong como terminador TLS na borda | Coberto |
| Zero segredos no Git | Injeção manual + política de bootstrap | Coberto |
| Imunidade a eviction | PriorityClasses na base de Kong e Keycloak | Coberto |
| Sobrevivência 60min | Cache JWKS + sincronização TTL | Coberto |
| Footprint local | Limites no `k3d.yaml` + validação por linter | Coberto |

### Análise de Lacunas

**Lacunas Críticas:** Nenhuma encontrada.

**Lacunas Importantes Resolvidas Durante a Validação:**
- PriorityClasses adicionadas às bases de infra (NFR-R01).
- Exemplo concreto de consumo do Boilerplate via Kustomize adicionado aos padrões.
- Mecanismo de descoberta automática de apps via glob no `apps-app.yaml` documentado.
- Cenários de recuperação separados (Parcial vs. Total) definidos.
- Primeira história de implementação desambiguada.

**Lacunas Menores (Nice-to-Have):**
- Conteúdo inicial do `docs/contrato-do-desenvolvedor.md` deve ser gerado como história de implementação.
- `docs/bootstrap-emergencia.md` deve ser gerado como história de implementação.

### Checklist de Completude da Arquitetura

**Análise de Requisitos**
- [x] Contexto do projeto analisado profundamente
- [x] Escala e complexidade avaliadas
- [x] Restrições técnicas identificadas
- [x] Preocupações transversais mapeadas

**Decisões Arquiteturais**
- [x] Decisões críticas documentadas com versões
- [x] Stack tecnológico totalmente especificado
- [x] Padrões de integração definidos
- [x] Considerações de performance endereçadas

**Padrões de Implementação**
- [x] Convenções de nomenclatura estabelecidas
- [x] Padrões de estrutura definidos
- [x] Padrões de comunicação especificados
- [x] Padrões de processo documentados

**Estrutura do Projeto**
- [x] Estrutura completa de diretórios definida
- [x] Limites de componentes estabelecidos
- [x] Pontos de integração mapeados
- [x] Mapeamento de requisitos para estrutura completo

### Avaliação de Prontidão da Arquitetura

**Status Geral:** PRONTO PARA IMPLEMENTAÇÃO

**Nível de Confiança:** Alto — baseado em validação abrangente com 16/16 itens do checklist confirmados e nenhuma lacuna crítica remanescente.

**Pontos Fortes:**
- Cobertura funcional completa (24/24 FRs mapeados).
- Segurança validada por Time Vermelho com mitigações concretas.
- Padrões testados por auto-consistência (convergência de agentes validada).
- Jornada do desenvolvedor testada por Teste do Novo Membro (autocontida).
- Decisões fundamentais validadas por Análise de 5 Porquês (raízes reais).

**Áreas para Aprimoramento Futuro:**
- Migração para Gateway API (HTTPRoute) quando o ecossistema amadurecer.
- Service Mesh interno (mTLS) para tráfego East-West na Fase 3.
- Cofres de Segredos Automatizados para rotação contínua.
- IP Whitelisting para rotas de sistemas legados.

### Cenários de Recuperação

**Recuperação Parcial (ArgoCD ativo, componente caído):**
1. Restaurar o componente afetado (ex: backup do PostgreSQL).
2. O ArgoCD detecta a divergência automaticamente.
3. O ArgoCD resincroniza o estado desejado do Git para o cluster.

**Reconstrução Total (cluster perdido, dia zero):**
1. Criar namespaces de infraestrutura.
2. Injetar Secrets manualmente (credenciais do Keycloak, PostgreSQL).
3. Instalar o ArgoCD.
4. Aplicar o manifesto `root-app.yaml` — a partir daqui o ArgoCD assume via Sync Waves.

### Handoff de Implementação

**Diretrizes para Agentes de IA:**
- Seguir todas as decisões arquiteturais exatamente como documentadas.
- Usar padrões de implementação consistentemente em todos os componentes.
- Respeitar a estrutura do projeto e os limites definidos.
- Consultar este documento para todas as questões arquiteturais.

**Primeira História de Implementação (Story 0 — Scaffold):**
Criar a estrutura completa de diretórios do repositório conforme a árvore definida na seção "Estrutura Completa de Diretórios", incluindo o `Makefile` (com targets `up`, `down`, `token`, `lint`), o `k3d.yaml` (com limites de footprint), o `README.md` e os scripts placeholder em `/scripts/`. Esta história NÃO inclui a configuração dos componentes de infraestrutura (Kong, Keycloak, ArgoCD) — apenas o esqueleto vazio do repositório.

**Prioridade Imediata Após o Scaffold:**
- Criação do `CONTRACT.md` do Boilerplate (artefato crítico de adoção — valida a escolha do Kustomize).
- Criação do `docs/contrato-do-desenvolvedor.md` (referência canônica para onboarding).
- Criação do `docs/bootstrap-emergencia.md` (sequência de recuperação para SRE).

**Mecanismo de Descoberta de Apps:**
O `apps-app.yaml` DEVE utilizar descoberta automática de diretórios via padrão glob (`path: cluster/apps/*`). Novas APIs adicionadas em `/cluster/apps/<nome>/` são detectadas automaticamente pelo ArgoCD sem registro manual.

**Exemplo de Consumo do Boilerplate (Overlay do Desenvolvedor):**
```yaml
# kustomization.yaml do Overlay do desenvolvedor em /cluster/apps/api-estoque/overlays/local/
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
# A base referencia o boilerplate:
# /cluster/apps/api-estoque/base/kustomization.yaml contém:
# resources:
#   - ../../../boilerplates/api-base-v1/base
```

### Índice de Referência Rápida

| Componente | Seção do Documento |
|---|---|
| Kong DB-Less | Decisões Arquiteturais Centrais → Padrões de API |
| Keycloak / PostgreSQL | Decisões Centrais → Autenticação e Segurança |
| ArgoCD / Bootstrap | Decisões Centrais → Infraestrutura e Implantação |
| Kustomize / Boilerplates | Padrões de Implementação → Estrutura + Contrato |
| Nomenclatura / Labels | Padrões de Implementação → Nomenclatura |
| Sync Waves / Healthchecks | Padrões de Implementação → Processo |
| Segurança / Hardening | Análise de Contexto → Mitigação e Hardening |
| Estrutura de Diretórios | Estrutura do Projeto → Árvore Completa |
| Limites Arquiteturais | Estrutura do Projeto → Limites |
| Recuperação / Emergência | Validação → Cenários de Recuperação |

# Ata de Decisão Técnica: Estratégia de Escopo de IA para a Pasta .tracker/

* **Data:** 18 de Maio de 2026
* **Filiado a:** cluster-kubernetes
* **Participantes:**
  * **Ismael** (Desenvolvedor Humano / Líder do Projeto)
  * 🏗️ **Winston** (System Architect - Agente BMad)
  * 📚 **Paige** (Technical Writer - Agente BMad)

---

## 1. Contexto e Objetivo

O repositório possui uma pasta utilitária chamada `.tracker/` que contém scripts, Makefile apartado e logs locais para medição de esforço ativo e tempo de desenvolvimento com IAs. 

O objetivo desta mesa redonda foi definir a melhor estratégia técnica para **evitar que assistentes de IA desperdicem tokens de contexto, sofram com poluição visual ou interfiram na lógica de infraestrutura do cluster Kubernetes**, mas garantindo que o próprio utilitário do tracker possa receber manutenção assistida por IA quando explicitamente solicitado.

---

## 2. Abordagens Debatidas

| Abordagem | Funcionamento Técnico | Prós | Contras |
| :--- | :--- | :--- | :--- |
| **1. Bloqueio Nativo Direto** | Criar `.cursorignore`, `.claudeignore` e `.antigravityignore` impedindo qualquer varredura física em `.tracker/`. | Eficiência extrema de tokens (consumo zero); a pasta fica invisível para as engines de IA. | Silent failure (cegueira da IA). Impossibilita manutenção do próprio script do tracker via IA no futuro. Overhead de manter múltiplos arquivos de ignore específicos. |
| **2. Regras Contextuais Globais** | Documentar a restrição apenas no arquivo global de contexto de IA (`project-context.md`). | Mantém a pasta visível sob demanda. Setup único para qualquer assistente de IA. | Carga cognitiva inútil. A IA ainda lê e indexa a pasta em buscas amplas, gerando token drift e possível confusão com makefiles homônimos. |
| **3. Modelo Híbrido Original** | Bloqueio físico nas ignore-lists nativas + documentação contextual em `project-context.md`. | Duplo nível de proteção (físico e lógico). | Mantém a desvantagem do bloqueio nativo (necessidade de alterar arquivos de ignore manualmente na hora de dar manutenção no tracker). |
| **4. Bloqueio Semântico Condicional (Escolhida)** | Sem ignore-lists físicas locais. O acesso ao diretório `.tracker/` é liberado fisicamente, mas isolado semanticamente no arquivo global de contexto. | Preserva 100% a manutenibilidade do tracker por IA. Sem overhead de arquivos de ignore. Regras claras de barreira condicional em pt-BR. | Exige que a IA seja capaz de interpretar e respeitar as fronteiras semânticas de domínio declaradas. |

---

## 3. Pressupostos da Decisão

Os itens abaixo são condições implícitas que sustentam a validade da Abordagem 4. Ao documentá-los explicitamente, garantimos rastreabilidade de causa-raiz caso a decisão precise ser revisitada no futuro.

| # | Pressuposto | Risco se Inválido |
| :--- | :--- | :--- |
| P1 | O assistente de IA carrega `project-context.md` por padrão em cada sessão de trabalho. | A barreira semântica não existe para a IA — colapso silencioso da Abordagem 4. |
| P2 | Há no máximo um desenvolvedor principal operando o repositório por vez. | Um novo colaborador pode integrar um assistente sem a configuração correta, gerando acoplamento indesejado. |
| P3 | O custo operacional de manter regras semânticas é menor que o de manter arquivos de ignore físicos ao longo do tempo. | Pressuposto não quantificado — revisitar se o número de assistentes de IA integrados ao projeto crescer. |

---

## 4. A Decisão Arquitetural e Racional Técnico

Por decisão consensual dos participantes provocada pela intervenção crítica do desenvolvedor humano (**Ismael**), a **Abordagem 4 (Bloqueio Semântico Condicional)** foi eleita como a solução oficial do repositório.

### Justificativa de Winston (Arquitetura & Tokens):
> *"O bloqueio físico silencia o ferramental e gera um silo técnico ineficiente. Toda alteração futura no script `work-tracker.py` exigiria alteração manual de ignores locais do Git. Ao remover os arquivos físicos de ignore e adotar o isolamento semântico de domínio no arquivo global de regras, mantemos a produtividade do desenvolvedor estável, com acoplamento zero de configuração local."*

### Justificativa de Paige (Comunicação & Clareza):
> *"A IA atua muito melhor com regras de 'Acesso Condicional' do que com 'Portas Trancadas Sem Sinalização'. Ao centralizar o escopo sob demanda no `project-context.md`, mitigamos alucinações técnicas caso o desenvolvedor execute comandos locais do tracker, deixando claro o limite de atuação da IA e blindando o Makefile principal."*

---

## 5. Plano de Ação Executado

1. **Abstenção de Ignorações Físicas:** Não foram criados arquivos de ignore locais (`.cursorignore`, `.claudeignore`, `.antigravityignore`). O diretório `.tracker/` continua varrível.
2. **Atualização do Contexto Central:** O arquivo de diretrizes do projeto (`_bmad-output/project-context.md`) foi reestruturado inteiramente para o **Português do Brasil (pt-BR)** para seguir os padrões globais de documentação do repositório.
3. **Escrita da Regra de Escopo:** Foi implementada a nova seção `Isolamento do Domínio do Tracker (.tracker/)` em [project-context.md](file:///_bmad-output/project-context.md#L102-L108) estabelecendo:
   * **Escopo Sob Demanda:** A IA só lê ou altera a pasta `.tracker/` se houver comando direto explícito do humano.
   * **Acoplamento Zero:** Proibição de mesclagem de código ou geração de dependências entre o tracker e o cluster Kubernetes.
   * **Makefile Autônomo:** Garantia de que o `.tracker/Makefile` seja considerado isolado do `Makefile` da raiz do repositório.
4. **Critério de Validação:** A barreira semântica será considerada efetiva se, em uma sessão típica de trabalho de infraestrutura Kubernetes, a IA não referenciar espontaneamente `.tracker/` ou `.tracker/Makefile` sem solicitação explícita do desenvolvedor. Verificação: **manual**, a cada integração de novo assistente de IA no projeto.
5. **Protocolo de Fallback:** Se a barreira semântica falhar (IA referenciando `.tracker/` fora de escopo de forma recorrente), a ação corretiva imediata é reverter para a **Abordagem 3 (Modelo Híbrido):** criar `.cursorignore`, `.claudeignore` e `.antigravityignore` apontando para `.tracker/`, mantendo as regras semânticas no `project-context.md` como camada complementar.

---

Aprovado por aclamação na mesa redonda de desenvolvimento do `cluster-kubernetes`.

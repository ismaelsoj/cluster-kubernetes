# Proposta de Mudança de Sprint (Sprint Change Proposal) - Suporte a Windows via WSL2 Estrito

**ID do Documento:** sprint-change-proposal-2026-05-17
**Data:** 2026-05-17
**Autor:** Antigravity (IA) / Ismael

---

## Seção 1: Resumo do Problema (Issue Summary)

### Declaração do Problema
O planejamento inicial do projeto `cluster-kubernetes` definiu o ciclo de vida local do desenvolvedor baseado em um `Makefile` e scripts Bash (`scripts/*.sh`). No entanto, o `Makefile` e os utilitários Unix padrão não são nativamente compatíveis com sistemas operacionais Windows (CMD/PowerShell) de forma direta.

Para garantir que desenvolvedores Windows consigam executar a esteira local com **atrito zero** e manter a paridade com o padrão da indústria (que utiliza `Makefile` e scripts `shell` como padrões indiscutíveis de automação), definimos o **uso mandatório do WSL2 (Windows Subsystem for Linux)** para ambientes Windows. Isso elimina a necessidade de duplicar lógicas de script em PowerShell (`.ps1`), mantendo a integridade e DRY do repositório.

### Contexto de Descoberta
Identificado e ajustado de forma colaborativa durante a Story 1.2, alinhando a preferência do usuário com as melhores práticas de engenharia de plataforma para evitar débitos técnicos de scripts duplicados.

---

## Seção 2: Análise de Impacto (Impact Analysis)

- **Impacto em Épicos:** O **Épico 1 (Fundação e Automação Local)** permanece idêntico em sua essência, mas com restrições operacionais multiplataforma baseadas em ambiente Unix-like.
- **Impacto em Histórias:** A **Story 1.2 (Makefile e Scripts de Automação Local)** foi estendida para prever a execução do Makefile no WSL2 para máquinas Windows.
- **Conflitos de Artefatos:**
  - **PRD:** Requisitos **FR01, FR02** e **NFR-P02** atualizados para citar explicitamente o WSL2 como o canal de entrada no Windows.
  - **Architecture:** Documentação do Starter atualizada para impor a decisão do uso do WSL2 no Windows, mantendo apenas `Makefile` e `Bash` como linguagens/runtimes da automação local.
- **Impacto Técnico:** Sem impacto técnico prejudicial ou duplicação de automação. Zero código extra no repositório.

---

## Seção 3: Abordagem Recomendada (Recommended Approach)

### Caminho Escolhido: Uso do WSL2 Estrito (WSL2 Mandatory Integration)
Manter o `Makefile` e os scripts `.sh` originais e obrigar os desenvolvedores Windows a rodar a esteira local dentro de uma distribuição Linux (como Ubuntu) no WSL2 com integração ao Docker Desktop.

- **Esforço Estimado:** Extremamente Baixo. Não requer criação de novos códigos no repositório, apenas documentação precisa.
- **Nível de Risco:** Nulo (sem risco de divergência sintática de scripts).
- **Justificativa:** Consolida a simplicidade do repositório, evita a redundância de manter scripts PowerShell (`.ps1`) paralelos e incentiva o uso de ferramentas nativas do ecossistema Kubernetes (que operam de forma muito mais natural em ambientes baseados em Linux).

---

## Seção 4: Propostas Detalhadas de Mudança (Detailed Change Proposals)

### 1. Documento de Requisitos (PRD)
*   **Seção Afetada:** Requisitos Funcionais (FR01, FR02) e Não-Funcionais (NFR-P02).
*   **Ajuste:** Os caminhos de entrada do cluster continuam sendo estritamente `make up` e `make down`, devendo rodar no macOS/Linux nativamente ou sob o ambiente WSL2 no Windows.

### 2. Documento de Decisão de Arquitetura (Architecture)
*   **Seção Afetada:** Starter Decisions, Padrões de Estrutura e Cobertura de Requisitos.
*   **Ajuste:** Inclusão do WSL2 no Windows como decisão central de runtime local, mantendo a árvore estrutural do projeto limpa de scripts `.ps1`.

### 3. Backlog de Épicos e Histórias (Epics)
*   **Seção Afetada:** Story 1.2.
*   **Ajuste:** Critérios de aceitação focados exclusivamente no funcionamento do `Makefile` e scripts `.sh` sob WSL2 no caso do Windows.

### 4. Guia do Repositório (README.md)
*   **Seção Afetada:** Pré-requisitos e Início Rápido.
*   **Ajuste:** Criação de um guia de setup rápido e limpo de 3 passos para usuários Windows instalarem as dependências dentro do WSL2 (Ubuntu) e ativarem a integração com o Docker Desktop.

---

## Seção 5: Handoff de Implementação (Implementation Handoff)

*   **Classificação do Escopo:** Menor (Minor).
*   **Responsáveis pelo Handoff:** Engenheiro de Plataforma (IA) para o Desenvolvedor Humano (Ismael).
*   **Critérios de Sucesso para Implementação:**
    1.  O `README.md` explica de forma clara como habilitar a integração WSL no Docker Desktop e como instalar `make`, `kubectl` e `k3d` no Ubuntu do WSL2.
    2.  O repositório está limpo de quaisquer arquivos duplicados (como `.ps1`).
    3.  Toda automação continua baseada no `Makefile` e scripts `/scripts/*.sh`.

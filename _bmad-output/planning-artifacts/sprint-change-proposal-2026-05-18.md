# Proposta de Mudança de Sprint (Sprint Change Proposal) - Substituição de Linter Manual por Conftest (OPA)

**ID do Documento:** sprint-change-proposal-2026-05-18  
**Data:** 2026-05-18  
**Autor:** Antigravity (IA) / Ismael  
**Status:** Aprovado  
**Data de Aprovação:** 2026-05-18  

---

## Seção 1: Resumo do Problema (Issue Summary)

### Declaração do Problema
O planejamento inicial da **Story 1.4 (Linter YAML, Pipeline CI e README)** previu a validação de nomenclatura de recursos e namespaces no formato `kebab-case`. Para atender a este requisito, a implementação inicial desenvolveu um script em Python (`scripts/validate_yaml.py`). 

No entanto, o script implementado realiza uma análise **linha a linha textual do YAML com expressões regulares**, tentando simular um parser de escopo de indentação de espaços para identificar os blocos de `metadata:`. 

Esta estratégia é altamente frágil porque tenta tratar dados estruturados complexos como texto plano. Ela falha facilmente diante de:
* Comentários inline ou multilinhados.
* Chaves `metadata` aninhadas sob especificações de templates (como Deployments ou Custom Resources).
* Diferentes estilos de formatação e espaçamento gerados pelo Kustomize.
* Uso de separadores de documentos `---` em arquivos consolidados.

A prova de sua fragilidade técnica é que, apenas na fase de code review, foram necessários **5 patches emergenciais** para consertar problemas do parser caseiro. Manter esse script Python customizado criará um gargalo operacional crônico para a equipe de desenvolvimento à medida que novos manifestos e CRDs forem adicionados à plataforma.

### Contexto de Descoberta
Identificado de forma proativa após a finalização da Story 1.4, durante a avaliação crítica de viabilidade e sustentabilidade da automação do repositório a longo prazo.

---

## Seção 2: Análise de Impacto (Impact Analysis)

*   **Impacto em Épicos:** O **Épico 1 (Fundação do Repositório, Automação Local e Bootstrap GitOps)** permanece viável e sem alteração de prazos. A validação estrita de manifestos continua como gate local e em CI, mas apoiada em motores de mercado maduros.
*   **Impacto em Histórias:** A **Story 1.4 (Linter YAML, Pipeline CI e README)** sofrerá um ajuste em suas subtasks técnicas e critérios de aceitação. Substitui-se o script customizado `validate_yaml.py` pela implementação de uma política declarativa Rego em `policy/kebab-case.rego` e sua execução via **Conftest**.
*   **Conflitos de Artefatos:**
    *   **PRD:** Sem conflito com os requisitos ou metas de negócio. O FR01 (validação local) e NFR-S02 (segurança de segredos) continuam plenamente atendidos.
    *   **Decisão de Arquitetura (architecture.md):** A seção `Padrões de Processo -> Validação Automatizada (Linter)` deve ser atualizada para citar explicitamente o uso do `Conftest (OPA)` como a engine oficial de lint estrutural ao lado do `kube-linter`.
    *   **Contexto do Projeto (project-context.md):** A listagem de Stack de Tecnologia deve incluir o `Conftest (OPA)`.
    *   **História 1.4 (1-4-linter-yaml-pipeline-ci-readme.md):** Atualização do escopo de tarefas e critérios de aceitação para formalizar a transição para Conftest e exclusão do script Python antigo.
*   **Impacto Técnico:** Extremamente positivo. Remove código proprietário frágil, elimina o débito técnico de parser Regex caseiro de YAML e adota um padrão consolidado na indústria de SecOps e Cloud-Native (OPA/Rego).

---

## Seção 3: Abordagem Recomendada (Recommended Approach)

### Caminho Escolhido: Substituição Integral por Conftest (OPA)
Adoção do **Conftest (Open Policy Agent)** para realizar a validação de nomenclatura `kebab-case` e quaisquer regras estruturais futuras sobre os manifestos YAML compilados.

*   **Esforço Estimado:** Baixo (Low). A criação de uma política declarativa em Rego contendo poucas linhas é rápida e trivial. A integração no `lint.sh` exige poucas substituições de linhas.
*   **Nível de Risco:** Nulo a Muito Baixo. O Conftest é uma ferramenta compilada em Go com alto desempenho, rodando nativamente no pipeline do GitHub Actions e com suporte transparente via Docker local (atrito zero).
*   **Justificativa:** Trata o YAML como árvore estruturada de dados real, imunizando o linter de falhar com estilos de comentários ou formatação sintática. Estabelece uma fundação extensível de "Policy-as-Code" pronta para as Fases 2, 3 e 4.

---

## Seção 4: Propostas Detalhadas de Mudança (Detailed Change Proposals)

### 1. Documento de Decisão de Arquitetura (architecture.md)
*   **Seção Afetada:** `Padrões de Processo -> Validação Automatizada (Linter)` (Linha 297)
*   **Ajuste:**
```diff
- - O repositório DEVE incluir um linter YAML (ex: `kube-linter`) configurado para validar automaticamente nomenclatura, labels obrigatórios e proibição da tag `latest`.
+ - O repositório DEVE incluir validações automatizadas de manifestos YAML através do `kube-linter` (para boas práticas e segurança) e do `Conftest` baseado em Open Policy Agent - OPA (para regras estruturais e de nomenclatura, como o padrão kebab-case).
```

---

### 2. Contexto do Projeto (project-context.md)
*   **Seção Afetada:** `Stack de Tecnologia e Versões` (Linha 26)
*   **Ajuste:**
```diff
- - **kube-linter** (a configurar na Story 1.4) — validação automática de manifestos YAML
+ - **kube-linter** & **Conftest (OPA)** (a configurar na Story 1.4) — validação automática estrutural e de segurança de manifestos YAML
```

---

### 3. Backlog de Épicos e Histórias (epics.md)
*   **Seção Afetada:** `Story 1.4: Linter YAML, Pipeline CI e README` (Linha 193)
*   **Ajuste:**
```diff
- **Então** valida: `kebab-case`, labels `app.kubernetes.io/*`, proibição `latest`, probes obrigatórios
- **E** `make up` falha se violações detectadas
+ **Então** valida: `kebab-case` (via Conftest OPA), labels `app.kubernetes.io/*`, proibição `latest` e probes obrigatórios (via kube-linter)
+ **E** `make up` falha se violações em qualquer validador forem detectadas
```

---

### 4. História 1.4 (1-4-linter-yaml-pipeline-ci-readme.md)
*   **Seção Afetada:** `Acceptance Criteria 1` e `Tasks`
*   **Ajustes:**

#### Critério de Aceitação 1:
```diff
- 1. **[LINT-SCRIPT-IMPLEMENTATION]** Dado que o script `scripts/lint.sh` está configurado para usar `kube-linter` e `kustomize`, quando executado (tanto de forma avulsa pelo `make lint` quanto pelo `make up`), então ele deve validar de forma recursiva todos os recursos gerados pelo `kustomize build` nos diretórios do cluster (incluindo `cluster/bootstrap/` e `cluster/infrastructure/`). A validação deve garantir de forma rígida:
-    - **Nomenclatura Kubernetes**: Recursos e namespaces em `kebab-case` (`kebab-case-names-only`).
+ 1. **[LINT-SCRIPT-IMPLEMENTATION]** Dado que o script `scripts/lint.sh` está configurado para usar `kube-linter`, `conftest` (OPA) e `kustomize`, quando executado (tanto de forma avulsa pelo `make lint` quanto pelo `make up`), então ele deve validar de forma recursiva todos os recursos gerados pelo `kustomize build` nos diretórios do cluster. A validação deve garantir de forma rígida:
+    - **Nomenclatura Kubernetes (Conftest OPA)**: Recursos e namespaces em `kebab-case` avaliados estruturalmente por políticas declarativas escritas em Rego sob a pasta `policy/`.
```

#### Tarefas:
```diff
- - [x] **Tarefa 1: Implementar o script `scripts/lint.sh` completo** (AC: #1)
-   - [x] Adicionar suporte à verificação e bypass imediato se `SKIP_LINT=1` estiver setada no topo do script.
-   - [x] Implementar a lógica de busca local do binário `kube-linter`.
-   - [x] Se `kube-linter` não for encontrado no PATH, implementar o fallback transparente via Docker:
-     - [x] Rodar container `docker run --rm -v "$(pwd):/dir" stackrox/kube-linter:v0.8.3 lint /dir/cluster/` (com fallback para v0.8.3 estável e imutável).
-   - [x] Garantir que o linter valide manifestos gerados pelo `kustomize build` para todas as pastas de infraestrutura (`cluster/infrastructure/namespaces`, `cluster/infrastructure/keycloak-auth`, `cluster/infrastructure/kong-gateway`, etc.).
-   - [x] Adicionar guarda anti-"Falso Verde": ler o output do `kustomize build` e garantir que o número de manifestos compilados é maior que 0 (`grep -c "kind:"` ou similar). Abortar com erro se 0 objetos forem encontrados para lint.
-   - [x] Garantir que o script retorne exit code não nulo se violações de nomenclatura, labels ausentes, tags `:latest` ou falta de probes forem detectadas.
+ - [x] **Tarefa 1: Implementar a orquestração do script `scripts/lint.sh` com Conftest e Kube-linter** (AC: #1)
+   - [x] Adicionar suporte à verificação e bypass imediato se `SKIP_LINT=1` estiver setada no topo do script.
+   - [x] Garantir que o linter valide manifestos gerados pelo `kustomize build` para todas as pastas de infraestrutura.
+   - [x] Adicionar guarda anti-"Falso Verde": ler o output do `kustomize build` e garantir que o número de manifestos compilados é maior que 0. Abortar com erro se 0 objetos forem encontrados.
+   - [x] Garantir que o script retorne exit code não nulo se violações forem detectadas por qualquer ferramenta.
+   - [ ] Implementar a política OPA/Rego de validação de nomenclatura `kebab-case` para recursos e namespaces em `policy/kebab-case.rego`.
+   - [ ] Integrar a execução do `conftest` localmente no `scripts/lint.sh`.
+   - [ ] Se o `conftest` não for encontrado localmente, implementar o fallback automático via Docker rodando a imagem `openpolicyagent/conftest:v0.45.0` (ou estável equivalente) para analisar a pasta `.tmp-lint`.
+   - [ ] Remover completamente o script legado e frágil `scripts/validate_yaml.py` e suas referências.
```

---

## Seção 5: Handoff de Implementação (Implementation Handoff)

*   **Classificação do Escopo:** Menor (Minor).
*   **Destinatário do Handoff:** Desenvolvedor (Agente Dev / Ismael) para implementação imediata no ramo `1-4-linter-yaml-pipeline-ci-readme`.
*   **Critérios de Sucesso para Implementação:**
    1.  Políticas escritas em Rego sob a pasta `/policy/` validam com precisão nomes e namespaces em `kebab-case`.
    2.  O arquivo `/scripts/validate_yaml.py` foi sumariamente deletado do repositório.
    3.  O script `/scripts/lint.sh` executa `kube-linter` e `conftest` em sequência sobre a pasta temporária compilada.
    4.  O pipeline do GitHub Actions `/ .github/workflows/lint.yml` está atualizado para rodar ambas as ferramentas sobre os manifestos, rejeitando execuções com erros de segurança ou nomenclatura.
    5.  Validador local e em CI resilientes a comentários e quebras de linhas de YAML.

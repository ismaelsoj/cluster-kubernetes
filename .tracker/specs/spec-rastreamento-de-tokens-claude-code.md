---
title: 'Rastreamento de Tokens (Claude Code)'
type: 'feature'
created: '2026-05-25'
status: 'pronto-para-desenvolvimento'
baseline_commit: 'de16f1a'
complexity: 'Média Complexidade'
context: []
---

# História BKL-001: Rastreamento de Tokens (Claude Code)

Status: pronto-para-desenvolvimento

## História

Como desenvolvedor ou gestor do projeto,
Quero rastrear o consumo detalhado de tokens (entrada, saída e cache) nas interações com o Claude Code,
Para estimar o custo por modelo, responder a perguntas de viabilidade financeira (ex: Claude Opus vs. Claude Sonnet) e analisar métricas de investimento baseadas em consumo de tokens.

## Critérios de Aceite

1. **Coleta de dados de tokens:**
   - O script `work-tracker.py` na função `analyze_claude_code(repo_root)` deve ler com sucesso o campo `usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`) contido na estrutura `message.usage` das entradas cujo `type` seja `"assistant"` nos logs de sessão JSONL do Claude Code (`~/.claude/projects/*/*.jsonl`).

2. **Propagação de campos no pipeline:**
   - Os tokens coletados devem ser associados aos respectivos eventos de ping do Claude Code.
   - Na função `aggregate_sessions(sessions)`, os tokens devem ser acumulados nas estruturas `daily_stats` e `branch_stats` por dia de trabalho, ferramenta ("Claude Code") e modelo.

3. **Schema e Persistência de Eventos:**
   - Os eventos do tipo `activity_daily` e `activity_branch` persistidos em `.tracker/events/dev-<hash>.jsonl` devem incluir novos campos de tokens:
     - `input_tokens` (inteiro)
     - `output_tokens` (inteiro)
     - `cache_creation_input_tokens` (inteiro)
     - `cache_read_input_tokens` (inteiro)
   - O evento do tipo `dev_summary` deve incluir os totais acumulados para o escopo correspondente:
     - `total_input_tokens` (inteiro)
     - `total_output_tokens` (inteiro)
     - `total_cache_creation_input_tokens` (inteiro)
     - `total_cache_read_input_tokens` (inteiro)

4. **Compatibilidade Reversa (Resiliência):**
   - Ao ler eventos passados ou eventos sem dados de tokens em `load_all_events(events_dir)` e `emit_events(...)`, a ausência dos novos campos não deve quebrar a execução e deve ser interpretada com fallback automático para `0`.
   - Como o Antigravity não expõe dados de tokens localmente (BKL-002), os seus eventos devem possuir campos de tokens zerados (`0`5. **Interface e Apresentação do Relatório (Markdown - TEMPO_DE_TRABALHO.md):**
   - **Novo Relatório/Tabela de Tokens:** Se houver consumo de tokens registrado para o desenvolvedor atual, exibir a nova seção `### 🪙 Consumo de Tokens (Claude Code)` contendo:
     ```markdown
     ### 🪙 Consumo de Tokens (Claude Code)

     | Dia de Trabalho | Modelo LLM | Entrada (Prompt) | Saída (Completion) | Cache Lido | Cache Criado | Total |
     | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
     | DD/MM/AAAA | Nome do Modelo | N.NNN | N.NNN | N.NNN | N.NNN | N.NNN |
     ```
     A tabela deve conter a formatação de milhar com pontos (ex: `142.500`) e exibir a soma acumulada de todas as colunas no rodapé.
   - **Atualização das Tabelas Existentes:**
     - Na tabela `### 🛠️ Totais por Ferramenta`, adicionar a coluna `Tokens (Entrada / Saída)` no final. Exemplo para o Claude Code: `1.240.500 / 312.000`. Para o Antigravity: `N/A`.
     - Na tabela `### 🗓️ Detalhamento Diário das Horas (Brasília)`, adicionar a coluna `Tokens (Entrada / Saída)` no final. Para o Antigravity: `N/A`.
     - Na tabela `### 🌿 Detalhamento Diário por Branch / História (Brasília)`, adicionar a coluna `Tokens (Entrada / Saída)` no final, somando todos os tokens consumidos pelo Claude Code naquela branch/dia. Se a branch só usou Antigravity: `N/A`.
     - No cabeçalho principal do desenvolvedor, atualizar a linha de interações para incluir o total de tokens do Claude Code consumidos. Exemplo: `* **Total de Interações:** **X comandos** em Y sessões (Z tokens totais no Claude Code)`.
   - **Resiliência visual:** Se nenhum token for registrado para o desenvolvedor no período analisado, as colunas nas tabelas existentes devem exibir `0` ou `N/A` de forma limpa, e a tabela de tokens específica não deve ser renderizada.

6. **Relatório impresso no Terminal (Console Read-only):**
   - No relatório exibido via `make -f .tracker/Makefile track-time`, adicionar a exibição de tokens abreviada ao lado de cada modelo sob a seção `[Claude Code]`.
   - Exemplo:
     ```
     [Claude Code]
      • Claude Sonnet 4.6: 1h 30m (Tokens: 1.2M In / 312k Out)
     ```

## Plano de Validação Manual

### 1. Testes Automatizados
- Executar os testes unitários existentes para garantir regressão zero:
  ```bash
  python3 -m unittest scratch/test_tracker.py
  ```
- Criar novos casos de teste unitário em `scratch/test_tracker.py` contemplando:
  - O parsing de linhas do Claude Code contendo o campo `usage`.
  - A agregação de tokens na função `aggregate_sessions`.
  - O fallback seguro para registros passados/Antigravity sem as chaves de tokens.
  - A correta formatação dos números de tokens para a renderização Markdown.

### 2. Validação Visual e Persistência
- Rodar o rastreador em modo de console (apenas leitura):
  ```bash
  make -f .tracker/Makefile track-time
  ```
  - Verificar se a listagem sob `[Claude Code]` exibe o consumo de tokens correspondente de forma abreviada (`K` para milhares, `M` para milhões).
- Executar a exportação do relatório:
  ```bash
  make -f .tracker/Makefile track-time EXPORT=true
  ```
  - Verificar se o arquivo `.tracker/events/dev-<hash>.jsonl` possui os novos campos estruturados.
  - Verificar no arquivo `.tracker/TEMPO_DE_TRABALHO.md`:
    1. A nova tabela `### 🪙 Consumo de Tokens (Claude Code)` com formatação de pontos.
    2. A nova coluna `Tokens (Entrada / Saída)` nas tabelas de `Totais por Ferramenta`, `Detalhamento Diário` e `Detalhamento por Branch`.
    3. A indicação de tokens totais no resumo geral do desenvolvedor.

## Tarefas / Subtarefas

- [ ] **Fase de Preparação e Infraestrutura**
  - [ ] Validar e ajustar os testes existentes se necessário.
  - [ ] Implementar mock de log do Claude Code com dados de `usage` na suite de testes para viabilizar TDD.
- [ ] **Coleta e Processamento (work-tracker.py)**
  - [ ] Atualizar `analyze_claude_code` para ler o campo `usage` aninhado em `message` quando `type == "assistant"`.
  - [ ] Modificar o retorno de pings da função para incluir campos de tokens.
  - [ ] Atualizar `aggregate_sessions` para somar os tokens nas estatísticas diárias e por branch.
- [ ] **Persistência de Dados**
  - [ ] Atualizar `build_live_events` para propagar os valores agregados de tokens para `activity_daily` e `activity_branch`.
  - [ ] Modificar `emit_events` para somar e injetar os campos de tokens totais no `dev_summary` correspondente.
  - [ ] Ajustar `load_all_events` e o parser de `legacy` para garantir resiliência e fallbacks corretos para `0`.
- [ ] **Apresentação no Terminal**
  - [ ] Formatar o consumo de tokens de forma abreviada (ex: `1.2M`, `142k`).
  - [ ] Atualizar `show_console_report` para injetar a string de tokens nos modelos listados sob o Claude Code.
- [ ] **Apresentação no Markdown (Visualização)**
  - [ ] Atualizar a função `render_report` para gerar a tabela `### 🪙 Consumo de Tokens (Claude Code)` se houver tokens registrados.
  - [ ] Adicionar coluna de tokens nas tabelas existentes (`Totais por Ferramenta`, `Detalhamento Diário`, `Detalhamento por Branch`).
  - [ ] Injetar os tokens formatados com pontos de milhar no Markdown.
  - [ ] Adicionar o total de tokens no cabeçalho do desenvolvedor.
  - [ ] Garantir resiliência visual (exibir `N/A` ou `0` para o Antigravity).
- [ ] **Validação Final**
  - [ ] Executar regressão completa usando a suite de testes.
  - [ ] Validar a escrita correta no JSONL e no Markdown de saída.

## Notas de Desenvolvimento

- **Estrutura de dados agregada:**
  As tabelas `daily_stats` e `branch_stats` devem expandir a folha de dados para incluir os contadores de tokens:
  ```python
  # Novo formato da folha daily_stats[d][t][m]
  {
      "hours": 0.0, 
      "sessions": 0, 
      "interactions": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 0
  }
  ```
- **Campos opcionais:** O Python suporta `.get(key, 0)` para manipulação de dicionários sem quebras por chaves inexistentes. Use este padrão em toda a deserialização.
- **Função de formatação de tokens:** Recomenda-se criar uma função utilitária para formatar números inteiros com pontos (ex: `1.234.567`) para uso no Markdown, e outra para formato abreviado (ex: `1.2M` ou `123k`) para o console.

### Notas sobre a Estrutura do Projeto
- A alteração é estritamente localizada em `.tracker/work-tracker.py` e `.tracker/scratch/test_tracker.py`. O isolamento semântico de `.tracker/` está mantido.

### Referências
- Documentação do Backlog do Tracker: [.tracker/tracker-distillate/03-backlog-e-divida-tecnica.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/tracker-distillate/03-backlog-e-divida-tecnica.md)
- Decisões de Arquitetura do Tracker (ADR-07): [.tracker/tracker-distillate/01-arquitetura-e-visao-geral.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/tracker-distillate/01-arquitetura-e-visao-geral.md)

## Registro do Agente de Desenvolvimento

### Modelo de Agente Utilizado
Gemini 3.5 Flash (High)

### Referências de Log de Depuração
N/A

### Lista de Notas de Conclusão
N/A

### Lista de Arquivos
N/A

## Histórico de Alterações (Change Log)

| Data e Hora (Brasília) | Autor | Modelo | Descrição |
| :---: | :--- | :--- | :--- |
| 2026-05-25 15:13:30-03:00 | Gemini 3.5 Flash | Gemini 3.5 Flash (High) | Criação da especificação de história inicial para rastreamento de tokens. |
| 2026-05-25 15:17:35-03:00 | Gemini 3.5 Flash | Gemini 3.5 Flash (High) | Inclusão de exibição de tokens em relatórios e tabelas atuais a pedido do usuário. |

---
Autoria/Implementação: Gemini 3.5 Flash (High)

---
title: 'Exportação JSON/CSV'
type: 'feature'
created: '2026-05-25'
status: 'revisao'
baseline_commit: '0b6c273'
complexity: 'Baixa Complexidade'
context:
  - '.tracker/specs/spec-rastreamento-de-tokens-claude-code.md'
---

# História BKL-003: Exportação JSON/CSV

Status: revisao

## Contexto

Atualmente, o script de rastreamento de tempo (`work-tracker.py`) gera e atualiza relatórios exclusivamente em formato Markdown (`.tracker/TEMPO_DE_TRABALHO.md`). Embora seja legível para humanos, o formato Markdown dificulta a extração e a análise automatizada das métricas de esforço e tokens por ferramentas de dados (como Jupyter Notebooks, Pandas, planilhas eletrônicas ou dashboards BI).

Para facilitar análises programáticas avançadas (ex: cálculo de médias, projeção de custos e consolidação de tempo multi-desenvolvedor sem a necessidade de parsing de tabelas Markdown complexas), o script deve permitir exportar todos os eventos compilados de forma nativa em formatos JSON e CSV.

## História

Como desenvolvedor ou analista que analisa os dados de esforço de IA no projeto,
Quero exportar as métricas consolidadas de tempo e tokens em formatos JSON e CSV através de parâmetros de linha de comando,
Para facilitar a análise de dados externa e a integração com scripts analíticos ou planilhas.

## Critérios de Aceitação

1. **Opção de Formato de Saída (`--format`):**
   - O script `work-tracker.py` deve aceitar um novo argumento opcional `--format` com as opções válidas: `markdown`, `json` e `csv`. O padrão deve ser `markdown`.
   - Exemplo de uso: `python3 .tracker/work-tracker.py --export --format json`
   - O argumento `--format` deve funcionar somente quando `--export` for especificado. Se o usuário rodar sem `--export`, o script exibirá apenas o relatório no console e ignorará a flag `--format`.
   - Se for informado um formato inválido ou não suportado, o `argparse` deve impedir a execução e exibir o erro padrão de argumentos inválidos.

2. **Lógica de Exportação JSON:**
   - Ao rodar com `--export --format json`, o script deve consolidar todos os eventos armazenados nos arquivos `dev-*.jsonl` da pasta `.tracker/events/` (carregados via `load_all_events()`).
   - Os eventos consolidados devem ser gravados no arquivo `.tracker/TEMPO_DE_TRABALHO.json`.
   - O arquivo JSON exportado deve conter um array contendo todos os objetos de eventos compilados (sem alteração nos campos).
   - A escrita do arquivo deve ser atômica usando o padrão `.tmp` e `os.replace()`. O JSON final deve ser formatado com indentação de 2 espaços e suporte a caracteres UTF-8 (`ensure_ascii=False`).

3. **Lógica de Exportação CSV:**
   - Ao rodar com `--export --format csv`, o script deve consolidar todos os eventos e gravá-los no arquivo `.tracker/TEMPO_DE_TRABALHO.csv`.
   - Como os eventos possuem tipos e estruturas diferentes (`dev_summary`, `activity_daily` e `activity_branch`), a exportação CSV deve tabular todos os eventos em uma única estrutura de tabela plana (denormalizada).
   - O arquivo CSV final deve conter exatamente as seguintes colunas, com os respectivos mapeamentos de campos:
     - `developer`: ID mascarado do desenvolvedor (`developer`).
     - `event_type`: Tipo do evento (`event_type`).
     - `scope`: Escopo do sumário (campo `scope` para `dev_summary`, vazio para os outros).
     - `date`: Data do evento no formato `YYYY-MM-DD` (campos `date` para `activity_daily` e `activity_branch`, vazio para `dev_summary`).
     - `branch`: Branch ativa (campo `branch` para `activity_branch`, vazio para os outros).
     - `tool`: Ferramenta utilizada (campo `tool` para `activity_daily`, lista consolidada separada por vírgula para `activity_branch`, vazio para `dev_summary`).
     - `model`: Modelo de linguagem (campo `model` para `activity_daily`, lista consolidada separada por vírgulas para `activity_branch`, vazio para `dev_summary`).
     - `hours`: Horas de desenvolvimento registradas (tipo decimal float, ou vazio se não houver).
     - `sessions`: Número de sessões ativas (campo `sessions` para `dev_summary` ou `activity_daily`, vazio para `activity_branch`).
     - `interactions`: Quantidade de interações (campo `interactions` de `activity_daily` / `activity_branch` ou `total_interactions` de `dev_summary`).
     - `input_tokens`: Quantidade de tokens de entrada (`input_tokens` / `total_input_tokens`).
     - `output_tokens`: Quantidade de tokens de saída (`output_tokens` / `total_output_tokens`).
     - `cache_creation_input_tokens`: Tokens de criação de cache (`cache_creation_input_tokens` / `total_cache_creation_input_tokens`).
     - `cache_read_input_tokens`: Tokens lidos de cache (`cache_read_input_tokens` / `total_cache_read_input_tokens`).
     - `generated_at`: Timestamp de geração do evento.
   - O delimitador deve ser a vírgula (`,`) e o cabeçalho deve ser a primeira linha. Valores ausentes devem ser representados como string vazia `""`. Strings contendo vírgulas devem ser escapadas com aspas duplas, de acordo com o padrão RFC 4180.
   - A escrita do arquivo deve ser atômica usando o padrão `.tmp` e `os.replace()`.

4. **Integração com o Makefile:**
   - O arquivo `.tracker/Makefile` deve ser atualizado para suportar o parâmetro `FORMAT` no target `track-time`.
   - O target `track-time` deve aceitar a variável `FORMAT` (opções: `json`, `csv`, com fallback para `markdown` se não especificada ou se não coincidir com as opções válidas).
   - Exemplo: `make -f .tracker/Makefile track-time EXPORT=true FORMAT=json` deve rodar o script python com `--export --format json`.

## Plano de Validação Manual

### 1. Testes Automatizados

Devem ser criados casos de teste unitários no arquivo `.tracker/test_tracker.py` para garantir o funcionamento correto:
- `test_export_json_format`: Cria eventos de teste mock, chama a rotina de exportação no formato JSON, lê o arquivo gerado e valida se o conteúdo é um JSON válido e se contém todos os eventos com os respectivos tipos.
- `test_export_csv_format`: Cria eventos de teste mock, chama a rotina de exportação no formato CSV, lê as linhas e valida se a quantidade de colunas está correta, se o cabeçalho é respeitado e se os valores de cada coluna correspondem aos dados de teste.
- `test_export_formats_atomic_write`: Valida se o processo de escrita cria os arquivos temporários e substitui de forma segura, garantindo atomicidade.

Para executar os testes:
```bash
python3 .tracker/test_tracker.py -v
```

### 2. Testes de Integração Local (Validação Manual)

Execute os comandos a seguir no terminal para testar a geração local dos relatórios:

```bash
# 1. Exportar em formato JSON
make -f .tracker/Makefile track-time EXPORT=true FORMAT=json

# Verificar a existência do arquivo JSON
cat .tracker/TEMPO_DE_TRABALHO.json | jq .

# 2. Exportar em formato CSV
make -f .tracker/Makefile track-time EXPORT=true FORMAT=csv

# Verificar as primeiras linhas do CSV
head -n 5 .tracker/TEMPO_DE_TRABALHO.csv

# 3. Validar se a execução normal em Markdown continua intacta
make -f .tracker/Makefile track-time EXPORT=true FORMAT=markdown
ls -la .tracker/TEMPO_DE_TRABALHO.md
```

## Tarefas / Subtarefas

- [x] **Fase de Preparação e Testes**
  - [x] Adicionar casos de teste no arquivo `test_tracker.py` para verificar a exportação nos formatos JSON e CSV (devem falhar inicialmente - RED).
- [x] **Modificação do Script `work-tracker.py`**
  - [x] Adicionar a flag `--format` com `choices=["markdown", "json", "csv"]` e padrão `"markdown"` no parser CLI (`ArgumentParser`).
  - [x] Adaptar a função `main()` para repassar o formato escolhido.
  - [x] Criar a função `export_json_report(events_dir, masked_id, live_events, repo_root)` que consolida os eventos e gera o JSON formatado.
  - [x] Criar a função `export_csv_report(events_dir, masked_id, live_events, repo_root)` que consolida os eventos, faz a tabulação plana mapeando as colunas e escreve o arquivo CSV respeitando o padrão RFC 4180.
  - [x] Implementar a escrita atômica nas novas funções utilizando arquivos temporários e `os.replace()`.
- [x] **Modificação do Makefile**
  - [x] Atualizar `.tracker/Makefile` para aceitar a variável `FORMAT` (padrão `markdown`) e repassar para o script python.
- [x] **Validação e Finalização**
  - [x] Executar todos os testes unitários (`python3 .tracker/test_tracker.py`) e garantir que estão verdes (GREEN).
  - [x] Executar manualmente comandos de exportação para JSON e CSV, verificando se os arquivos `.tracker/TEMPO_DE_TRABALHO.json` e `.tracker/TEMPO_DE_TRABALHO.csv` são criados com os dados corretos.

## Notas de Desenvolvimento

- **Consolidação de Eventos:** O script já possui a função `load_all_events(events_dir)` que lê e unifica todos os eventos de todos os arquivos `dev-*.jsonl` na pasta de eventos. Essa função deve ser reutilizada para os exports JSON e CSV, exatamente como é feito em `export_markdown_report()`.
- **Mapeamento de colunas CSV:** Como o CSV é plano, eventos que não possuem certas propriedades devem conter o valor correspondente em branco `""` na linha. Por exemplo, `dev_summary` não possui campo `date`, portanto sua coluna `date` ficará como `""`.
- **Delimitador de CSV:** Utilizar vírgula (`,`) como delimitador. É essencial tratar strings que contenham vírgula (como a lista de ferramentas/modelos no evento `activity_branch`), envolvendo esses valores em aspas duplas: `f'"{", ".join(tools)}"'`.

### Notas sobre a Estrutura do Projeto

- Sem dependências externas de bibliotecas adicionais Python (utilizar apenas módulos integrados da stdlib como `json`, `csv` e `os`). Isso respeita a diretriz de **Stdlib pura** definida no arquivo `.tracker/AGENTS.md`.

### Referências

- Script principal de rastreamento: [.tracker/work-tracker.py](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/work-tracker.py)
- Makefile do rastreador: [.tracker/Makefile](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/Makefile)
- Suite de testes: [.tracker/test_tracker.py](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/test_tracker.py)

## Registro do Agente de Desenvolvimento

### Modelo de IA Utilizado

Gemini 3.5 Flash (High) via Antigravity

### Referências de Log de Depuração

N/A (Testes unitários e manuais executados com sucesso)

### Lista de Notas de Conclusão

- Implementação de `--format` para exportações no `work-tracker.py`.
- Adicionada exportação JSON atômica com 2 espaços de recuo e UTF-8.
- Adicionada exportação CSV atômica tabulada e plana de acordo com a RFC 4180.
- Atualizado o target `track-time` no `Makefile` para suportar fallback de `FORMAT`.
- Cobertura de testes unitários adicionada para JSON, CSV e atomicidade com sucesso.

### Lista de Arquivos

- [.tracker/work-tracker.py](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/work-tracker.py)
- [.tracker/Makefile](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/Makefile)
- [.tracker/test_tracker.py](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/test_tracker.py)
- [.tracker/TEMPO_DE_TRABALHO.json](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.json)
- [.tracker/TEMPO_DE_TRABALHO.csv](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.csv)

## Histórico de Alterações (Change Log)

| Data e Hora (Brasília) | Autor | Modelo | Descrição |
| :---: | :--- | :--- | :--- |
| 2026-05-25 19:49:00-03:00 | Gemini 3.5 Flash (High) | Gemini 3.5 Flash (High) | Iniciado desenvolvimento da história BKL-003. |
| 2026-05-25 16:25:00-03:00 | Gemini 3.5 Flash (High) | Gemini 3.5 Flash (High) | Criação da especificação para a história BKL-003 (Exportação JSON/CSV) a partir do backlog priorizado do subprojeto `.tracker`. |

---
Autoria/Especificação: Gemini 3.5 Flash (High) via Antigravity — 2026-05-25
Autoria/Implementação: Gemini 3.5 Flash (High) via Antigravity — 2026-05-25

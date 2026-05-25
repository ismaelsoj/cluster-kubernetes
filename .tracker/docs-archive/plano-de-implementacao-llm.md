# Plano de Implementação: Rastreamento Granular por LLM e Sistema de Sobrescritas de Modelos

Este documento apresenta o plano de implementação completo, elaborado no padrão BMad e enriquecido com a **Propagação Cronológica de Estado**, para o rastreamento tridimensional de tempo de desenvolvimento por LLM. 

Ele resolve a subestimação de uso de modelos rápidos (como o Gemini 3 Flash) no Antigravity e integra a mineração direta de metadados determinísticos no Claude CLI.

---

## 1. Diagnóstico Técnico Forense (Esgotamento das Fontes)

Para garantir o máximo de determinismo físico, vasculhamos todas as possíveis fontes de metadados do editor:

1. **Logs da Extensão Host (`~/.config/Antigravity/logs/`)**: Mapeiam endpoints internos, mas gravam nomes de modelos apenas na ocorrência de erros 503 HTTP (`ls-main.log`), não registrando requisições bem-sucedidas normais.
2. **Bancos SQLite Globais e Locais (`state.vscdb`)**: Armazenam estados de interface, logs de terminal e histórico de arquivos recentes, porém a tabela de sincronização de trajetórias não registra a LLM ativa de forma legível ou estruturada.
3. **Históricos Binários de Conversas (`conversations/*.pb`)**: Os arquivos de histórico do Antigravity são criptografados localmente com chaves geradas em tempo de execução, impedindo qualquer decodificação offline de seus conteúdos.
4. **Log Sequencial da Conversa (`overview.txt`)**: Contém a tag dinâmica `<USER_SETTINGS_CHANGE>` apenas se você alternar manualmente a LLM pelo dropdown durante a sessão de chat. Conversas que iniciam com o modelo padrão (ou o Gemini 3 Flash pré-selecionado) não geram registros físicos no log do chat.

### A Revelação Determinística para Claude Code
O plugin CLI **Claude Code** armazena logs locais em formato JSONL sob `/home/ismael.sjunior/.claude/projects/` contendo a chave `"model":"claude-sonnet-4-6"` de forma 100% determinística. Incorporaremos a varredura desses arquivos JSONL para garantir a integridade absoluta dos dados de esforço do Claude CLI.

---

## 2. A Solução Arquitetural de Calibração: Propagação Cronológica

Para eliminar a necessidade de fallbacks estáticos arbitrários por conversa, adotaremos duas estratégias complementares:

1. **Propagação Cronológica de Estado:** 
   Em vez de resetar o modelo ativo para o padrão de fábrica a cada nova conversa de chat, o analisador processará todos os eventos cronologicamente. Quando houver uma mudança explícita de modelo registrada via dropdown (`<USER_SETTINGS_CHANGE>`), o novo modelo (ex: **Gemini 3 Flash**) passará a ser o **modelo ativo global**. As conversas subsequentes herdarão automaticamente esse último modelo configurado na linha do tempo até que outra troca manual seja registrada no histórico.

2. **O Dilema do Modelo Inicial e Fallback de Fábrica:**
   Como o Antigravity sempre inicia com o **"Gemini 3.1 Pro (High)"** por padrão (estado de fábrica), o rastreador assumirá matematicamente que todas as interações e horas iniciais de um projeto recém-criado pertencem a este modelo, até que ele intercepte o primeiro `<USER_SETTINGS_CHANGE>` no histórico cronológico, momento a partir do qual aplicará a propagação cronológica. Não faremos uso de arquivos de configuração externos, garantindo uma heurística autônoma e de zero manutenção para o desenvolvedor.

### 2.1. Métricas da Tabela de Saída
A fim de fornecer máxima assertividade na volumetria de trabalho e garantir visibilidade de auditoria, a tabela de saída agrupará os resultados por Dia e por Modelo, mas adicionará novos níveis de detalhamento quantitativo:
- **Modelo LLM**
- **Sessões Ativas** (Agrupamentos de comandos com gap <= 45 min)
- **Total de Interações/Comandos** (Volume de pings no editor/CLI)
- **Horas Efetivamente Trabalhadas**

---

## 3. Mudanças Propostas

### Componente de Tempo e Rastreamento (`.tracker`)

---

#### [MODIFICAR] [work-tracker-architecture.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/work-tracker-architecture.md)
* Inclusão das decisões arquiteturais (ADR-05 e ADR-06 sobre Propagação Cronológica e Arquitetura Zero-Config).

#### [MODIFICAR] [work-tracker.py](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/work-tracker.py)
* **Design Zero-Config**: Nenhuma dependência de arquivos de configuração externos.
* **Sanitização de Logs (Filtro Anti-Poluição)**: Descarte de pings vazios (ex: sessões de inicialização sem histórico de mensagens de prompt humano).
* **Motor de Ordenação e Propagação de Modelos**:
  * Ordenação global dos eventos de ambas as ferramentas (IDE e CLI) em uma única linha do tempo consolidada.
  * Agrupamento cruzado (evitando dupla contagem) creditando tempos ociosos ao último LLM pingado na linha.
  * Aplicação da precedência de decisão com propagação cronológica:
    1. Tags físicas extraídas no chat (`overview.txt` ➔ `<USER_SETTINGS_CHANGE>`), atualizando o estado do "modelo ativo global" herdado subsequente.
    2. Fallback de fábrica `"Gemini 3.1 Pro (High)"` para o estado inicial de qualquer linha do tempo sem tag prévia.
* **Parser de Claude CLI**: Scanner para ler as pastas de projeto em `/home/ismael.sjunior/.claude/projects/` e decodificar a tag `"model"` exata de cada requisição genuína.
* **Taxonomia Comercial Exata**: Implementação rigorosa do mapeamento de strings para contemplar os modelos das capturas físicas:
  * *Antigravity:* `Gemini 3.1 Pro (High)`, `Gemini 3.1 Pro (Low)`, `Gemini 3 Flash`, `Claude Sonnet 4.6 (Thinking)`, `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`.
  * *Claude Code:* `Sonnet 4.6`, `Opus 4.7`, `Haiku 4.5`.

#### [MODIFICAR] [README.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/README.md)
* Atualização do manual do desenvolvedor para documentar a natureza *zero-config* e autônoma do rastreador, reforçando que ele lê os logs e adota o padrão Pro (High) de fábrica sem a necessidade de interferência humana.

---

## 4. Plano de Verificação

### Testes Automatizados
* Criação de testes unitários offline temporários em `scratch/test_tracker.py` para validar:
  * Parse do JSONL do Claude CLI.
  * Lógica de ordenação cronológica e propagação do último modelo ativo entre conversas.
  * Validação das regras de precedência.
  ```bash
  python3 -m unittest scratch/test_tracker.py
  ```

### Verificação Manual
1. Executar o analisador para gerar o relatório final na pasta raiz do repositório:
   ```bash
   make -f .tracker/Makefile track-time EXPORT=true
   ```
3. Inspecionar visualmente o arquivo gerado [TEMPO_DE_TRABALHO.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.md) e verificar as horas e proporções recalculadas.

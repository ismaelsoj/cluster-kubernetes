# 📊 Project Context — Rastreador de Tempo de Desenvolvimento (IA)

> Documento consolidado de contexto do projeto para a ferramenta de rastreamento de tempo ativo com assistentes de IA. Reúne todas as especificações, decisões arquiteturais, pesquisas técnicas e trabalho diferido num único ponto de referência.

---

## 1. Visão Geral do Produto

O **Rastreador de Tempo Ativo (IA)** é um micro-sistema analítico privado e offline que vive isolado na pasta `.tracker/` do repositório `cluster-kubernetes`. Ele minera dados de transações locais de dois assistentes de IA — **Antigravity** (extensão de IDE) e **Claude Code** (CLI) — e consolida as métricas em tabelas diárias compartilhadas de forma segura, anônima e colaborativa.

### Objetivos
- Auditar de forma justa e transparente o tempo produtivo acumulado com ferramentas de IA
- Rastreamento tridimensional: **tempo × modelo LLM × ferramenta**
- Rastreamento de esforço por **branch/história** (story tracking)
- Consolidação multi-desenvolvedor com anonimato por hash SHA-256
- Zero dependências externas, zero configuração manual

---

## 2. Stack Tecnológica

| Componente | Tecnologia |
|------------|-----------|
| Linguagem | Python 3.x (stdlib pura: `os`, `re`, `json`, `glob`, `hashlib`, `socket`, `datetime`) |
| Interface DX | GNU Make (Makefile apartado em `.tracker/Makefile`) |
| Fuso Horário | Brasília GMT-3 (America/Sao_Paulo) |
| Saída Analítica | Markdown GFM (GitHub Flavored Markdown) |
| Fontes de Dados | `~/.claude/projects/*.jsonl` (Claude Code) + `~/.gemini/antigravity/brain/*/overview.txt` (Antigravity) |

---

## 3. Estrutura de Arquivos

```text
.tracker/
├── Makefile                        # DX Interface: make -f .tracker/Makefile track-time [EXPORT=true]
├── README.md                       # Guia do desenvolvedor
├── BACKLOG.md                      # Backlog consolidado de melhorias e dívida técnica
├── work-tracker-architecture.md    # Documento de Decisões de Arquitetura (ADR)
├── plano-de-implementacao-llm.md   # Plano de implementação do rastreamento por LLM
├── work-tracker.py                 # Engine analítico (698 linhas)
├── TEMPO_DE_TRABALHO.md            # Relatório colaborativo gerado automaticamente
├── project-context.md              # Este documento
├── specs/                          # Especificações de features e bugfixes
│   ├── spec-branch-tracking-work-tracker.md
│   ├── spec-tempo-total-desenvolvedores-e-branches.md
│   ├── spec-ferramenta-dimensao-relatorio.md
│   └── spec-fix-antigravity-model-extraction-regex.md
├── reviews/                        # Reviews e prompts de revisão
│   └── review-tempo-total-desenvolvedores-prompt.md
└── research/                       # Pesquisas técnicas
    └── technical-identificar-modelo-llm-antigravity-research-2026-05-19.md
```

---

## 4. Decisões de Arquitetura (ADRs)

### ADR-01: Isolamento de Escopo
Toda a lógica, automações e relatórios vivem em `.tracker/`. O Makefile principal e `scripts/` permanecem focados apenas em infraestrutura.

### ADR-02: Agrupamento por Sessões Ativas (Session Gap)
- Gap máximo entre interações: **45 minutos** (configurável via `--gap`)
- Sessões com menos de 15 minutos: padding automático para 15 min (engajamento mínimo)

### ADR-03: Prevenção de Dupla Contagem
- **Mesclagem Global:** Todos os timestamps (ambas ferramentas) são concatenados e ordenados cronologicamente antes do agrupamento
- **Alocação de Ociosidade:** Tempo idle creditado ao modelo da interação anterior imediata
- **Filtro Anti-Poluição:** Pings órfãos sem prompt de usuário são descartados

### ADR-04: Privacidade por Mascaramento SHA-256
Identidade mascarada com hash determinístico de 8 caracteres: `dev-[hash]` calculado de `usuario@hostname`.

### ADR-05: Rastreamento Dinâmico por Modelo (LLM)
- **Claude Code:** Mineração de `"model"` em JSONL sob `~/.claude/projects/`
- **Antigravity:** Rastreamento de `<USER_SETTINGS_CHANGE>` em `overview.txt`

### ADR-06: Propagação Cronológica de Estado e Zero-Config
- Modelo de fábrica padrão: `Gemini 3.1 Pro (High)`
- Trocas de modelo propagam estado para sessões subsequentes até nova troca
- Pass 1: Ancora modelo inicial 1ms antes do primeiro turno (captura "from" real)
- Pass 2: Rastreia mudanças subsequentes via `<USER_SETTINGS_CHANGE>`

---

## 5. Funcionalidades Implementadas

### 5.1 Relatório por Modelo LLM e Ferramenta
- Tabela diária com dimensões: **Dia × Ferramenta × Modelo LLM**
- Seção de totais por ferramenta (Antigravity vs Claude Code)
- Normalização de nomes de modelos (`normalize_model_name`)

### 5.2 Rastreamento por Branch / História
- Parsing de `.git/logs/HEAD` (reflog) para reconstruir timeline de checkouts
- Mapeamento de cada ping para branch ativa no timestamp exato
- Tabela com colunas: **Dia × Branch × Ferramentas × Modelos × Tempo × Interações**

### 5.3 Consolidação Multi-Desenvolvedor
- Resumo geral com tempo total somado de todos os devs
- Tabela global de tempo por branch consolidado
- Preservação de blocos de outros desenvolvedores (imutabilidade)

### 5.4 Saída de Console
- Métricas formatadas com cores ANSI agrupadas por ferramenta/modelo
- Exibição do ID anônimo para rastreabilidade interna

---

## 6. Fluxo de Dados (Pipeline)

```mermaid
sequenceDiagram
    participant D as Desenvolvedor
    participant M as Makefile
    participant W as work-tracker.py
    participant FS as Logs Locais
    participant MD as TEMPO_DE_TRABALHO.md
    
    D->>M: make -f .tracker/Makefile track-time EXPORT=true
    M->>W: python3 work-tracker.py --export
    W->>W: SHA-256(user@host) → masked_id
    W->>FS: Ler ~/.claude/projects/*.jsonl
    W->>FS: Ler ~/.gemini/antigravity/brain/*/overview.txt
    W->>W: Filtro anti-poluição
    W->>W: UTC → Brasília (GMT-3)
    W->>W: Concatenar + ordenar cronologicamente
    W->>W: Propagar estado de modelo (ADR-06)
    W->>W: Branch mapping via reflog
    W->>W: Agrupar sessões (gap ≤ 45 min)
    W->>MD: Ler blocos existentes de outros devs
    W->>MD: Substituir bloco atual + gerar resumo global
```

---

## 7. Trabalho Diferido (Backlog Técnico)

### Prioridade Alta
- **Antigravity trunca eventos de troca de modelo:** O arquivo `overview.txt` trunca entradas `USER_EXPLICIT` acima de ~1024 caracteres com `<truncated N bytes>`, perdendo a tag `<USER_SETTINGS_CHANGE>` que é adicionada no final do payload. Causa perda de eventos de troca de modelo quando o `ADDITIONAL_METADATA` é muito grande. Deve ser reportado à equipe do Antigravity. (BKL-026)
- **Regex `(.*?)\.` trunca nomes com ponto:** payload `"to Gemini 3.1 Pro."` captura `"Gemini 3"`. Precisa sentinela mais robusto. (BKL-004)

### Prioridade Média
- **Detached HEAD como SHA de branch:** checkout para SHA aparece como nome de branch no relatório. Adicionar pós-processamento com regex `^[0-9a-f]{7,40}$`.
- **Sessões cruzando meia-noite:** toda a sessão é atribuída à data do primeiro evento. Dividir no limite de meia-noite.
- **Interações entre troca de branch em sessão:** gap entre pings de branches diferentes é inteiramente atribuído à branch anterior.

### Prioridade Baixa
- **Múltiplos `<USER_SETTINGS_CHANGE>` por linha JSON:** `re.search` captura apenas a primeira ocorrência.
- **`-\d{8}\b` pode remover sufixos numéricos não-data:** latente, nenhum modelo atual é afetado.
- **Inconsistência de padrão de guarda de tabelas vazias:** Tabela 1 vs Tabela 2 usam padrões diferentes.
- **Eventos `is_change` sem campo `active_model`:** risco de KeyError se o filtro `is_ping` mudar.

---

## 8. Segurança e Validação

- **Prevenção de Injeção:** Logs purificados contra quebras de linha e caracteres não-JSON
- **Idempotência:** Execuções sucessivas não causam efeitos colaterais
- **Segurança de Paths:** Caminhos de varredura baseados em `os.path.expanduser`, sem travessia de diretório
- **Imutabilidade de Outros Blocos:** Blocos de outros desenvolvedores nunca são alterados
- **Deduplicação Dinâmica:** Registro antigo do mesmo dev é substituído in-place

---

## 9. Comandos de Uso

```bash
# Visualizar métricas no terminal (sem persistir)
make -f .tracker/Makefile track-time

# Exportar/atualizar relatório colaborativo
make -f .tracker/Makefile track-time EXPORT=true

# Executar com gap customizado (default: 45 min)
python3 .tracker/work-tracker.py --gap 30 --export
```

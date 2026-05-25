---
stepsCompleted: [1]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Viabilidade de rastreamento de tokens e correção da captura de modelo no novo Antigravity IDE'
research_goals: 'Verificar se é possível contabilizar tokens de input/output do Antigravity e documentar a resolução do bug de truncamento que impedia a detecção do modelo LLM'
user_name: 'Ismael'
date: '2026-05-20'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-20
**Author:** Ismael / Antigravity Agent
**Research Type:** technical

---

## Confirmação do Escopo da Pesquisa Técnica

**Tópico da Pesquisa:** Viabilidade de rastreamento de tokens no novo Antigravity IDE
**Objetivos da Pesquisa:** Verificar se é possível contabilizar tokens de input/output do Antigravity para equiparar com a funcionalidade do Claude Code.

**Escopo da Pesquisa Técnica:**
- Inspeção dos novos arquivos de log (ex: `transcript.jsonl`).
- Verificação do diretório de App Data da nova IDE (`~/.gemini/antigravity-ide/`).
- Análise de payloads secundários (arquivos Protocol Buffers, bancos de dados, etc.).
- Validação da correção do bug de truncamento de contexto (BKL-026).

---

## 1. Análise dos Novos Logs (`transcript.jsonl`)

Na nova arquitetura do Antigravity IDE, os eventos da conversa passaram a ser registrados no arquivo `~/.gemini/antigravity-ide/brain/<id>/.system_generated/logs/transcript.jsonl`.
Foi realizada uma varredura completa (`grep`, expressões regulares) em todas as chaves e objetos JSON gravados pelas interações ativas:

**Descobertas:**
- Os arquivos mantêm as chaves estruturais: `step_index`, `source`, `type`, `status`, `created_at`, `content`, `thinking` e `tool_calls`.
- **Ausência de Metadados de Uso:** Nenhuma chave relacionada a tokens (como `usage`, `tokens`, `input_tokens`, `output_tokens`) é registrada pelo serviço do Antigravity nestes arquivos texto em claro.

## 2. Análise do Armazenamento Binário (Protocol Buffers)

O Antigravity também mantém arquivos isolados para cada conversa na pasta `~/.gemini/antigravity-ide/conversations/*.pb`.

**Descobertas:**
- Estes arquivos utilizam serialização binária complexa (Protocol Buffers).
- Realizamos análises de extração de texto (hexdump/strings) no cabeçalho e corpo desses arquivos.
- **Resultado:** Os dados são ofuscados/criptografados e não expõem metadados abertos que possam ser facilmente parseados por utilitários de texto como nosso `.tracker/work-tracker.py`. Não há marcadores acessíveis para `usage` ou tokens sem a posse da chave/schema correto e da capacidade de descriptografar o payload da IDE local.

## 3. Ausência de Outras Bases de Dados

Foi feita uma inspeção na árvore completa de diretórios de configuração e de estado do sistema (`~/.gemini/antigravity-ide/`).
- Não existem bancos de dados SQLite (`.db` ou `.sqlite`).
- Todo o histórico textual legível reside em `transcript.jsonl`, o qual, conforme constatado acima, não guarda esses valores.

## 4. Resolução da Captura do Modelo LLM (Bug de Truncamento)

A atualização para o novo Antigravity IDE trouxe uma mudança crucial na persistência dos logs, alterando de `overview.txt` para `transcript.jsonl`.
Anteriormente, o `overview.txt` aplicava um truncamento forçado de `~1024` caracteres em interações `USER_EXPLICIT`. Como a tag `<USER_SETTINGS_CHANGE>` sempre era adicionada ao final do payload (após o bloco metadados), ela invariavelmente era perdida, impedindo a detecção de mudança de modelo pelo rastreador.

**Descobertas:**
- **Fim da Truncação:** O `transcript.jsonl` provou que preserva os payloads originais do usuário em sua totalidade (testamos turnos com mais de 24.000 bytes e o `<USER_SETTINGS_CHANGE>` estava intacto).
- **Conclusão Positiva:** A limitação técnica de retenção do modelo foi resolvida nativamente pela IDE. 
- **Nova Dependência:** Para que o `.tracker/work-tracker.py` volte a coletar modelos perfeitamente, o script precisará ser atualizado para ler os novos logs (`transcript.jsonl`) na nova pasta App Data (`~/.gemini/antigravity-ide/`).

## Conclusão e Próximos Passos (Deliverable)

A pesquisa forneceu respostas definitivas para dois problemas-chave do ecossistema de rastreamento:

1. **Bug do Modelo LLM (Resolvido pela IDE):** O truncamento excessivo de entradas de usuário foi eliminado no novo formato JSONL. A IDE atualizada agora persiste a tag `<USER_SETTINGS_CHANGE>` integralmente, o que significa que o problema técnico de fundo do **`BKL-026`** está solucionado.
2. **Uso de Tokens (Inviável):** A ferramenta **continua não expondo de forma acessível e local** os dados de consumo de tokens (diferentemente do que o Claude Code faz em sua pasta de projetos).

**Decisões Técnicas e Próximos Passos:**
- **Refatorar Tracker (`BKL-026`):** Atualizar o `work-tracker.py` para apontar para `~/.gemini/antigravity-ide/brain/` e processar os arquivos `transcript.jsonl` (preservando também a compatibilidade com o antigo `overview.txt`). Após essa simples correção de caminhos, poderemos dar o BKL-026 como fechado.
- **Rastreamento de Tokens (`BKL-002`):** Permanece como **⛔ Inviável / Bloqueado**. O script deve continuar medindo esforço baseado unicamente em "Tempo Ativo" (horas) para interações da IDE.
- **Ação Sugerida (Tokens):** Recomendar via *Feature Request* que os desenvolvedores do Antigravity adicionem a chave `"usage": {"input_tokens": X, "output_tokens": Y}` nos arquivos `transcript.jsonl` em atualizações futuras.

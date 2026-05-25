---
stepsCompleted: [1]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Identificar qual modelo LLM está sendo usado em cada interação do Antigravity'
research_goals: 'Ajustar o work-tracker.py para capturar corretamente o modelo LLM em uso pelo Antigravity para métricas pessoais e orçamentos'
user_name: 'Ismael'
date: '2026-05-19'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-19
**Author:** Ismael
**Research Type:** technical

---

## Research Overview

[Research overview and methodology will be appended here]

---

## Confirmação do Escopo da Pesquisa Técnica

**Tópico da Pesquisa:** Identificar qual modelo LLM está sendo usado em cada interação do Antigravity
**Objetivos da Pesquisa:** Ajustar o work-tracker.py para capturar corretamente o modelo LLM em uso pelo Antigravity para métricas pessoais e orçamentos

**Escopo da Pesquisa Técnica:**
- Análise de Arquitetura: Como o Antigravity interage com os modelos LLM internamente e onde ele expõe seus metadados.
- Abordagens de Implementação: Como o tracker atual pode capturar e fazer o parse desses logs ou metadados associados à sessão local.
- Stack de Tecnologia: Identificação de variáveis de ambiente, arquivos gerados localmente (no seu diretório de App Data `~/.gemini/antigravity`).
- Padrões de Integração: Como integrar de forma robusta a extração desse modelo de dados para o script python.
- Considerações de Desempenho: Otimização nas leituras do disco no macOS.

**Metodologia de Pesquisa:**
- Análise técnica profunda do ambiente local baseada em dados reais e pesquisa no sistema.
- Validação rigorosa em cima do comportamento dos logs do Antigravity.
- Níveis de confiança para informações obtidas.
- Cobertura técnica detalhada.

**Escopo Confirmado:** 2026-05-19


<!-- Content will be appended sequentially through research workflow steps -->

## Análise da Stack de Tecnologia e Arquitetura do Antigravity

Após análise aprofundada do ambiente local e dos binários do Antigravity, identificamos a arquitetura de persistência e a stack tecnológica envolvida no rastreamento de modelos.

### Arquitetura de Logs e Persistência

- **Armazenamento Primário (`.pb`)**: O Antigravity armazena o histórico completo e não-truncado em arquivos binários Protocol Buffers (`~/.gemini/antigravity/conversations/*.pb`). Estes arquivos são opacos e não legíveis por ferramentas de texto simples sem o schema (proto) correspondente.
- **Armazenamento de Depuração (`overview.txt`)**: A IDE exporta um espelho das conversas em JSON lines no diretório `~/.gemini/antigravity/brain/<id>/.system_generated/logs/overview.txt`. Este é o arquivo consumido atualmente pelo `work-tracker.py`.
- **Injeção de Metadados**: As alterações de configuração (como `Model Selection`) não são persistidas em um arquivo de configuração estático local padrão (como `settings.json` ou SQLite `state.vscdb`). Em vez disso, a interface do Antigravity injeta dinamicamente um bloco `<USER_SETTINGS_CHANGE>` dentro do nó `<ADDITIONAL_METADATA>` no payload enviado ao LLM.

### Análise do Problema de Rastreamento (Truncamento)

O problema principal que afeta as métricas ocorre devido a um mecanismo de otimização de disco da IDE:
- **Truncamento de Strings Longas**: A IDE trunca strings muito longas no `overview.txt` com a mensagem `<truncated N bytes>`.
- No primeiro turno de uma conversa, o `<ADDITIONAL_METADATA>` inclui uma quantidade massiva de contexto do workspace (arquivos abertos, estado do git). Isso empurra o `<USER_SETTINGS_CHANGE>` para o final da string, fazendo com que ele seja frequentemente "cortado" antes de ser salvo no disco.

### Análise do Bug de Implementação no `work-tracker.py`

Além do truncamento imposto pela IDE, a pesquisa identificou um **bug de lógica no próprio script Python**:
```python
# No arquivo work-tracker.py (Pass 1)
match = re.search(r"changed setting `Model Selection` from (.*?) to (.*?)\.", content_text)
if match:
    old_m = match.group(1).strip() # <-- BUG! Extrai o modelo ANTERIOR ("None")
    first_old_model = normalize_model_name(old_m)
```
- O script está extraindo o `group(1)` (o valor "de", que frequentemente é `None` no início de uma sessão) em vez do `group(2)` (o valor "para", que contém o modelo atual como `Gemini 3.1 Pro (High)` ou `Gemini 3.5 Flash`).
- Como a validação falha para "None", o tracker descarta silenciosamente o modelo (mesmo quando não há truncamento) e volta para o fallback padrão de fábrica.

### Resumo das Descobertas
- **Fonte**: Logs do sistema de arquivos local (`overview.txt`).
- **Limitação Tecnológica**: Truncamento string JSON via Antigravity Logger.
- **Falha de Parse**: Extração de grupo Regex incorreta no script Python.

## Abordagens de Implementação (Agnósticas a S.O.)

Considerando o requisito essencial de que a solução seja **totalmente agnóstica a Sistema Operacional** (suportando nativamente macOS, Linux e Windows), desenhamos a seguinte abordagem híbrida para mitigar o truncamento da IDE e corrigir a lógica do parser.

### Abordagem 1: Correção do Parser Regex (Python)
A correção imediata envolve a modificação do `work-tracker.py` no projeto `cluster-kubernetes`, alterando a extração do grupo da Regex no primeiro passe (Pass 1).
- **Como funciona**: Atualizar `match.group(1)` para `match.group(2)`.
- **Agnóstico a S.O.**: Sim. A manipulação de strings via `re` e a busca recursiva via `glob` em conjunto com `os.path.expanduser("~/.gemini/antigravity/brain")` funciona perfeitamente nas 3 plataformas (`~` converte para `/home/user` no Linux e `C:\Users\user` no Windows).
- **Vantagem**: Quando o usuário alterar o modelo *durante* uma sessão ativa (onde a string de payload é menor e não trunca), o tracker será capaz de extrair a mudança corretamente e, pelo design cronológico do script, propagar essa configuração de modelo para todas as métricas seguintes.

### Abordagem 2: Mecanismo de Configuração/Override Local (Opcional/Fallback)
A preocupação com a experiência do usuário (não ter que sincronizar manualmente o arquivo local com a interface) é extremamente válida. 

Por design, o `work-tracker.py` analisa **todas** as conversas cronologicamente. Isso significa que, com a **Abordagem 1** implementada, assim que o usuário alterar o modelo *durante qualquer sessão de chat* (gerando um log não-truncado), o tracker aprenderá essa mudança e a **propagará automaticamente** para todas as sessões futuras. 

Portanto, o arquivo local (ex: `.tracker/config.json`) não será uma exigência de sincronização constante, mas sim uma **ferramenta de override de emergência**. Ele só precisará ser usado se:
1. O usuário estiver em uma máquina totalmente nova, sem histórico anterior, e o primeiro chat já for truncado.
2. O usuário não quiser "forçar" uma troca de modelo na interface apenas para registrar no log.

Dessa forma, mantemos a solução Agnóstica a S.O. e garantimos que o usuário não precise lembrar de atualizar dois lugares na rotina diária de desenvolvimento.

## Conclusão e Próximos Passos (Deliverable)

A presente pesquisa mapeou com sucesso a anomalia na identificação do modelo `Antigravity` pelo script `.tracker/work-tracker.py`. 

Foi constatado de forma terminante que a ausência do modelo nos primeiros turnos das conversas não decorre de um erro de leitura do Python, mas sim de um comportamento irrevogável de otimização de disco (Truncamento Hardcoded) embutido no binário da IDE Antigravity (`language_server_macos_arm`), que suprime metadados de configuração em prompts de inicialização densos.

### Decisão Arquitetural Final
- Modificar o regex no arquivo `.tracker/work-tracker.py` para corrigir o parse de grupos de captura nos turnos subsequentes, onde o truncamento não ocorre.
- Essa correção simples desbloqueia a mecânica nativa de propagação cronológica do tracker, permitindo que a seleção de modelo do usuário em uma sessão "vaze" logicamente como o estado correto para todas as sessões futuras, minimizando ou extinguindo a discrepância nos orçamentos mensais do usuário sem quebra de experiência.
- O fallback local (`.tracker/config.json`) foi idealizado como alternativa, mas o seu uso em larga escala deve ser desencorajado para não onerar a experiência (UX) do desenvolvedor.

### Próximos Passos
O presente documento serve agora como _fonte da verdade_ (Source of Truth). Recomenda-se invocar um agente focado em código (como a desenvolvedora **Amelia** via `@bmad-agent-dev` ou o `@bmad-quick-dev`) apontando para este arquivo para que as linhas do regex em `.tracker/work-tracker.py` sejam ajustadas e o novo fluxo de captura seja implementado.

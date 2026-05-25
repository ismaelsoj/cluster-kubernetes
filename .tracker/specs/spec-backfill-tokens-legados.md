---
title: 'Backfill de Tokens em Sessões Legadas (Claude Code)'
type: 'feature'
created: '2026-05-25'
status: 'pronto-para-desenvolvimento'
baseline_commit: '8f86d4b'
complexity: 'Baixa Complexidade'
context:
  - '.tracker/specs/spec-rastreamento-de-tokens-claude-code.md'
---

# História BKL-030: Backfill de Tokens em Sessões Legadas (Claude Code)

Status: pronto-para-desenvolvimento

## Contexto

A história BKL-001 implementou o rastreamento de tokens para sessões **novas** do Claude Code (a partir do primeiro `EXPORT=true` após a feature). Sessões anteriores foram persistidas como eventos `"legacy": true` sem campos de token — mesmo que os arquivos JSONL originais do Claude Code ainda existam em `~/.claude/projects/` e contenham os dados de `usage`.

Resultado observado:

```
| 12/05/2026 | Claude Sonnet 4.6 | 0 / 0 |   ← JSONL existe, tokens perdidos
| 13/05/2026 | Claude Sonnet 4.6 | 0 / 0 |   ← idem
| 25/05/2026 | Claude Sonnet 4.6 | 8.925 / 138.373 | ← correto (live)
```

## História

Como desenvolvedor que implementou BKL-001 depois de já ter sessões registradas,
Quero executar um comando de backfill que leia os JSONLs originais do Claude Code
e preencha os campos de tokens nos eventos legados,
Para ter um histórico completo e correto de consumo de tokens desde o início do uso do Claude Code.

## Critérios de Aceite

1. **Flag de backfill:**
   - O script `work-tracker.py` deve aceitar o argumento `--backfill-tokens` (compatível com `--export`).
   - Exemplo de uso: `python3 .tracker/work-tracker.py --export --backfill-tokens`
   - Makefile target opcional: `make -f .tracker/Makefile track-time EXPORT=true BACKFILL_TOKENS=true`

2. **Lógica de backfill:**
   - Para cada evento `activity_daily` com `tool == "Claude Code"` e `legacy == true` no JSONL de eventos:
     - Re-ler os arquivos `~/.claude/projects/*/*.jsonl` e filtrar pings cuja data coincide com o campo `date` do evento e o campo `model` com `model` do evento.
     - Somar todos os campos de token (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`) para esse dia/modelo.
     - Atualizar o evento com os valores encontrados.
     - Se nenhum JSONL for encontrado para a data (arquivo já deletado pelo Claude Code), manter `0` e registrar aviso no console.
   - Os eventos `activity_branch` legados com `tool` incluindo `"Claude Code"` também devem ser retroalimentados com a soma de tokens das sessões correspondentes por `date` e `branch`.

3. **Idempotência:**
   - Executar `--backfill-tokens` múltiplas vezes deve produzir o mesmo resultado (não acumula tokens).
   - Eventos já não-legados (`"legacy": false`) não devem ser modificados pelo backfill.

4. **Atualização do `dev_summary`:**
   - Após o backfill, os campos `total_input_tokens`, `total_output_tokens`, `total_cache_creation_input_tokens`, `total_cache_read_input_tokens` do `dev_summary` de escopo `"legacy"` devem refletir os novos totais.
   - O `dev_summary` de escopo `"live"` permanece inalterado.

5. **Resiliência:**
   - Se o arquivo JSONL original de uma sessão foi deletado pelo Claude Code (rotação automática), o evento legado deve manter `0` e o console deve exibir aviso: `[backfill] Aviso: nenhuma sessão encontrada para <data>/<modelo> — JSONL pode ter sido rotacionado.`
   - A ausência de dados não deve interromper o backfill das outras datas.

6. **Saída no console:**
   - Durante o backfill, exibir progresso:
     ```
     [backfill] Processando tokens legados...
       12/05/2026 Claude Sonnet 4.6 → 42.150 in / 18.320 out / 1.240.000 cache_read / 84.200 cache_creation
       13/05/2026 Claude Sonnet 4.6 → ...
     [backfill] Concluído. X evento(s) atualizado(s), Y sem dados disponíveis.
     ```

## Plano de Validação Manual

### 1. Testes Automatizados
```bash
python3 .tracker/test_tracker.py -v
```
Novos casos a adicionar em `TestTokenBackfill`:
- `test_backfill_updates_legacy_event_with_real_data` — mock de JSONL com `usage`; verifica que evento legado recebe os valores corretos
- `test_backfill_keeps_zero_when_no_jsonl_found` — data sem JSONL; verifica que o evento fica com `0` e aviso é emitido
- `test_backfill_is_idempotent` — executar duas vezes; verificar que resultado é idêntico
- `test_backfill_does_not_modify_live_events` — evento com `legacy: false` não deve ser alterado

### 2. Validação Visual
```bash
# Antes do backfill: verificar que dias anteriores mostram 0 / 0
make -f .tracker/Makefile track-time EXPORT=true

# Executar backfill
make -f .tracker/Makefile track-time EXPORT=true BACKFILL_TOKENS=true

# Verificar que dias anteriores agora têm tokens ou aviso de JSONL rotacionado
make -f .tracker/Makefile track-time
```

Verificar no `TEMPO_DE_TRABALHO.md`:
- Coluna `Tokens (Entrada / Saída)` dos dias legados agora exibe valores reais ou `0 / 0` com aviso
- Totais no cabeçalho do desenvolvedor e na tabela `### 🪙 Consumo de Tokens` aumentam proporcionalmente

## Tarefas / Subtarefas

- [ ] **Fase de Preparação**
  - [ ] Adicionar casos de teste `TestTokenBackfill` em `test_tracker.py` (mock de JSONL com usage) — RED
- [ ] **Argumento CLI**
  - [ ] Adicionar `--backfill-tokens` em `argparse` de `main()`
  - [ ] Passar flag para `emit_events(...)` como parâmetro `backfill_tokens: bool`
- [ ] **Lógica de Backfill**
  - [ ] Implementar `backfill_legacy_tokens(events_dir, claude_projects_dir)` que:
    - Lê o JSONL de eventos atual
    - Para cada evento `activity_daily` com `legacy=True` e `tool="Claude Code"`:
      - Chama `analyze_claude_code()` (ou função auxiliar) filtrando pela data e modelo
      - Atualiza os 4 campos de token no evento
    - Faz o mesmo para `activity_branch`
    - Atualiza `dev_summary` de escopo `"legacy"` com os novos totais
    - Persiste o arquivo de volta com escrita atômica (`.tmp` + `os.replace()`)
- [ ] **Makefile**
  - [ ] Adicionar suporte a `BACKFILL_TOKENS=true` no target `track-time`
- [ ] **Validação Final**
  - [ ] Todos os testes passando (zero regressões)
  - [ ] Validação visual com `EXPORT=true BACKFILL_TOKENS=true`

## Notas de Desenvolvimento

- **Por que não re-processar sempre?** Os eventos legados do Antigravity não têm como ser re-lidos (transcript.jsonl é rotacionado). O padrão legacy/live existe para preservar esses dados. Para Claude Code, os JSONLs duram mais, mas o Claude Code também os rotaciona eventualmente — por isso o backfill é uma operação one-shot explícita, não automática.
- **Matching date/model:** `analyze_claude_code()` já retorna pings com `timestamp`, `active_model` e tokens. Basta filtrar por `date` (extraído do timestamp) e `model` para somar os tokens correspondentes ao evento legado.
- **Branch matching:** Os eventos `activity_branch` não têm field `model` isolado (têm lista `models`). O backfill de branch deve somar todos os tokens de Claude Code para aquele `date` e `branch`, independente do modelo.
- **Dependência:** Reusa completamente `analyze_claude_code()` de BKL-001. Não há nova leitura de JSONL a implementar.

### Referências
- BKL-001 implementado em: `.tracker/work-tracker.py`
- Formato dos eventos: `.tracker/events/dev-<hash>.jsonl`
- Raiz dos JSONLs do Claude Code: `~/.claude/projects/*/*.jsonl`

## Registro do Agente de Desenvolvimento

### Modelo de Agente Utilizado
N/A (spec criada por Claude Sonnet 4.6)

### Referências de Log de Depuração
N/A

### Lista de Notas de Conclusão
N/A

### Lista de Arquivos
N/A

## Histórico de Alterações (Change Log)

| Data e Hora (Brasília) | Autor | Modelo | Descrição |
| :---: | :--- | :--- | :--- |
| 2026-05-25 | Claude Sonnet 4.6 | Claude Sonnet 4.6 | Criação da especificação após identificar que eventos legados (12/05–20/05) persistiram sem campos de token pois a feature BKL-001 foi adicionada depois. |

---
Autoria/Especificação: Claude Sonnet 4.6

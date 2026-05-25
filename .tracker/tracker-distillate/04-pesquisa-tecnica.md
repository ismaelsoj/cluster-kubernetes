Esta seção cobre as pesquisas técnicas com fatos únicos não cobertos pelos ADRs. Parte 4 de 4.

---

## Pesquisa: Identificação de Modelo LLM no Antigravity (2026-05-19)

**Fontes investigadas e descartadas para uso ao vivo:**
- `~/.config/Antigravity/logs/` (`ls-main.log`): registra modelo apenas em erros 503 HTTP — não registra requests bem-sucedidos
- `state.vscdb` (SQLite local e global): histórico de interface; tabela de trajetórias sem LLM legível
- `conversations/*.pb`: arquivos Protocol Buffers criptografados com chaves geradas em runtime — não decodificáveis offline sem schema
- `overview.txt`: continha `<USER_SETTINGS_CHANGE>` apenas se usuário alternasse LLM manualmente no dropdown durante sessão; truncamento hardcoded ~1024 chars (embutido no binário `language_server_*`) descartava a tag em prompts densos

**Conclusão definitiva (2026-05-19):** truncamento é comportamento irrevogável do binário; solução era corrigir o parse de grupos da regex para capturar `group(2)` ("to") em vez de `group(1)` ("from")

---

## Pesquisa: Rastreamento de Tokens no Antigravity IDE (2026-05-20)

**Nova arquitetura confirmada:** `transcript.jsonl` em `~/.gemini/antigravity-ide/brain/<id>/.system_generated/logs/`
- Chaves presentes: `step_index`, `source`, `type`, `status`, `created_at`, `content`, `thinking`, `tool_calls`
- **Ausência confirmada de metadados de uso:** nenhuma chave relacionada a tokens (`usage`, `input_tokens`, `output_tokens`) nos arquivos `transcript.jsonl`

**Protocol Buffers em `.gemini/antigravity-ide/conversations/*.pb`:**
- Dados ofuscados/criptografados; hexdump/strings não expõem tokens acessíveis sem schema+chave
- Sem bancos SQLite na nova pasta App Data

**Rastreamento de tokens do Antigravity: ⛔ Inviável até nova atualização da IDE**

**Resolução do BKL-026 confirmada:**
- `transcript.jsonl` preserva payloads completos (testado: > 24.000 bytes sem truncamento)
- `<USER_SETTINGS_CHANGE>` intacto em turnos com payloads densos
- Solução: atualizar o tracker para ler `transcript.jsonl` na nova pasta App Data — implementado pela spec-tracker-orientado-a-eventos

---

## Rastreamento de Tokens — Claude Code ✅ Viável (contraste)

Disponível hoje nos JSONL de `~/.claude/projects/`:
```json
{"role":"assistant","message":{"usage":{
  "input_tokens": 4321,
  "output_tokens": 512,
  "cache_creation_input_tokens": 1024,
  "cache_read_input_tokens": 256
}}}
```
Implementação pendente: BKL-001 (Prioridade Alta, pronto para implementação)

---

## Dados do Review (review-tempo-total-desenvolvedores-prompt.md)

Contexto: review adversarial do diff que implementou `parse_hours_from_str()` + `parse_existing_developers_stats()` + painel `📊 Resumo Geral Consolidado` — sem bugs bloqueadores encontrados; implementação aprovada.

---
*Autoria/Implementação: Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-05-25*

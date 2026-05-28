# Trabalho Diferido

Use este companion apenas quando a tarefa estiver próxima de um ponto já conhecido como diferido ou frágil.

## Diferidos relevantes ao projeto principal

- `inject-secrets.sh` ainda tem fallback de entropia inferior ao caminho com `openssl`.
- PriorityClass não garante sozinha imunidade a eviction; hardening futuro pode exigir QoS e PDB.
- `Makefile` deveria ganhar `.DEFAULT_GOAL := help` e um alvo `help`.
- Repositório ainda precisa de `.gitignore` e `.gitattributes`.
- README ainda deveria apontar com mais clareza para a arquitetura e convenção de idiomas.
- O lint de kebab-case pode gerar falso positivo para nomes com ponto, como operadores.
- `kustomize build` vazio com exit 0 ainda não aponta claramente qual diretório falhou.

## Fora do escopo de infra

- Itens da `.tracker/` não entram no contexto de infraestrutura, salvo solicitação explícita do usuário.

---
Autoria/Implementação: GPT-5 Codex

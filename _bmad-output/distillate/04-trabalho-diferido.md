# Trabalho Diferido — Destilado. Parte 4 de 4.

## Diferido para Story 2.x+ (Infra/Security)

- [inject-secrets.sh:38,50] Fallback de geração de senha com ~64 bits entropia vs 128 bits do openssl; afeta containers Alpine/minimais; harmonizar quando sistema de secrets centralizado (Story 3.4+)

## Diferido para Cross-Story/Repo

- Makefile sem `.DEFAULT_GOAL` — `make` puro executa `up` acidentalmente; definir `.DEFAULT_GOAL := help`
- Makefile sem alvo `help` para descoberta
- Repo sem `.gitignore` — kubeconfig, logs, artefatos podem ser commitados
- Repo sem `.gitattributes` — clones Windows corrompem shebang `*.sh` com `core.autocrlf=true`
- README sem link para architecture.md na seção Documentação
- Sem ADR formalizando convenção de idiomas (PT-BR docs/comentários + EN nomes técnicos + `homologacao` sem cedilha)

## Diferido para Hardening do Lint (Story futura)

- [policy/kebab-case.rego:9] `kebab_case_pattern` rejeita nomes com ponto — operadores como cert-manager geram recursos com `.` (ex: `cert-manager.io`); causará falsos positivos; adicionar exceções por prefixo/sufixo
- Output vazio de `kustomize build` (exit 0, 0 bytes) indistinguível de stub intencional; guard `total_manifests > 0` mitiga no agregado mas não reporta qual diretório falhou

## Diferido para .tracker/ (Fora do escopo infra)

- Detached HEAD capturado como SHA de branch; sessões cruzando meia-noite; Antigravity change events sem `active_model`; regex `(.*?)\.` trunca modelos com ponto no nome; `re.search` captura apenas primeiro `<USER_SETTINGS_CHANGE>` por linha JSON; `-\d{8}\b` pode comer sufixos numéricos não-data; inconsistência de padrão de guarda de tabelas vazias

## Itens Resolvidos (Implementados)

- ~~Docker fallback sensível ao diretório~~ → implementado com `$(git rev-parse --show-toplevel)`
- ~~Mensagem de erro genérica com diretórios de scan ausentes~~ → implementado com validação explícita de existência
- ~~Instalar conftest nativamente no GitHub Actions~~ → implementado a pedido do dev
- ~~kebab-case.rego colon-check excessivamente amplo~~ → descartado (política real usa lista estrita)

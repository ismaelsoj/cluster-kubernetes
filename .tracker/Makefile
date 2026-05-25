# Makefile apartado de rastreamento de tempo de trabalho (IA)
# Uso: make -f .tracker/Makefile [track-time] [help]

.DEFAULT_GOAL := help

# Resolve raiz do repositório independentemente de onde make é chamado
REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

.PHONY: track-time help

help: ## Exibe os comandos disponíveis neste Makefile de métricas
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[35m%-12s\033[0m %s\n", $$1, $$2}'

FORMAT ?= markdown
VALID_FORMATS := markdown json csv
ifeq ($(filter $(FORMAT),$(VALID_FORMATS)),)
override FORMAT := markdown
endif

track-time: ## Rastreia o tempo ativo local (Claude Code + Antigravity) e anexa com EXPORT=true FORMAT=[json|csv|markdown]
ifeq ($(EXPORT),true)
	@python3 "$(REPO_ROOT)/.tracker/work-tracker.py" --export --format $(FORMAT)
ifeq ($(FORMAT),markdown)
	@echo "Dica: Você pode commitar o arquivo .tracker/TEMPO_DE_TRABALHO.md para compartilhar suas horas!"
else ifeq ($(FORMAT),json)
	@echo "Dica: Você pode commitar o arquivo .tracker/TEMPO_DE_TRABALHO.json para compartilhar suas horas!"
else ifeq ($(FORMAT),csv)
	@echo "Dica: Você pode commitar o arquivo .tracker/TEMPO_DE_TRABALHO.csv para compartilhar suas horas!"
endif
else
	@python3 "$(REPO_ROOT)/.tracker/work-tracker.py"
endif

bootstrap: ## Executa o script de bootstrap dos eventos legados (one-shot)
	@python3 "$(REPO_ROOT)/.tracker/bootstrap_events.py"

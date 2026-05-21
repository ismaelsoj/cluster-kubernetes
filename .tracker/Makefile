# Makefile apartado de rastreamento de tempo de trabalho (IA)
# Uso: make -f .tracker/Makefile [track-time] [help]

.DEFAULT_GOAL := help

# Resolve raiz do repositório independentemente de onde make é chamado
REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

.PHONY: track-time help

help: ## Exibe os comandos disponíveis neste Makefile de métricas
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[35m%-12s\033[0m %s\n", $$1, $$2}'

track-time: ## Rastreia o tempo ativo local (Claude Code + Antigravity) e anexa em .tracker/TEMPO_DE_TRABALHO.md com EXPORT=true
ifeq ($(EXPORT),true)
	@python3 "$(REPO_ROOT)/.tracker/work-tracker.py" --export
	@echo "Dica: Você pode commitar o arquivo .tracker/TEMPO_DE_TRABALHO.md para compartilhar suas horas!"
else
	@python3 "$(REPO_ROOT)/.tracker/work-tracker.py"
endif

bootstrap: ## Executa o script de bootstrap dos eventos legados (one-shot)
	@python3 "$(REPO_ROOT)/.tracker/bootstrap_events.py"

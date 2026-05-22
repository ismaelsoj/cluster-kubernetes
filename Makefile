# Makefile de automação local - cluster-kubernetes
# Orquestrador do ciclo de vida do cluster k3d
# Uso: make up | make down | make token | make lint | make status | make help

.DEFAULT_GOAL := help

# Resolve raiz do repositório independentemente de onde make é chamado
REPO_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

export CLUSTER_NAME ?= cluster-kubernetes

.PHONY: up up-force down token lint status secrets help

help: ## Exibe esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: lint ## Provisiona o cluster k3d completo
	@echo "Provisionando cluster k3d (cluster-kubernetes)..."
	@bash "$(REPO_ROOT)/scripts/cluster-up.sh"

up-force: ## Provisiona o cluster k3d sem rodar a validação de lint
	@echo "Provisionando cluster k3d (forçado)..."
	@SKIP_LINT=1 $(MAKE) up

down: ## Destrói o cluster sem resíduos
	@echo "Destruindo cluster k3d..."
	@bash "$(REPO_ROOT)/scripts/cluster-down.sh"

token: ## Gera e exibe o token M2M de teste
	@bash "$(REPO_ROOT)/scripts/generate-token.sh"

lint: ## Valida todos os manifestos YAML
	@bash "$(REPO_ROOT)/scripts/lint.sh"

status: ## Exibe status dos componentes e URLs locais
	@bash "$(REPO_ROOT)/scripts/status.sh"

secrets: ## Injeta/atualiza os Secrets de infraestrutura no cluster
	@bash "$(REPO_ROOT)/scripts/inject-secrets.sh"

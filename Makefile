# Makefile de automação local - cluster-kubernetes
# Orquestrador do ciclo de vida do cluster k3d
# Uso: make up | make down | make token | make lint | make status

.PHONY: up down token lint status

up: lint
	@echo "Provisionando cluster k3d (cluster-kubernetes)..."
	@bash scripts/cluster-up.sh

down:
	@echo "Destruindo cluster k3d..."
	@bash scripts/cluster-down.sh

token:
	@bash scripts/generate-token.sh

lint:
	@bash scripts/lint.sh

status:
	@bash scripts/status.sh

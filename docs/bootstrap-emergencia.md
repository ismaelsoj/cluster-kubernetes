# Guia de Bootstrap de Emergência - cluster-kubernetes

> Esqueleto inicial — Story 1.5 documenta a sequência com placeholders.
> Story 3.4 refina com comandos e nomes reais de Secrets.

## Sequência de Recuperação (Visão Geral)

1. Criar namespaces base
2. Injetar Secrets manualmente via `kubectl create secret`
3. Instalar ArgoCD
4. Aplicar `cluster/bootstrap/root-app.yaml` — ArgoCD assume via Sync Waves

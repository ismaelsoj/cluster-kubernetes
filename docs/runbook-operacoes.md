# Runbook de Operações — cluster-kubernetes

Referência rápida para operações do dia-a-dia no cluster local (k3d + ArgoCD).

---

## ArgoCD

### Forçar sync de uma aplicação

```bash
# Com argocd CLI
argocd app sync infra-app --force

# Apenas com kubectl (dispara hard refresh + reconciliação)
kubectl annotate app infra-app -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

Apps disponíveis: `root-app`, `infra-app`, `apps-app`.

### Verificar status das aplicações

```bash
argocd app list

# Ou via kubectl
kubectl get applications -n argocd
```

### Ver detalhes de sync (eventos e erros)

```bash
argocd app get infra-app

# Ou via kubectl
kubectl describe application infra-app -n argocd
```

### Forçar sync de todos os apps de uma vez

```bash
argocd app sync root-app infra-app apps-app --force
```

---

## Keycloak

### Verificar status do pod

```bash
kubectl get pods -l app.kubernetes.io/name=keycloak -n keycloak-auth
```

### Ver logs em tempo real

```bash
kubectl logs -f -l app.kubernetes.io/name=keycloak -n keycloak-auth
```

### Reiniciar o deployment (aplicar nova imagem ou configmap)

```bash
kubectl rollout restart deployment/keycloak-deployment -n keycloak-auth
kubectl rollout status deployment/keycloak-deployment -n keycloak-auth
```

### Verificar health manualmente de dentro do cluster

```bash
# Health e métricas ficam na porta 9000 (management interface do Keycloak 26+)
kubectl exec -n keycloak-auth deploy/keycloak-deployment -- \
  curl -sf http://localhost:9000/health/ready
```

### Acessar o Keycloak no navegador local

> **Contexto:** Traefik está desabilitado no k3d (Kong DB-less assume o roteamento na Wave 3).
> Enquanto o Kong não for implantado, use port-forward para acessar o Keycloak diretamente.

```bash
# Port-forward: expõe o serviço na porta 8090 local (evita conflito com o 8080 do k3d)
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80

# Em outro terminal, acesse via navegador ou curl:
open http://localhost:8090          # painel web do Keycloak
curl http://localhost:8090/health/ready   # retorna {"status":"UP",...}
```

> Após implantar o Kong (Wave 3), o acesso externo passará pela porta 8080 do host
> (mapeada no k3d para a porta 80 do loadbalancer). Nesse caso, adicione ao `/etc/hosts`:
> ```
> 127.0.0.1 keycloak.local
> ```
> E acesse `http://keycloak.local:8080`.

### Checar PriorityClass do pod

```bash
kubectl get pod -l app.kubernetes.io/name=keycloak -n keycloak-auth \
  -o jsonpath='{.items[0].spec.priorityClassName}'
```

---

## PostgreSQL

### Verificar status do pod

```bash
kubectl get pods -l app.kubernetes.io/name=postgresql -n keycloak-auth
```

### Conectar ao banco via psql (dentro do cluster)

```bash
kubectl exec -n keycloak-auth deploy/postgresql-deployment -- \
  psql -U keycloak -d keycloak -c '\l'
```

### Ver logs do PostgreSQL

```bash
kubectl logs -f -l app.kubernetes.io/name=postgresql -n keycloak-auth
```

---

## Cluster k3d

### Subir o cluster e aplicar GitOps

```bash
make up
```

### Derrubar o cluster

```bash
make down
```

### Recriar secrets após reinicialização

```bash
make secrets
# ou
./scripts/inject-secrets.sh
```

---

## Diagnóstico Geral

### Ver todos os pods da infraestrutura

```bash
kubectl get pods -n keycloak-auth
kubectl get pods -n argocd
```

### Checar eventos recentes (erros de scheduling, pull, etc.)

```bash
kubectl get events -n keycloak-auth --sort-by='.lastTimestamp' | tail -20
```

### Checar uso de recursos dos pods

```bash
kubectl top pods -n keycloak-auth
```

### Inspecionar um pod em CrashLoopBackOff

```bash
# Logs da execução atual
kubectl logs <nome-do-pod> -n keycloak-auth

# Logs da execução anterior (antes do crash)
kubectl logs <nome-do-pod> -n keycloak-auth --previous
```

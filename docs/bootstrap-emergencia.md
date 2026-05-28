# Guia de Bootstrap de Emergência - cluster-kubernetes

Este guia documenta o procedimento de recuperação do cluster em cenários de desastre ou reconstrução do "Dia Zero" (Bootstrap de Emergência).

> [!NOTE]
> Este documento é o esqueleto inicial com placeholders (conforme a Story 1.5) e será refinado com comandos e testes de endpoints na Story 3.4.
> Nenhum segredo (senha, chave privada) deve ser persistido no repositório Git.

## Sequência de Recuperação

A reconstrução da plataforma a partir do zero deve seguir rigorosamente a sequência abaixo para garantir a conformidade GitOps e evitar erros de sincronização:

1. **Inicialização do Cluster Local (K3d)**
2. **Criação Prévia dos Namespaces**
3. **Injeção Manual dos Secrets**
4. **Instalação do ArgoCD**
5. **Aplicação do root-app.yaml (Orquestrador do GitOps)**

---

## 1. Inicialização do Cluster Local (K3d)

Para provisionar a infraestrutura de contêineres local com as configurações recomendadas e limites de recursos adequados, execute:

```bash
make up
```

Ou, se preferir inicializar manualmente usando a especificação `k3d.yaml` da raiz do repositório:

```bash
k3d cluster create --config k3d.yaml
```

---

## 2. Criação Prévia dos Namespaces

Antes de iniciar a reconciliação automática pelo ArgoCD, os namespaces fundamentais da infraestrutura devem ser criados previamente. Isso evita falhas de dependência na aplicação dos segredos e componentes.

Crie os namespaces obrigatórios executando:

```bash
kubectl create namespace keycloak-auth
kubectl create namespace kong-gateway
```

---

## 3. Injeção Manual dos Secrets

Os segredos sensíveis nunca devem ser versionados ou armazenados no Git (NFR-S02 / FR22). Em cenários de emergência, o SRE deve injetar os Secrets no cluster de forma estática antes de aplicar a governança do ArgoCD.

### 3.1. Secrets do Identity Provider e Banco de Dados (Namespace: `keycloak-auth`)

*   **Secret de conexão com o Banco de Dados (PostgreSQL):**
    
    Substitua `<VALOR_USUARIO_DB>` e `<VALOR_SENHA_DB>` com suas credenciais reais:
    
    ```bash
    kubectl create secret generic keycloak-db-secret \
      --namespace=keycloak-auth \
      --from-literal=database-user=<VALOR_USUARIO_DB> \
      --from-literal=database-password=<VALOR_SENHA_DB>
    ```
    
    **Exemplo concreto (para referência apenas — use seus próprios valores):**
    ```bash
    kubectl create secret generic keycloak-db-secret \
      --namespace=keycloak-auth \
      --from-literal=database-user=keycloak_user \
      --from-literal=database-password=MySecurePostgresPass2026!
    ```
    
    **Requisitos:**
    - `database-user`: lowercase alphanumeric + underscore, min 3 caracteres
    - `database-password`: mínimo 12 caracteres (recomendado 16+), sem espaços

*   **Secret de administração do console Keycloak:**
    
    Substitua `<VALOR_ADMIN_USER>` e `<VALOR_ADMIN_PASSWORD>` com suas credenciais reais:
    
    ```bash
    kubectl create secret generic keycloak-admin-secret \
      --namespace=keycloak-auth \
      --from-literal=admin-username=<VALOR_ADMIN_USER> \
      --from-literal=admin-password=<VALOR_ADMIN_PASSWORD>
    ```
    
    **Exemplo concreto (para referência apenas — use seus próprios valores):**
    ```bash
    kubectl create secret generic keycloak-admin-secret \
      --namespace=keycloak-auth \
      --from-literal=admin-username=admin_sre \
      --from-literal=admin-password=MySecureAdminPass2026!
    ```
    
    **Requisitos:**
    - `admin-username`: lowercase alphanumeric + underscore, min 3 caracteres
    - `admin-password`: mínimo 12 caracteres (recomendado 16+), sem espaços

### 3.2. Script Utilitário Local (Opcional)

Para acelerar o processo e evitar erros de digitação, você pode utilizar o script utilitário interativo:

```bash
make secrets
```

Ou diretamente:

```bash
./scripts/inject-secrets.sh
```

> [!WARNING]
> O script lê os valores de um arquivo local `.env` (ignorado no Git) ou os solicita de forma interativa. Em ambientes não-interativos, ele gera senhas seguras automaticamente e as exibe. NUNCA envie ou comite o arquivo `.env` gerado.

---

## 4. Instalação do ArgoCD

Com os namespaces criados e os Secrets injetados, instale o ArgoCD de forma idempotente. A instalação utiliza a versão estável e imutável definida nas especificações (`v3.4.2` por padrão) com suporte a manifestos grandes via *Server-Side Apply*:

```bash
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd --server-side=true --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.4.2/manifests/install.yaml
```

Aguarde o ArgoCD ficar totalmente pronto:

```bash
kubectl wait --for=condition=Available --namespace argocd --timeout=180s deployment/argocd-server
```

---

## 5. Aplicação do root-app.yaml (Orquestrador do GitOps)

Aplique a governança recursiva do ArgoCD (padrão App-of-Apps).
Substitua temporariamente a branch de destino (`targetRevision`) no manifesto para coincidir com a sua branch de desenvolvimento local (o script `cluster-up.sh` faz isso de forma transparente, mas o SRE pode fazê-lo manualmente se necessário):

```bash
# Substitua <BRANCH_DESEJADA> pelo branch de trabalho (ex: main ou feature/sua-feature)
sed "s|targetRevision: main|targetRevision: <BRANCH_DESEJADA>|" cluster/bootstrap/root-app.yaml | kubectl apply -f -
```

Uma vez aplicado o `root-app.yaml`, o ArgoCD iniciará a sincronização em cascata de todos os recursos do repositório respeitando rigorosamente as ordens das **Sync Waves** declaradas.

---

## 6. Recuperação via Backup PostgreSQL (FR23)

Use esta seção quando o banco de dados do Keycloak estiver corrompido ou perdido e houver backup disponível. Execute **após** a Etapa 5, com a infraestrutura pronta e em uma janela de manutenção.

### 6.1. Gerar backup (operação de rotina)

```bash
./scripts/pg-backup.sh
# Gera: ./backups/keycloak-db-backup-YYYYMMDD-HHMMSS.dump
```

Armazene o arquivo de dump em local externo ao cluster (ex: S3, NFS, disco externo).

### 6.2. Restaurar banco a partir de backup

Antes do restore:

1. Aguarde o PostgreSQL ficar `Ready`
2. Desative temporariamente o auto-heal de `root-app` e `infra-app` no ArgoCD para evitar que o GitOps religue o Keycloak no meio do procedimento

```bash
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=postgresql \
  -n keycloak-auth --timeout=180s

kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":false}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'

./scripts/pg-restore.sh ./backups/keycloak-db-backup-<timestamp>.dump
```

O script:
1. Escala Keycloak para 0 réplicas (interrupção controlada)
2. Copia o dump para o mesmo pod PostgreSQL que executará o restore
3. Valida o dump com `pg_restore --list` antes de alterar o banco
4. Executa `pg_restore --clean --if-exists`
5. Escala Keycloak de volta para a contagem original de réplicas (hoje, `1`)

### 6.3. Validar restore

O `client_secret` abaixo (`dev-m2m-local-secret`) é um fixture de **desenvolvimento local** criado na Story 2.3 para validar o realm `cluster-local`. Não reutilize esse valor como padrão para outros ambientes.

```bash
kubectl port-forward svc/keycloak-service -n keycloak-auth 8090:80 >/tmp/keycloak-port-forward.log 2>&1 &
PF_PID=$!
sleep 3

if ! kill -0 "$PF_PID" 2>/dev/null; then
  cat /tmp/keycloak-port-forward.log
  exit 1
fi

curl -sf -X POST http://localhost:8090/realms/cluster-local/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=m2m-client&client_secret=dev-m2m-local-secret" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); token=d.get('access_token'); assert token, 'ERRO: access_token ausente'; print('Token OK:', len(token) > 0)"

kill "$PF_PID" 2>/dev/null || true
wait "$PF_PID" 2>/dev/null || true
# Esperado: Token OK: True
```

Após a validação, reative o auto-heal:

```bash
kubectl patch application root-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

kubectl patch application infra-app -n argocd \
  --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":true}}}}'
```

<!-- Autoria/Implementação: claude-sonnet-4-6 -->
<!-- Revisão: GPT-5 Codex -->

# cluster-kubernetes

Plataforma GitOps local-produção construída com k3d, Kong DB-Less e Keycloak. Espelha a topologia de produção no ambiente local, com ciclo de vida automatizado via `make` e bootstrap GitOps via ArgoCD (Sync Waves).

## Pré-requisitos

- **Docker Desktop** com no mínimo **6GB RAM** e **4 CPUs** configurados em Settings → Resources
- **kubectl** (qualquer versão recente compatível com k8s 1.28+)
- **k3d** ≥ 5.8.3 (`brew install k3d` ou [releases oficiais](https://github.com/k3d-io/k3d/releases))
- **make** (padrão na maioria dos sistemas Unix/macOS)

## Início Rápido

```bash
make up
```

O comando valida os manifestos (`lint`) e provisiona o cluster k3d com Kong e Keycloak conforme declarado em `k3d.yaml`.

## Comandos Disponíveis

| Comando       | Descrição                                             |
|---------------|-------------------------------------------------------|
| `make up`     | Provisiona o cluster k3d completo (executa lint antes) |
| `make down`   | Destrói o cluster sem resíduos                        |
| `make token`  | Gera e exibe o token M2M de teste via Keycloak        |
| `make lint`   | Valida todos os manifestos YAML com kube-linter       |
| `make status` | Exibe status dos componentes e URLs locais            |

## Documentação

- [Contrato do Desenvolvedor](docs/contrato-do-desenvolvedor.md) — como publicar APIs na plataforma usando os Boilerplates YAML
- [Bootstrap de Emergência](docs/bootstrap-emergencia.md) — sequência de recuperação manual do cluster

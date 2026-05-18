# cluster-kubernetes

Plataforma GitOps local-produção construída com k3d, Kong DB-Less e Keycloak. Espelha a topologia de produção no ambiente local, com ciclo de vida automatizado via `make` e bootstrap GitOps via ArgoCD (Sync Waves).

## Pré-requisitos

- **Docker Desktop** com no mínimo **6GB RAM** e **4 CPUs** configurados em Settings → Resources
- **kubectl** (qualquer versão recente compatível com k8s 1.28+)
- **k3d** ≥ 5.8.3 (`brew install k3d` ou [releases oficiais](https://github.com/k3d-io/k3d/releases))
- **make** (padrão em sistemas Unix/macOS)

---

### 💻 Usuários Windows (WSL2 Obrigatório)
Para rodar este ambiente no Windows de forma padronizada e com atrito zero, **é obrigatório o uso do WSL2** (Windows Subsystem for Linux), mantendo assim o uso do `Makefile` e scripts shell:
1. Certifique-se de que o **WSL2** está habilitado e configurado com uma distribuição (como Ubuntu).
2. No **Docker Desktop para Windows**, ative a integração com o WSL2 em *Settings → Resources → WSL Integration* para a sua distribuição.
3. Dentro do seu terminal da distribuição WSL2, instale as dependências executando:
   ```bash
   sudo apt update && sudo apt install -y make kubectl
   # Para instalar o k3d no WSL2:
   curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG=v5.8.3 bash
   ```

---

## Início Rápido

```bash
make up
```

O comando compila e valida todos os manifestos recursivamente (`make lint`) e, se aprovados nas validações de segurança e nomenclatura kebab-case, provisiona o cluster k3d com Kong e Keycloak localmente conforme declarado em `k3d.yaml`.

## Comandos Disponíveis (executados sob macOS/Linux ou WSL2)

| Comando        | Descrição                                                               |
|----------------|-------------------------------------------------------------------------|
| `make up`      | Provisiona o cluster k3d completo (executa lint antes)                  |
| `make up-force`| Provisiona o cluster k3d bypassando a validação de lint (depuração)     |
| `make down`    | Destrói o cluster sem resíduos                                          |
| `make token`   | Gera e exibe o token M2M de teste via Keycloak                          |
| `make lint`    | Executa validação de nomenclatura (kebab-case) e segurança (kube-linter) |
| `make status`  | Exibe status detalhado de todos os componentes e URLs locais            |

## Links Úteis & Documentação

- [Contrato do Desenvolvedor](docs/contrato-do-desenvolvedor.md) — guia e contratos para publicação de APIs de negócio usando os boilerplates da plataforma.
- [Bootstrap de Emergência](docs/bootstrap-emergencia.md) — guia passo a passo para recuperação e provisionamento manual em caso de falhas catastróficas.
- [Decisão de Arquitetura](_bmad-output/planning-artifacts/architecture.md) — documento de referência com as decisões arquiteturais de rede, fluxo M2M, gateway Kong e IDP Keycloak.

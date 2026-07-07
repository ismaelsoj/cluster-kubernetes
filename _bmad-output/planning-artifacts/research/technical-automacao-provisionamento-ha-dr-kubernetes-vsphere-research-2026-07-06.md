---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'Automação de provisionamento, HA e disaster recovery de clusters Kubernetes on-premise multi-nó sobre VMware vSphere (dois ambientes) — com comparativo vs. bare-metal'
research_goals: 'Recriar cada cluster do zero de forma reproduzível, com HA real de control plane/etcd e DR em três camadas (VMs, k8s, estado+dados); recomendação priorizada com caminho de migração a partir do processo manual atual; topologia de HA para produção; apêndice comparando bare-metal físico'
user_name: 'Ismael'
date: '2026-07-06'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-07-06
**Author:** Ismael
**Research Type:** technical

---

## Research Overview

Pesquisa técnica para automatizar o provisionamento, garantir HA real e projetar Disaster Recovery de dois clusters Kubernetes on-premise (homologação e produção) rodando como VMs sobre VMware vSphere/ESXi/vCenter, hoje instalados manualmente. Objetivo: recriar cada cluster do zero de forma reproduzível, reaproveitando o GitOps/Kustomize existente (ArgoCD, Kong, MetalLB, Keycloak) e os recursos do vSphere, com apêndice comparativo para bare-metal físico.

**Recomendação principal:** provisionar VMs com **Terraform/OpenTofu (provider `vsphere`)** a partir de um **golden image construído com Packer**, fazer o bootstrap do Kubernetes HA com **Kubespray** e expor o control plane por um **VIP via kube-vip** — mantendo o **ArgoCD + Kustomize existentes** como plano de estado desejado (soldados via bootstrap de App-of-Apps, sem sobreposição). A **alternativa estratégica de futuro** é **Talos Linux + Cluster API (CAPV)**, superior em TCO/segurança e portável para bare-metal via Metal3. Só a camada **VMware é proprietária**; toda a automação do k8s é open source.

**Achado crítico de HA:** a produção atual com **2 control planes tem zero tolerância a falha** (quórum de etcd exige maioria ímpar) — a topologia recomendada é **3 CP com stacked etcd + regras DRS anti-affinity** em hosts ESXi distintos. O **DR é projetado em 3 camadas** (VMs → snapshot de etcd → estado Git/ArgoCD + dados de PV via Velero/CSI), com backups fora do datastore original. O detalhamento completo, matriz comparativa dos 5 candidatos, roadmap de migração e apêndice bare-metal estão na seção **Research Synthesis** ao final deste documento.

---

## Technical Research Scope Confirmation

**Research Topic:** Automação de provisionamento, HA e disaster recovery de clusters Kubernetes on-premise multi-nó sobre VMware vSphere (dois ambientes) — com comparativo vs. bare-metal.
**Research Goals:** Recriar cada cluster do zero de forma reproduzível, com HA real de control plane/etcd e DR em três camadas; recomendação priorizada com caminho de migração a partir do processo manual; topologia de HA para produção; apêndice comparando bare-metal físico.

**Technical Research Scope:**

- Architecture Analysis — topologia de HA do control plane, quórum de etcd, stacked vs. external etcd, integração vSphere (CSI, CPI, HA/vMotion)
- Implementation Approaches — Terraform/OpenTofu+Ansible, Kubespray, Rancher/RKE2/Fleet, Talos+Cluster API (CAPV), Packer
- Technology Stack — proprietário (hypervisor VMware) vs. open source (camada de automação do k8s)
- Integration Patterns — reaproveitamento do GitOps/Kustomize, golden image (Packer + cloud-init/guestinfo), inventário por ambiente
- DR Robustness — três camadas de DR, snapshots de etcd, vSphere CSI + Velero; apêndice bare-metal (MAAS/Tinkerbell/Metal3, PXE+autoinstall)

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims (HA de etcd, matriz de suporte CAPV)
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-07-06

---

## Technology Stack Analysis

> Nota de framing: por ser pesquisa de **infraestrutura/IaC**, a "stack" aqui são camadas — hypervisor, provisionamento de VM, bootstrap do k8s, orquestração de ciclo de vida, e backup/DR — e não linguagens de aplicação. Cada camada é classificada como **proprietária** (VMware) ou **open source** (automação do k8s), atendendo ao requisito de deixar isso explícito.

### Camada de Virtualização (Proprietária — VMware)

- **VMware vSphere / ESXi / vCenter** é a única camada proprietária da solução. Fornece o hypervisor, o gerenciamento centralizado (vCenter) e recursos de resiliência de infraestrutura reutilizáveis como **vSphere HA** (reinício automático de VM em outro host após falha de host) e **vMotion** (migração viva). Esses recursos funcionam como uma camada extra de DR *abaixo* do Kubernetes, independente da automação do cluster.
- **vSphere CSI Driver** (open source, mantido pela VMware/Broadcom) expõe o armazenamento vSphere como `StorageClass`/PV no Kubernetes e habilita **snapshots de volume via CSI Snapshot API** — pré-requisito para backup de dados de PVs.
- _Confiança: Alta._ _Fontes: [Broadcom TechDocs – Velero + CSI Snapshotting](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-supervisor/8-0/backup-and-restore-workloads-using-velero-with-csi-snapshotting.html)_

### Camada de Provisionamento de VM (Open Source)

- **Terraform / OpenTofu com o provider `vsphere`**: infraestrutura como código declarativa para clonar templates, definir CPU/RAM/disco, redes e injetar dados via `guestinfo`/cloud-init. OpenTofu é o fork open source (licença MPL) do Terraform, drop-in para o provider vsphere. É a abordagem madura e amplamente documentada para VMs de nós k8s em vSphere.
- **Packer (provider vSphere-ISO / vsphere-clone)**: constrói o **golden image** (template imutável) — SO base + kubelet/kubeadm/containerd + datasource `guestinfo` do cloud-init pré-instalados. Reduz drift e acelera o bootstrap. Observação relevante: o datasource guestinfo da VMware historicamente exigia uma versão custom do cloud-init, mas **cloud-init 21.3+ traz o datasource VMware nativo**.
- _Confiança: Alta._ _Fontes: [runtimeterror – K8s node template com Packer no vSphere](https://runtimeterror.dev/k8s-on-vsphere-node-template-with-packer/), [Packer vSphere Builder (HashiCorp)](https://developer.hashicorp.com/packer/integrations/vmware/vsphere/latest/components/builder/vsphere-clone), [packer-vsphere-cloud-init (GitHub)](https://github.com/kalenarndt/packer-vsphere-cloud-init)_

### Camada de Bootstrap/Configuração do Kubernetes (Open Source)

- **kubeadm + Ansible**: caminho "de baixo nível" — Terraform cria as VMs, Ansible instala e faz `kubeadm init`/`join`, configura o control plane HA e o etcd. Máximo controle, máxima responsabilidade operacional.
- **Kubespray**: distribuição Ansible opinada e pronta para produção. Cria **etcd HA mantendo quórum durante upgrades**, control plane HA por load balancer, inventário por ambiente. Regras de upgrade importantes: control plane e etcd sobem juntos, **não pular minor releases** (upgrade tag a tag). Já existe módulo `terraform-vsphere-kubespray` que combina provisionamento vSphere + Kubespray.
- **RKE2** (Rancher): distribuição Kubernetes conformante com foco em segurança (padrões CIS), etcd embutido com **snapshots agendados por padrão (00:00 e 12:00, retenção de 5)**, com upload opcional para S3.
- **Talos Linux**: SO minimalista e **imutável** dedicado a Kubernetes, sem SSH e configurado 100% por API declarativa. Reduz drasticamente a superfície de manutenção do SO, ao custo de um modelo mental novo (não há "servidor Linux" tradicional para administrar).
- _Confiança: Alta._ _Fontes: [Kubespray (site oficial)](https://kubespray.io/), [Kubespray – docs de upgrades](https://github.com/kubernetes-sigs/kubespray/blob/master/docs/operations/upgrades.md), [RKE2 – Backup and Restore](https://docs.rke2.io/datastore/backup_restore), [Sidero – Talos Linux](https://www.talos.dev/)_

### Camada de Orquestração de Ciclo de Vida / Multi-cluster (Open Source)

- **Cluster API (CAPI) + provider CAPV (vSphere)**: modelo declarativo Kubernetes-native onde clusters são objetos gerenciados por um cluster de gerenciamento. CAPV provisiona VMs no vSphere; o mesmo CAPI cobre **bare-metal via Metal3**, o que torna a stack portável entre VM e físico. Ponto de atenção verificado: há incompatibilidades conhecidas entre CAPV + IPAM estático e Talos (Talos não consome guestinfo/cloud-init do mesmo modo), exigindo cuidado na configuração de rede.
- **Rancher + Fleet**: painel de gestão (UI/RBAC) para múltiplos clusters e **Fleet** para GitOps em escala de frota. Sobreposição potencial com o ArgoCD já existente (ver análise de integração).
- _Confiança: Média-Alta (o ecossistema CAPI/CAPV evolui rápido; validar matriz de versões na adoção)._ _Fontes: [Cluster API Book – Provider List](https://cluster-api.sigs.k8s.io/reference/providers), [Provisionar Talos com CAPI no vSphere](https://oneuptime.com/blog/post/2026-03-03-provision-talos-clusters-with-capi-on-vsphere/view), [Issue CAPV + Talos IPAM](https://github.com/kubernetes-sigs/cluster-api-provider-vsphere/issues/3647)_

### Camada de Backup e Disaster Recovery (Open Source)

- **etcd snapshot**: base de DR do estado do control plane. Nativo em kubeadm (`etcdctl snapshot`), agendado por padrão em RKE2, e gerenciado por Rancher Backup / CAPI conforme a stack.
- **Velero**: backup/restore de objetos Kubernetes + dados de PV. A partir do **Velero 1.14 o plugin CSI está integrado** (não precisa instalar separado); desde o 1.12 há **data movement** de snapshots CSI para object storage (S3/MinIO), essencial para DR fora do datastore original. Para vSphere, a VMware recomenda o método **CSI snapshot para volumes de bloco CNS**.
- **Git (GitOps existente)**: a fonte de verdade do *estado desejado* de workloads/infra (ArgoCD + Kustomize) já é, por si só, a camada de DR do estado declarativo — não precisa ser reconstruída.
- _Confiança: Alta._ _Fontes: [Velero – CSI Snapshot Support](https://velero.io/docs/main/csi/), [Broadcom TechDocs – Velero + CSI](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-supervisor/8-0/backup-and-restore-workloads-using-velero-with-csi-snapshotting.html), [Rancher – Backup/Restore e DR](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/backup-restore-and-disaster-recovery/restore-rancher-launched-kubernetes-clusters-from-backup)_

### Camada Bare-Metal (Open Source — apêndice comparativo)

- **MAAS (Canonical)**: o mais maduro (~10 anos), gerência de hardware estilo IaaS via IPMI/Redfish, ampla cobertura de fabricantes (Dell, HP, Cisco). Robusto, porém mais pesado/menos ágil.
- **Tinkerbell**: provisionamento moderno baseado em workflows (cada passo é uma imagem Docker), flexível, ganhando tração como alternativa ao MAAS.
- **Metal3**: "Bare Metal Host Provisioning for Kubernetes" — Kubernetes-native, construído sobre **Ironic**, com integração **Cluster API** nativa (provider CAPM3). É o caminho que **preserva o modelo declarativo CAPI** ao migrar de VM para físico.
- _Confiança: Média-Alta._ _Fontes: [Spectro Cloud – Bare Metal K8s com CAPI + MAAS](https://www.spectrocloud.com/blog/how-to-provision-bare-metal-k8s-clusters-with-cluster-api-and-canonical-maas), [awesome-baremetal (alexellis)](https://github.com/alexellis/awesome-baremetal/blob/master/README.md), [The New Stack – Provision Bare Metal K8s with CAPI](https://thenewstack.io/provision-bare-metal-kubernetes-with-the-cluster-api/)_

### Technology Adoption Trends

- **Convergência para modelos declarativos e imutáveis**: Talos + Cluster API representam a fronteira "cloud-native de infra" (o cluster gerencia clusters); Terraform+Ansible e Kubespray permanecem como o mainstream pragmático para equipes pequenas.
- **Portabilidade VM↔bare-metal via CAPI**: escolher a camada de orquestração pensando em Metal3 preserva investimento caso o vSphere seja abandonado no futuro.
- **Object storage como âncora de DR**: a tendência clara (Velero data movement, RKE2 S3, etcd snapshot em S3) é externalizar backups para um alvo S3/MinIO independente do datastore vSphere.
- _Confiança: Média (leitura de tendência)._ _Fontes: [Sidero – Reference Architecture com Talos (2025)](https://www.siderolabs.com/wp-content/uploads/2025/08/Kubernetes-Cluster-Reference-Architecture-with-Talos-Linux-for-2025-05.pdf), [The New Stack – Bare Metal in a Cloud Native World](https://thenewstack.io/bare-metal-in-a-cloud-native-world/)_

## Integration Patterns Analysis

> Framing: "integração" aqui é como as camadas se acoplam entre si e com o vSphere e o GitOps já existente — os *handoffs* entre provisionar VM → bootstrap k8s → estado desejado → dados.

### Handoff vSphere → VM → OS (guestinfo / cloud-init)

- O ponto de integração fundamental é a injeção de configuração na primeira boot da VM. Terraform/OpenTofu (ou CAPV) grava dados na propriedade **`guestinfo.metadata` / `guestinfo.userdata`** da VM; o **cloud-init** (datasource VMware, nativo desde 21.3) lê e aplica hostname, IP estático, chaves e o script de `kubeadm`/RKE2. O golden image do Packer garante que esse datasource já venha instalado.
- **Atenção verificada:** Talos **não** consome cloud-init/guestinfo como o Linux tradicional — usa `machineconfig` próprio via guestinfo, e há incompatibilidades conhecidas com CAPV + IPAM estático. Se optar por Talos, o padrão de injeção de rede muda.
- _Confiança: Alta._ _Fontes: [packer-vsphere-cloud-init](https://github.com/kalenarndt/packer-vsphere-cloud-init), [Issue CAPV+Talos IPAM #3647](https://github.com/kubernetes-sigs/cluster-api-provider-vsphere/issues/3647)_

### Endpoint HA do Control Plane (VIP) — integração de rede

- Para HA real do control plane on-premise sem hardware, o padrão atual é **kube-vip**: fornece um **VIP para o `kube-apiserver`** (porta 6443) e faz load balancing L4 (IPVS round-robin) entre os control planes, rodando como pod estático no próprio cluster — elimina as 2 VMs extras de HAProxy+Keepalived e o custo de manutenção associado. Modos: **ARP/L2** (leader election) ou **BGP/L3**.
- Alternativa tradicional: **HAProxy + Keepalived** em 2 VMs dedicadas (mais peça móvel, fora do controle do k8s).
- Observação de convivência: o projeto já usa **MetalLB** para Services `LoadBalancer`. kube-vip também sabe fazer LB de Services — **não** duplicar essa função; manter MetalLB para dados e usar kube-vip **apenas para o VIP do control plane** evita sobreposição. (RKE2/Kubespray/CAPV frequentemente já embutem kube-vip como opção.)
- _Confiança: Alta._ _Fontes: [kube-vip (GitHub)](https://github.com/kube-vip/kube-vip), [kube-vip Architecture](https://kube-vip.io/docs/about/architecture/), [kubeadm – HA considerations](https://github.com/kubernetes/kubeadm/blob/main/docs/ha-considerations.md)_

### Integração com o GitOps existente (ArgoCD + Kustomize) — evitar sobreposição

- **Fronteira recomendada — dois planos distintos:**
  - **Plano de infraestrutura de cluster** (provisionar VM + bootstrap k8s + VIP + CNI/CSI/CPI base): responsabilidade da nova camada de automação (Terraform/Kubespray/CAPI). Isso roda **antes** de existir um cluster para o ArgoCD.
  - **Plano de estado desejado** (Kong, MetalLB, Keycloak, PostgreSQL, apps de negócio): permanece **exclusivamente** no repositório GitOps atual com ArgoCD + Kustomize, respeitando sync-waves e overlays por ambiente já definidos no `project-context.md`.
- **Ponto de conexão (o "último passo" do provisionamento):** após o cluster subir, a automação só precisa **instalar o ArgoCD (bootstrap) e aplicar o App-of-Apps raiz** apontando para o repositório existente. A partir daí o ArgoCD reconcilia tudo. Isso mantém o GitOps como fonte de verdade e evita reescrever qualquer manifesto.
- **Sobre Rancher/Fleet:** Fleet e ArgoCD **podem coexistir** (Fleet para config de nível de cluster, ArgoCD para apps), mas para uma equipe pequena que **já opera ArgoCD**, adicionar Fleet cria sobreposição de GitOps e curva de aprendizado dupla. Se Rancher entrar, o racional é usá-lo pela **gestão/UI/snapshots de etcd**, mantendo o ArgoCD como o motor de entrega — não migrar para Fleet.
- _Confiança: Alta._ _Fontes: [Rancher Fleet vs ArgoCD](https://oneuptime.com/blog/post/2026-03-20-rancher-fleet-vs-argocd/view), [Rancher – Continuous Delivery with Fleet](https://ranchermanager.docs.rancher.com/integrations-in-rancher/fleet)_

### Injeção de Secrets no bootstrap (fronteira de segurança)

- O `project-context.md`/SPEC impõem: **Secrets nunca no Git**; são injetados manualmente no bootstrap. A camada de automação deve integrar-se a esse contrato — credenciais do vSphere (para o provider) e Secrets iniciais do cluster ficam fora do Git (ex.: variáveis de ambiente, `terraform.tfvars` não versionado, ou um cofre). A automação **não** deve versionar esses segredos junto do IaC.
- _Confiança: Alta (regra do próprio repositório)._ _Fonte: `_bmad-output/project-context.md` (Segurança e Limites Arquiteturais)._

### Padrão de Ciclo de Vida CAPI: bootstrap → pivot → self-managed

- Se a escolha for Cluster API (CAPV), o padrão de integração é: um **cluster de gerenciamento temporário** (KIND local) cria o cluster alvo; em seguida `clusterctl move` faz o **pivot** dos objetos CAPI para dentro de um cluster de gerenciamento permanente (ou para o próprio alvo, self-managed). Isso define **onde vive a fonte de verdade da topologia** — decisão arquitetural relevante para uma equipe pequena (um cluster de gerenciamento a mais para operar).
- _Confiança: Alta._ _Fontes: [clusterctl move (CAPI Book)](https://cluster-api.sigs.k8s.io/clusterctl/commands/move), [CAPV (GitHub)](https://github.com/kubernetes-sigs/cluster-api-provider-vsphere)_

### Integração das camadas de DR (encadeamento)

- As três camadas de DR precisam se integrar em uma sequência de restore coerente: **(1)** re-provisionar VMs (Terraform/CAPV a partir do golden image) → **(2)** re-bootstrap do k8s + restaurar **snapshot de etcd** (recupera o estado do control plane) → **(3)** ArgoCD reconcilia o estado desejado do Git **e** Velero restaura os **dados de PV** (CSI snapshot movido para S3/MinIO). O acoplamento chave é: o etcd snapshot e o Velero/S3 devem estar **fora do datastore vSphere original** para sobreviver à perda do ambiente.
- _Confiança: Alta._ _Fontes: [Velero – CSI](https://velero.io/docs/main/csi/), [RKE2 – Backup/Restore](https://docs.rke2.io/datastore/backup_restore)_

## Architectural Patterns and Design

### System Architecture Patterns — Topologia de HA do Control Plane

- **Regra do quórum (fundamento):** etcd usa consenso Raft e exige **maioria**. Números pares não agregam tolerância: 2 nós toleram **0** falhas (igual a 1), 4 toleram 1 (igual a 3). Produção **sempre ímpar**: 3 (tolera 1), 5 (tolera 2), 7 (tolera 3). **A produção atual com 2 CP tem zero tolerância a falha e é mais frágil que 1 CP** (duas peças que precisam concordar). Portanto: **3 control planes é o mínimo de HA real.**
- **Stacked vs External etcd** (decisão arquitetural central):
  - **Stacked** (etcd como static pod em cada CP — default do kubeadm): mais simples de instalar e operar, comunicação apiserver↔etcd por loopback (menor latência), **3 hosts**. Risco: falha de um nó derruba um CP **e** um membro etcd juntos (acoplamento).
  - **External** (etcd em nós dedicados): desacopla falhas e permite discos/IO dedicados ao etcd, mas exige **o dobro de hosts** (3 CP + 3 etcd = 6) e mais complexidade.
  - **Recomendação para equipe pequena:** **stacked etcd com 3 CP.** O ganho do external etcd não compensa a complexidade operacional e o consumo de VMs para 2 clusters pequenos; escalar para external só se o etcd virar gargalo comprovado.
- **Anti-afinidade no vSphere (crítico e frequentemente esquecido):** os 3 CP/etcd **devem** rodar em hosts ESXi físicos distintos. Usar **regras DRS anti-affinity ("VM-VM anti-affinity")** para impedir que o vSphere co-localize dois membros etcd no mesmo host — senão a falha de **um host físico** derruba 2 dos 3 membros e o quórum cai, anulando a HA. Cuidado equivalente ao fazer vMotion manual.
- _Confiança: Alta._ _Fontes: [Kubernetes – HA Topology](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/), [Kubernetes – Creating HA Clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/), [Sidero – Why 3 nodes](https://www.siderolabs.com/blog/why-should-a-kubernetes-control-plane-be-three-nodes), [VMware Tanzu Hub – etcd design](https://hub.vmware.com/cluster-designs/etcd/)_

### Topologia de HA Recomendada (Produção)

| Elemento | Recomendação |
|---|---|
| Control planes | **3 nós** (stacked etcd), quórum 2, tolera falha de 1 |
| Workers | 3+ (o atual atende; escalar por demanda) |
| Endpoint do apiserver | **VIP via kube-vip** (L2/ARP ou BGP), porta 6443 |
| Distribuição física | 3 CP em **3 hosts ESXi distintos** via **DRS anti-affinity** |
| Homologação | 1 CP + 2 workers é aceitável (não-HA); mas o **mesmo código/automação** deve permitir subir 3 CP — validar o caminho HA em homolog |
| Números ímpares | Nunca 2 nem 4 CP; escalar 3 → 5 só se necessário |

- **Escalar de 2 → 3 CP** com kubeadm: `kubeadm join --control-plane` adiciona automaticamente um membro etcd ao quórum — caminho suportado e de baixo risco quando a automação é idempotente.

### Data Architecture Patterns — Design de DR em 3 Camadas

Arquitetura de DR como **pirâmide de restore**, cada camada com sua fonte de verdade e alvo de backup **fora do datastore vSphere original**:

1. **Camada 1 — Infra/VM (vSphere):** re-provisionar VMs a partir do **golden image (Packer template)** via Terraform/CAPV. Fonte de verdade = código IaC no Git. DR extra "grátis" do hypervisor: **vSphere HA** (reinício de VM em outro host) e **snapshot de VM** (rollback rápido pré-upgrade). RPO da infra ≈ commit do IaC.
2. **Camada 2 — Control Plane/Estado do cluster (etcd):** **snapshots de etcd** agendados (a cada 2–6h conforme taxa de mudança), verificados após criação, **armazenados off-cluster (S3/MinIO) com encriptação**. Restore só como último recurso (ação destrutiva). Guardar o arquivo de encriptação separado do snapshot. **RTO/RPO do control plane** definido pela cadência do snapshot.
3. **Camada 3 — Estado desejado + Dados:**
   - **Estado desejado** (workloads/infra): já coberto pelo **Git + ArgoCD** — reconcilia automaticamente ao subir o cluster. RPO ≈ 0 (é o Git).
   - **Dados persistentes (PVs):** **Velero** com **CSI snapshot** (volumes CNS de bloco) + **data movement para S3/MinIO** (Velero 1.12+; plugin CSI integrado no 1.14+). Cobre o que o Git não guarda (estado de bancos, uploads etc.).

- **Sequência de restore end-to-end:** re-provisionar VMs (Cam.1) → re-bootstrap k8s + restore etcd (Cam.2) → ArgoCD reconcilia Git + Velero restaura PVs (Cam.3). **Teste periódico obrigatório** — "um backup nunca testado é um backup em que não se pode confiar".
- _Confiança: Alta._ _Fontes: [etcd – Disaster recovery](https://etcd.io/docs/v3.5/op-guide/recovery/), [Kubernetes – Operating etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/), [Velero – CSI](https://velero.io/docs/main/csi/), [Restore etcd snapshot – guia](https://oneuptime.com/blog/post/2026-02-09-restore-etcd-snapshot-cluster-state/view)_

### Design Principles — Reprodutibilidade e Imutabilidade

- **Golden image imutável (Packer)** + **injeção declarativa (cloud-init/guestinfo)** = nós reproduzíveis bit-a-bit, sem drift de configuração manual.
- **Inventário/estado por ambiente:** homolog e produção como diretórios/inventários separados (Kubespray inventory, Terraform workspaces/tfvars, ou CAPI Cluster objects), espelhando os overlays Kustomize `homologacao`/`production` já existentes.
- **Idempotência:** toda a automação deve ser re-executável para "recriar do zero" sem estado escondido — critério central do objetivo.
- _Confiança: Alta._ _Fontes: [runtimeterror – Packer K8s node template](https://runtimeterror.dev/k8s-on-vsphere-node-template-with-packer/), [Kubespray](https://kubespray.io/)_

### Security Architecture Patterns

- **Fronteira proprietário↔open source explícita:** só o vSphere é proprietário; toda automação do k8s é open source e portável (via CAPI) para bare-metal.
- **Secrets fora do Git** no bootstrap (contrato do repositório); credenciais vSphere fora do IaC versionado.
- **Segregação de ambientes** (chaves/realms Keycloak distintos dev↔prod) preservada — a automação não deve unificar segredos entre ambientes.
- **etcd encriptado em repouso** e snapshots encriptados no object storage.
- _Confiança: Alta._ _Fontes: `project-context.md`; [etcd – recovery/encryption](https://etcd.io/docs/v3.5/op-guide/recovery/)_

### Deployment and Operations Architecture

- **Separação de planos:** provisionamento (Terraform/CAPI/Kubespray) **abaixo**, GitOps (ArgoCD+Kustomize) **acima**; ponto de solda = bootstrap do ArgoCD + App-of-Apps raiz.
- **Upgrades:** tratados pela camada de bootstrap — Kubespray sobe CP+etcd juntos, tag a tag (não pular minor); RKE2/Talos/CAPI têm fluxos declarativos de upgrade (rolling de nós). vSphere snapshot de VM como rollback de segurança pré-upgrade.
- _Confiança: Alta._ _Fontes: [Kubespray – upgrades](https://github.com/kubernetes-sigs/kubespray/blob/master/docs/operations/upgrades.md), [RKE2 – Backup/Restore](https://docs.rke2.io/datastore/backup_restore)_

## Implementation Approaches and Technology Adoption

### Matriz Comparativa dos 5 Candidatos

Avaliação por critério (⭐ = fraco … ⭐⭐⭐⭐⭐ = forte) para o cenário: 2 clusters pequenos, VMs vSphere, equipe pequena, GitOps ArgoCD já em uso.

| Critério | 1. Terraform/OpenTofu + Ansible | 2. Kubespray | 3. Rancher + RKE2/Fleet | 4. Talos + Cluster API (CAPV) | 5. Packer (complemento) |
|---|---|---|---|---|---|
| Reprodutibilidade | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (habilita todas) |
| HA de etcd | ⭐⭐⭐ (você monta) | ⭐⭐⭐⭐⭐ (opinado, quórum em upgrade) | ⭐⭐⭐⭐⭐ (snapshot nativo) | ⭐⭐⭐⭐⭐ (declarativo) | n/a |
| Fit vSphere | ⭐⭐⭐⭐⭐ (provider nativo) | ⭐⭐⭐⭐ (via TF wrapper) | ⭐⭐⭐ (node driver vSphere) | ⭐⭐⭐⭐ (CAPV; cuidado guestinfo) | ⭐⭐⭐⭐⭐ |
| Upgrades | ⭐⭐ (manual) | ⭐⭐⭐⭐ (tag a tag) | ⭐⭐⭐⭐⭐ (UI/rolling) | ⭐⭐⭐⭐⭐ (replace node) | n/a |
| Robustez de DR | ⭐⭐⭐ (você monta) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (etcd+Rancher backup) | ⭐⭐⭐⭐ (declarativo+Velero) | n/a |
| Esforço p/ equipe pequena | ⭐⭐ (muito código próprio) | ⭐⭐⭐ (curva íngreme, deploy longo) | ⭐⭐⭐⭐ (UI ajuda; +componente) | ⭐⭐⭐ (curva alta, mas menos manutenção contínua) | ⭐⭐⭐⭐ |
| Gestão de 2 ambientes | ⭐⭐⭐ (workspaces/tfvars) | ⭐⭐⭐⭐ (inventário/ambiente) | ⭐⭐⭐⭐⭐ (UI multi-cluster) | ⭐⭐⭐⭐ (Cluster objects) | n/a |
| Curva de aprendizado | ⭐⭐⭐ (já conhecido) | ⭐⭐ (Ansible avançado) | ⭐⭐⭐ (ecossistema Rancher) | ⭐⭐ (imutável = paradigma novo) | ⭐⭐⭐⭐ |
| Aproveitamento vSphere | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

_Fontes: [Choosing the Right K8s Distribution](https://oneuptime.com/blog/post/2025-11-27-choosing-the-right-kubernetes-distribution/view), [Equinix: Kubespray → Talos](https://www.siderolabs.com/case-studies/equinix-switches-from-kubespray-to-talos-linux-cutting-deployment-time-while-maintaining-security), [Kubespray vs Cluster API (issue #8753)](https://github.com/kubernetes-sigs/kubespray/issues/8753), [CAPI – guia prático](https://pradeepl.com/blog/kubernetes/cluster-api-capi/)_

### Technology Adoption Strategies — Prós/Contras por opção

- **1. Terraform/OpenTofu + Ansible:** Máximo controle e fit vSphere; reaproveita conhecimento comum. **Contra:** você constrói e mantém a HA de etcd, upgrades e DR "na mão" — muito código próprio para uma equipe pequena. Bom como **camada de provisionamento de VM**, fraco como solução completa de k8s sozinho.
- **2. Kubespray:** Opinado e pronto para produção, HA de etcd sólida, inventário por ambiente encaixa nos overlays. **Contra:** Ansible avançado, deploys longos (caso Equinix: 45 min) e upgrades tag-a-tag; "curar" nó é difícil (não é cattle).
- **3. Rancher + RKE2/Fleet:** Melhor experiência de **gestão de 2 clusters** (UI, RBAC, snapshots de etcd nativos, DR robusto). **Contra:** adiciona um componente de plataforma para operar e **Fleet sobrepõe o ArgoCD**; para equipe que já usa ArgoCD, o valor está na gestão/RKE2, não no Fleet.
- **4. Talos + Cluster API (CAPV):** Fronteira cloud-native: SO imutável (sem SSH, ~20–40h de segurança/ano vs 80–160h no kubeadm), upgrades por "replace node", declarativo, **portável para bare-metal via Metal3**. TCO 40–60% menor que kubeadm em estudos. **Contra:** paradigma novo (curva alta), incompatibilidades conhecidas CAPV+guestinfo+IPAM, e o cluster de gerenciamento CAPI é uma peça a mais.
- **5. Packer:** Não compete — **complementa todas**. Golden image imutável é pré-requisito de reprodutibilidade. Deve entrar independentemente da opção principal.
- _Confiança: Alta._ _Fontes: acima + [Talos TCO](https://oneuptime.com/blog/post/2026-03-03-compare-talos-linux-tco-vs-other-kubernetes-distros/view)_

### Deployment and Operations Practices

- **Golden image primeiro (Packer):** base de tudo; versionar o template.
- **Provisionamento idempotente:** re-executável para "recriar do zero"; estado do IaC no Git, secrets fora.
- **Bootstrap → GitOps:** último passo instala ArgoCD + App-of-Apps; ArgoCD assume Kong/Keycloak/MetalLB/apps.
- **DR testado:** runbook das 3 camadas exercitado periodicamente (game day).

### Team Organization and Skills

- Equipe pequena → **minimizar superfície operacional contínua** pesa mais que sofisticação. Isso favorece soluções opinadas (Kubespray/RKE2) ou imutáveis (Talos) sobre "montar tudo com TF+Ansible".
- Reaproveitar skill existente (Terraform, ArgoCD/Kustomize) reduz curva.

### Risk Assessment and Mitigation

- **Risco: 2 CP em prod (zero tolerância)** → mitigação prioritária: ir a 3 CP + anti-affinity DRS.
- **Risco: backups no mesmo datastore** → externalizar para S3/MinIO.
- **Risco: lock-in vSphere** → escolher camada portável (CAPI) mantém saída para bare-metal.
- **Risco: curva do Talos/CAPI travar a equipe** → mitigar adotando primeiro a camada de provisionamento e migrando o bootstrap por etapas.

## Technical Research Recommendations

### Recomendação Priorizada

- **Opção principal recomendada: Kubespray sobre VMs provisionadas por Terraform/OpenTofu (provider vsphere) + Packer para o golden image + kube-vip para o VIP do control plane.**
  - **Por quê:** melhor equilíbrio entre **HA de etcd pronta e opinada**, **fit vSphere**, **reaproveitamento de skill (Terraform/Ansible)** e **curva aceitável** sem introduzir um paradigma totalmente novo nem um componente de plataforma extra. Encaixa nos overlays por ambiente e no GitOps existente sem sobreposição. Terraform provisiona VM (Cam.1 do DR), Kubespray faz o k8s HA (Cam.2), ArgoCD+Velero cobrem Cam.3.
- **Alternativa estratégica (visão de futuro): Talos Linux + Cluster API (CAPV).** Escolha superior em TCO, segurança e **portabilidade para bare-metal (Metal3)**. Recomendada se a equipe aceitar investir na curva imutável/declarativa — é o destino natural se o roadmap incluir sair do vSphere.
- **Rancher/RKE2:** adotar **apenas se** a gestão visual de 2+ clusters e snapshots nativos forem prioridade explícita; nesse caso usar RKE2 pela robustez, **mantendo ArgoCD** (não migrar para Fleet).
- **Packer:** adotar **sempre**, independentemente da opção.

### Implementation Roadmap (migração a partir do processo manual)

1. **Fase 0 — Golden image:** criar template vSphere com Packer (SO + containerd + kubelet/kubeadm + cloud-init/guestinfo). Entrega isolada, baixo risco.
2. **Fase 1 — Provisionamento IaC:** Terraform/OpenTofu (provider vsphere) para VMs de **homologação** a partir do template; injeção via guestinfo. Valida reprodutibilidade das VMs.
3. **Fase 2 — Bootstrap k8s em homolog:** Kubespray com inventário `homologacao` (1 CP) — porém **testar já o caminho de 3 CP** para validar HA. kube-vip para o VIP.
4. **Fase 3 — GitOps solda:** último passo do bootstrap instala ArgoCD + App-of-Apps apontando para o repo atual; validar que Kong/Keycloak/MetalLB sobem via sync-waves sem alteração.
5. **Fase 4 — DR:** configurar snapshots de etcd (S3/MinIO) + Velero CSI; **executar um restore completo em homolog** (game day) e escrever o runbook.
6. **Fase 5 — Produção com HA real:** aplicar em prod com **3 CP (stacked etcd) + DRS anti-affinity** e 3 workers. Migração pode ser "blue-green" (subir cluster novo reproduzível e cutover) ou in-place (escalar 2→3 CP).
7. **Fase 6 (opcional/futuro):** avaliar migração da camada de bootstrap para Talos+CAPI, ganhando portabilidade bare-metal, sem tocar no GitOps.

### Success Metrics and KPIs

- **Reprodutibilidade:** recriar homolog do zero em < X min por comando único, sem passos manuais.
- **HA real:** derrubar 1 CP em prod sem perda de plano de controle (teste de caos).
- **DR:** RTO/RPO medidos em game day; restore de etcd + PVs bem-sucedido.
- **Sobreposição zero:** nenhum manifesto do GitOps existente reescrito.
- **Cobertura de anti-affinity:** 3 CP comprovadamente em 3 hosts ESXi distintos.

---

# Research Synthesis — Clusters Reproduzíveis: Automação, HA e DR de Kubernetes sobre vSphere

## Executive Summary

Dois clusters Kubernetes on-premise (homologação e produção) construídos e configurados **manualmente** são, hoje, o principal risco operacional deste ambiente: não há garantia de recriá-los de forma idêntica, a produção roda com **2 control planes — uma topologia que, por causa do quórum de etcd, tolera zero falhas** (pior que 1 nó), e o Disaster Recovery depende de conhecimento tácito em vez de procedimento testado. Em 2025 o consenso da indústria é claro: infraestrutura on-premise deve ser **declarativa, reproduzível e versionada** — organizações que adotam GitOps/IaC recriam ambientes inteiros com um comando e apresentam significativamente menos misconfigurações. Este projeto já tem metade do caminho andado (ArgoCD + Kustomize gerenciando Kong, MetalLB, Keycloak); falta automatizar a **camada abaixo do GitOps** — provisionar VMs e fazer o bootstrap do cluster HA.

A recomendação priorizada é **Terraform/OpenTofu (provider `vsphere`) provisionando VMs a partir de um golden image Packer, com Kubespray fazendo o bootstrap do Kubernetes HA e kube-vip fornecendo o VIP do control plane**. Essa combinação entrega HA de etcd opinada e pronta, máximo fit com vSphere, reaproveita skill de Terraform/Ansible e evita introduzir um paradigma radicalmente novo ou um componente de plataforma extra para uma equipe pequena. O ArgoCD existente permanece intocado: o último passo da automação apenas o instala e aplica o App-of-Apps raiz. Como **alternativa estratégica de futuro**, Talos Linux + Cluster API (CAPV) oferece TCO 40–60% menor, superfície de segurança drasticamente reduzida e **portabilidade para bare-metal via Metal3** — o destino natural caso sair do vSphere entre no roadmap.

A única camada proprietária de toda a solução é o **hypervisor VMware**; toda a automação do Kubernetes é open source e portável. O DR é desenhado em **três camadas encadeadas** — re-provisionar VMs, restaurar snapshot de etcd, e reconciliar estado desejado (Git/ArgoCD) + dados de PV (Velero/CSI) — com o princípio inegociável de manter backups **fora do datastore vSphere original** (S3/MinIO) e **testá-los periodicamente**.

**Key Technical Findings:**

- **Quórum ímpar é lei de HA:** 2 CP = 0 tolerância a falha; **3 CP (stacked etcd) é o mínimo de HA real**, e os 3 nós precisam de **DRS anti-affinity** em hosts ESXi distintos — sem isso, a falha de 1 host físico derruba o quórum.
- **Fronteira proprietário↔open source:** só o vSphere/ESXi/vCenter é proprietário; Terraform/OpenTofu, Packer, Kubespray, kube-vip, etcd, Velero, Talos, Cluster API e Metal3 são todos open source.
- **Reaproveitamento do GitOps sem sobreposição:** provisionamento e GitOps são planos distintos, soldados por um único ponto (bootstrap do ArgoCD + App-of-Apps). Fleet sobreporia o ArgoCD e é desnecessário.
- **DR em 3 camadas com backup externalizado:** VM (golden image + vSphere HA/snapshot) → etcd snapshot (2–6h, S3/MinIO, encriptado) → Git/ArgoCD (RPO≈0) + Velero CSI para PVs.
- **Bare-metal muda 3 coisas:** troca do provider de infra (vSphere → Metal3/MAAS/Tinkerbell + PXE/autoinstall), **perda dos snapshots de VM e do vSphere HA/vMotion**, e DR de nós mais manual (reprovisionar via PXE). A camada de bootstrap k8s e o GitOps permanecem iguais — especialmente se via Cluster API.

**Technical Recommendations:**

1. Adotar **Packer (golden image) sempre**, como base de reprodutibilidade — independente da opção principal.
2. Implementar **Terraform/OpenTofu (vsphere) + Kubespray + kube-vip** como stack principal de provisionamento e bootstrap HA.
3. Corrigir a topologia de produção para **3 control planes (stacked etcd) + DRS anti-affinity**, prioridade máxima de risco.
4. Desenhar e **testar (game day)** o DR em 3 camadas com etcd snapshot + Velero/CSI em **S3/MinIO externo**.
5. Manter **ArgoCD + Kustomize** como plano de estado desejado; **não** adotar Fleet.
6. Avaliar **Talos + Cluster API (CAPV/Metal3)** como evolução de médio prazo se portabilidade bare-metal ou redução de TCO virarem prioridade.

## Table of Contents

1. Introdução e Metodologia
2. Panorama Técnico e Análise de Arquitetura (HA)
3. Abordagens de Implementação e Melhores Práticas
4. Stack Tecnológica e Fronteira Proprietário↔Open Source
5. Padrões de Integração e Interoperabilidade (GitOps sem sobreposição)
6. Disaster Recovery em 3 Camadas
7. Segurança e Conformidade
8. Recomendações Técnicas Estratégicas
9. Roadmap de Implementação e Avaliação de Riscos
10. Perspectiva Futura (Talos/CAPI, bare-metal)
11. Metodologia de Pesquisa e Verificação de Fontes
12. Apêndices (Matriz comparativa, **Apêndice A — Bare-metal físico**)

## 1. Introdução e Metodologia

**Significância técnica.** Recriar clusters de forma reproduzível deixou de ser sofisticação e virou requisito de resiliência: em 2025, IaC + GitOps são o padrão para infraestrutura on-premise, permitindo recriar ambientes inteiros com um comando e reduzir misconfigurations de forma mensurável. Para este ambiente — dois clusters manuais, produção sem HA real e DR não testado — automatizar a camada de provisionamento é a maior alavanca de redução de risco disponível. _Fontes: [CNCF – GitOps in 2025](https://www.cncf.io/blog/2025/06/09/gitops-in-2025-from-old-school-updates-to-the-modern-way/), [GitOps 2025 – Declarative Automation](https://blog.madrigan.com/en/blog/202511291342/)_

**Metodologia.** Pesquisa em 6 etapas (escopo → stack → integração → arquitetura → implementação → síntese), cada afirmação técnica crítica ancorada em fontes públicas atuais (docs oficiais Kubernetes/kubeadm, etcd, Kubespray, RKE2, Talos/Sidero, Cluster API, Velero, Broadcom/VMware, HashiCorp) e validada por múltiplas fontes quando de alto impacto (HA de etcd, matriz CAPV, DR). Contexto do repositório (`SPEC.md`, `project-context.md`) tratado como fato persistente.

**Objetivos atingidos.** (a) recomendação priorizada com caminho de migração ✔; (b) topologia de HA para produção ✔; (c) DR em 3 camadas ✔; (d) apêndice bare-metal ✔; (e) fronteira proprietário↔open source explícita ✔; (f) reaproveitamento do GitOps sem sobreposição ✔.

## 2–7. Síntese das Seções Analíticas

As análises detalhadas estão nas seções acima deste documento:

- **Arquitetura de HA (§Architectural Patterns):** quórum ímpar, stacked vs external etcd, 3 CP + kube-vip, DRS anti-affinity, tabela de topologia recomendada para produção.
- **Implementação (§Implementation Approaches):** matriz comparativa dos 5 candidatos, prós/contras, TCO, e recomendação priorizada.
- **Stack (§Technology Stack Analysis):** camadas mapeadas e classificação proprietário↔open source.
- **Integração (§Integration Patterns):** handoff guestinfo/cloud-init, VIP kube-vip vs MetalLB, fronteira ArgoCD, secrets no bootstrap, ciclo CAPI.
- **DR (§Data Architecture Patterns):** pirâmide de restore em 3 camadas e sequência end-to-end.
- **Segurança:** só VMware é proprietária; secrets fora do Git; segregação de ambientes; etcd/snapshots encriptados.

## 8. Recomendações Técnicas Estratégicas

- **Stack principal:** Packer + Terraform/OpenTofu (vsphere) + Kubespray + kube-vip, com ArgoCD/Kustomize preservados.
- **Topologia de prod:** 3 CP stacked etcd + 3 workers + DRS anti-affinity + VIP kube-vip.
- **Vantagem competitiva/estratégica:** escolher camadas portáveis (e, no futuro, CAPI) mantém saída para bare-metal e evita lock-in além do hypervisor.

## 9. Roadmap e Riscos

Ver **Implementation Roadmap** (6 fases: golden image → IaC → bootstrap homolog → solda GitOps → DR game day → prod HA; fase 6 opcional Talos/CAPI) e **Risk Assessment** nas seções acima. Risco #1: 2 CP em prod → migrar para 3 CP com anti-affinity.

## 10. Perspectiva Futura

- **Curto prazo (1–2 anos):** consolidar Terraform+Kubespray+GitOps; maturar DR testado.
- **Médio prazo (3–5 anos):** avaliar migração para **Talos + Cluster API**, ganhando imutabilidade, menor TCO e portabilidade bare-metal via Metal3 sem tocar no GitOps.
- **Tendência de fundo:** object storage (S3/MinIO) como âncora universal de DR; modelos declarativos/imutáveis como direção do ecossistema.

## 11. Metodologia e Verificação de Fontes

**Fontes primárias:** documentação oficial Kubernetes/kubeadm, etcd.io, Kubespray, RKE2/Rancher, Sidero/Talos, Cluster API Book, Velero, Broadcom/VMware TechDocs, HashiCorp Packer. **Secundárias:** estudos de caso (Equinix), guias técnicos e análises comparativas 2025–2026. **Confiança geral: Alta**, com sinalização de *Média* onde o ecossistema evolui rápido (CAPV/Talos — validar matriz de versões na adoção). **Limitação:** benchmarks de esforço/TCO variam por contexto; usar como ordem de grandeza, não número absoluto.

## 12. Apêndices

### Apêndice — Matriz Comparativa

Ver a tabela completa em **§Implementation Approaches → Matriz Comparativa dos 5 Candidatos**.

### Apêndice A — Como tudo mudaria em Bare-Metal Físico

Requisito explícito da pesquisa: o comparativo de como a stack e o DR mudariam sem o hypervisor.

**O que muda (camada de infra):**

| Aspecto | vSphere (atual) | Bare-metal físico |
|---|---|---|
| Provisionamento de "máquina" | Clone de template + guestinfo (Terraform `vsphere`/CAPV) | **PXE/iPXE + autoinstall** (cloud-init/ignition) via **MAAS / Tinkerbell / Metal3** |
| Golden image | Template de VM (Packer vsphere) | Imagem de SO/OS image servida por PXE (Packer ainda ajuda a construí-la) |
| Ligar/desligar/reset | vCenter API | **IPMI / Redfish** (BMC do servidor) |
| Provider Cluster API | CAPV | **CAPM3 (Metal3)** / CAPI+MAAS |
| Inventário de hardware | vCenter | Descoberta de hardware (Ironic no Metal3, comissionamento no MAAS) |

**O que se perde (impacto direto no DR):**

- **Snapshots de VM** — não existem em bare-metal; some o "rollback rápido pré-upgrade". Mitigação: confiar mais em golden image reprovisionável + backup de dados (ReaR/imagem de disco para o SO, se necessário).
- **vSphere HA** (reinício automático de VM em outro host após falha de host) — não há equivalente automático; a resiliência passa a depender **inteiramente** do quórum do Kubernetes/etcd e de nós sobressalentes.
- **vMotion / DRS** — sem migração viva nem balanceamento automático; um host que cai leva seus pods, e o rescheduling é responsabilidade do k8s.
- **Elasticidade** — não se "clona uma VM"; adicionar nó = provisionar hardware físico (mais lento, exige capacidade ociosa).

**O que permanece igual:**

- **Camada de bootstrap do k8s** (Kubespray/Talos/kubeadm) e a **topologia de HA** (3 CP, quórum, kube-vip) — idênticas.
- **GitOps (ArgoCD + Kustomize)** — 100% inalterado; é agnóstico à infra subjacente.
- **DR de estado e dados** — etcd snapshot + Velero/CSI continuam válidos (desde que a StorageClass bare-metal — ex.: Rook/Ceph, Longhorn — suporte CSI snapshots).
- **Se usar Cluster API**, a migração VM→bare-metal é a **troca de provider (CAPV→CAPM3)** preservando o modelo declarativo — o maior argumento a favor de investir em CAPI desde já.

**Implicações de DR em bare-metal:** a estratégia se desloca de "snapshot + HA do hypervisor" para "**reprovisionar do zero rápido + backup robusto de dados**". O golden image + PXE/autoinstall precisa ser tão confiável que perder um nó seja resolvido por **reprovisionamento** (modelo "cattle"), não por restore de imagem. Bare-metal exige backup de dados mais disciplinado justamente porque não há a rede de segurança da virtualização, e restaurações podem esbarrar em **compatibilidade de hardware** (BIOS/controladoras/discos) — algo que VMs abstraem. _Fontes: [Spectro Cloud – CAPI + MAAS](https://www.spectrocloud.com/blog/how-to-provision-bare-metal-k8s-clusters-with-cluster-api-and-canonical-maas), [The New Stack – Provision Bare Metal K8s with CAPI](https://thenewstack.io/provision-bare-metal-kubernetes-with-the-cluster-api/), [Plural – Bare Metal K8s Guide](https://www.plural.sh/blog/bare-metal-kubernetes-guide/), [ReaR – Bare Metal Recovery](https://computingforgeeks.com/rear-bare-metal-linux-recovery/), [awesome-baremetal](https://github.com/alexellis/awesome-baremetal/blob/master/README.md)_

---

## Technical Research Conclusion

**Resumo dos achados-chave.** A maior fragilidade atual não é a ferramenta, e sim a ausência de reprodutibilidade e de HA real: 2 control planes em produção é uma falsa sensação de redundância. A correção arquitetural (3 CP stacked + anti-affinity), a automação de provisionamento (Terraform+Packer+Kubespray+kube-vip) e o DR testado em 3 camadas endereçam o risco de ponta a ponta, reaproveitando integralmente o GitOps já existente e mantendo a fronteira proprietário↔open source restrita ao hypervisor.

**Impacto estratégico.** Além de resiliência imediata, escolher camadas portáveis preserva a opção de migrar para bare-metal (via Metal3/CAPI) sem reescrever o plano de estado — desacoplando o futuro do investimento em VMware.

**Próximos passos.** (1) Prototipar o golden image Packer; (2) automatizar homologação com Terraform+Kubespray validando o caminho de 3 CP; (3) soldar o ArgoCD por bootstrap; (4) executar um game day de DR; (5) aplicar em produção a topologia HA corrigida. Recomenda-se transformar este documento em um PRD/épico de plataforma para execução.

---

**Technical Research Completion Date:** 2026-07-06
**Source Verification:** Todas as afirmações críticas citadas com fontes públicas atuais
**Technical Confidence Level:** Alta — múltiplas fontes autoritativas

_Este documento serve como referência técnica autoritativa sobre automação, HA e DR de Kubernetes sobre vSphere (com comparativo bare-metal) para decisão informada e implementação._

---

Autoria/Implementação: Claude Opus 4.8

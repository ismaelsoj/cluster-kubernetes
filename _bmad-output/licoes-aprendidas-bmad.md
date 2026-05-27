# Lições Aprendidas: Uma Jornada Prática com o BMad Method

**Projeto:** cluster-kubernetes (GitOps local com k3d, ArgoCD, Kong e Keycloak)  
**Período:** maio–junho 2026  
**Audiência:** Desenvolvedores que estão começando ou já usam o BMad e querem entender as decisões de customização, distilação e governança de agentes que emergem no uso real.

---

## O Que Esse Documento É

Não é um tutorial do BMad. É um relato honesto do que aprendemos ao usar o BMad em um projeto real de infraestrutura: quando as coisas funcionaram como esperado, onde sentimos atrito, e quais ferramentas do próprio BMad usamos para resolver esses atritos.

Se você está começando um projeto com BMad, este documento te dará um mapa de decisões que provavelmente você também vai enfrenta — e vai te poupar algumas iterações dolorosas.

---

## A Jornada em 4 Fases

### Fase 1–3: Planejamento (Funcionou como Anunciado)

O fluxo de planejamento foi seguido linearmente e entregou exatamente o que promete:

- **Pesquisa técnica** (`bmad-technical-research`) produziu um relatório sólido sobre as opções de stack (k3d vs. kind, Kong vs. Nginx etc.), que baseou decisões de arquitetura com rastreabilidade real.
- **PRD** (`bmad-create-prd`) capturou os requisitos funcionais e não-funcionais de forma estruturada. Quando surgiu a necessidade de suportar Windows via WSL2, o processo formal de Sprint Change Proposal documentou a decisão e atualizou PRD, arquitetura e épicos de forma coordenada — sem deixar artefatos desalinhados.
- **Arquitetura e Épicos** (`bmad-create-architecture`, `bmad-create-epics-and-stories`) produziram artefatos que os agentes de implementação realmente usam. A quebra de histórias foi granular o suficiente para que cada uma fosse implementável em uma sessão de contexto.

**Takeaway:** Não pule a fase de planejamento. Os artefatos produzidos não são burocracia — são o contexto que os agentes vão carregar para implementar. Um PRD vago gera histórias vagas, que geram código que não atende ao objetivo.

---

### Fase 4: Implementação — Onde a Realidade Encontra o Processo

O Épico 1 (fundação do repositório) entregou 5/5 histórias. Mas foi durante essa fase que identificamos os principais pontos de atrito com o fluxo padrão do BMad. Cada atrito virou uma decisão de customização.

---

## As Customizações: Quando e Por Que

### Ponto de Atrito 1: Comportamento Inconsistente Entre Sessões

**O que aconteceu:** Cada sessão começa em contexto limpo. Regras que pareciam "combinadas" com o agente — como "sempre classifique a complexidade da história" ou "nunca faça commit sem autorização explícita" — precisavam ser relembradas a cada nova sessão.

**A solução:** `bmad-customize` + `AGENTS.md`

O BMad oferece dois mecanismos para persistir comportamento:

1. **Arquivos TOML em `_bmad/custom/`**: overrides específicos por workflow. Exemplo: o `bmad-create-story.toml` ganhou `persistent_facts` que forçam o agente a incluir classificação de complexidade e Plano de Validação Manual em *toda* história criada.

2. **`AGENTS.md` na raiz**: para regras universais que se aplicam a *todos* os agentes (Claude Code, Antigravity/Gemini, Cursor). Git workflow, permissões de commit, rastreabilidade de autoria LLM — tudo que é política do repositório, não de um workflow específico.

A distinção é importante: **regras de processo → TOML**; **políticas do repositório → AGENTS.md**. Misturar os dois cria duplicação que fica difícil de manter.

---

### Ponto de Atrito 2: Code Review Sem Rede de Segurança

**O que aconteceu:** Na Story 1.5, o code review gerou 12 findings e 10 patches foram aplicados. Um desses patches removeu a criação manual de namespaces com uma justificativa tecnicamente correta ("confie no ArgoCD Wave 0"). O patch foi aceito sem teste end-to-end. Na retrospectiva, descobrimos que o patch causava falha no `make up` em ambiente limpo — um bug clássico de "correto em estado contínuo, quebrado no bootstrap".

**A raiz do problema:** não havia nenhum gate que pedisse ao usuário para validar os testes antes de marcar a história como concluída.

**A solução:** customizar o `bmad-code-review.toml` com a regra:

```
Após aplicar todos os patches, HALT. Pergunte ao usuário:
"Os testes e validações do Plano de Validação Manual continuam passando?"
Aguarde resposta antes de prosseguir.
```

Essa única regra transformou o code review de um processo que *sugere* validação para um que *exige* confirmação explícita. O agente não pode "esquecer" de perguntar — está no TOML.

---

### Ponto de Atrito 3: Histórias Sem Instruções de Validação

**O que aconteceu:** As primeiras histórias descreviam *o que* fazer, mas não incluíam os comandos exatos para *verificar* se o que foi feito está correto. Isso criava ambiguidade na entrega: o agente declarava a história pronta, mas o desenvolvedor humano não sabia exatamente o que executar para confirmar.

**A solução:** `persistent_fact` no `bmad-create-story.toml`:

```
TODA história DEVE conter uma seção "Plano de Validação Manual"
com os comandos exatos (kubectl, curl, make) e os resultados esperados.
```

O resultado prático: cada história passou a ter um checklist de validação que o desenvolvedor humano executa antes de aprovar a entrega. Isso tornou a interface humano-agente mais clara: o agente implementa, o humano valida com comandos explícitos, o code review faz a análise adversarial.

---

### Ponto de Atrito 4: Regras Espalhadas, Difíceis de Manter

**O que aconteceu:** Após algumas iterações, cada arquivo TOML tinha variações das mesmas regras de git workflow. Uma mudança de política exigia editar 5 arquivos.

**A solução:** Consolidar tudo que é política universal no `AGENTS.md` e deixar os TOMLs apenas com overrides específicos do workflow. Os arquivos TOML que tinham regras de git ficaram com apenas um comentário:

```toml
# Regras globais (GIT WORKFLOW, GIT PERMISSIONS)
# migradas para /AGENTS.md — aplicam-se automaticamente a todos os agentes.
```

**Takeaway:** Use `bmad-customize` para comportamentos específicos de cada skill. Use `AGENTS.md` para políticas do repositório. Você vai precisar de ambos, e a distinção evita que o repositório vire um labirinto de regras duplicadas e conflitantes.

---

## O Distillator: Quando o Contexto Ficou Grande Demais

### Por Que Surgiu a Necessidade

No início do Épico 2, o acumulado de artefatos era considerável: PRD, arquitetura, épicos, 5 histórias concluídas com seus change logs, pesquisa técnica, deferred-work. Carregar tudo em contexto para implementar uma história simples era desperdício de tokens — e, pior, aumentava a chance do agente se perder em informação irrelevante.

### O Que o Distillator Faz

`bmad-distillator` recebe um conjunto de documentos e produz um arquivo (ou conjunto de arquivos) comprimido para consumo por LLMs. O resultado não é um resumo — é uma representação densa que preserva as informações relevantes para um agente que vai *agir*, não *ler*.

### Como Usamos: Distillate Principal do Cluster

Ao final do Épico 1, rodamos o distillator sobre os principais artefatos do projeto. O output foi 4 arquivos em `_bmad-output/distillate/`:

| Arquivo | Conteúdo |
|---|---|
| `01-regras-implementacao.md` | Stack, padrões de código, ADRs vigentes |
| `02-arquitetura-decisoes.md` | Decisões arquiteturais e suas justificativas |
| `03-epicos-stories-status.md` | Status de cada história (concluída, em progresso, bloqueada) |
| `04-trabalho-diferido.md` | 23+ itens diferidos com origem e prioridade |

Os TOMLs de `bmad-dev-story` e `bmad-code-review` foram atualizados para apontar para esses arquivos:

```toml
"CRITICAL REQUIREMENT: Você DEVE ler e seguir as regras em
`_bmad-output/distillate/01-regras-implementacao.md` antes de implementar."
```

O resultado: o agente carrega apenas o que precisa para a tarefa, sem vasculhar os artefatos originais.

### Como Usamos: Distillate do Subprojeto `.tracker/`

O repositório tem um subprojeto paralelo — um rastreador de tempo de desenvolvimento com IA (`work-tracker.py`). Esse projeto acumulou sua própria documentação: arquitetura, 4 specs de features, 29 itens de backlog, 2 pesquisas técnicas, reviews adversariais.

Rodamos o distillator especificamente sobre esse subprojeto, produzindo 4 arquivos em `.tracker/tracker-distillate/`. O motivo: ao trabalhar no tracker, o agente precisa de contexto sobre *aquele* subprojeto, não sobre o cluster Kubernetes em geral. Distillates segregados por domínio permitem carregar exatamente o contexto certo para cada tarefa.

**Takeaway:** Rode o distillator quando você notar que precisa repetir o mesmo contexto de projeto em todas as sessões. Se você está explicando para o agente "lembre que nesse projeto usamos X" toda vez, é hora de distillar.

---

## O Party Mode: Alinhamento Coletivo de Decisões

Em um momento de transição — quando reestruturamos a organização de documentação do tracker para seguir o padrão SDD (Sistema de Documentação Distribuída) do BMad — usamos o `bmad-party-mode` para fazer os agentes (Winston/Arquiteto, Amelia/Dev, Mary/Analista) discutirem a proposta em conjunto antes de implementar.

O valor não foi a decisão em si, mas o processo: ao apresentar a proposta para múltiplas perspectivas especializadas, encontramos buracos que uma única perspectiva não teria visto. O arquiteto questionou a granularidade, o analista validou o alinhamento com requisitos, a dev apontou implicações de implementação.

**Takeaway:** Use party mode para decisões que afetam múltiplos aspectos do projeto — arquitetura, processo e produto ao mesmo tempo. Não use para decisões técnicas pontuais onde uma perspectiva especializada é suficiente.

---

## Lições da Retrospectiva do Épico 1

Essas são as lições mais práticas, tiradas diretamente da retrospectiva:

### 1. Bootstrap É Uma Exceção Legítima ao GitOps Puro

Kubernetes precisa de namespaces antes do ArgoCD durante o bootstrap inicial. O ArgoCD cria namespaces no Wave 0 — mas o ArgoCD ainda não está instalado nesse momento. Se você aplicar "confie no ArgoCD" sem checar a sequência de bootstrap, vai quebrar o `make up` em ambiente limpo.

**Regra resultante:** Histórias que tocam o fluxo de bootstrap devem ter como AC explícito: *"dado cluster inexistente, quando `make down && make up` executado, então funciona sem intervenção manual."*

### 2. Processo Captura Comportamento Melhor Que Intenção

A verificação de regressão de ACs não pode depender de o revisor "lembrar" de checar. Ela precisa estar no template do code review como seção fixa. Se não está no processo, não vai acontecer sistematicamente.

### 3. Volume de Patches Cria Risco de Aceitação Acrítica

Com 10+ patches em uma única história, a tendência humana é aceitar em bloco. O antídoto é o Plano de Validação Manual — ao testar cada AC após os patches, você detecta regressões antes de aprovar.

### 4. Versões Devem Ser Pesquisadas Antes da Implementação, Não Durante

Se a spec diz `v0.68.2` e o teste usa `v0.45.0`, você tem uma história que nunca foi realmente validada na versão documentada. Pesquise e fixe versões *antes* de marcar a história como pronta para desenvolvimento.

### 5. Deferred Work É uma Feature, Não uma Confissão de Fracasso

O `deferred-work.md` rastreou 23+ itens ao longo do Épico 1. Isso não é débito técnico mal gerenciado — é reconhecimento explícito de que nem tudo pode ser feito agora, com visibilidade para o futuro. A alternativa (não registrar) é muito pior.

---

## Resumo das Ferramentas e Quando Usar

| Ferramenta | Quando usar |
|---|---|
| `bmad-customize` | Quando você percebe que está dizendo ao agente a mesma coisa em sessões diferentes |
| `AGENTS.md` | Para políticas do repositório que se aplicam a *todos* os agentes e ferramentas |
| `bmad-distillator` | Quando o contexto do projeto ficou grande demais para carregar a cada sessão |
| `bmad-party-mode` | Para decisões que impactam arquitetura, produto e processo ao mesmo tempo |
| Sprint Change Proposal | Para mudanças de escopo que afetam múltiplos artefatos — documenta a decisão e mantém os artefatos alinhados |
| Retrospectiva (`bmad-retrospective`) | Ao final de cada épico — não como formalidade, mas para capturar o que mudou no processo |

---

## O Padrão que Emergiu

Depois de um épico completo, o fluxo que funcionou foi:

```
História criada com Plano de Validação Manual
  → Dev implementa (lê regras do distillate)
  → Code review adversarial
  → Patches aplicados com aprovação explícita
  → Humano valida contra o Plano de Validação Manual
  → História marcada como done
  → Itens fora de escopo → deferred-work.md
```

Cada etapa dessa cadeia virou uma regra nos TOMLs. Não porque o processo seja rígido demais, mas porque sem as regras, o processo se degradava em cada sessão.

---

*Autoria: claude-sonnet-4-6 | 2026-05-25*

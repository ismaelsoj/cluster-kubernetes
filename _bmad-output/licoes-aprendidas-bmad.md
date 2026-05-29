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

### Confirmação no Changelog do BMAD

Essa evolução deixou de ser apenas uma preferência nossa e passou a ficar alinhada com o próprio BMAD. No changelog oficial da **v6.8.0** do BMAD Method, o `bmad-distillator` aparece como **retired**, explicitamente **superseded by `bmad-spec`**. O mesmo changelog apresenta o `bmad-spec` como skill core para destilar qualquer intenção em um `SPEC.md` com kernel enxuto e companions nomeados.

Em outras palavras: o que fizemos no projeto não foi um desvio do método, mas uma convergência com a direção oficial da ferramenta.

### O Próximo Passo: Forçar `bmad-spec` Para Unificar o Contexto Ativo

Com o tempo, percebemos um limite importante do uso isolado do distillator: ele comprime bem, mas não resolve sozinho o problema de **precedência de contexto**. Depois de algumas iterações, já existiam:

- o distillate original do projeto principal;
- o distillate do subprojeto `.tracker/`;
- specs ativas novas que não existiam quando o distillate inicial foi gerado;
- regras em `AGENTS.md` apontando para caminhos diferentes ao longo do tempo.

Na prática, isso criava uma dúvida perigosa para agentes e humanos: **qual é a fonte ativa de verdade?**  
Mesmo com distillates bons, ainda havia risco de releitura defensiva, duplicação e conflito entre resumo antigo e estado atual.

### A Solução: Aplicar a Lógica do `bmad-spec`

Em vez de continuar criando apenas novos resumos comprimidos, passamos a **forçar a disciplina do `bmad-spec`**:

- um **kernel explícito** (`SPEC.md`) com o contrato mínimo do contexto;
- **companions separados por intenção** (`implementation`, `architecture`, `planning`, `research`, `deferred work`);
- uma regra de precedência clara: **v2 ativa, v1 legado**;
- `AGENTS.md` apontando para **uma única porta de entrada oficial**;
- árvore anterior marcada explicitamente como **LEGADO** para auditoria, não para uso operacional.

Isso foi aplicado tanto no projeto principal quanto na `.tracker/`.

### Os Conceitos Que Passaram a Guiar o Contexto

Para que a migração não virasse apenas "mais uma pasta de resumo", passamos a usar alguns conceitos de forma deliberada.

#### Kernel

O **kernel** é o núcleo mínimo e obrigatório do contexto. É o arquivo que todo agente deve ler primeiro para entender:

- o que é o projeto;
- quais são as restrições que realmente mudam decisão;
- qual é a fonte ativa de contexto;
- como continuar a leitura sem sair vasculhando o repositório inteiro.

No nosso caso, o kernel passou a ser o `SPEC.md` de cada domínio.

#### Companions

Os **companions** são arquivos irmãos do kernel, mas separados por intenção de uso. Eles existem para evitar inflar o `SPEC.md` com detalhes que são importantes, mas não universais.

Exemplos:

- `implementation-rules.md`
- `architecture-status.md`
- `planning.md`
- `research-decisions.md`
- `deferred-work.md`

A regra prática foi: **o kernel orienta; os companions aprofundam**.

#### Caminho Feliz de Leitura

O **caminho feliz de leitura** é a menor sequência de arquivos que resolve a maioria das tarefas sem recorrer ao acervo completo do projeto.

O padrão desejado passou a ser:

```text
AGENTS.md -> SPEC.md -> 1 companion
```

Se o agente precisa abrir 7 artefatos para começar uma tarefa comum, o contexto está mal desenhado.

#### Legado Congelado

**Legado congelado** é o material antigo que continua existindo para auditoria e rastreabilidade, mas deixa de competir como fonte ativa.

Na prática, isso significa:

- o conteúdo antigo não é apagado;
- ele recebe aviso explícito de supersessão;
- ele deixa de ser o caminho padrão de leitura;
- em caso de conflito, a árvore nova prevalece.

Isso evitou o pior cenário possível: duas "fontes oficiais" convivendo indefinidamente.

#### Load-Bearing

Chamamos de **load-bearing** toda informação que, se removida, mudaria uma decisão real do agente.

Exemplos do projeto:

- `sync-wave` obrigatório;
- `prune: false` para infra central;
- `.tracker/` invisível para tarefas de infra;
- `transcript.jsonl` como fonte válida do Antigravity;
- segregação criptográfica entre dev e produção.

Se uma informação altera implementação, review, arquitetura ou validação, ela é load-bearing e precisa morar no kernel ou num companion. Se não altera decisão, é forte candidata a sair do caminho feliz.

#### Design de Contexto

O conceito mais importante que emergiu foi **design de contexto**.

Antes, pensávamos o problema como: "tem texto demais, precisamos comprimir".  
Depois, passamos a pensar como:

- o que entra no kernel?
- o que vai para companions?
- o que é leitura padrão?
- o que vira legado congelado?
- o que é realmente load-bearing?

Essa mudança de mentalidade foi decisiva. O problema deixou de ser apenas custo de tokens e passou a ser **arquitetura da informação para agentes**.

### Benefício Real no Projeto

O benefício não foi só "organização melhor". Ele foi mensurável no carregamento de contexto por sessão.

#### Projeto principal

Fluxo típico de implementação/arquitetura:

- **Antes:** `AGENTS + _index + regras + arquitetura` = **1641 palavras**
- **Depois:** `AGENTS + SPEC + implementation-rules + architecture-status` = **1197 palavras**
- **Redução:** **27,1%**

Fluxo típico de planejamento:

- **Antes:** `AGENTS + _index + épicos/stories` = **1217 palavras**
- **Depois:** `AGENTS + SPEC + planning` = **862 palavras**
- **Redução:** **29,2%**

#### Subprojeto `.tracker/`

Fluxo típico de implementação:

- **Antes:** `AGENTS + _index + arquitetura` = **1837 palavras**
- **Depois:** `AGENTS + SPEC + implementation-status` = **845 palavras**
- **Redução:** **54,0%**

Fluxo típico de planejamento:

- **Antes:** `AGENTS + _index + backlog` = **1769 palavras**
- **Depois:** `AGENTS + SPEC + planning` = **945 palavras**
- **Redução:** **46,6%**

Fluxo típico de pesquisa:

- **Antes:** `AGENTS + _index + pesquisa` = **1233 palavras**
- **Depois:** `AGENTS + SPEC + research-decisions` = **684 palavras**
- **Redução:** **44,5%**

### Por Que o `bmad-spec` Funcionou Melhor

O `bmad-spec` trouxe algo que o distillator sozinho não garante: **contrato operacional**.

O distillator responde bem a "como comprimir?".  
O `bmad-spec` força responder também:

- o que é **kernel**;
- o que vira **companion**;
- o que é **caminho feliz de leitura**;
- o que é **legado congelado**;
- o que realmente é **load-bearing** para implementação e review.

Essa diferença foi decisiva. O problema deixou de ser apenas "tokens demais" e passou a ser tratado como **design de contexto**.

### A Regra que Emergimos

**Distillator comprime. `bmad-spec` governa.**

Em projetos pequenos, o distillator pode bastar.  
Em projetos vivos, com múltiplas iterações, stories, revisões e subdomínios, o padrão que se mostrou mais robusto foi:

1. distillar quando o contexto ficar grande;
2. quando surgirem múltiplas versões de resumo, aplicar `bmad-spec`;
3. promover um `SPEC.md` ativo com companions por intenção;
4. marcar o material anterior como legado;
5. apontar `AGENTS.md` apenas para a fonte ativa.

**Takeaway:** Se você já tem um distillate, mas ainda percebe ambiguidade sobre "qual contexto carregar", não precisa de mais compressão; precisa de um **kernel governado por `bmad-spec`**.

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
| `bmad-spec` | Quando o projeto já tem resumos/distillates suficientes, mas ainda falta uma fonte ativa única, com kernel, companions e precedência clara |
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
*Revisão/Atualização: GPT-5 Codex | 2026-05-28 00:05:48-03:00*

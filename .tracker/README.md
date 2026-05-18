# ⏱️ Rastreador de Tempo de Desenvolvimento (IA)

Este diretório contém uma ferramenta privada e offline desenvolvida para mapear, consolidar e reportar o tempo ativo de trabalho dedicado ao desenvolvimento deste repositório com o auxílio de assistentes de Inteligência Artificial: **Antigravity** (extensão VS Code/Cursor) e **Claude Code** (CLI).

---

## 🛡️ Segurança de Dados e Anonimato Externo

Por questões de conformidade e privacidade em repositórios públicos, o script adota a seguinte estratégia de segurança para ocultar dados confidenciais (como nomes de usuários e nomes de hosts físicos de redes internas):

*   **Identidade Baseada em Hash SHA-256:** O script combina o seu `usuário` e o `nome do host` da sua máquina e calcula um hash criptográfico SHA-256 determinístico de 8 caracteres (ex: `dev-39d71ab2`).
*   **Identificação Interna pelo Time:** Cada desenvolvedor pode ver o seu próprio ID de anonimato impresso na tela ao rodar localmente no console:
    ```bash
    make -f .tracker/Makefile track-time
    ```
    Isso permite que você e seu time saibam facilmente a correspondência interna de quem é cada ID no arquivo [TEMPO_DE_TRABALHO.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.md) sem expor dados reais ao público externo no GitHub.

---

## 🚀 Como Executar

Toda a automação é gerenciada pelo Makefile apartado neste diretório. Execute os comandos a partir da raiz do repositório:

### 1. Visualizar o Tempo de Trabalho no Terminal
Este comando faz uma varredura local, converte todos os dados para o **Horário de Brasília (GMT-3)** e exibe um resumo formatado direto no console:
```bash
make -f .tracker/Makefile track-time
```

### 2. Exportar/Atualizar Métricas no Relatório Compartilhado
Este comando executa a análise e atualiza de forma incremental ou anexa o seu bloco no arquivo colaborativo [TEMPO_DE_TRABALHO.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.md):
```bash
make -f .tracker/Makefile track-time EXPORT=true
```

---

## 🗓️ Estrutura do Relatório (Tabela Diária)

Diferente do resumo de sessões sequenciais, o relatório exportado agora consolida as horas **por dia de trabalho ativo** no fuso de Brasília, mostrando a contribuição exata de cada ferramenta:

*   **Tempo no Antigravity:** Horas ativas exclusivas na extensão de chat do VS Code/Cursor.
*   **Tempo no Claude Code:** Horas ativas exclusivas na CLI do Claude Code.
*   **Tempo Combinado (Sem sobreposição):** O total líquido trabalhado por dia (eliminando duplicidade caso você tenha alternado o uso de ambas as ferramentas em um mesmo bloco de tempo).
*   **Eventos (Antigravity / Claude Code):** Volume de interações realizadas por dia em cada ferramenta.

---

## ❓ Perguntas Frequentes (FAQ)

### 📌 Se eu rodar o comando de exportação novamente, ele registra apenas a sessão atual ou recria tudo?
**Ele recalcula o seu tempo histórico total local e substitui a sua entrada antiga.**

Toda vez que você executa o comando com `EXPORT=true`, o script:
1. Lê todos os logs históricos locais do Claude Code e Antigravity na sua máquina.
2. Converte todas as interações para o **fuso horário de Brasília (GMT-3)**.
3. Recalcula o seu tempo ativo total por dia até o presente momento.
4. **Substitui de forma inteligente** apenas o seu bloco antigo baseado no seu hash ID no arquivo [TEMPO_DE_TRABALHO.md](file:///home/ismael.sjunior/git-pessoal/cluster-kubernetes/.tracker/TEMPO_DE_TRABALHO.md).

Isso significa que:
*   **Sem Duplicatas:** O arquivo nunca terá registros repetidos poluindo a sua máquina. Ele simplesmente atualiza o seu bloco com as métricas mais recentes e a nova data de registro.
*   **Colaboração Limpa:** Registros de outros membros do time com hashes diferentes são **100% preservados**!

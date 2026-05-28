# Planning

Use este companion para descobrir rapidamente o que está ativo no roadmap sem abrir decomposições longas.

## Roadmap resumido

- `Épico 1` Fundação do repositório e bootstrap GitOps: concluído.
- `Épico 2` Identidade, persistência e recuperação de desastres: backlog ativo.
- `Épico 3` Gateway de borda e segurança Zero-Trust: backlog dependente do Épico 2.
- `Épico 4` Boilerplate, habilitação dev e deep security: backlog dependente do Épico 3.

## Mapa rápido por épico

- `Épico 2`
  - 2.1 PostgreSQL Wave 1
  - 2.2 Keycloak Wave 2
  - 2.3 Realm e client M2M
  - 2.4 Backup e restore de PostgreSQL

- `Épico 3`
  - 3.1 Kong DB-Less Wave 3
  - 3.2 TLS, JWKS e rate limit
  - 3.3 Script de token e feedback terminal
  - 3.4 Refinamento do bootstrap de emergência

- `Épico 4`
  - 4.1 Boilerplate Kustomize e CONTRACT
  - 4.2 Overlays, rate limiting e bypass Swagger
  - 4.3 API teste end-to-end
  - 4.4 Sidecar oauth2-proxy deep security
  - 4.5 Contrato do desenvolvedor

## Próximos itens práticos

- `Story 2.1` PostgreSQL em `keycloak-auth`, Wave 1, com probes, labels, comentário pt-BR e NetworkPolicy.
- `Story 2.2` Keycloak em Wave 2, com Secret, PriorityClass, logs JSON e healthcheck público.
- `Story 2.3` Realm e client M2M com segregação criptográfica dev/prod.
- `Story 2.4` Backup e restore de PostgreSQL testados.

## Cobertura e ordem

- O roadmap mantém dependência linear `É1 -> É2 -> É3 -> É4`.
- Jornadas 1 e 2 do PRD já estão mapeadas; Jornada 3 fica pós-MVP.
- O marco de validação da Jornada 1 acontece ao final do Épico 3.

## Regra de leitura barata

- Não abrir `planning-artifacts/` para saber “o que vem agora”.
- Não abrir o distillate antigo inteiro para confirmar regras de nomenclatura.
- Abrir histórias detalhadas só quando a tarefa realmente exigir critérios de aceite finos.

---
Autoria/Implementação: GPT-5 Codex

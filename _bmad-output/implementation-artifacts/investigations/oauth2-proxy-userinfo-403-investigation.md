# Investigação: OAuth2-Proxy 403 na rota protegida userinfo

## Resumo de Passagem

1. **O que aconteceu.** A rota `https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo` retornou `HTTP/2 403 Forbidden` mesmo com Bearer token emitido pelo Keycloak.
2. **Evidência principal.** O log do OAuth2-Proxy registrou: `Error retrieving session from token in Authorization header: [unable to verify bearer token, could not create session from token: email in id_token () isn't verified]`.
3. **Conclusão.** O Kong encaminhou corretamente para a rota protegida; o bloqueio veio do OAuth2-Proxy ao tentar criar sessão a partir de um token M2M sem email verificado.

## Informações do Caso

| Campo | Valor |
| ----- | ----- |
| Data de abertura | 2026-05-29 |
| Status | Concluído |
| Sistema | Kong Gateway 3.14.0.3, OAuth2-Proxy v7.15.2, Keycloak realm `cluster-local` |
| Sintoma | `curl -k -i https://localhost/protected/realms/cluster-local/protocol/openid-connect/userinfo -H "Authorization: Bearer ${TOKEN}"` retorna `403 Forbidden` |

## Achados Confirmados

### Achado 1: O token chegou ao OAuth2-Proxy

**Evidência:** a resposta continha headers do Kong e `x-kong-upstream-latency`, e o log do OAuth2-Proxy registrou a tentativa sobre `/realms/cluster-local/protocol/openid-connect/userinfo`.

**Conclusão:** a rota e o rate limit do Kong funcionaram; a falha não é roteamento HTTP/HTTPS.

### Achado 2: O OAuth2-Proxy rejeitou a criação de sessão por email não verificado

**Evidência:** log do OAuth2-Proxy: `email in id_token () isn't verified`.

**Conclusão:** o token M2M foi tratado como entrada válida para validação JWT, mas a camada de sessão do OAuth2-Proxy exigiu um email verificado, requisito inadequado para service account.

## Direção de Correção

- Configurar o OAuth2-Proxy para usar `preferred_username` como claim de identidade (`OAUTH2_PROXY_OIDC_EMAIL_CLAIM=preferred_username`).
- Permitir email não verificado no fluxo M2M (`OAUTH2_PROXY_INSECURE_OIDC_ALLOW_UNVERIFIED_EMAIL=true`), mantendo a segurança baseada em `issuer`, `audience` e assinatura JWT via JWKS.
- Registrar guardrails OPA para impedir regressão dessa configuração.

## Resultado

Correção aplicada nos manifests e guardrails em 2026-05-29. A validação runtime final depende de sincronizar os manifests pelo fluxo GitOps e reiniciar o OAuth2-Proxy com o novo ConfigMap.

---
Autoria/Implementação: GPT-5 Codex

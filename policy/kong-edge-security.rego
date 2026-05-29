# policy/kong-edge-security.rego
# Guardrails da borda Kong/OAuth2-Proxy para TLS, JWKS e rate limit default.

package main

import rego.v1

is_kong_env_config if {
    input.kind == "ConfigMap"
    input.metadata.name == "kong-configmap"
}

is_kong_declarative_config if {
    input.kind == "ConfigMap"
    input.metadata.name == "kong-declarative-config"
}

is_kong_deployment if {
    input.kind == "Deployment"
    input.metadata.name == "kong-deployment"
}

is_oauth2_proxy_deployment if {
    input.kind == "Deployment"
    input.metadata.name == "oauth2-proxy-deployment"
}

is_oauth2_proxy_config if {
    input.kind == "ConfigMap"
    input.metadata.name == "oauth2-proxy-configmap"
}

kong_yaml := input.data["kong.yml"] if {
    is_kong_declarative_config
}

oauth2_proxy_container := container if {
    is_oauth2_proxy_deployment
    some container in input.spec.template.spec.containers
    container.name == "oauth2-proxy"
}

deny contains msg if {
    is_kong_env_config
    not input.data.KONG_SSL_CERT
    msg := "Kong deve declarar KONG_SSL_CERT apontando para o certificado TLS montado."
}

deny contains msg if {
    is_kong_env_config
    not input.data.KONG_SSL_CERT_KEY
    msg := "Kong deve declarar KONG_SSL_CERT_KEY apontando para a chave TLS montada."
}

deny contains msg if {
    is_kong_deployment
    not kong_tls_secret_mounted
    msg := "Deployment do Kong deve montar o Secret TLS kong-tls-secret como volume read-only."
}

kong_tls_secret_mounted if {
    some volume in input.spec.template.spec.volumes
    volume.name == "kong-tls"
    volume.secret.secretName == "kong-tls-secret"
    some mount in input.spec.template.spec.containers[0].volumeMounts
    mount.name == "kong-tls"
    mount.readOnly == true
}

deny contains msg if {
    is_kong_declarative_config
    contains(kong_yaml, "- http\n              - https")
    msg := "Rotas principais do Kong nao devem manter protocols [http, https] como caminho feliz."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "name: keycloak-http-block-route")
    msg := "Kong deve declarar rota HTTP explicita para bloquear ou redirecionar trafego inseguro."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "status_code: 426")
    msg := "A rota HTTP insegura deve rejeitar com status explicito 426 Upgrade Required."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "name: keycloak-protected-route")
    msg := "Kong deve declarar rota protegida para validar JWT/JWKS antes do upstream."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "host: oauth2-proxy-service.kong-gateway.svc.cluster.local")
    msg := "Rota protegida do Kong deve encaminhar para OAuth2-Proxy OSS."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "name: rate-limiting")
    msg := "Kong deve aplicar plugin rate-limiting na rota protegida."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "minute: 100")
    msg := "Rate limit default deve ser 100 requisicoes por minuto."
}

deny contains msg if {
    is_kong_declarative_config
    not contains(kong_yaml, "policy: local")
    msg := "Rate limit default deve usar policy local para o MVP DB-Less de replica unica."
}

deny contains msg if {
    is_kong_declarative_config
    contains(kong_yaml, "name: openid-connect")
    msg := "Nao usar plugin Kong openid-connect no caminho feliz OSS."
}

deny contains msg if {
    is_kong_declarative_config
    contains(kong_yaml, "jwt-signer")
    msg := "Nao usar plugin Kong jwt-signer no caminho feliz OSS."
}

deny contains msg if {
    is_oauth2_proxy_deployment
    oauth2_proxy_container.image != "quay.io/oauth2-proxy/oauth2-proxy:v7.15.2"
    msg := "OAuth2-Proxy deve usar imagem oficial pinada em quay.io/oauth2-proxy/oauth2-proxy:v7.15.2."
}

deny contains msg if {
    is_oauth2_proxy_config
    input.data.OAUTH2_PROXY_SKIP_JWT_BEARER_TOKENS != "true"
    msg := "OAuth2-Proxy deve habilitar validacao de Bearer JWT para o fluxo M2M."
}

deny contains msg if {
    is_oauth2_proxy_config
    not input.data.OAUTH2_PROXY_OIDC_JWKS_URL
    msg := "OAuth2-Proxy deve apontar explicitamente para o JWKS interno do Keycloak."
}

deny contains msg if {
    is_oauth2_proxy_deployment
    env_blob := json.marshal(oauth2_proxy_container.env)
    not contains(env_blob, "oauth2-proxy-secret")
    msg := "Segredos do OAuth2-Proxy devem vir do Secret oauth2-proxy-secret, nao de ConfigMap."
}

# Autoria/Implementação: GPT-5 Codex

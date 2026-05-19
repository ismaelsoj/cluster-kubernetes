# policy/kebab-case.rego
# Regras de validação de nomenclatura para o cluster Kubernetes
# Garante que todos os recursos e namespaces utilizem estritamente o padrão kebab-case.

package main

import rego.v1

# Regex estrito para kebab-case (apenas letras minúsculas, números e hifens)
# Começa com caractere alfanumérico e termina com alfanumérico.
kebab_case_pattern := "^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"

# Conjunto de exceções permitidas
exceptions := {
    "default",
    "system:serviceaccount:argocd:argocd-application-controller"
}

# Verifica se o valor é uma exceção
is_exception(val) if {
    exceptions[val]
}

# Regra para negar recursos cujo nome não segue o padrão kebab-case
deny contains msg if {
    name := input.metadata.name
    not is_exception(name)
    not regex.match(kebab_case_pattern, name)
    msg := sprintf("Recurso '%s' (Kind: %s) não está seguindo o padrão kebab-case (deve conter apenas letras minúsculas, números e hifens).", [name, input.kind])
}

# Regra para negar recursos cujo namespace não segue o padrão kebab-case
deny contains msg if {
    ns := input.metadata.namespace
    not is_exception(ns)
    not regex.match(kebab_case_pattern, ns)
    msg := sprintf("Namespace '%s' do recurso '%s' (Kind: %s) não está seguindo o padrão kebab-case (deve conter apenas letras minúsculas, números e hifens).", [ns, input.metadata.name, input.kind])
}

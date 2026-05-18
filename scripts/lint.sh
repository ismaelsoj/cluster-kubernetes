#!/usr/bin/env bash
# scripts/lint.sh - Validação rigorosa e automatizada de manifestos YAML do cluster
# Implementação completa: Story 1.4

set -euo pipefail

# 1. Escape Hatch (SKIP_LINT)
if [ "${SKIP_LINT:-0}" = "1" ]; then
  echo "⚠️  Aviso: SKIP_LINT=1 está ativa. Pulando a validação de manifestos!"
  exit 0
fi

echo "🔍 Iniciando validação de manifestos do cluster..."

# 2. Resolução do compilador Kustomize (Kustomize nativo no kubectl)
KUSTOMIZE_CMD=""
if command -v kustomize &>/dev/null; then
  KUSTOMIZE_CMD="kustomize build"
elif command -v kubectl &>/dev/null; then
  KUSTOMIZE_CMD="kubectl kustomize"
else
  echo "❌ Erro: Nem 'kustomize' nem 'kubectl' foram encontrados no PATH!" >&2
  exit 1
fi

# 3. Criação do diretório temporário no workspace para compilação dos manifestos
TEMP_DIR=".tmp-lint"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Função para garantir a remoção do diretório temporário ao sair do script
cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 4. Compilação recursiva de todos os componentes kustomize
echo "🛠️  Compilando componentes com $KUSTOMIZE_CMD..."

# Encontra todas as pastas ativas que possuem kustomization.yaml (ignorando boilerplates vazios)
find cluster/bootstrap cluster/infrastructure cluster/apps -name "kustomization.yaml" 2>/dev/null | while read -r kustomize_file; do
  dir=$(dirname "$kustomize_file")
  
  # Cria um nome de arquivo único para o manifesto compilado (trocando '/' por '-')
  safe_name=$(echo "$dir" | tr '/' '-')
  output_file="${TEMP_DIR}/${safe_name}.yaml"
  
  # Executa compilação do Kustomize
  $KUSTOMIZE_CMD "$dir" > "$output_file"
  
  # Conta manifestos gerados nesta pasta
  manifest_count=$(grep -c "^kind:" "$output_file" || true)
  if [ "$manifest_count" -gt 0 ]; then
    echo "   - Compilado: $dir ($manifest_count manifestos)"
  else
    # Se gerou 0 manifestos (stubs de infraestrutura vazios por design), removemos para não poluir o linter
    rm -f "$output_file"
  fi
done

# 5. Guarda anti-"Falso Verde": valida se de fato há manifestos para validar no total do repositório
total_manifests=0
if [ -d "$TEMP_DIR" ] && [ "$(ls -A "$TEMP_DIR")" ]; then
  total_manifests=$(grep -r "^kind:" "$TEMP_DIR" | wc -l | tr -d ' ')
fi

if [ "$total_manifests" -eq 0 ]; then
  echo "❌ Erro: O processo de build gerou um total de 0 manifestos em todo o repositório!" >&2
  echo "   Isso previne falso-verde (falso positivo) em bases vazias ou desconfiguradas." >&2
  exit 1
fi

echo "📊 Total de manifestos consolidados para validação: $total_manifests"

# 6. Execução do scripts/validate_yaml.py para validar nomenclatura kebab-case
echo "🏷️  Validando nomenclatura kebab-case dos recursos..."
python3 scripts/validate_yaml.py "$TEMP_DIR"

# 7. Execução do kube-linter (local ou fallback transparente via Docker)
echo "🛡️  Validando políticas de segurança e robustez com kube-linter..."

if command -v kube-linter &>/dev/null; then
  echo "✅ kube-linter local detectado. Executando..."
  kube-linter lint "$TEMP_DIR" --config .kube-linter.yaml
else
  # Fallback transparente via Docker
  if ! command -v docker &>/dev/null; then
    echo "❌ Erro: kube-linter não está instalado localmente e o Docker não está em execução!" >&2
    echo "   Para rodar localmente sem Docker, instale o kube-linter ou configure SKIP_LINT=1." >&2
    exit 1
  fi
  
  echo "ℹ️  kube-linter não encontrado localmente. Rodando via Docker (stackrox/kube-linter:v0.8.3)..."
  # NOTA: O kube-linter via Docker precisa montar o diretório atual
  docker run --rm \
    -v "$(pwd):/dir" \
    -w /dir \
    stackrox/kube-linter:v0.8.3 lint "$TEMP_DIR" --config .kube-linter.yaml
fi

echo "🎉 Excelente! Todos os manifestos passaram nas validações de segurança e nomenclatura!"
exit 0

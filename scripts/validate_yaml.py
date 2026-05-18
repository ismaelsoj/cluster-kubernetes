#!/usr/bin/env python3
# scripts/validate_yaml.py - Validador de Nomenclatura Kubernetes (kebab-case)
# Validadores extras para complementar o kube-linter nos manifestos gerados.

import os
import sys
import re

# Regex estrita para kebab-case (letras minúsculas, números e hifens)
KEBAB_CASE_RE = re.compile(r'^[a-z0-9-]+$')

# Exceções aceitas (recursos do sistema ou do próprio k8s que não podemos alterar)
EXCEPTIONS = {
    'default',
    'system:serviceaccount:argocd:argocd-application-controller'
}

def validate_file(filepath):
    errors = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_metadata = False
    metadata_indent = -1
    
    for i, line in enumerate(lines, 1):
        # Ignorar comentários ou linhas em branco
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # Calcular indentação (número de espaços iniciais)
        indent = len(line) - len(line.lstrip())
        
        if in_metadata:
            # Se a indentação for menor ou igual à indentação do 'metadata:', saímos do bloco
            if indent <= metadata_indent and not stripped.startswith('metadata:'):
                in_metadata = False
                metadata_indent = -1
            else:
                # Verificações de campos de nome e namespace
                name_match = re.match(r'^name:\s*["\']?([a-zA-Z0-9-.:_]+)["\']?\s*$', stripped)
                namespace_match = re.match(r'^namespace:\s*["\']?([a-zA-Z0-9-.:_]+)["\']?\s*$', stripped)
                
                if name_match:
                    name_val = name_match.group(1)
                    if name_val not in EXCEPTIONS and not KEBAB_CASE_RE.match(name_val):
                        # Ignorar nomes de regras de roles ou environment variables se houver (mas name: sob metadata é seguro)
                        # Garante que estamos sob metadata/nome do recurso
                        errors.append(f"Linha {i}: Recurso '{name_val}' não está em kebab-case (deve conter apenas letras minúsculas, números e hifens).")
                
                elif namespace_match:
                    ns_val = namespace_match.group(1)
                    if ns_val not in EXCEPTIONS and not KEBAB_CASE_RE.match(ns_val):
                        errors.append(f"Linha {i}: Namespace '{ns_val}' não está em kebab-case (deve conter apenas letras minúsculas, números e hifens).")
        
        # Detectar entrada no bloco metadata
        if stripped == 'metadata:':
            in_metadata = True
            metadata_indent = indent

    return errors

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 validate_yaml.py <diretorio_ou_arquivo>")
        sys.exit(1)
    
    target = sys.argv[1]
    all_errors = {}
    
    if os.path.isfile(target):
        files_to_check = [target]
    else:
        files_to_check = []
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    files_to_check.append(os.path.join(root, file))
    
    for filepath in files_to_check:
        file_errors = validate_file(filepath)
        if file_errors:
            all_errors[filepath] = file_errors
            
    if all_errors:
        print("\n❌ Erros de Nomenclatura Kubernetes (kebab-case) detectados:")
        for file, errs in all_errors.items():
            print(f"\n   Arquivo: {file}")
            for err in errs:
                print(f"     - {err}")
        sys.exit(1)
    
    print("✅ Todos os recursos e namespaces estão seguindo o padrão kebab-case!")
    sys.exit(0)

if __name__ == '__main__':
    main()

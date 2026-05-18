#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitário Apartado de Rastreamento de Tempo de Trabalho Ativo (Claude Code + Antigravity)
Roda localmente de forma privada com fuso horário de Brasília (GMT-3), 
mascara a identidade do desenvolvedor com hash SHA-256 para anonimato externo, 
e gera tabelas agregadas detalhadas por dia de trabalho.
"""

import os
import re
import json
import glob
import hashlib
import argparse
import socket
import getpass
from datetime import datetime, timedelta

def parse_iso(dt_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S %z"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            pass
    try:
        clean_str = dt_str.split('.')[0].replace('Z', '')
        return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

def to_brasilia(dt):
    if not dt:
        return None
    # Como as entradas nos arquivos de log são geradas em UTC,
    # subtraímos 3 horas para converter para o fuso horário de Brasília (GMT-3).
    return dt - timedelta(hours=3)

def get_masked_identity(username, hostname):
    # Combina usuário e máquina e gera um hash SHA-256 de 8 caracteres
    identity_str = f"{username}@{hostname}"
    h = hashlib.sha256(identity_str.encode('utf-8')).hexdigest()[:8]
    return f"dev-{h}"

def analyze_claude_code(repo_root):
    project_dir_name = re.sub(r'[^a-zA-Z0-9]', '-', repo_root)
    claude_dir = os.path.expanduser(f"~/.claude/projects/{project_dir_name}")
    
    timestamps = []
    total_events = 0
    
    if not os.path.isdir(claude_dir):
        return [], 0, 0
        
    files = glob.glob(os.path.join(claude_dir, "*.jsonl"))
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        total_events += 1
                        ts = data.get("timestamp")
                        if ts:
                            dt = parse_iso(ts)
                            if dt:
                                timestamps.append(dt)
                    except Exception:
                        pass
        except Exception:
            pass
            
    return sorted(timestamps), len(files), total_events

def analyze_antigravity(repo_root):
    antigravity_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    timestamps = []
    total_steps = 0
    conversations_found = 0
    
    if not os.path.isdir(antigravity_dir):
        return [], 0, 0
        
    pattern = os.path.join(antigravity_dir, "*", ".system_generated", "logs", "overview.txt")
    files = glob.glob(pattern)
    
    for filepath in files:
        try:
            belongs_to_repo = False
            file_timestamps = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if repo_root in line:
                        belongs_to_repo = True
                        
                    try:
                        data = json.loads(line)
                        created_at = data.get("created_at")
                        if created_at:
                            dt = parse_iso(created_at)
                            if dt:
                                file_timestamps.append(dt)
                    except Exception:
                        pass
            
            if belongs_to_repo and file_timestamps:
                timestamps.extend(file_timestamps)
                total_steps += len(file_timestamps)
                conversations_found += 1
                
        except Exception:
            pass
            
    return sorted(timestamps), conversations_found, total_steps

def calculate_active_time(timestamps, session_gap_minutes=45, default_interaction_minutes=15):
    if not timestamps:
        return 0.0, []
        
    sessions = []
    current_session = [timestamps[0]]
    
    for t in timestamps[1:]:
        last_t = current_session[-1]
        gap = (t - last_t).total_seconds() / 60.0
        if gap <= session_gap_minutes:
            current_session.append(t)
        else:
            sessions.append(current_session)
            current_session = [t]
    sessions.append(current_session)
    
    total_hours = 0.0
    session_details = []
    
    for i, sess in enumerate(sessions):
        start = sess[0]
        end = sess[-1]
        duration_minutes = (end - start).total_seconds() / 60.0
        if duration_minutes < default_interaction_minutes:
            duration_minutes = default_interaction_minutes
        
        total_hours += duration_minutes / 60.0
        session_details.append({
            "session_num": i + 1,
            "start": start,
            "end": end,
            "interactions": len(sess),
            "hours": duration_minutes / 60.0
        })
        
    return total_hours, session_details

def main():
    parser = argparse.ArgumentParser(description="Calculador de tempo de trabalho de IA apartado e seguro.")
    parser.add_argument("--export", action="store_true", help="Se definido, anexa/atualiza o relatório em formato Markdown.")
    parser.add_argument("--gap", type=int, default=45, help="Intervalo máximo em minutos entre comandos para agrupar na mesma sessão.")
    args = parser.parse_args()
    
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Identidade Real vs Mascarada
    username = getpass.getuser()
    hostname = socket.gethostname()
    masked_id = get_masked_identity(username, hostname)
    
    # Horário atual em Brasília (GMT-3) baseado em UTC
    brasilia_now = datetime.utcnow() - timedelta(hours=3)
    brasilia_now_str = brasilia_now.strftime('%d/%m/%Y %H:%M:%S')
    
    # Executa a auditoria
    claude_times, claude_files, claude_events = analyze_claude_code(repo_root)
    anti_times, anti_files, anti_steps = analyze_antigravity(repo_root)
    
    # Conversão de todos os carimbos de data/hora para fuso horário de Brasília (GMT-3)
    claude_br = sorted([to_brasilia(t.replace(tzinfo=None)) for t in claude_times if t])
    anti_br = sorted([to_brasilia(t.replace(tzinfo=None)) for t in anti_times if t])
    
    # Agrupamento das horas por dia de trabalho
    unique_dates = sorted(list(set(
        [t.date() for t in claude_br] + [t.date() for t in anti_br]
    )))
    
    daily_rows = []
    total_anti_hours = 0.0
    total_claude_hours = 0.0
    total_comb_hours = 0.0
    
    for d in unique_dates:
        claude_day = [t for t in claude_br if t.date() == d]
        anti_day = [t for t in anti_br if t.date() == d]
        combined_day = sorted(claude_day + anti_day)
        
        c_hours, _ = calculate_active_time(claude_day, session_gap_minutes=args.gap)
        a_hours, _ = calculate_active_time(anti_day, session_gap_minutes=args.gap)
        comb_hours, _ = calculate_active_time(combined_day, session_gap_minutes=args.gap)
        
        total_anti_hours += a_hours
        total_claude_hours += c_hours
        total_comb_hours += comb_hours
        
        daily_rows.append({
            "date_str": d.strftime("%d/%m/%Y"),
            "claude_hours": c_hours,
            "anti_hours": a_hours,
            "combined_hours": comb_hours,
            "anti_events": len(anti_day),
            "claude_events": len(claude_day)
        })
        
    if args.export:
        report_path = os.path.join(repo_root, ".tracker", "TEMPO_DE_TRABALHO.md")
        
        header = (
            f"# Registro de Tempo de Desenvolvimento do Repositório (IA)\n\n"
            f"Este arquivo consolida o tempo de desenvolvimento ativo auxiliado por ferramentas de Inteligência Artificial (Antigravity + Claude Code) coletados localmente por cada desenvolvedor de forma privada e colaborativa.\n\n"
            f"> [!NOTE]\n"
            f"> Por motivos de segurança e privacidade corporativa, as identidades dos desenvolvedores e de suas máquinas físicas foram mascaradas usando hashes SHA-256 determinísticos. Cada desenvolvedor pode checar seu ID anônimo no terminal local ao executar `make -f .tracker/Makefile track-time`.\n\n"
            f"---\n\n"
        )
        
        blocks = []
        
        try:
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if content:
                    raw_parts = re.split(r'\n\s*---\s*\n', content)
                    for part in raw_parts:
                        part_str = part.strip()
                        if not part_str:
                            continue
                        
                        if part_str.startswith("# Registro de Tempo"):
                            # Ignora o cabeçalho antigo para usar o novo com a nota de anonimato
                            continue
                        
                        # Verifica se é um bloco de desenvolvedor pelo ID Mascarado
                        match = re.match(r'## 👤 Desenvolvedor:\s+`([^`]+)`', part_str)
                        if match:
                            block_masked = match.group(1)
                            # Se for o MESMO ID mascarado, substitui pela versão atualizada
                            if block_masked == masked_id:
                                continue
                        
                        blocks.append(part_str)
            
            # Monta o novo bloco deste desenvolvedor
            new_block = (
                f"## 👤 Desenvolvedor: `{masked_id}`\n\n"
                f"* **Última Atualização:** {brasilia_now_str} (Horário de Brasília)\n"
                f"* **Tempo Ativo Combinado (IA):** **{total_comb_hours:.2f} horas**\n"
                f"* **Interações no Antigravity:** **{total_anti_hours:.2f} horas** ({anti_steps} passos em {anti_files} conversas)\n"
                f"* **Sessões no Claude Code:** **{total_claude_hours:.2f} horas** ({claude_events} eventos em {claude_files} sessões)\n\n"
                f"### 🗓️ Detalhamento Diário das Horas (Brasília)\n\n"
                f"| Dia de Trabalho | Tempo no Antigravity | Tempo no Claude Code | Tempo Combinado (Sem Sobreposição) | Eventos (Antigravity / Claude Code) |\n"
                f"| :---: | :---: | :---: | :---: | :---: |\n"
            )
            for row in daily_rows:
                new_block += (
                    f"| {row['date_str']} | {row['anti_hours']:.2f} h | {row['claude_hours']:.2f} h | "
                    f"**{row['combined_hours']:.2f} h** | {row['anti_events']} / {row['claude_events']} |\n"
                )
            
            blocks.append(new_block.strip())
            
            # Escreve o arquivo consolidado
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(header)
                for b in blocks:
                    f.write(b)
                    f.write("\n\n---\n\n")
                
            print(f"\033[92m✔ Métricas de tempo atualizadas com sucesso no arquivo: {report_path}\033[0m")
        except Exception as e:
            print(f"\033[91m✘ Erro ao atualizar métricas de tempo: {e}\033[0m")
            
    else:
        # Imprime no terminal um layout elegante
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(f"\033[1;37m RASTREADOR DE TEMPO: {username}@{hostname} \033[0m")
        print(f"\033[1;90m ID de Anonimato Externo: {masked_id}\033[0m")
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(f" Repositório: \033[94m{repo_root}\033[0m")
        print(f" Data/Hora (Brasília): {brasilia_now_str}")
        print("-"*60)
        print(f" \033[1mMétricas locais compiladas por Dia (Gap: {args.gap} min):\033[0m")
        print(f"  • Tempo Ativo no Antigravity: \033[92m{total_anti_hours:.2f} horas\033[0m")
        print(f"  • Tempo Ativo no Claude Code:  \033[92m{total_claude_hours:.2f} horas\033[0m")
        print("-"*60)
        print(f" \033[1;93m✔ TOTAL LOCAL COMBINADO ACUMULADO: {total_comb_hours:.2f} horas\033[0m")
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(" Dica: Execute \033[96mmake -f .tracker/Makefile track-time EXPORT=true\033[0m para anexar/atualizar.")
        print("\033[1;35m" + "="*60 + "\033[0m")

if __name__ == "__main__":
    main()

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
from collections import defaultdict

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
    identity_str = f"{username}@{hostname}"
    h = hashlib.sha256(identity_str.encode('utf-8')).hexdigest()[:8]
    return f"dev-{h}"

def format_hours(hours):
    if hours < 0:
        hours = 0
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h}h {m:02d}m"

def build_branch_timeline(repo_root):
    reflog_path = os.path.join(repo_root, ".git", "logs", "HEAD")
    timeline = []
    if not os.path.isfile(reflog_path):
        return timeline
    try:
        with open(reflog_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n")
                if "\t" not in line:
                    continue
                try:
                    meta, msg = line.split("\t", 1)
                    m = re.search(r"checkout: moving from .+ to (.+)", msg)
                    if not m:
                        continue
                    branch = m.group(1).strip()
                    parts = meta.split()
                    unix_ts = int(parts[-2])
                    entry_dt = datetime.utcfromtimestamp(unix_ts) - timedelta(hours=3)
                    timeline.append((entry_dt, branch))
                except Exception:
                    continue
    except Exception:
        return []
    timeline.sort(key=lambda x: x[0])
    return timeline


def get_branch_at(timeline, ping_dt):
    if not timeline:
        return "main"
    result = None
    for entry_dt, branch in timeline:
        if entry_dt <= ping_dt:
            result = branch
        else:
            break
    if result is None:
        return "Desconhecida"
    return result


def analyze_claude_code(repo_root):
    project_dir_name = re.sub(r'[^a-zA-Z0-9]', '-', repo_root)
    claude_dir = os.path.expanduser(f"~/.claude/projects/{project_dir_name}")
    
    events = []
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
                        ts = data.get("timestamp")
                        if not ts:
                            continue
                        dt = parse_iso(ts)
                        if not dt:
                            continue
                        raw_model = data.get("message", {}).get("model")
                        if not raw_model:
                            raw_model = "Claude CLI (Unknown)"
                            
                        if "sonnet-4-6" in raw_model.lower() or "sonnet" in raw_model.lower():
                            mapped_model = "Sonnet 4.6"
                        elif "opus" in raw_model.lower():
                            mapped_model = "Opus 4.7"
                        elif "haiku" in raw_model.lower():
                            mapped_model = "Haiku 4.5"
                        else:
                            mapped_model = raw_model
                            
                        events.append({
                            "dt": dt,
                            "tool": "Claude Code",
                            "is_change": False,
                            "model": None,
                            "is_ping": True,
                            "active_model": mapped_model
                        })
                        total_events += 1
                    except Exception:
                        pass
        except Exception:
            pass
            
    return events, len(files), total_events

def analyze_antigravity(repo_root):
    antigravity_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    events = []
    conversations_found = 0
    total_steps = 0
    
    if not os.path.isdir(antigravity_dir):
        return [], 0, 0
        
    pattern = os.path.join(antigravity_dir, "*", ".system_generated", "logs", "overview.txt")
    files = glob.glob(pattern)
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            belongs_to_repo = (repo_root in content)
            has_user_input = ("USER_REQUEST" in content or "USER_EXPLICIT" in content)
            
            if belongs_to_repo and has_user_input:
                conversations_found += 1
                
            lines = content.strip().split('\n')
            
            # Pass 1: Identificar o modelo inicial desta conversa olhando o primeiro USER_SETTINGS_CHANGE
            first_dt = None
            first_old_model = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    created_at = data.get("created_at")
                    if created_at and not first_dt:
                        first_dt = parse_iso(created_at)
                        
                    content_text = data.get("content", "")
                    if "<USER_SETTINGS_CHANGE>" in content_text and first_old_model is None:
                        match = re.search(r"changed setting `Model Selection` from (.*?) to (.*?)\.", content_text)
                        if match:
                            old_m = match.group(1).strip()
                            first_old_model = old_m
                except Exception:
                    pass
                    
            if first_old_model and first_old_model != "None" and first_dt:
                events.append({
                    "dt": first_dt - timedelta(milliseconds=1),
                    "tool": "Antigravity",
                    "is_change": True,
                    "model": first_old_model,
                    "is_ping": False
                })
                
            # Pass 2: Parsing normal de pings e mudanças
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    created_at = data.get("created_at")
                    if not created_at:
                        continue
                        
                    dt = parse_iso(created_at)
                    if not dt:
                        continue
                    
                    content_text = data.get("content", "")
                    
                    is_change = False
                    new_model = None
                    if "<USER_SETTINGS_CHANGE>" in content_text:
                        match = re.search(r"changed setting `Model Selection` from .*? to (.*?)\.", content_text)
                        if match:
                            new_model = match.group(1).strip()
                            is_change = True
                            
                    if is_change:
                        events.append({
                            "dt": dt,
                            "tool": "Antigravity",
                            "is_change": True,
                            "model": new_model,
                            "is_ping": False
                        })
                    
                    if belongs_to_repo and has_user_input:
                        events.append({
                            "dt": dt,
                            "tool": "Antigravity",
                            "is_change": False,
                            "model": None,
                            "is_ping": True
                        })
                        total_steps += 1
                except Exception:
                    pass
        except Exception:
            pass
            
    return events, conversations_found, total_steps

def main():
    parser = argparse.ArgumentParser(description="Calculador de tempo de trabalho de IA apartado e seguro.")
    parser.add_argument("--export", action="store_true", help="Se definido, anexa/atualiza o relatório em formato Markdown.")
    parser.add_argument("--gap", type=int, default=45, help="Intervalo máximo em minutos entre comandos para agrupar na mesma sessão.")
    args = parser.parse_args()
    
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    username = getpass.getuser()
    hostname = socket.gethostname()
    masked_id = get_masked_identity(username, hostname)
    
    brasilia_now = datetime.utcnow() - timedelta(hours=3)
    brasilia_now_str = brasilia_now.strftime('%d/%m/%Y %H:%M:%S')
    
    branch_timeline = build_branch_timeline(repo_root)

    claude_events, claude_files, claude_steps = analyze_claude_code(repo_root)
    anti_events, anti_files, anti_steps = analyze_antigravity(repo_root)
    
    all_events = claude_events + anti_events
    for ev in all_events:
        ev["dt_br"] = to_brasilia(ev["dt"].replace(tzinfo=None))
        
    all_events.sort(key=lambda x: x["dt_br"])
    
    # Propagação cronológica de estado com fallback de fábrica
    current_anti_model = "Gemini 3.1 Pro (High)"
    
    ping_events = []
    for ev in all_events:
        if ev["tool"] == "Antigravity":
            if ev["is_change"]:
                current_anti_model = ev["model"]
            if ev["is_ping"]:
                ev["active_model"] = current_anti_model
                ping_events.append(ev)
        else:
            if ev["is_ping"]:
                ping_events.append(ev)

    for ev in ping_events:
        ev["branch"] = get_branch_at(branch_timeline, ev["dt_br"])
                
    # Agrupar em sessões ativas
    sessions = []
    if ping_events:
        current_session = [ping_events[0]]
        for ev in ping_events[1:]:
            last_ev = current_session[-1]
            gap = (ev["dt_br"] - last_ev["dt_br"]).total_seconds() / 60.0
            if gap <= args.gap:
                current_session.append(ev)
            else:
                sessions.append(current_session)
                current_session = [ev]
        sessions.append(current_session)
        
    # Estatísticas diárias
    daily_stats = defaultdict(lambda: defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0}))
    branch_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0})))
    total_hours = 0.0

    for sess in sessions:
        date_str = sess[0]["dt_br"].strftime("%d/%m/%Y")

        models_in_session = set(ev["active_model"] for ev in sess)
        for m in models_in_session:
            daily_stats[date_str][m]["sessions"] += 1

        branches_in_session = set(ev["branch"] for ev in sess)
        for b in branches_in_session:
            models_in_branch_session = set(ev["active_model"] for ev in sess if ev["branch"] == b)
            for m in models_in_branch_session:
                branch_stats[date_str][b][m]["sessions"] += 1

        for ev in sess:
            daily_stats[date_str][ev["active_model"]]["interactions"] += 1
            branch_stats[date_str][ev["branch"]][ev["active_model"]]["interactions"] += 1

        model_duration_minutes = defaultdict(float)
        branch_model_duration_minutes = defaultdict(lambda: defaultdict(float))
        for i in range(len(sess) - 1):
            gap = (sess[i+1]["dt_br"] - sess[i]["dt_br"]).total_seconds() / 60.0
            model = sess[i]["active_model"]
            branch = sess[i]["branch"]
            model_duration_minutes[model] += gap
            branch_model_duration_minutes[branch][model] += gap

        session_duration = (sess[-1]["dt_br"] - sess[0]["dt_br"]).total_seconds() / 60.0
        if session_duration < 15.0:
            padding = 15.0 - session_duration
            last_model = sess[-1]["active_model"]
            last_branch = sess[-1]["branch"]
            model_duration_minutes[last_model] += padding
            branch_model_duration_minutes[last_branch][last_model] += padding

        for m, m_mins in model_duration_minutes.items():
            h = m_mins / 60.0
            daily_stats[date_str][m]["hours"] += h
            total_hours += h

        for b, bm_map in branch_model_duration_minutes.items():
            for m, m_mins in bm_map.items():
                branch_stats[date_str][b][m]["hours"] += m_mins / 60.0

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
                        if not part_str or part_str.startswith("# Registro de Tempo"):
                            continue
                        match = re.match(r'## 👤 Desenvolvedor:\s+`([^`]+)`', part_str)
                        if match and match.group(1) == masked_id:
                            continue
                        blocks.append(part_str)
            
            new_block = (
                f"## 👤 Desenvolvedor: `{masked_id}`\n\n"
                f"* **Última Atualização:** {brasilia_now_str} (Horário de Brasília)\n"
                f"* **Tempo Ativo Combinado (IA):** **{format_hours(total_hours)}**\n"
                f"* **Total de Interações:** **{len(ping_events)} comandos** em {len(sessions)} sessões\n\n"
                f"### 🗓️ Detalhamento Diário das Horas (Brasília)\n\n"
                f"| Dia de Trabalho | Modelo LLM | Tempo Ativo | Sessões Ativas | Interações |\n"
                f"| :---: | :---: | :---: | :---: | :---: |\n"
            )
            
            for d in sorted(daily_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
                for m in sorted(daily_stats[d].keys()):
                    h = daily_stats[d][m]["hours"]
                    s = daily_stats[d][m]["sessions"]
                    i = daily_stats[d][m]["interactions"]
                    new_block += f"| {d} | **{m}** | {format_hours(h)} | {s} | {i} |\n"
            
            if not daily_stats:
                new_block += f"| N/A | Nenhum | 0h 00m | 0 | 0 |\n"

            new_block += (
                f"\n### 🌿 Detalhamento Diário por Branch / História (Brasília)\n\n"
                f"| Dia de Trabalho | Branch Ativa | Modelos Utilizados | Tempo Ativo | Interações |\n"
                f"| :---: | :---: | :---: | :---: | :---: |\n"
            )

            if branch_stats:
                for d in sorted(branch_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
                    for b in sorted(branch_stats[d].keys()):
                        branch_hours = sum(branch_stats[d][b][m]["hours"] for m in branch_stats[d][b])
                        branch_interactions = sum(branch_stats[d][b][m]["interactions"] for m in branch_stats[d][b])
                        models_used = ", ".join(sorted(branch_stats[d][b].keys()))
                        new_block += f"| {d} | `{b}` | {models_used} | {format_hours(branch_hours)} | {branch_interactions} |\n"
            else:
                new_block += f"| N/A | Nenhuma | Nenhum | 0h 00m | 0 |\n"

            blocks.append(new_block.strip())
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(header)
                for b in blocks:
                    f.write(b)
                    f.write("\n\n---\n\n")
                
            print(f"\033[92m✔ Métricas de tempo atualizadas com sucesso no arquivo: {report_path}\033[0m")
        except Exception as e:
            print(f"\033[91m✘ Erro ao atualizar métricas de tempo: {e}\033[0m")
            
    else:
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(f"\033[1;37m RASTREADOR DE TEMPO: {username}@{hostname} \033[0m")
        print(f"\033[1;90m ID de Anonimato Externo: {masked_id}\033[0m")
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(f" Repositório: \033[94m{repo_root}\033[0m")
        print(f" Data/Hora (Brasília): {brasilia_now_str}")
        print("-"*60)
        print(f" \033[1mMétricas locais compiladas por Modelo (Gap: {args.gap} min):\033[0m")
        
        model_totals = defaultdict(float)
        for d in daily_stats:
            for m in daily_stats[d]:
                model_totals[m] += daily_stats[d][m]["hours"]
                
        for m, h in sorted(model_totals.items()):
            print(f"  • {m}: \033[92m{format_hours(h)}\033[0m")
            
        print("-"*60)
        print(f" \033[1;93m✔ TOTAL LOCAL COMBINADO ACUMULADO: {format_hours(total_hours)}\033[0m")
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(" Dica: Execute \033[96mmake -f .tracker/Makefile track-time EXPORT=true\033[0m para anexar/atualizar.")
        print("\033[1;35m" + "="*60 + "\033[0m")

if __name__ == "__main__":
    main()

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

def parse_hours_from_str(h_str):
    m_h = re.search(r'(\d+)\s*h', h_str)
    m_m = re.search(r'(\d+)\s*m', h_str)
    hours = 0.0
    if m_h:
        hours += float(m_h.group(1))
    if m_m:
        hours += float(m_m.group(1)) / 60.0
    return hours

def normalize_model_name(raw_model):
    if not raw_model:
        return "Unknown"
    
    # 1. Trata tipos não-string com segurança
    raw_model = str(raw_model).strip()
    if not raw_model or raw_model.lower() == "none":
        return "None"
        
    # 2. Remove sufixos de datas de forma abrangente (ex: -20241022 ou -2024-10-22)
    clean = re.sub(r'-\d{8}\b', '', raw_model)
    clean = re.sub(r'-\d{4}-\d{2}-\d{2}\b', '', clean)
    
    # 3. Normaliza separadores de versão curtos (dígito-dígito) para pontos (ex: 3-5 -> 3.5).
    #    \b e dígito único evitam capturar sufixos de build longos (ex: 4-1106 não casa).
    clean = re.sub(r'\b(\d)-(\d)\b', r'\1.\2', clean)
    
    # 4. Substitui hífens e sublinhados por espaços comuns
    clean = clean.replace('-', ' ').replace('_', ' ')
    
    # 5. Processa palavra por palavra
    words = clean.split()
    capitalized_words = []
    
    for w in words:
        # Capitaliza sequências de letras isoladas ou delimitadas por não-alfanuméricos (ex: "(unknown)" -> "(Unknown)")
        # Mantém sufixos como "4o" em minúsculas, pois não há limite de palavra (\b) entre o dígito e a letra.
        w_cap = re.sub(r'\b[a-zA-Z]+\b', lambda m: m.group(0).capitalize(), w)
        
        # Ajusta acrônimos específicos com limites de palavra (\b) para evitar corrupção em substrings (ex: Client)
        w_cap = re.sub(r'\bgpt\b', 'GPT', w_cap, flags=re.IGNORECASE)
        w_cap = re.sub(r'\bcli\b', 'CLI', w_cap, flags=re.IGNORECASE)
        w_cap = re.sub(r'\boss\b', 'OSS', w_cap, flags=re.IGNORECASE)
        
        capitalized_words.append(w_cap)
        
    normalized = " ".join(capitalized_words)

    
    # 6. Garante prefixo "Claude" de forma case-insensitive e segura
    norm_lower = normalized.lower()
    if any(k in norm_lower for k in ('sonnet', 'opus', 'haiku')) and 'claude' not in norm_lower:
        normalized = "Claude " + normalized
        
    return normalized


def parse_existing_developers_stats(content, current_masked_id):
    parts = re.split(r'\n\s*---\s*\n', content)
    dev_stats = {}
    
    for part in parts:
        part_str = part.strip()
        if not part_str or part_str.startswith("# Registro de Tempo") or part_str.startswith("## 📊 Resumo Geral"):
            continue
        
        match = re.match(r'## 👤 Desenvolvedor:\s+`([^`]+)`', part_str)
        if not match:
            continue
            
        dev_id = match.group(1).strip()
        if dev_id == current_masked_id:
            continue
            
        branch_hours = defaultdict(float)
        lines = part_str.split('\n')
        in_branch_table = False
        for line in lines:
            if "### 🌿 Detalhamento Diário por Branch" in line:
                in_branch_table = True
                continue
            if in_branch_table:
                stripped = line.strip()
                if not stripped.startswith('|'):
                    if stripped:
                        in_branch_table = False
                    continue
                if "Dia de Trabalho" in line or ":---:" in line:
                    continue
                cols = [c.strip() for c in stripped.split('|')]
                if len(cols) >= 7:
                    branch_raw = cols[2].replace('`', '').strip()
                    time_raw = cols[5].strip()
                    if branch_raw and branch_raw not in ("N/A", "Nenhuma"):
                        h = parse_hours_from_str(time_raw)
                        branch_hours[branch_raw] += h
        
        total_h = 0.0
        tot_match = re.search(r'\*\s*\*\*Tempo Ativo Combinado \(IA\):\*\*\s*\*\*([^*]+)\*\*', part_str)
        if tot_match:
            total_h = parse_hours_from_str(tot_match.group(1))
        else:
            total_h = sum(branch_hours.values())
            
        dev_stats[dev_id] = {
            "total_hours": total_h,
            "branch_hours": branch_hours
        }
    return dev_stats

def extract_repo_name(content):
    match = re.search(r'Active Document:\s*(/\S+)', content)
    if match:
        path = match.group(1).strip().rstrip(')')
        while path and path != '/':
            if os.path.isdir(os.path.join(path, '.git')):
                return os.path.basename(path)
            path = os.path.dirname(path)
    return "unknown"

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
        return "main"
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
            # Pré-varredura para encontrar o primeiro modelo da conversa.
            # Entradas "user" e "queue-operation" não têm message.model — sem isso,
            # cada turno do usuário vira "Unknown" mesmo sem troca de modelo.
            first_model = None
            lines_data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        lines_data.append(data)
                        if first_model is None:
                            raw = data.get("message", {}).get("model")
                            if raw:
                                first_model = normalize_model_name(raw)
                    except Exception:
                        pass

            current_model = first_model or "Claude CLI (Unknown)"
            for data in lines_data:
                try:
                    ts = data.get("timestamp")
                    if not ts:
                        continue
                    dt = parse_iso(ts)
                    if not dt:
                        continue
                    raw = data.get("message", {}).get("model")
                    if raw:
                        current_model = normalize_model_name(raw)

                    events.append({
                        "dt": dt,
                        "tool": "Claude Code",
                        "is_change": False,
                        "model": None,
                        "is_ping": True,
                        "active_model": current_model
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

            repo_name = extract_repo_name(content)

            # Normalizar caminhos para Windows/Linux/Mac e JSON escaped strings
            repo_root_fwd = repo_root.replace('\\', '/')
            repo_root_escaped = repo_root.replace('\\', '\\\\')

            belongs_to_repo = (repo_root in content) or (repo_root_fwd in content) or (repo_root_escaped in content)
            has_user_input = ("USER_REQUEST" in content or "USER_EXPLICIT" in content)

            if belongs_to_repo and has_user_input:
                conversations_found += 1
                
            lines = content.strip().split('\n')
            
            # Pass 1: Determina o modelo inicial da conversa ancorado 1ms antes do primeiro turno.
            # Quando a conversa começa com um modelo já selecionado (ex: Claude), a IDE não emite
            # USER_SETTINGS_CHANGE inicial — só emite ao trocar. Por isso capturamos o "from" do
            # primeiro evento de mudança como modelo inicial quando não é "None". O "to" é o modelo
            # após a troca, emitido normalmente no Pass 2.
            first_dt = None
            first_active_model = None
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
                    if "<USER_SETTINGS_CHANGE>" in content_text and first_active_model is None:
                        match = re.search(r"changed setting `Model Selection` from (.*?) to (.*?)(?:\. No need|\.?\s*$)", content_text)
                        if match:
                            from_m = match.group(1).strip()
                            to_m = match.group(2).strip()
                            # Se "from" é um modelo real (não None), a sessão iniciou com ele
                            if from_m and from_m.lower() not in ("none", ""):
                                first_active_model = normalize_model_name(from_m)
                            else:
                                first_active_model = normalize_model_name(to_m)
                except Exception:
                    pass

            if first_active_model and first_active_model != "None" and first_dt:
                events.append({
                    "dt": first_dt - timedelta(milliseconds=1),
                    "tool": "Antigravity",
                    "is_change": True,
                    "model": first_active_model,
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
                        match = re.search(r"changed setting `Model Selection` from .*? to (.*?)(?:\. No need|\.?\s*$)", content_text)
                        if match:
                            new_model = normalize_model_name(match.group(1).strip())
                            is_change = True
                            
                    if is_change and new_model and new_model != "None":
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
    daily_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0})))
    branch_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0}))))
    total_hours = 0.0

    for sess in sessions:
        date_str = sess[0]["dt_br"].strftime("%d/%m/%Y")

        models_in_session = set((ev["tool"], ev["active_model"]) for ev in sess)
        for t, m in models_in_session:
            daily_stats[date_str][t][m]["sessions"] += 1

        branches_in_session = set(ev["branch"] for ev in sess)
        for b in branches_in_session:
            tool_models_in_branch_session = set((ev["tool"], ev["active_model"]) for ev in sess if ev["branch"] == b)
            for t, m in tool_models_in_branch_session:
                branch_stats[date_str][b][t][m]["sessions"] += 1

        # Interações e durações atribuídas à data real de cada ping (corrige sessões que atravessam meia-noite)
        for ev in sess:
            ev_date = ev["dt_br"].strftime("%d/%m/%Y")
            daily_stats[ev_date][ev["tool"]][ev["active_model"]]["interactions"] += 1
            branch_stats[ev_date][ev["branch"]][ev["tool"]][ev["active_model"]]["interactions"] += 1

        date_tool_model_mins = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        date_branch_tool_model_mins = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
        for i in range(len(sess) - 1):
            if sess[i]["tool"] != sess[i+1]["tool"]:
                continue
            gap = (sess[i+1]["dt_br"] - sess[i]["dt_br"]).total_seconds() / 60.0
            ev_date = sess[i]["dt_br"].strftime("%d/%m/%Y")
            tool = sess[i]["tool"]
            model = sess[i]["active_model"]
            branch = sess[i]["branch"]
            date_tool_model_mins[ev_date][tool][model] += gap
            date_branch_tool_model_mins[ev_date][branch][tool][model] += gap

        session_duration = (sess[-1]["dt_br"] - sess[0]["dt_br"]).total_seconds() / 60.0
        if session_duration < 15.0:
            padding = 15.0 - session_duration
            last_ev_date = sess[-1]["dt_br"].strftime("%d/%m/%Y")
            last_tool = sess[-1]["tool"]
            last_model = sess[-1]["active_model"]
            last_branch = sess[-1]["branch"]
            date_tool_model_mins[last_ev_date][last_tool][last_model] += padding
            date_branch_tool_model_mins[last_ev_date][last_branch][last_tool][last_model] += padding

        for d, tm_map in date_tool_model_mins.items():
            for t, m_map in tm_map.items():
                for m, m_mins in m_map.items():
                    h = m_mins / 60.0
                    daily_stats[d][t][m]["hours"] += h
                    total_hours += h

        for d, btm_map in date_branch_tool_model_mins.items():
            for b, tm_map in btm_map.items():
                for t, m_map in tm_map.items():
                    for m, m_mins in m_map.items():
                        branch_stats[d][b][t][m]["hours"] += m_mins / 60.0

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
        all_devs_stats = {}
        try:
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content:
                    raw_parts = re.split(r'\n\s*---\s*\n', content)
                    for part in raw_parts:
                        part_str = part.strip()
                        if not part_str or part_str.startswith("# Registro de Tempo") or part_str.startswith("## 📊 Resumo Geral"):
                            continue
                        match = re.match(r'## 👤 Desenvolvedor:\s+`([^`]+)`', part_str)
                        if match and match.group(1) == masked_id:
                            continue
                        blocks.append(part_str)
                    
                    all_devs_stats = parse_existing_developers_stats(content, masked_id)
            
            # Compute current developer branch stats
            current_branch_hours = defaultdict(float)
            for d in branch_stats:
                for b in branch_stats[d]:
                    for t in branch_stats[d][b]:
                        for m in branch_stats[d][b][t]:
                            current_branch_hours[b] += branch_stats[d][b][t][m]["hours"]
            
            all_devs_stats[masked_id] = {
                "total_hours": total_hours,
                "branch_hours": current_branch_hours
            }
            
            global_total_hours = sum(d["total_hours"] for d in all_devs_stats.values())
            global_branch_hours = defaultdict(float)
            for d in all_devs_stats.values():
                for b, h in d["branch_hours"].items():
                    global_branch_hours[b] += h
            
            global_summary = (
                f"## 📊 Resumo Geral Consolidado (Todos os Desenvolvedores)\n\n"
                f"* **Tempo Total de Desenvolvimento:** **{format_hours(global_total_hours)}**\n\n"
                f"### 🌿 Tempo Total por Branch\n\n"
                f"| Branch / História | Tempo Ativo Total |\n"
                f"| :--- | :---: |\n"
            )
            if global_branch_hours:
                for b in sorted(global_branch_hours.keys()):
                    bh = global_branch_hours[b]
                    global_summary += f"| `{b}` | **{format_hours(bh)}** |\n"
            else:
                global_summary += f"| Nenhuma | **0h 00m** |\n"
            
            new_block = (
                f"## 👤 Desenvolvedor: `{masked_id}`\n\n"
                f"* **Última Atualização:** {brasilia_now_str} (Horário de Brasília)\n"
                f"* **Tempo Ativo Combinado (IA):** **{format_hours(total_hours)}**\n"
                f"* **Total de Interações:** **{len(ping_events)} comandos** em {len(sessions)} sessões\n\n"
            )
 
            # Seção: Totais por Ferramenta (inserida ANTES da Tabela 1)
            tool_totals = defaultdict(lambda: {"hours": 0.0, "interactions": 0})
            for d in daily_stats:
                for t in daily_stats[d]:
                    for m in daily_stats[d][t]:
                        tool_totals[t]["hours"] += daily_stats[d][t][m]["hours"]
                        tool_totals[t]["interactions"] += daily_stats[d][t][m]["interactions"]
 
            new_block += (
                f"### 🛠️ Totais por Ferramenta\n\n"
                f"| Ferramenta | Tempo Ativo | Interações |\n"
                f"| :---: | :---: | :---: |\n"
            )
            if tool_totals:
                for t in sorted(tool_totals.keys()):
                    th = tool_totals[t]["hours"]
                    ti = tool_totals[t]["interactions"]
                    new_block += f"| **{t}** | {format_hours(th)} | {ti} |\n"
            else:
                new_block += f"| Nenhuma | 0h 00m | 0 |\n"

            # Tabela 1: Detalhamento Diário com coluna Ferramenta
            new_block += (
                f"\n### 🗓️ Detalhamento Diário das Horas (Brasília)\n\n"
                f"| Dia de Trabalho | Ferramenta | Modelo LLM | Tempo Ativo | Sessões Ativas | Interações |\n"
                f"| :---: | :---: | :---: | :---: | :---: | :---: |\n"
            )
 
            for d in sorted(daily_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
                for t in sorted(daily_stats[d].keys()):
                    for m in sorted(daily_stats[d][t].keys()):
                        h = daily_stats[d][t][m]["hours"]
                        s = daily_stats[d][t][m]["sessions"]
                        i = daily_stats[d][t][m]["interactions"]
                        new_block += f"| {d} | **{t}** | {m} | {format_hours(h)} | {s} | {i} |\n"
 
            if not daily_stats:
                new_block += f"| N/A | Nenhuma | Nenhum | 0h 00m | 0 | 0 |\n"
 
            # Tabela 2: Detalhamento por Branch com colunas Ferramentas + Modelos Utilizados
            new_block += (
                f"\n### 🌿 Detalhamento Diário por Branch / História (Brasília)\n\n"
                f"| Dia de Trabalho | Branch Ativa | Ferramentas | Modelos Utilizados | Tempo Ativo | Interações |\n"
                f"| :---: | :---: | :---: | :---: | :---: | :---: |\n"
            )
 
            if branch_stats:
                for d in sorted(branch_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
                    for b in sorted(branch_stats[d].keys()):
                        branch_hours = sum(
                            branch_stats[d][b][t][m]["hours"]
                            for t in branch_stats[d][b]
                            for m in branch_stats[d][b][t]
                        )
                        branch_interactions = sum(
                            branch_stats[d][b][t][m]["interactions"]
                            for t in branch_stats[d][b]
                            for m in branch_stats[d][b][t]
                        )
                        tools_used = ", ".join(sorted(branch_stats[d][b].keys()))
                        models_used = ", ".join(sorted({m for t in branch_stats[d][b].values() for m in t.keys()}))
                        new_block += f"| {d} | `{b}` | {tools_used} | {models_used} | {format_hours(branch_hours)} | {branch_interactions} |\n"
            else:
                new_block += f"| N/A | Nenhuma | Nenhuma | Nenhum | 0h 00m | 0 |\n"
 
            blocks.append(new_block.strip())
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(global_summary.strip())
                f.write("\n\n---\n\n")
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
        print(f" \033[1mMétricas locais compiladas por Ferramenta/Modelo (Gap: {args.gap} min):\033[0m")

        tool_model_totals = defaultdict(lambda: defaultdict(float))
        for d in daily_stats:
            for t in daily_stats[d]:
                for m in daily_stats[d][t]:
                    tool_model_totals[t][m] += daily_stats[d][t][m]["hours"]

        for t in sorted(tool_model_totals.keys()):
            print(f"  [{t}]")
            for m, h in sorted(tool_model_totals[t].items()):
                print(f"   • {m}: \033[92m{format_hours(h)}\033[0m")

        print("-"*60)
        print(f" \033[1;93m✔ TOTAL LOCAL COMBINADO ACUMULADO: {format_hours(total_hours)}\033[0m")
        print("\033[1;35m" + "="*60 + "\033[0m")
        print(" Dica: Execute \033[96mmake -f .tracker/Makefile track-time EXPORT=true\033[0m para anexar/atualizar.")
        print("\033[1;35m" + "="*60 + "\033[0m")

if __name__ == "__main__":
    main()

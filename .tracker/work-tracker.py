#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitário Apartado de Rastreamento de Tempo de Trabalho Ativo (Claude Code + Antigravity)
Roda localmente de forma privada com fuso horário de Brasília (GMT-3), 
mascara a identidade do desenvolvedor com hash SHA-256 para anonimato externo, 
e gera tabelas agregadas detalhadas por dia de trabalho."""
import os
import re
import json
import glob
import hashlib
import argparse
import socket
import getpass
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Constantes do modelo de evento
SCHEMA_VERSION = 1
EVENTS_DIRNAME = "events"
MANIFEST_NAME = "manifest.json"
LEGACY_MODEL_LABEL = "Indeterminado (pré-migração)"

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
        hours += float(m_m.group(2) if len(m_m.groups()) > 1 else m_m.group(1)) / 60.0
    return hours

def date_to_iso(d_str):
    parts = d_str.strip().split('/')
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str

def iso_to_date(iso_str):
    parts = iso_str.strip().split('-')
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return iso_str

def normalize_model_name(raw_model):
    if not raw_model:
        return "Unknown"
    
    # 1. Trata tipos não-string com segurança
    raw_model = str(raw_model).strip()
    if not raw_model or raw_model.lower() == "none":
        return "None"

    # Evita falsos positivos com strings de regex / código discutido nas próprias conversas
    if any(char in raw_model for char in ('*', '?', '\\', '|', '[', ']')):
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
    antigravity_dir = os.path.expanduser("~/.gemini/antigravity-ide/brain")
    events = []
    conversations_found = 0
    total_steps = 0
    
    if not os.path.isdir(antigravity_dir):
        return [], 0, 0
        
    pattern = os.path.join(antigravity_dir, "*", ".system_generated", "logs", "transcript.jsonl")
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

                    content_text = data.get("content") or ""
                    if "<USER_SETTINGS_CHANGE>" in content_text and first_active_model is None:
                        match = re.search(r"changed setting `Model Selection` from (.*?) to (.*?)(?:\. No need|\.?\s*$)", content_text)
                        if match:
                            from_m = match.group(1).strip()
                            to_m = match.group(2).strip()
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
                    
                    content_text = data.get("content") or ""
                    
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

def load_manifest(events_dir):
    manifest_path = os.path.join(events_dir, MANIFEST_NAME)
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"schema_version": SCHEMA_VERSION, "developers": {}}

def emit_events(events_dir, masked_id, live_events):
    file_name = f"dev-{masked_id}.jsonl" if not masked_id.startswith("dev-") else f"{masked_id}.jsonl"
    file_path = os.path.join(events_dir, file_name)
    
    legacy_events = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("legacy") is True:
                        legacy_events.append(ev)
                except json.JSONDecodeError:
                    pass

    live_hours = sum(ev["hours"] for ev in live_events if ev["event_type"] == "activity_daily")
    live_interactions = sum(ev["interactions"] for ev in live_events if ev["event_type"] == "activity_daily")
    live_sessions = sum(ev["sessions"] for ev in live_events if ev["event_type"] == "activity_daily")

    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz=tz_br)
    generated_at_str = now_br.isoformat()
    live_daily = [ev for ev in live_events if ev["event_type"] == "activity_daily"]
    if live_daily:
        max_date_iso = max(ev["date"] for ev in live_daily)
        max_dt = datetime.strptime(max_date_iso, "%Y-%m-%d")
        last_active_date_str = max_dt.strftime('%d/%m/%Y')
    else:
        last_active_date_str = "N/A"

    live_summary = {
        "event_type": "dev_summary",
        "schema_version": SCHEMA_VERSION,
        "developer": masked_id,
        "scope": "live",
        "total_hours": round(live_hours, 4),
        "total_interactions": live_interactions,
        "total_sessions": live_sessions,
        "last_active_date": last_active_date_str,
        "legacy": False,
        "generated_at": generated_at_str
    }

    if not os.path.exists(events_dir):
        os.makedirs(events_dir)

    tmp_path = file_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        for ev in legacy_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        f.write(json.dumps(live_summary, ensure_ascii=False) + "\n")
        for ev in live_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    os.replace(tmp_path, file_path)

def load_all_events(events_dir):
    events = []
    if os.path.exists(events_dir):
        pattern = os.path.join(events_dir, "dev-*.jsonl")
        files = glob.glob(pattern)
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass
    return events

def collect_events(repo_root):
    claude_events, _, _ = analyze_claude_code(repo_root)
    anti_events, _, _ = analyze_antigravity(repo_root)
    all_events = claude_events + anti_events
    for ev in all_events:
        ev["dt_br"] = to_brasilia(ev["dt"].replace(tzinfo=None))
    all_events.sort(key=lambda x: x["dt_br"])
    return all_events

def compute_sessions(events, gap_minutes, legacy_boundary, branch_timeline):
    boundary_dt = None
    if legacy_boundary:
        if isinstance(legacy_boundary, str):
            boundary_dt = datetime.strptime(legacy_boundary, "%Y-%m-%dT%H:%M:%S")
        else:
            boundary_dt = legacy_boundary

    current_anti_model = "Gemini 3.1 Pro (High)"
    
    ping_events = []
    for ev in events:
        if ev["tool"] == "Antigravity":
            if ev["is_change"]:
                current_anti_model = ev["model"]
            if ev["is_ping"]:
                if boundary_dt and ev["dt_br"] <= boundary_dt:
                    continue
                ev["active_model"] = current_anti_model
                ping_events.append(ev)
        else:
            if ev["is_ping"]:
                if boundary_dt and ev["dt_br"] <= boundary_dt:
                    continue
                ping_events.append(ev)

    for ev in ping_events:
        ev["branch"] = get_branch_at(branch_timeline, ev["dt_br"])
                
    sessions = []
    if ping_events:
        current_session = [ping_events[0]]
        for ev in ping_events[1:]:
            last_ev = current_session[-1]
            gap = (ev["dt_br"] - last_ev["dt_br"]).total_seconds() / 60.0
            if gap <= gap_minutes:
                current_session.append(ev)
            else:
                sessions.append(current_session)
                current_session = [ev]
        sessions.append(current_session)
    return sessions, ping_events

def aggregate_sessions(sessions):
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

    return daily_stats, branch_stats, total_hours

def build_live_events(daily_stats, branch_stats, masked_id):
    live_events = []
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz=tz_br)
    generated_at_str = now_br.isoformat()

    for d in sorted(daily_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
        date_iso = date_to_iso(d)
        for t in sorted(daily_stats[d].keys()):
            for m in sorted(daily_stats[d][t].keys()):
                h = daily_stats[d][t][m]["hours"]
                s = daily_stats[d][t][m]["sessions"]
                i = daily_stats[d][t][m]["interactions"]
                
                live_events.append({
                    "event_type": "activity_daily",
                    "schema_version": SCHEMA_VERSION,
                    "developer": masked_id,
                    "date": date_iso,
                    "tool": t,
                    "model": m,
                    "raw_model": m,
                    "model_confidence": "confirmado",
                    "hours": round(h, 4),
                    "sessions": s,
                    "interactions": i,
                    "legacy": False,
                    "generated_at": generated_at_str
                })

    for d in sorted(branch_stats.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
        date_iso = date_to_iso(d)
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
            tools_used = sorted(branch_stats[d][b].keys())
            models_used = sorted({m for t in branch_stats[d][b].values() for m in t.keys()})

            live_events.append({
                "event_type": "activity_branch",
                "schema_version": SCHEMA_VERSION,
                "developer": masked_id,
                "date": date_iso,
                "branch": b,
                "tools": tools_used,
                "models": models_used,
                "hours": round(branch_hours, 4),
                "interactions": branch_interactions,
                "legacy": False,
                "generated_at": generated_at_str
            })

    return live_events

def render_report(all_events):
    header = (
        f"# Registro de Tempo de Desenvolvimento do Repositório (IA)\n\n"
        f"Este arquivo consolida o tempo de desenvolvimento ativo auxiliado por ferramentas de Inteligência Artificial (Antigravity + Claude Code) coletados localmente por cada desenvolvedor de forma privada e colaborativa.\n\n"
        f"> [!NOTE]\n"
        f"> Por motivos de segurança e privacidade corporativa, as identidades dos desenvolvedores e de suas máquinas físicas foram mascaradas usando hashes SHA-256 determinísticos. Cada desenvolvedor pode checar seu ID anônimo no terminal local ao executar `make -f .tracker/Makefile track-time`.\n\n"
        f"---\n\n"
    )

    global_total_hours = 0.0
    global_branch_hours = defaultdict(float)

    devs_events = defaultdict(list)
    for ev in all_events:
        devs_events[ev["developer"]].append(ev)

    for dev_id, dev_evs in devs_events.items():
        dev_summaries = [ev for ev in dev_evs if ev["event_type"] == "dev_summary"]
        global_total_hours += sum(ev["total_hours"] for ev in dev_summaries)
        
        for ev in dev_evs:
            if ev["event_type"] == "activity_branch":
                global_branch_hours[ev["branch"]] += ev["hours"]

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

    blocks = []
    for dev_id in sorted(devs_events.keys()):
        dev_evs = devs_events[dev_id]
        
        dev_summaries = [ev for ev in dev_evs if ev["event_type"] == "dev_summary"]
        daily_events = [ev for ev in dev_evs if ev["event_type"] == "activity_daily"]
        branch_events = [ev for ev in dev_evs if ev["event_type"] == "activity_branch"]

        total_hours = sum(ev["total_hours"] for ev in dev_summaries)
        total_interactions = sum(ev["total_interactions"] for ev in dev_summaries)
        total_sessions = sum(ev["total_sessions"] for ev in dev_summaries)

        last_active_date = "N/A"
        live_summary = [ev for ev in dev_summaries if ev["scope"] == "live"]
        legacy_summary = [ev for ev in dev_summaries if ev["scope"] == "legacy"]
        if live_summary:
            # Support both old "last_updated" (with time) and new "last_active_date" (date only)
            ev = live_summary[0]
            if "last_active_date" in ev:
                last_active_date = ev["last_active_date"]
            elif "last_updated" in ev:
                # Extract date portion from old format "DD/MM/YYYY HH:MM:SS"
                last_active_date = ev["last_updated"].split()[0]
        elif legacy_summary:
            # Support both old "last_updated" (with time) and new "last_active_date" (date only)
            ev = legacy_summary[0]
            if "last_active_date" in ev:
                last_active_date = ev["last_active_date"]
            elif "last_updated" in ev:
                # Extract date portion from old format "DD/MM/YYYY HH:MM:SS"
                last_active_date = ev["last_updated"].split()[0]

        tool_totals = defaultdict(lambda: {"hours": 0.0, "interactions": 0})
        for ev in daily_events:
            t = ev["tool"]
            tool_totals[t]["hours"] += ev["hours"]
            tool_totals[t]["interactions"] += ev["interactions"]

        daily_grouped = defaultdict(lambda: {"hours": 0.0, "sessions": 0, "interactions": 0})
        for ev in daily_events:
            date_br = iso_to_date(ev["date"])
            key = (date_br, ev["tool"], ev["model"])
            daily_grouped[key]["hours"] += ev["hours"]
            daily_grouped[key]["sessions"] += ev["sessions"]
            daily_grouped[key]["interactions"] += ev["interactions"]

        branch_grouped = defaultdict(lambda: {"tools": set(), "models": set(), "hours": 0.0, "interactions": 0})
        for ev in branch_events:
            date_br = iso_to_date(ev["date"])
            key = (date_br, ev["branch"])
            branch_grouped[key]["hours"] += ev["hours"]
            branch_grouped[key]["interactions"] += ev["interactions"]
            for t in ev["tools"]:
                branch_grouped[key]["tools"].add(t)
            for m in ev["models"]:
                branch_grouped[key]["models"].add(m)

        dev_summary_block = (
            f"## 👤 Desenvolvedor: `{dev_id}`\n\n"
            f"* **Última Data Ativa:** {last_active_date} (Horário de Brasília)\n"
            f"* **Tempo Ativo Combinado (IA):** **{format_hours(total_hours)}**\n"
            f"* **Total de Interações:** **{total_interactions} comandos** em {total_sessions} sessões\n\n"
        )

        dev_summary_block += (
            f"### 🛠️ Totais por Ferramenta\n\n"
            f"| Ferramenta | Tempo Ativo | Interações |\n"
            f"| :---: | :---: | :---: |\n"
        )
        if tool_totals:
            for t in sorted(tool_totals.keys()):
                th = tool_totals[t]["hours"]
                ti = tool_totals[t]["interactions"]
                dev_summary_block += f"| **{t}** | {format_hours(th)} | {ti} |\n"
        else:
            dev_summary_block += f"| Nenhuma | 0h 00m | 0 |\n"

        dev_summary_block += (
            f"\n### 🗓️ Detalhamento Diário das Horas (Brasília)\n\n"
            f"| Dia de Trabalho | Ferramenta | Modelo LLM | Tempo Ativo | Sessões Ativas | Interações |\n"
            f"| :---: | :---: | :---: | :---: | :---: | :---: |\n"
        )
        if daily_grouped:
            for (d, t, m) in sorted(daily_grouped.keys(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y")):
                h = daily_grouped[(d, t, m)]["hours"]
                s = daily_grouped[(d, t, m)]["sessions"]
                i = daily_grouped[(d, t, m)]["interactions"]
                dev_summary_block += f"| {d} | **{t}** | {m} | {format_hours(h)} | {s} | {i} |\n"
        else:
            dev_summary_block += f"| N/A | Nenhuma | Nenhum | 0h 00m | 0 | 0 |\n"

        dev_summary_block += (
            f"\n### 🌿 Detalhamento Diário por Branch / História (Brasília)\n\n"
            f"| Dia de Trabalho | Branch Ativa | Ferramentas | Modelos Utilizados | Tempo Ativo | Interações |\n"
            f"| :---: | :---: | :---: | :---: | :---: | :---: |\n"
        )
        if branch_grouped:
            for (d, b) in sorted(branch_grouped.keys(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y")):
                bh = branch_grouped[(d, b)]["hours"]
                bi = branch_grouped[(d, b)]["interactions"]
                tools_used = ", ".join(sorted(branch_grouped[(d, b)]["tools"]))
                models_used = ", ".join(sorted(branch_grouped[(d, b)]["models"]))
                dev_summary_block += f"| {d} | `{b}` | {tools_used} | {models_used} | {format_hours(bh)} | {bi} |\n"
        else:
            dev_summary_block += f"| N/A | Nenhuma | Nenhuma | Nenhum | 0h 00m | 0 |\n"

        blocks.append(dev_summary_block.strip())

    report_str = header + global_summary.strip() + "\n\n---\n\n"
    for b in blocks:
        report_str += b + "\n\n---\n\n"
    return report_str

def show_console_report(username, hostname, masked_id, repo_root, brasilia_now_str, gap, dev_jsonl_path, daily_stats, live_total_hours):
    # Modo console read-only
    print("\033[1;35m" + "="*60 + "\033[0m")
    print(f"\033[1;37m RASTREADOR DE TEMPO: {username}@{hostname} \033[0m")
    print(f"\033[1;90m ID de Anonimato Externo: {masked_id}\033[0m")
    print("\033[1;35m" + "="*60 + "\033[0m")
    print(f" Repositório: \033[94m{repo_root}\033[0m")
    print(f" Data/Hora (Brasília): {brasilia_now_str}")
    print("-"*60)
    print(f" \033[1mMétricas locais compiladas por Ferramenta/Modelo (Gap: {gap} min):\033[0m")

    legacy_hours = 0.0
    tool_model_totals = defaultdict(lambda: defaultdict(float))

    if os.path.exists(dev_jsonl_path):
        try:
            with open(dev_jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    if ev.get("legacy") is True:
                        if ev.get("event_type") == "dev_summary":
                            legacy_hours = ev.get("total_hours", 0.0)
                        elif ev.get("event_type") == "activity_daily":
                            tool_model_totals[ev["tool"]][ev["model"]] += ev["hours"]
        except Exception:
            pass

    for d in daily_stats:
        for t in daily_stats[d]:
            for m in daily_stats[d][t]:
                tool_model_totals[t][m] += daily_stats[d][t][m]["hours"]

    for t in sorted(tool_model_totals.keys()):
        print(f"  [{t}]")
        for m, h in sorted(tool_model_totals[t].items()):
            print(f"   • {m}: \033[92m{format_hours(h)}\033[0m")

    total_combined_hours = legacy_hours + live_total_hours
    print("-"*60)
    print(f" \033[1;93m✔ TOTAL LOCAL COMBINADO ACUMULADO: {format_hours(total_combined_hours)}\033[0m")
    print("\033[1;35m" + "="*60 + "\033[0m")
    print(" Dica: Execute \033[96mmake -f .tracker/Makefile track-time EXPORT=true\033[0m para anexar/atualizar.")
    print("\033[1;35m" + "="*60 + "\033[0m")

def export_markdown_report(events_dir, masked_id, live_events, repo_root):
    # Se for exportar, emite os eventos (preserva legacy, substitui live)
    emit_events(events_dir, masked_id, live_events)

    # Carrega TODOS os eventos de todos os desenvolvedores
    all_compiled_events = load_all_events(events_dir)

    # Renderiza o relatório completo
    report_content = render_report(all_compiled_events)

    # Salva o relatório
    report_path = os.path.join(repo_root, ".tracker", "TEMPO_DE_TRABALHO.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\033[92m✔ Métricas de tempo atualizadas com sucesso no arquivo: {report_path}\033[0m")

def main():
    parser = argparse.ArgumentParser(description="Calculador de tempo de trabalho de IA apartado e seguro.")
    parser.add_argument("--export", action="store_true", help="Se definido, anexa/atualiza o relatório em formato Markdown.")
    parser.add_argument("--gap", type=int, default=45, help="Intervalo máximo em minutos entre comandos para agrupar na mesma sessão.")
    args = parser.parse_args()
    
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    username = getpass.getuser()
    hostname = socket.gethostname()
    masked_id = get_masked_identity(username, hostname)

    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz=tz_br)
    brasilia_now_str = now_br.strftime('%d/%m/%Y %H:%M:%S')

    events_dir = os.path.join(repo_root, ".tracker", EVENTS_DIRNAME)
    manifest = load_manifest(events_dir)
    legacy_boundary = manifest.get("developers", {}).get(masked_id, {}).get("legacy_boundary")

    branch_timeline = build_branch_timeline(repo_root)

    # 1. Coletar eventos live do sistema
    all_raw_events = collect_events(repo_root)

    # 2. Computar sessões e pings
    sessions, live_pings = compute_sessions(all_raw_events, args.gap, legacy_boundary, branch_timeline)

    # 3. Agregar sessões do período live
    daily_stats, branch_stats, live_total_hours = aggregate_sessions(sessions)

    # 4. Construir eventos live estruturados
    live_events = build_live_events(daily_stats, branch_stats, masked_id)

    if args.export:
        export_markdown_report(events_dir, masked_id, live_events, repo_root)
    else:
        dev_jsonl_path = os.path.join(events_dir, f"dev-{masked_id}.jsonl" if not masked_id.startswith("dev-") else f"{masked_id}.jsonl")
        show_console_report(username, hostname, masked_id, repo_root, brasilia_now_str, args.gap, dev_jsonl_path, daily_stats, live_total_hours)

if __name__ == "__main__":
    main()

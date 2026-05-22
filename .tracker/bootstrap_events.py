#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import sys
from datetime import datetime, timedelta, timezone

def parse_hours_from_str(h_str):
    m_h = re.search(r'(\d+)\s*h', h_str)
    m_m = re.search(r'(\d+)\s*m', h_str)
    hours = 0.0
    if m_h:
        hours += float(m_h.group(1))
    if m_m:
        hours += float(m_m.group(2) if len(m_m.groups()) > 1 else m_m.group(1)) / 60.0
    return round(hours, 4)

def date_to_iso(d_str):
    # "DD/MM/YYYY" -> "YYYY-MM-DD"
    parts = d_str.strip().split('/')
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str

def datetime_to_iso(dt_str):
    # "DD/MM/YYYY HH:MM:SS" -> "YYYY-MM-DDTHH:MM:SS"
    parts = dt_str.strip().split()
    if len(parts) == 2:
        d_iso = date_to_iso(parts[0])
        return f"{d_iso}T{parts[1]}"
    return dt_str

def main():
    tracker_dir = os.path.dirname(os.path.abspath(__file__))
    events_dir = os.path.join(tracker_dir, "events")
    manifest_path = os.path.join(events_dir, "manifest.json")
    report_path = os.path.join(tracker_dir, "TEMPO_DE_TRABALHO.md")

    # Guard de idempotência
    if os.path.exists(events_dir):
        # Verificar se manifest.json ou qualquer arquivo jsonl com legacy: true existe
        if os.path.exists(manifest_path):
            print("Idempotency guard: manifest.json already exists. Aborting bootstrap.")
            sys.exit(0)
        
        jsonl_files = [f for f in os.listdir(events_dir) if f.endswith(".jsonl")]
        for jf in jsonl_files:
            jf_path = os.path.join(events_dir, jf)
            with open(jf_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        if json.loads(line).get("legacy") is True:
                            print(f"Idempotency guard: legacy events found in {jf}. Aborting bootstrap.")
                            sys.exit(0)
                    except (json.JSONDecodeError, Exception):
                        pass

    if not os.path.exists(events_dir):
        os.makedirs(events_dir)

    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found.")
        sys.exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split contents by ---
    parts = re.split(r'\n\s*---\s*\n', content)
    
    developers_manifest = {}
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz=tz_br)
    generated_at_str = now_br.isoformat()

    for part in parts:
        part_str = part.strip()
        if not part_str or part_str.startswith("# Registro de Tempo") or part_str.startswith("## 📊 Resumo Geral"):
            continue
        
        # Match dev block
        dev_match = re.match(r'## 👤 Desenvolvedor:\s+`([^`]+)`', part_str)
        if not dev_match:
            continue
        
        dev_id = dev_match.group(1).strip()
        
        # Parse last updated
        lu_match = re.search(r'\*\s*\*\*Última Atualização:\*\*\s*(.*?)\s*(?:\(|$)', part_str)
        if not lu_match:
            print(f"Warning: Could not parse last updated for dev {dev_id}")
            continue
        last_updated_str = lu_match.group(1).strip()
        legacy_boundary = datetime_to_iso(last_updated_str)
        
        # Parse combined hours
        ch_match = re.search(r'\*\s*\*\*Tempo Ativo Combinado \(IA\):\*\*\s*\*\*([^*]+)\*\*', part_str)
        total_hours = parse_hours_from_str(ch_match.group(1)) if ch_match else 0.0
        
        # Parse total interactions and sessions
        ti_match = re.search(r'\*\s*\*\*Total de Interações:\*\*\s*\*\*(\d+)\s+comandos\*\*\s+em\s+(\d+)\s+sessões', part_str)
        total_interactions = int(ti_match.group(1)) if ti_match else 0
        total_sessions = int(ti_match.group(2)) if ti_match else 0

        developers_manifest[dev_id] = {
            "legacy_boundary": legacy_boundary
        }

        # Parse Tabela 1: Daily Stats
        daily_events = []
        t1_start = part_str.find("### 🗓️ Detalhamento Diário das Horas (Brasília)")
        if t1_start != -1:
            t2_start = part_str.find("### 🌿 Detalhamento Diário por Branch / História (Brasília)", t1_start)
            t1_chunk = part_str[t1_start:t2_start] if t2_start != -1 else part_str[t1_start:]
            
            lines = t1_chunk.strip().split('\n')
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped.startswith('|') or "Dia de Trabalho" in line_stripped or ":---:" in line_stripped:
                    continue
                cols = [c.strip() for c in line_stripped.split('|')[1:-1]]
                if len(cols) >= 6:
                    date_val = date_to_iso(cols[0])
                    tool_val = cols[1].replace('**', '').strip()
                    model_val = cols[2].strip()
                    hours_val = parse_hours_from_str(cols[3])
                    sessions_val = int(cols[4])
                    interactions_val = int(cols[5])

                    # Relabel Antigravity model only in daily events
                    raw_model = model_val
                    model_confidence = "confirmado"
                    if tool_val == "Antigravity":
                        model_val = "Indeterminado (pré-migração)"
                        model_confidence = "indeterminado"

                    daily_events.append({
                        "event_type": "activity_daily",
                        "schema_version": 1,
                        "developer": dev_id,
                        "date": date_val,
                        "tool": tool_val,
                        "model": model_val,
                        "raw_model": raw_model,
                        "model_confidence": model_confidence,
                        "hours": hours_val,
                        "sessions": sessions_val,
                        "interactions": interactions_val,
                        "legacy": True,
                        "generated_at": generated_at_str
                    })

        # Parse Tabela 2: Branch Stats
        branch_events = []
        t2_start = part_str.find("### 🌿 Detalhamento Diário por Branch / História (Brasília)")
        if t2_start != -1:
            t2_chunk = part_str[t2_start:]
            lines = t2_chunk.strip().split('\n')
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped.startswith('|') or "Dia de Trabalho" in line_stripped or ":---:" in line_stripped:
                    continue
                cols = [c.strip() for c in line_stripped.split('|')[1:-1]]
                if len(cols) >= 6:
                    date_val = date_to_iso(cols[0])
                    branch_val = cols[1].replace('`', '').strip()
                    tools_list = [t.strip() for t in cols[2].split(',')]
                    models_list = [m.strip() for m in cols[3].split(',')]
                    hours_val = parse_hours_from_str(cols[4])
                    interactions_val = int(cols[5])

                    branch_events.append({
                        "event_type": "activity_branch",
                        "schema_version": 1,
                        "developer": dev_id,
                        "date": date_val,
                        "branch": branch_val,
                        "tools": tools_list,
                        "models": models_list,
                        "hours": hours_val,
                        "interactions": interactions_val,
                        "legacy": True,
                        "generated_at": generated_at_str
                    })

        # Generate dev_summary event
        summary_event = {
            "event_type": "dev_summary",
            "schema_version": 1,
            "developer": dev_id,
            "scope": "legacy",
            "total_hours": total_hours,
            "total_interactions": total_interactions,
            "total_sessions": total_sessions,
            "last_updated": last_updated_str,
            "legacy": True,
            "generated_at": generated_at_str
        }

        # Write dev jsonl file
        dev_jsonl_path = os.path.join(events_dir, f"dev-{dev_id}.jsonl" if not dev_id.startswith("dev-") else f"{dev_id}.jsonl")
        with open(dev_jsonl_path, "w", encoding="utf-8") as dev_f:
            # Write dev_summary first
            dev_f.write(json.dumps(summary_event, ensure_ascii=False) + "\n")
            # Write daily events
            for ev in daily_events:
                dev_f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            # Write branch events
            for ev in branch_events:
                dev_f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        
        print(f"Processed dev {dev_id}: {len(daily_events)} daily events, {len(branch_events)} branch events.")

    # Write manifest.json
    manifest_data = {
        "schema_version": 1,
        "developers": developers_manifest
    }
    with open(manifest_path, "w", encoding="utf-8") as m_f:
        json.dump(manifest_data, m_f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated manifest.json at {manifest_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import json
import shutil
import tempfile
import re
from datetime import datetime, timedelta, timezone

import importlib.util
spec = importlib.util.spec_from_file_location("work_tracker", os.path.join(os.path.dirname(os.path.abspath(__file__)), "work-tracker.py"))
work_tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(work_tracker)

class TestWorkTracker(unittest.TestCase):

    def test_normalize_model_name(self):
        self.assertEqual(work_tracker.normalize_model_name("gemini-3.5-pro"), "Gemini 3.5 Pro")
        self.assertEqual(work_tracker.normalize_model_name("claude-3-5-sonnet-20241022"), "Claude 3.5 Sonnet")
        self.assertEqual(work_tracker.normalize_model_name("gpt-4o"), "GPT 4o")
        self.assertEqual(work_tracker.normalize_model_name(None), "Unknown")
        self.assertEqual(work_tracker.normalize_model_name(""), "Unknown")
        self.assertEqual(work_tracker.normalize_model_name("none"), "None")

    def test_reject_regex_metacharacters_in_model_name(self):
        self.assertEqual(work_tracker.normalize_model_name("(.*?)(?:\\"), "None")
        self.assertEqual(work_tracker.normalize_model_name("model-with-*"), "None")
        self.assertEqual(work_tracker.normalize_model_name("model-with-?"), "None")
        self.assertEqual(work_tracker.normalize_model_name("model|[another]"), "None")

    def test_parse_transcript_line_with_null_content(self):
        line_null = '{"step_index": 1, "created_at": "2026-05-21T03:10:00Z", "content": null}'
        line_missing = '{"step_index": 2, "created_at": "2026-05-21T03:10:01Z"}'
        
        data_null = json.loads(line_null)
        content_null = data_null.get("content") or ""
        self.assertEqual(content_null, "")
        
        data_missing = json.loads(line_missing)
        content_missing = data_missing.get("content") or ""
        self.assertEqual(content_missing, "")

    def test_model_selection_regex(self):
        pattern = r"changed setting `Model Selection` from (.*?) to (.*?)(?:\. No need|\.?\s*$)"
        
        content = "changed setting `Model Selection` from Gemini 3 Flash to Claude Sonnet 4.6. No need to update settings."
        match = re.search(pattern, content)
        self.assertTrue(match)
        self.assertEqual(match.group(1).strip(), "Gemini 3 Flash")
        self.assertEqual(match.group(2).strip(), "Claude Sonnet 4.6")
        
        content2 = "changed setting `Model Selection` from Gemini 3 Flash to Claude Sonnet 4.6"
        match2 = re.search(pattern, content2)
        self.assertTrue(match2)
        self.assertEqual(match2.group(1).strip(), "Gemini 3 Flash")
        self.assertEqual(match2.group(2).strip(), "Claude Sonnet 4.6")

    def test_compute_sessions_drops_legacy_events(self):
        events = [
            {"tool": "Antigravity", "is_change": False, "is_ping": True, "dt_br": datetime(2026, 5, 20, 10, 0, 0)},
            {"tool": "Antigravity", "is_change": True, "is_ping": False, "model": "Claude Sonnet 4.6", "dt_br": datetime(2026, 5, 20, 12, 0, 0)},
            {"tool": "Antigravity", "is_change": False, "is_ping": True, "dt_br": datetime(2026, 5, 20, 14, 0, 0)},
            {"tool": "Antigravity", "is_change": False, "is_ping": True, "dt_br": datetime(2026, 5, 20, 14, 10, 0)},
        ]
        
        legacy_boundary = "2026-05-20T13:00:00"
        branch_timeline = []
        
        sessions, pings = work_tracker.compute_sessions(events, 45, legacy_boundary, branch_timeline)
        
        self.assertEqual(len(pings), 2)
        self.assertEqual(pings[0]["dt_br"], datetime(2026, 5, 20, 14, 0, 0))
        self.assertEqual(pings[0]["active_model"], "Claude Sonnet 4.6")
        
        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sessions[0]), 2)

    def test_aggregate_sessions(self):
        pings = [
            {"tool": "Antigravity", "active_model": "Claude Sonnet 4.6", "dt_br": datetime(2026, 5, 20, 14, 0, 0), "branch": "main"},
            {"tool": "Antigravity", "active_model": "Claude Sonnet 4.6", "dt_br": datetime(2026, 5, 20, 14, 10, 0), "branch": "main"},
        ]
        sessions = [pings]
        
        daily_stats, branch_stats, total_hours = work_tracker.aggregate_sessions(sessions)
        
        self.assertEqual(total_hours, 0.25)
        self.assertEqual(daily_stats["20/05/2026"]["Antigravity"]["Claude Sonnet 4.6"]["hours"], 0.25)
        self.assertEqual(daily_stats["20/05/2026"]["Antigravity"]["Claude Sonnet 4.6"]["sessions"], 1)
        self.assertEqual(daily_stats["20/05/2026"]["Antigravity"]["Claude Sonnet 4.6"]["interactions"], 2)
        
        self.assertEqual(branch_stats["20/05/2026"]["main"]["Antigravity"]["Claude Sonnet 4.6"]["hours"], 0.25)
        self.assertEqual(branch_stats["20/05/2026"]["main"]["Antigravity"]["Claude Sonnet 4.6"]["sessions"], 1)
        self.assertEqual(branch_stats["20/05/2026"]["main"]["Antigravity"]["Claude Sonnet 4.6"]["interactions"], 2)

    def test_emit_events_preserves_legacy_overwrites_live(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dev_id = "dev-test"
            file_name = f"{dev_id}.jsonl"
            file_path = os.path.join(temp_dir, file_name)
            
            legacy_ev = {
                "event_type": "activity_daily",
                "schema_version": 1,
                "developer": dev_id,
                "date": "2026-05-19",
                "tool": "Antigravity",
                "model": "Indeterminado (pré-migração)",
                "hours": 1.5,
                "sessions": 1,
                "interactions": 10,
                "legacy": True,
                "generated_at": "2026-05-20T00:00:00-03:00"
            }
            
            old_live_ev = {
                "event_type": "activity_daily",
                "schema_version": 1,
                "developer": dev_id,
                "date": "2026-05-20",
                "tool": "Antigravity",
                "model": "Claude Sonnet 4.6",
                "hours": 0.5,
                "sessions": 1,
                "interactions": 5,
                "legacy": False,
                "generated_at": "2026-05-20T00:00:00-03:00"
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(legacy_ev) + "\n")
                f.write(json.dumps(old_live_ev) + "\n")
                
            new_live_ev = {
                "event_type": "activity_daily",
                "schema_version": 1,
                "developer": dev_id,
                "date": "2026-05-21",
                "tool": "Antigravity",
                "model": "Gemini 3 Flash",
                "hours": 2.0,
                "sessions": 2,
                "interactions": 20,
                "legacy": False,
                "generated_at": "2026-05-21T00:00:00-03:00"
            }
            
            work_tracker.emit_events(temp_dir, dev_id, [new_live_ev])
            
            output_events = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    output_events.append(json.loads(line.strip()))
                    
            self.assertEqual(len(output_events), 3)
            self.assertTrue(output_events[0]["legacy"])
            self.assertEqual(output_events[0]["date"], "2026-05-19")
            
            self.assertEqual(output_events[1]["event_type"], "dev_summary")
            self.assertEqual(output_events[1]["scope"], "live")
            self.assertEqual(output_events[1]["total_hours"], 2.0)
            
            self.assertFalse(output_events[2]["legacy"])
            self.assertEqual(output_events[2]["date"], "2026-05-21")
            self.assertEqual(output_events[2]["model"], "Gemini 3 Flash")
            
        finally:
            shutil.rmtree(temp_dir)

class TestTokenTracking(unittest.TestCase):

    def test_format_tokens_pt(self):
        self.assertEqual(work_tracker.format_tokens_pt(0), "0")
        self.assertEqual(work_tracker.format_tokens_pt(500), "500")
        self.assertEqual(work_tracker.format_tokens_pt(1234), "1.234")
        self.assertEqual(work_tracker.format_tokens_pt(1234567), "1.234.567")
        self.assertEqual(work_tracker.format_tokens_pt(142500), "142.500")

    def test_format_tokens_abbreviated(self):
        self.assertEqual(work_tracker.format_tokens_abbreviated(0), "0")
        self.assertEqual(work_tracker.format_tokens_abbreviated(500), "500")
        self.assertEqual(work_tracker.format_tokens_abbreviated(1500), "1k")
        self.assertEqual(work_tracker.format_tokens_abbreviated(123000), "123k")
        self.assertEqual(work_tracker.format_tokens_abbreviated(1200000), "1.2M")
        self.assertEqual(work_tracker.format_tokens_abbreviated(312000), "312k")

    def test_aggregate_sessions_accumulates_tokens(self):
        pings = [
            {
                "tool": "Claude Code", "active_model": "Claude Sonnet 4.6",
                "dt_br": datetime(2026, 5, 20, 14, 0, 0), "branch": "main",
                "input_tokens": 100, "output_tokens": 50,
                "cache_creation_input_tokens": 10, "cache_read_input_tokens": 20,
            },
            {
                "tool": "Claude Code", "active_model": "Claude Sonnet 4.6",
                "dt_br": datetime(2026, 5, 20, 14, 10, 0), "branch": "main",
                "input_tokens": 200, "output_tokens": 80,
                "cache_creation_input_tokens": 0, "cache_read_input_tokens": 5,
            },
        ]
        sessions = [pings]

        daily_stats, branch_stats, total_hours = work_tracker.aggregate_sessions(sessions)

        stats = daily_stats["20/05/2026"]["Claude Code"]["Claude Sonnet 4.6"]
        self.assertEqual(stats["input_tokens"], 300)
        self.assertEqual(stats["output_tokens"], 130)
        self.assertEqual(stats["cache_creation_input_tokens"], 10)
        self.assertEqual(stats["cache_read_input_tokens"], 25)

        b_stats = branch_stats["20/05/2026"]["main"]["Claude Code"]["Claude Sonnet 4.6"]
        self.assertEqual(b_stats["input_tokens"], 300)
        self.assertEqual(b_stats["output_tokens"], 130)

    def test_aggregate_sessions_tokens_fallback_for_antigravity(self):
        pings = [
            {
                "tool": "Antigravity", "active_model": "Gemini 3.1 Pro",
                "dt_br": datetime(2026, 5, 20, 14, 0, 0), "branch": "main",
            },
            {
                "tool": "Antigravity", "active_model": "Gemini 3.1 Pro",
                "dt_br": datetime(2026, 5, 20, 14, 10, 0), "branch": "main",
            },
        ]
        sessions = [pings]

        daily_stats, branch_stats, _ = work_tracker.aggregate_sessions(sessions)

        stats = daily_stats["20/05/2026"]["Antigravity"]["Gemini 3.1 Pro"]
        self.assertEqual(stats.get("input_tokens", 0), 0)
        self.assertEqual(stats.get("output_tokens", 0), 0)
        self.assertEqual(stats.get("cache_creation_input_tokens", 0), 0)
        self.assertEqual(stats.get("cache_read_input_tokens", 0), 0)

    def test_build_live_events_propagates_tokens(self):
        daily_stats = {
            "25/05/2026": {
                "Claude Code": {
                    "Claude Sonnet 4.6": {
                        "hours": 0.5, "sessions": 1, "interactions": 5,
                        "input_tokens": 1000, "output_tokens": 200,
                        "cache_creation_input_tokens": 50, "cache_read_input_tokens": 100,
                    }
                }
            }
        }
        branch_stats = {
            "25/05/2026": {
                "main": {
                    "Claude Code": {
                        "Claude Sonnet 4.6": {
                            "hours": 0.5, "sessions": 1, "interactions": 5,
                            "input_tokens": 1000, "output_tokens": 200,
                            "cache_creation_input_tokens": 50, "cache_read_input_tokens": 100,
                        }
                    }
                }
            }
        }

        events = work_tracker.build_live_events(daily_stats, branch_stats, "dev-test")

        daily_ev = next(e for e in events if e["event_type"] == "activity_daily")
        self.assertEqual(daily_ev["input_tokens"], 1000)
        self.assertEqual(daily_ev["output_tokens"], 200)
        self.assertEqual(daily_ev["cache_creation_input_tokens"], 50)
        self.assertEqual(daily_ev["cache_read_input_tokens"], 100)

        branch_ev = next(e for e in events if e["event_type"] == "activity_branch")
        self.assertEqual(branch_ev["input_tokens"], 1000)
        self.assertEqual(branch_ev["output_tokens"], 200)
        self.assertEqual(branch_ev["cache_creation_input_tokens"], 50)
        self.assertEqual(branch_ev["cache_read_input_tokens"], 100)

    def test_emit_events_includes_token_totals_in_summary(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dev_id = "dev-tokentest"
            live_events = [
                {
                    "event_type": "activity_daily",
                    "schema_version": 1,
                    "developer": dev_id,
                    "date": "2026-05-25",
                    "tool": "Claude Code",
                    "model": "Claude Sonnet 4.6",
                    "raw_model": "Claude Sonnet 4.6",
                    "model_confidence": "confirmado",
                    "hours": 0.5,
                    "sessions": 1,
                    "interactions": 5,
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "cache_creation_input_tokens": 50,
                    "cache_read_input_tokens": 100,
                    "legacy": False,
                    "generated_at": "2026-05-25T10:00:00-03:00",
                }
            ]

            work_tracker.emit_events(temp_dir, dev_id, live_events)

            file_path = os.path.join(temp_dir, f"{dev_id}.jsonl")
            events_out = []
            with open(file_path, "r") as f:
                for line in f:
                    events_out.append(json.loads(line.strip()))

            summary = next(e for e in events_out if e["event_type"] == "dev_summary")
            self.assertEqual(summary["total_input_tokens"], 1000)
            self.assertEqual(summary["total_output_tokens"], 200)
            self.assertEqual(summary["total_cache_creation_input_tokens"], 50)
            self.assertEqual(summary["total_cache_read_input_tokens"], 100)
        finally:
            shutil.rmtree(temp_dir)

    def test_analyze_claude_code_reads_usage(self):
        temp_repo = tempfile.mkdtemp()
        project_dir_name = re.sub(r'[^a-zA-Z0-9]', '-', temp_repo)
        claude_dir = os.path.expanduser(f"~/.claude/projects/{project_dir_name}")
        os.makedirs(claude_dir, exist_ok=True)
        try:
            test_lines = [
                json.dumps({
                    "type": "user",
                    "timestamp": "2026-05-25T10:00:00Z",
                    "message": {"role": "user", "content": "hello"},
                }),
                json.dumps({
                    "type": "assistant",
                    "timestamp": "2026-05-25T10:00:10Z",
                    "message": {
                        "role": "assistant",
                        "model": "claude-sonnet-4-6-20250514",
                        "usage": {
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "cache_creation_input_tokens": 10,
                            "cache_read_input_tokens": 20,
                        },
                    },
                }),
            ]
            jsonl_path = os.path.join(claude_dir, "session-001.jsonl")
            with open(jsonl_path, "w") as f:
                f.write("\n".join(test_lines))

            events, num_files, total_events = work_tracker.analyze_claude_code(temp_repo)

            self.assertEqual(len(events), 2)
            assistant_events = [e for e in events if e.get("input_tokens", 0) > 0]
            self.assertEqual(len(assistant_events), 1)
            self.assertEqual(assistant_events[0]["input_tokens"], 100)
            self.assertEqual(assistant_events[0]["output_tokens"], 50)
            self.assertEqual(assistant_events[0]["cache_creation_input_tokens"], 10)
            self.assertEqual(assistant_events[0]["cache_read_input_tokens"], 20)

            user_events = [e for e in events if e.get("input_tokens", 0) == 0]
            self.assertGreaterEqual(len(user_events), 1)
        finally:
            shutil.rmtree(claude_dir, ignore_errors=True)
            shutil.rmtree(temp_repo, ignore_errors=True)

    def test_render_report_handles_events_without_tokens(self):
        all_events = [
            {
                "event_type": "dev_summary",
                "developer": "dev-aabbccdd",
                "scope": "live",
                "total_hours": 0.5,
                "total_interactions": 5,
                "total_sessions": 1,
                "last_active_date": "25/05/2026",
                "legacy": False,
                "generated_at": "2026-05-25T10:00:00-03:00",
            },
            {
                "event_type": "activity_daily",
                "developer": "dev-aabbccdd",
                "date": "2026-05-25",
                "tool": "Claude Code",
                "model": "Claude Sonnet 4.6",
                "hours": 0.5,
                "sessions": 1,
                "interactions": 5,
                "legacy": False,
            },
            {
                "event_type": "activity_branch",
                "developer": "dev-aabbccdd",
                "date": "2026-05-25",
                "branch": "main",
                "tools": ["Claude Code"],
                "models": ["Claude Sonnet 4.6"],
                "hours": 0.5,
                "interactions": 5,
                "legacy": False,
            },
        ]

        report = work_tracker.render_report(all_events)
        self.assertIsInstance(report, str)
        self.assertIn("dev-aabbccdd", report)


class TestExportFormats(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = self.temp_dir
        # Criamos o subdiretório .tracker dentro do diretório temporário para simular a estrutura real
        self.tracker_dir = os.path.join(self.temp_dir, ".tracker")
        os.makedirs(self.tracker_dir, exist_ok=True)
        self.events_dir = os.path.join(self.tracker_dir, "events")
        os.makedirs(self.events_dir, exist_ok=True)
        self.dev_id = "dev-testexport"
        
        # Cria alguns eventos mock de entrada
        self.live_events = [
            {
                "event_type": "activity_daily",
                "schema_version": 1,
                "developer": self.dev_id,
                "date": "2026-05-25",
                "tool": "Claude Code",
                "model": "Claude Sonnet 4.6",
                "raw_model": "Claude Sonnet 4.6",
                "model_confidence": "confirmado",
                "hours": 1.25,
                "sessions": 1,
                "interactions": 10,
                "input_tokens": 1500,
                "output_tokens": 300,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 50,
                "legacy": False,
                "generated_at": "2026-05-25T10:00:00-03:00"
            },
            {
                "event_type": "activity_branch",
                "schema_version": 1,
                "developer": self.dev_id,
                "date": "2026-05-25",
                "branch": "feature-test",
                "tools": ["Claude Code"],
                "models": ["Claude Sonnet 4.6"],
                "hours": 1.25,
                "interactions": 10,
                "input_tokens": 1500,
                "output_tokens": 300,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 50,
                "legacy": False,
                "generated_at": "2026-05-25T10:00:00-03:00"
            }
        ]

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_export_json_format(self):
        work_tracker.export_json_report(self.events_dir, self.dev_id, self.live_events, self.repo_root)

        json_path = os.path.join(self.tracker_dir, "TEMPO_DE_TRABALHO.json")
        self.assertTrue(os.path.exists(json_path))

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        daily_ev = next((e for e in data if e.get("event_type") == "activity_daily"), None)
        self.assertIsNotNone(daily_ev, "Evento activity_daily não encontrado no JSON")
        self.assertEqual(daily_ev["developer"], self.dev_id)
        self.assertEqual(daily_ev["hours"], 1.25)
        self.assertEqual(daily_ev["model"], "Claude Sonnet 4.6")

        # Verifica tipos dos campos numéricos
        self.assertIsInstance(daily_ev["hours"], float)
        self.assertIsInstance(daily_ev["sessions"], int)
        self.assertIsInstance(daily_ev["interactions"], int)
        self.assertIsInstance(daily_ev["input_tokens"], int)
        self.assertIsInstance(daily_ev["output_tokens"], int)
        self.assertIsInstance(daily_ev["event_type"], str)

    def test_export_csv_format(self):
        work_tracker.export_csv_report(self.events_dir, self.dev_id, self.live_events, self.repo_root)

        csv_path = os.path.join(self.tracker_dir, "TEMPO_DE_TRABALHO.csv")
        self.assertTrue(os.path.exists(csv_path))

        import csv as csv_module
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv_module.reader(f)
            headers = next(reader)
            rows = list(reader)

        self.assertIn("developer", headers)
        self.assertIn("event_type", headers)
        self.assertIn("hours", headers)
        self.assertGreater(len(rows), 0)

        for row in rows:
            self.assertEqual(len(row), len(headers))

        # Verifica valores da linha activity_daily
        def col(row, name):
            return row[headers.index(name)]

        daily_row = next((r for r in rows if col(r, "event_type") == "activity_daily"), None)
        self.assertIsNotNone(daily_row, "Linha activity_daily não encontrada no CSV")
        self.assertEqual(col(daily_row, "developer"), self.dev_id)
        self.assertEqual(col(daily_row, "hours"), "1.25")
        self.assertEqual(col(daily_row, "tool"), "Claude Code")
        self.assertEqual(col(daily_row, "model"), "Claude Sonnet 4.6")
        self.assertEqual(col(daily_row, "date"), "2026-05-25")
        self.assertEqual(col(daily_row, "branch"), "")
        self.assertEqual(col(daily_row, "scope"), "")

        # Verifica valores da linha activity_branch
        branch_row = next((r for r in rows if col(r, "event_type") == "activity_branch"), None)
        self.assertIsNotNone(branch_row, "Linha activity_branch não encontrada no CSV")
        self.assertEqual(col(branch_row, "developer"), self.dev_id)
        self.assertEqual(col(branch_row, "branch"), "feature-test")
        self.assertEqual(col(branch_row, "sessions"), "")
        self.assertEqual(col(branch_row, "date"), "2026-05-25")

    def test_export_csv_format_comma_in_field(self):
        # Garante que campos com vírgula (multi-tool/model) são escapados corretamente (RFC 4180)
        # e que o csv.reader ainda lê a linha com o número correto de colunas.
        multi_tool_events = [
            {
                "event_type": "activity_branch",
                "schema_version": 1,
                "developer": self.dev_id,
                "date": "2026-05-25",
                "branch": "feature-multi",
                "tools": ["Antigravity", "Claude Code"],
                "models": ["Claude Haiku 4.5", "Claude Sonnet 4.6"],
                "hours": 2.0,
                "interactions": 5,
                "input_tokens": 800,
                "output_tokens": 200,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "legacy": False,
                "generated_at": "2026-05-25T12:00:00-03:00",
            }
        ]
        work_tracker.export_csv_report(self.events_dir, self.dev_id, multi_tool_events, self.repo_root)

        csv_path = os.path.join(self.tracker_dir, "TEMPO_DE_TRABALHO.csv")
        import csv as csv_module
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv_module.reader(f)
            headers = next(reader)
            rows = list(reader)

        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertEqual(len(row), len(headers), f"Linha com número errado de colunas: {row}")

        # Verifica que o campo tool contém os dois tools separados por vírgula
        tool_idx = headers.index("tool")
        branch_row = next((r for r in rows if r[headers.index("event_type")] == "activity_branch"), None)
        self.assertIsNotNone(branch_row)
        self.assertIn(",", branch_row[tool_idx])

    def test_export_formats_atomic_write(self):
        json_path = os.path.join(self.tracker_dir, "TEMPO_DE_TRABALHO.json")

        with open(json_path, "w", encoding="utf-8") as f:
            f.write("dados antigos")

        work_tracker.export_json_report(self.events_dir, self.dev_id, self.live_events, self.repo_root)

        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotEqual(content, "dados antigos")
        self.assertTrue(content.startswith("["))

    def test_export_csv_atomic_write(self):
        csv_path = os.path.join(self.tracker_dir, "TEMPO_DE_TRABALHO.csv")

        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("dados antigos")

        work_tracker.export_csv_report(self.events_dir, self.dev_id, self.live_events, self.repo_root)

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotEqual(content, "dados antigos")
        self.assertTrue(content.startswith("developer,"))

    def test_argparse_rejects_invalid_format(self):
        import subprocess
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work-tracker.py")
        result = subprocess.run(
            [sys.executable, script, "--export", "--format", "invalido"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0, "argparse deveria rejeitar --format inválido com exit code != 0")
        self.assertIn("invalido", result.stderr)


if __name__ == "__main__":
    unittest.main()

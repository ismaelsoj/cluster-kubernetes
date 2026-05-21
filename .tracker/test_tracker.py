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

if __name__ == "__main__":
    unittest.main()

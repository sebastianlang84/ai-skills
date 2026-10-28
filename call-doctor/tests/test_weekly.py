#!/usr/bin/env python3
"""Tests for weekly.py on synthetic transcripts: python3 tests/test_weekly.py"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import weekly  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)
SINCE = NOW - dt.timedelta(days=7)


def ts(days_ago=0):
    return (NOW - dt.timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")


def user(text, days_ago=0, **kw):
    kw.setdefault("entrypoint", "claude-desktop")
    return {"type": "user", "timestamp": ts(days_ago), "cwd": "/x", "message": {"content": text}, **kw}


def asst(text):
    return {"type": "assistant", "timestamp": ts(), "message": {"content": [{"type": "text", "text": text}]}}


class Sessions(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def write(self, name, lines):
        p = os.path.join(self.d, name)
        with open(p, "w") as f:
            f.write("\n".join(json.dumps(x) for x in lines) + "\n")
        return p

    def test_single_prompt_run_is_not_human(self):
        p = self.write("a.jsonl", [user("das ist falsch, prüf es"), asst("ok")])
        self.assertIsNone(weekly.load(p, "claude", SINCE, set()))

    def test_sdk_run_with_several_prompts_is_not_human(self):
        p = self.write("a.jsonl", [user("mach X", entrypoint="sdk-cli"), asst("a"),
                                   user("nein, falsch", entrypoint="sdk-cli"), asst("b")])
        self.assertIsNone(weekly.load(p, "claude", SINCE, set()))

    def test_injected_messages_neither_count_nor_hit(self):
        p = self.write("a.jsonl", [user("mach X"), asst("a"),
                                   user("<task-notification>nein, falsch</task-notification>"), asst("b"),
                                   user("<system-reminder>falsch</system-reminder>"), asst("c")])
        self.assertIsNone(weekly.load(p, "claude", SINCE, set()))

    def test_correction_and_interruption_hit_only_inside_window(self):
        p = self.write("a.jsonl", [user("nein, das war falsch", days_ago=9), asst("a"), user("mach X"), asst("b"),
                                   user("nein, hab ich doch gesagt"), asst("c"), user("[Request interrupted by user]")])
        s = weekly.load(p, "claude", SINCE, set())
        self.assertEqual([(n, k) for n, k, _ in s.hits], [(5, "korrektur"), (7, "abbruch")])

    def test_forked_transcript_repeats_no_hit(self):
        lines = [user("mach X"), asst("a"), user("schon wieder falsch"), asst("b")]
        seen = set()
        self.assertIsNotNone(weekly.load(self.write("a.jsonl", lines), "claude", SINCE, seen))
        self.assertIsNone(weekly.load(self.write("b.jsonl", lines), "claude", SINCE, seen))

    def test_unresolvable_reference_demotes_finding(self):
        s = weekly.load(self.write("a.jsonl", [user("mach X"), asst("a"), user("nein, falsch"), asst("b"),
                                               user("<system-reminder>x</system-reminder>"), asst("c")]),
                        "claude", SINCE, set())
        s.key = "S1"
        weekly.evidence([s])
        data = {"befunde": [{"titel": "t", "staerke": "stark", "belege": ["S1:L99", "S7:L3", "S1:L5"], "weg": "ticket"},
                            {"titel": "u", "staerke": "mittel", "belege": ["S1:L3"], "weg": "ticket"}]}
        text, found = weekly.render("2026-10-29", "2026-10-22", [s], [{"vendor": "claude", "keys": {"S1": s},
                                                                       "data": data}], [])
        self.assertEqual([f["staerke"] for f in found], ["schwach", "mittel"])
        self.assertIn("## Starke Belege (0)", text)
        self.assertIn("Nicht im Beleg auffindbar: S1:L99, S7:L3, S1:L5", text)

    def test_answer_without_required_fields_is_refused(self):
        for bad in ("```json\n{}\n```", '```json\n{"befunde": [{"titel": "t"}], "modellverhalten": []}\n```'):
            with self.assertRaises(ValueError):
                weekly.parse_answer(bad)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for collect.py on synthetic transcripts: python3 tests/test_collect.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

COLLECT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "collect.py")


def run(lines, *args):
    d = tempfile.mkdtemp()
    src, out = os.path.join(d, "s.jsonl"), os.path.join(d, "e.md")
    with open(src, "w") as f:
        f.write("\n".join(json.dumps(x) for x in lines) + "\n")
    env = {k: v for k, v in os.environ.items() if k not in ("CODEX_THREAD_ID", "CLAUDE_CODE_SESSION_ID")}
    p = subprocess.run([sys.executable, COLLECT, "--session", src, *args, out],
                       capture_output=True, text=True, env=env, check=True)
    with open(out) as f:
        doc = f.read()
    shutil.rmtree(d)
    return p.stdout, doc


def user(text, **kw):
    return {"type": "user", "message": {"content": text}, **kw}


def result(text):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": text}]}}


class Redaction(unittest.TestCase):
    def test_secrets_are_redacted_before_cutting(self):
        long_key = "x" * 490 + " sk-" + "A" * 40
        _, doc = run([user("go"), result("password=hunter2"), result("Authorization: Bearer opaqueVALUE1234567890"),
                      result("API_KEY=abc!def@ghi#jkl"), result(long_key), result("mail me at a.b@example.org"),
                      result('password="alpha beta"'), result("Authorization: Token abcdefg"),
                      result('{"password": "alpha \\"zeta\\" gamma"}')],
                     "--budget", "1")
        for leak in ("hunter2", "opaqueVALUE", "abc!def", "sk-AAAA", "a.b@example.org", "beta", "abcdefg", "zeta", "gamma"):
            self.assertNotIn(leak, doc)


class Structure(unittest.TestCase):
    def test_sidechain_context_is_not_the_patients(self):
        _, doc = run([user("go"), {"type": "attachment", "isSidechain": True, "attachment": {
            "type": "instructions", "files": [{"type": "Project", "path": "/x/AGENTS.md",
                                               "content": "Only child follows this rule"}]}}])
        self.assertNotIn("Only child follows this rule", doc)

    def test_compaction_boundary_names_preserved_lines(self):
        out, doc = run([user("first", uuid="u1"), {"type": "system", "subtype": "compact_boundary",
                        "compactMetadata": {"trigger": "auto", "preTokens": 9, "postTokens": 1,
                                            "preservedMessages": {"uuids": ["u1"]}}}, user("second")])
        self.assertIn("vendor: claude", out)
        self.assertIn("L2 COMPACTION", doc)
        self.assertIn("preserved messages: L1", doc)

    def test_cut_without_omission_is_flagged(self):
        _, doc = run([user("u" * 8100)])
        self.assertIn("EVIDENCE INCOMPLETE: 0 timeline entries omitted, 1 cut", doc)

    def test_cut_context_block_is_flagged(self):
        _, doc = run([{"type": "attachment", "attachment": {"type": "skill_listing", "content": "s" * 32000}}])
        self.assertIn("EVIDENCE INCOMPLETE", doc)

    def test_header_redaction_keeps_next_line(self):
        _, doc = run([result("Authorization: Bearer"), user("INCIDENT_HERE")])
        self.assertIn("L2 USER: INCIDENT_HERE", doc)

    def test_focus_survives_budget_and_omissions_are_marked(self):
        lines = [user("start")] + [result("filler " * 400) for _ in range(200)] + [
            result("x" * 3100 + " herdr server PROOF " * 50 + " DIAGNOSTIC_END")]
        _, doc = run(lines, "--budget", "8", "--focus", f"{len(lines)}-{len(lines)}")
        self.assertIn("EVIDENCE INCOMPLETE", doc)
        self.assertIn("entries omitted]", doc)
        self.assertEqual(doc.count("herdr server PROOF"), 50)
        self.assertIn("DIAGNOSTIC_END", doc)

    def test_codex_rollout(self):
        out, doc = run([{"type": "session_meta", "payload": {"cwd": "/w", "base_instructions": {"text": "base"}}},
                        {"type": "response_item", "payload": {"type": "message", "role": "user",
                                                              "content": [{"type": "input_text", "text": "hello"}]}},
                        {"type": "compacted", "payload": {}}])
        self.assertIn("vendor: codex", out)
        self.assertIn("L2 USER: hello", doc)
        self.assertIn("L3 COMPACTION", doc)


if __name__ == "__main__":
    unittest.main()

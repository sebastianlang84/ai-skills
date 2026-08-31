#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("debate.py")
SPEC = importlib.util.spec_from_file_location("peer_debate_driver", SCRIPT)
assert SPEC and SPEC.loader
debate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(debate)


def agy_json(response="answer\nSTATUS: contested — one point", conversation="conv-1", turns=1):
    return json.dumps({
        "conversation_id": conversation,
        "status": "SUCCESS",
        "response": response,
        "num_turns": turns,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 20,
            "thinking_tokens": 10,
            "cache_read_tokens": 0,
            "total_tokens": 120,
        },
    })


class DebateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        debate.ROOT = Path(self.tmp.name)
        self.run = debate.ROOT / "2026-08-31-test"
        self.run.mkdir()
        (self.run / "transcript.md").write_text("# test\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_rejects_headless_soft_denial(self):
        with self.assertRaisesRegex(debate.Failed, "empty reply"):
            debate.parse_agy_result(
                agy_json(response=""),
                'a tool required the "command" permission and was auto-denied',
                "A",
            )

    def test_parse_rejects_non_object_json(self):
        with self.assertRaisesRegex(debate.Failed, "non-object"):
            debate.parse_agy_result("[]", "", "B")

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/agy")
    @mock.patch.object(debate.subprocess, "run")
    def test_initial_turn_records_conversation_and_usage(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, agy_json(), "")

        reply = debate.turn(self.run.name, "A", "question")

        self.assertTrue(reply.startswith("answer"))
        self.assertEqual(
            (self.run / "conversation-A.txt").read_text(encoding="utf-8"), "conv-1\n"
        )
        argv = run.call_args.args[0]
        self.assertNotIn("--conversation", argv)
        self.assertNotIn("--sandbox", argv)
        self.assertIn("--dangerously-skip-permissions", argv)
        add_dir = argv.index("--add-dir")
        self.assertEqual(Path(argv[add_dir + 1]), self.run / "A")
        transcript = (self.run / "transcript.md").read_text(encoding="utf-8")
        self.assertIn("cli=agy model=gemini-3.7-flash-medium effort=medium", transcript)
        self.assertIn("total=120 cumulative-for-this-side", transcript)

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/agy")
    @mock.patch.object(debate.subprocess, "run")
    def test_later_turn_resumes_same_conversation(self, run, _which):
        (self.run / "conversation-B.txt").write_text("conv-b\n", encoding="utf-8")
        run.return_value = subprocess.CompletedProcess(
            [], 0, agy_json(conversation="conv-b", turns=2), ""
        )

        debate.turn(self.run.name, "B", "reply")

        argv = run.call_args.args[0]
        index = argv.index("--conversation")
        self.assertEqual(argv[index + 1], "conv-b")

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/agy")
    @mock.patch.object(debate.subprocess, "run")
    def test_conversation_fork_is_not_recorded(self, run, _which):
        (self.run / "conversation-A.txt").write_text("conv-old\n", encoding="utf-8")
        before = (self.run / "transcript.md").read_text(encoding="utf-8")
        run.return_value = subprocess.CompletedProcess(
            [], 0, agy_json(conversation="conv-new", turns=2), ""
        )

        with self.assertRaisesRegex(debate.Failed, "but agy returned"):
            debate.turn(self.run.name, "A", "reply")

        self.assertEqual(
            (self.run / "conversation-A.txt").read_text(encoding="utf-8"), "conv-old\n"
        )
        self.assertEqual((self.run / "transcript.md").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()

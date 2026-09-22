#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

    def test_default_selection_uses_medium(self):
        with mock.patch.dict(debate.os.environ, {}, clear=True):
            self.assertEqual(debate.sides_from_env()["A"], {
                "cli": "agy", "model": "gemini-3.8-flash-medium", "effort": "medium"})

    @mock.patch.object(debate.subprocess, "run")
    def test_check_rejects_model_effort_conflict_before_probing(self, run):
        env = {"PEER_DEBATE_MODEL_A": "agy:gemini-3.8-flash-high",
               "PEER_DEBATE_EFFORT_A": "medium"}
        with mock.patch.dict(debate.os.environ, env):
            with self.assertRaisesRegex(debate.Failed, "side A.*conflicts.*medium"):
                debate.cmd_check(None)
        run.assert_not_called()

    @mock.patch.object(debate, "machine_facts", return_value=([], True))
    @mock.patch.object(debate, "turn", return_value="unused")
    def test_init_rejects_conflict_without_creating_run(self, turn, facts):
        question = debate.ROOT / "question.md"
        question.write_text("Question", encoding="utf-8")
        before = set(debate.ROOT.iterdir())
        env = {"PEER_DEBATE_MODEL_B": "agy:gemini-3.8-flash-high",
               "PEER_DEBATE_EFFORT_B": "medium"}
        with mock.patch.dict(debate.os.environ, env):
            with self.assertRaisesRegex(debate.Failed, "side B.*conflicts"):
                debate.cmd_init(argparse.Namespace(slug="invalid", question=str(question)))
        self.assertEqual(set(debate.ROOT.iterdir()), before)

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/agy")
    @mock.patch.object(debate.subprocess, "run")
    def test_nonzero_json_error_is_visible_without_recording(self, run, _which):
        before = (self.run / "transcript.md").read_text()
        run.return_value = subprocess.CompletedProcess(
            [], 1, json.dumps({"error": "invalid model selection: conflicts with effort"}), "")
        with self.assertRaisesRegex(debate.Failed, "invalid model selection"):
            debate.turn(self.run.name, "A", "question")
        self.assertEqual((self.run / "transcript.md").read_text(), before)
        self.assertFalse((self.run / "conversation-A.txt").exists())

    def test_zero_exit_error_retains_diagnostic(self):
        with self.assertRaisesRegex(debate.Failed, "model unavailable"):
            debate.parse_agy_result('{"status":"ERROR","error":{"message":"model unavailable"}}', "", "A")

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
        self.assertIn("cli=agy model=gemini-3.8-flash-medium effort=medium", transcript)
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

    # --- codex transport -------------------------------------------------------------------

    def codex_jsonl(self, text="codex answer\nSTATUS: converged", thread="01a0-thread"):
        events = [
            {"type": "thread.started", "thread_id": thread},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "item_0", "type": "agent_message",
                                                 "text": text}},
            {"type": "turn.completed", "usage": {"input_tokens": 22900,
                                                 "cached_input_tokens": 11008,
                                                 "output_tokens": 6,
                                                 "reasoning_output_tokens": 0}},
        ]
        return "\n".join(json.dumps(e) for e in events) + "\n"

    def test_parse_model_defaults_to_agy_and_rejects_unknown_cli(self):
        self.assertEqual(debate.parse_model("gemini-3.8-flash-high"),
                         ("agy", "gemini-3.8-flash-high"))
        self.assertEqual(debate.parse_model("codex:gpt-5.6-terra"), ("codex", "gpt-5.6-terra"))
        self.assertEqual(debate.parse_model("claude:claude-opus-5-5"), ("claude", "claude-opus-5-5"))
        with self.assertRaisesRegex(debate.Failed, "unknown cli"):
            debate.parse_model("pi:glm")
        with self.assertRaisesRegex(debate.Failed, "no model id"):
            debate.parse_model("codex:")

    def test_parse_codex_reads_last_message_thread_and_usage(self):
        reply, thread, stamp = debate.parse_codex_result(self.codex_jsonl(), "", "B")
        self.assertEqual(reply, "codex answer\nSTATUS: converged")
        self.assertEqual(thread, "01a0-thread")
        self.assertIn("in=22900 cached=11008", stamp)

    def test_parse_codex_refused_model_is_loud(self):
        # Measured on codex-cli 0.152.1: a refused model exits 0 with error + turn.failed.
        stdout = "\n".join(json.dumps(e) for e in [
            {"type": "thread.started", "thread_id": "t"},
            {"type": "turn.started"},
            {"type": "error", "message": "The 'gpt-5.4-terra' model is not supported"},
            {"type": "turn.failed", "error": {"message": "The 'gpt-5.4-terra' model is not supported"}},
        ])
        with self.assertRaisesRegex(debate.Failed, "(?s)empty reply.*not supported"):
            debate.parse_codex_result(stdout, "", "B")

    def _sides(self, b="codex:gpt-5.6-terra"):
        (self.run / "sides.json").write_text(json.dumps({
            "A": {"cli": "agy", "model": "gemini-3.8-flash-high", "effort": "high"},
            "B": {"cli": "codex", "model": b.split(":", 1)[1], "effort": "low"},
        }), encoding="utf-8")

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/codex")
    @mock.patch.object(debate.subprocess, "run")
    def test_codex_initial_turn_runs_exec_without_hooks(self, run, which):
        self._sides()
        run.return_value = subprocess.CompletedProcess([], 0, self.codex_jsonl(), "")

        reply = debate.turn(self.run.name, "B", "question")

        self.assertTrue(reply.startswith("codex answer"))
        which.assert_called_with("codex")
        argv = run.call_args.args[0]
        self.assertEqual(argv[1], "exec")
        self.assertNotIn("resume", argv)
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-5.6-terra")
        self.assertIn("model_reasoning_effort=low", argv)
        self.assertIn("features.hooks=false", argv)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", argv)
        self.assertIn("--json", argv)
        self.assertEqual(Path(argv[argv.index("-C") + 1]), self.run / "B")
        self.assertEqual((self.run / "conversation-B.txt").read_text(encoding="utf-8"),
                         "01a0-thread\n")
        transcript = (self.run / "transcript.md").read_text(encoding="utf-8")
        self.assertIn("cli=codex model=gpt-5.6-terra effort=low", transcript)

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/codex")
    @mock.patch.object(debate.subprocess, "run")
    def test_codex_later_turn_resumes_thread_with_model(self, run, _which):
        self._sides()
        (self.run / "conversation-B.txt").write_text("01a0-thread\n", encoding="utf-8")
        run.return_value = subprocess.CompletedProcess([], 0, self.codex_jsonl(), "")

        debate.turn(self.run.name, "B", "reply")

        argv = run.call_args.args[0]
        self.assertEqual(argv[1:4], ["exec", "resume", "01a0-thread"])
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-5.6-terra")
        # resume rejects these (measured 0.152.1: exit 2 with usage text)
        for flag in ("-C", "--add-dir", "--color"):
            self.assertNotIn(flag, argv)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", argv)

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/agy")
    @mock.patch.object(debate.subprocess, "run")
    def test_sides_json_wins_over_environment(self, run, _which):
        self._sides()
        run.return_value = subprocess.CompletedProcess([], 0, agy_json(), "")
        with mock.patch.dict(debate.os.environ, {"PEER_DEBATE_MODEL_A": "codex:other"}):
            debate.turn(self.run.name, "A", "question")
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-3.8-flash-high")


    @staticmethod
    def claude_json(text="claude answer\nSTATUS: contested — one point", session="sess-a",
                    as_list=True, **result):
        # Shape measured on Claude Code 2.1.280: a list of events ending in `result`.
        event = {"type": "result", "subtype": "success", "is_error": False, "result": text,
                 "session_id": session, "num_turns": 3, "total_cost_usd": 0.12,
                 "usage": {"input_tokens": 40, "cache_read_input_tokens": 38000,
                           "cache_creation_input_tokens": 100, "output_tokens": 900}} | result
        events = [{"type": "system", "subtype": "init", "session_id": session},
                  {"type": "assistant", "message": {"content": []}}, event]
        return json.dumps(events if as_list else event)

    def _claude_sides(self):
        (self.run / "sides.json").write_text(json.dumps({
            "A": {"cli": "claude", "model": "claude-opus-5-5", "effort": "medium"},
            "B": {"cli": "codex", "model": "gpt-6-sol", "effort": "medium"},
        }), encoding="utf-8")

    def test_parse_claude_reads_list_and_object_forms(self):
        for as_list in (True, False):
            reply, session, stamp = debate.parse_claude_result(
                self.claude_json(as_list=as_list), "", "A")
            self.assertEqual((reply.splitlines()[0], session), ("claude answer", "sess-a"))
            self.assertIn("cached=38000", stamp)

    def test_parse_claude_errors_are_loud(self):
        for bad in (self.claude_json(is_error=True), self.claude_json(subtype="error_max_turns"),
                    self.claude_json(text="  "), self.claude_json(session=""),
                    json.dumps([{"type": "assistant"}]), "not json"):
            with self.assertRaises(debate.Failed):
                debate.parse_claude_result(bad, "", "A")

    def test_claude_effort_is_validated(self):
        debate.validate_selection({"cli": "claude", "model": "m", "effort": "xhigh"}, "A")
        with self.assertRaisesRegex(debate.Failed, "claude effort"):
            debate.validate_selection({"cli": "claude", "model": "m", "effort": "ultra"}, "A")

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/claude")
    @mock.patch.object(debate.subprocess, "run")
    def test_claude_initial_turn_then_resume(self, run, which):
        self._claude_sides()
        run.return_value = subprocess.CompletedProcess([], 0, self.claude_json(), "")

        debate.turn(self.run.name, "A", "question")

        which.assert_called_with("claude")
        argv = run.call_args.args[0]
        self.assertEqual(argv[1], "-p")
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-5-5")
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertIn("--dangerously-skip-permissions", argv)
        self.assertNotIn("--resume", argv)
        self.assertEqual(run.call_args.kwargs["cwd"], self.run / "A")
        self.assertEqual((self.run / "conversation-A.txt").read_text(encoding="utf-8"), "sess-a\n")
        self.assertIn("cli=claude model=claude-opus-5-5", (self.run / "transcript.md").read_text())

        debate.turn(self.run.name, "A", "reply")
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--resume") + 1], "sess-a")

    @mock.patch.object(debate.shutil, "which", return_value="/usr/bin/claude")
    @mock.patch.object(debate.subprocess, "run")
    def test_claude_fork_is_not_recorded(self, run, _which):
        self._claude_sides()
        (self.run / "conversation-A.txt").write_text("sess-a\n", encoding="utf-8")
        run.return_value = subprocess.CompletedProcess([], 0, self.claude_json(session="sess-b"), "")
        with self.assertRaisesRegex(debate.Failed, "resumed sess-a"):
            debate.turn(self.run.name, "A", "reply")
        self.assertFalse((self.run / "last-A.md").exists())


if __name__ == "__main__":
    unittest.main()

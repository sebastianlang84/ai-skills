#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).with_name("codex_call.py")
SPEC = importlib.util.spec_from_file_location("codex_call", SCRIPT)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)


def events(*kinds, thread="t-1", answer=True):
    lines = [{"type": "thread.started", "thread_id": thread}]
    if answer:
        lines.append({"type": "item.completed", "item": {"type": "agent_message", "text": "hi"}})
    lines += [{"type": k} if isinstance(k, str) else k for k in kinds]
    return "\n".join(json.dumps(x) for x in lines) + "\n"


class CodexCallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        cc.ROOT = Path(self.tmp.name)
        self.prompt = cc.ROOT / "p.md"
        self.prompt.write_text("review this", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, **kw):
        base = dict(prompt=str(self.prompt), label="t", model="gpt-6-sol", effort="medium",
                    sandbox="read-only", detach=False, cwd=None)
        return argparse.Namespace(**(base | kw))

    def fake_codex(self, stream, rc=0, answer="ANSWER"):
        def run(cmd, **kw):
            if cmd[-1] == "--version":
                return subprocess.CompletedProcess(cmd, 0, "codex-cli 9.9.9\n", "")
            kw["stdout"].write(stream.encode())
            Path(cmd[cmd.index("-o") + 1]).write_text(answer, encoding="utf-8")
            self.calls.append(cmd)
            return subprocess.CompletedProcess(cmd, rc)
        self.calls = []
        return run

    def call(self, parent=None, stream=None, rc=0, **kw):
        call = cc.prepare(self.args(**kw), parent)
        with mock.patch.object(cc.shutil, "which", return_value="/usr/bin/codex"), \
                mock.patch.object(cc.subprocess, "run", side_effect=self.fake_codex(
                    stream if stream is not None else events("turn.completed"), rc)):
            cc.run(call)
        return call, cc.read_meta(call)

    def test_new_pins_flags_and_keeps_the_thread(self):
        call, meta = self.call(cwd=self.tmp.name)
        cmd = self.calls[0]
        self.assertEqual(cmd[:4], ["/usr/bin/codex", "exec", "-C", str(Path(self.tmp.name).resolve())])
        for pin in (["-s", "read-only"], ["-m", "gpt-6-sol"], ["-c", "features.hooks=false"],
                    ["-c", "model_reasoning_effort=medium"]):
            self.assertIn(pin, [cmd[i:i + 2] for i in range(len(cmd) - 1)])
        self.assertIn("--json", cmd)
        self.assertNotIn("--ephemeral", cmd)
        self.assertEqual((meta["rc"], meta["thread_id"], meta["codex_version"]), (0, "t-1", "codex-cli 9.9.9"))

    def test_resume_repeats_model_and_sets_sandbox_by_config(self):
        _, meta = self.call(parent="t-9", stream=events("turn.completed", thread="t-9"))
        cmd = self.calls[0]
        self.assertEqual(cmd[1:4], ["exec", "resume", "t-9"])
        self.assertIn("gpt-6-sol", cmd)
        self.assertIn("sandbox_mode=read-only", cmd)
        for forbidden in ("-s", "-C", "--add-dir", "--color", "--ephemeral"):
            self.assertNotIn(forbidden, cmd)
        self.assertEqual((meta["thread_id"], meta["parent_thread"]), ("t-9", "t-9"))

    def test_failed_turn_with_exit_zero_is_a_failure(self):
        _, meta = self.call(stream=events({"type": "turn.failed", "error": {"message": "model refused"}}))
        self.assertEqual(meta["rc"], 1)
        self.assertEqual(meta["error"], "model refused")

    def test_answer_without_turn_completed_is_a_failure(self):
        _, meta = self.call(stream=events())
        self.assertEqual((meta["rc"], meta["error"]), (1, "no turn.completed event"))

    def test_nonzero_exit_is_a_failure(self):
        _, meta = self.call(rc=2)
        self.assertEqual((meta["rc"], meta["error"]), (1, "codex exited 2"))

    def test_resume_into_another_thread_is_a_failure(self):
        _, meta = self.call(parent="t-9", stream=events("turn.completed", thread="t-other"))
        self.assertEqual((meta["rc"], meta["error"]), (1, "resumed t-9 but codex reported thread t-other"))

    def test_empty_answer_and_missing_thread_are_failures(self):
        call = cc.prepare(self.args(), None)
        with mock.patch.object(cc.shutil, "which", return_value="/usr/bin/codex"), \
                mock.patch.object(cc.subprocess, "run", side_effect=self.fake_codex(
                    events("turn.completed"), answer="  \n")):
            cc.run(call)
        self.assertEqual(cc.read_meta(call)["error"], "empty answer in last.md")
        stream = "\n".join(json.dumps(e) for e in [
            {"type": "item.completed", "item": {"type": "agent_message"}}, {"type": "turn.completed"}])
        _, meta = self.call(stream=stream)
        self.assertEqual(meta["error"], "codex reported no thread id")
        _, meta = self.call(parent="t-9", stream=stream)
        self.assertEqual(meta["error"], "codex reported no thread id")

    def test_every_call_logs_one_line(self):
        self.call()
        self.call(parent="t-1")
        lines = (cc.ROOT / "calls.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["parent_thread"], "t-1")

    def test_wait_distinguishes_running_gone_and_done(self):
        call = cc.prepare(self.args(), None)
        meta = cc.read_meta(call)
        meta["pid"] = cc.os.getpid()
        cc.write_meta(call, meta)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cc.wait(call, 0), cc.STILL_RUNNING)
        (call / "runner.pid").write_text(str(2 ** 22 + 12345))
        (call / "last.md").write_text("half", encoding="utf-8")
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(cc.wait(call, 0), 1)
        self.assertIn("gone without an end state", err.getvalue())
        self.assertIn("partial answer, unconfirmed", err.getvalue())
        (call / "last.md").write_text("verdict", encoding="utf-8")
        cc.write_meta(call, meta | {"rc": 0, "thread_id": "t-1", "error": None})
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cc.wait(call, 0), 0)
        self.assertIn("thread: t-1", out.getvalue())
        self.assertIn("verdict", out.getvalue())

    def test_unreadable_meta_fails_loudly(self):
        call = cc.prepare(self.args(), None)
        (call / "meta.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(cc.Failed, "unreadable"):
            cc.read_meta(call)

    def test_empty_prompt_and_bad_sandbox_are_refused(self):
        self.prompt.write_text("  \n", encoding="utf-8")
        with self.assertRaisesRegex(cc.Failed, "empty prompt"):
            cc.prepare(self.args(), None)
        with self.assertRaisesRegex(cc.Failed, "--sandbox"):
            cc.prepare(self.args(sandbox="yolo"), None)


if __name__ == "__main__":
    unittest.main()

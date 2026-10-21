#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import importlib.util
import io
import json
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_call.py"
SPEC = importlib.util.spec_from_file_location("codex_call", SCRIPT)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)

# argv: -c _run CALL PIDFILE; starts a sleeping child and records its pid in PIDFILE
SPAWN_AND_SLEEP = ("import subprocess, sys, time; "
                   "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
                   "open(sys.argv[3], 'w').write(str(child.pid)); time.sleep(60)")


def running(pid):
    """Alive and not a Linux zombie that its new parent has yet to reap."""
    if not cc.alive(pid):
        return False
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return True


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
        base = dict(prompt=str(self.prompt), label="t", model="gpt-6.1-sol", effort="medium",
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
        for pin in (["-s", "read-only"], ["-m", "gpt-6.1-sol"], ["-c", "features.hooks=false"],
                    ["-c", "model_reasoning_effort=medium"]):
            self.assertIn(pin, [cmd[i:i + 2] for i in range(len(cmd) - 1)])
        self.assertIn("--json", cmd)
        self.assertNotIn("--ephemeral", cmd)
        self.assertEqual((meta["rc"], meta["thread_id"], meta["codex_version"]), (0, "t-1", "codex-cli 9.9.9"))

    def test_resume_repeats_model_and_sets_sandbox_by_config(self):
        _, meta = self.call(parent="t-9", stream=events("turn.completed", thread="t-9"))
        cmd = self.calls[0]
        self.assertEqual(cmd[1:4], ["exec", "resume", "t-9"])
        self.assertIn("gpt-6.1-sol", cmd)
        self.assertIn("sandbox_mode=read-only", cmd)
        for forbidden in ("-s", "-C", "--add-dir", "--color", "--ephemeral"):
            self.assertNotIn(forbidden, cmd)
        self.assertEqual((meta["thread_id"], meta["parent_thread"]), ("t-9", "t-9"))

    def test_search_is_a_top_level_flag_on_new_and_resume(self):
        self.call(search=True)
        self.assertEqual(self.calls[0][1:3], ["--search", "exec"])
        self.call(parent="t-9", stream=events("turn.completed", thread="t-9"), search=True)
        self.assertEqual(self.calls[0][1:4], ["--search", "exec", "resume"])

    def test_cancel_stops_the_runner_group_and_records_the_end(self):
        call = cc.prepare(self.args(), None)
        child_pid = call / "child.pid"
        # argv carries `_run <call>` like the real runner, so cancel recognises it; the child
        # stands in for codex, which cancel must stop too
        runner = subprocess.Popen([sys.executable, "-c", SPAWN_AND_SLEEP, "_run", str(call),
                                   str(child_pid)], start_new_session=True)
        child = None
        try:
            deadline = time.monotonic() + 10
            while not (child_pid.exists() and child_pid.read_text()) and time.monotonic() < deadline:
                time.sleep(0.1)
            child = int(child_pid.read_text())
            (call / "runner.pid").write_text(str(runner.pid), encoding="utf-8")
            relative = Path(os.path.relpath(call))  # a relative path names the same runner
            with mock.patch("sys.stderr"):
                self.assertEqual(cc.cancel(relative), 1)
            self.assertIsNotNone(runner.wait(timeout=5))
            deadline = time.monotonic() + 5
            while running(child) and time.monotonic() < deadline:
                time.sleep(0.1)
            self.assertFalse(running(child))
            meta = cc.read_meta(call)
            self.assertEqual((meta["rc"], meta["error"]), (1, "cancelled"))
        finally:
            runner.kill()
            runner.wait()
            if child and running(child):
                os.kill(child, signal.SIGTERM)

    def test_runner_identity_needs_this_exact_call_path(self):
        call = cc.prepare(self.args(label="prüfung-日"), None)
        sleep = [sys.executable, "-c", "import time; time.sleep(30)", "_run"]
        mine = subprocess.Popen([*sleep, str(call)], start_new_session=True)
        # a call in the same second gets the suffix -2: its path extends this one
        other = subprocess.Popen([*sleep, f"{call}-2"], start_new_session=True)
        try:
            self.assertTrue(cc.is_runner_of(mine.pid, call))
            self.assertFalse(cc.is_runner_of(other.pid, call))
        finally:
            for proc in (mine, other):
                proc.kill()
                proc.wait()

    def test_piped_streams_carry_utf8(self):
        # a real process with pipes, forced to the ANSI code page Windows gives them by default
        text = "Prüfung 日本 – ok"
        env = {k: v for k, v in os.environ.items() if k != "PYTHONUTF8"}
        env |= {"CODEX_CALL_ROOT": str(cc.ROOT), "PYTHONIOENCODING": "cp1252",
                "PATH": ""}  # no codex: the call fails at once
        new = subprocess.run([sys.executable, str(SCRIPT), "new", "-"], input=text.encode(),
                             capture_output=True, env=env, timeout=60)
        self.assertEqual(new.returncode, 1, new.stderr)
        (call,) = [d for d in cc.ROOT.iterdir() if d.is_dir()]
        self.assertEqual((call / "prompt.md").read_text(encoding="utf-8"), text)
        (call / "last.md").write_text(text, encoding="utf-8")
        cc.write_meta(call, cc.read_meta(call) | {"rc": 0, "thread_id": "t-1", "error": None})
        done = subprocess.run([sys.executable, str(SCRIPT), "wait", str(call)], capture_output=True,
                              env=env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(text, done.stdout.decode("utf-8"))

    @unittest.skipUnless(cc.WINDOWS, "Windows identity lookup")
    def test_failed_lookup_leaves_the_call_cancellable(self):
        call = cc.prepare(self.args(), None)
        (call / "runner.pid").write_text(str(os.getpid()), encoding="utf-8")
        cim_error = subprocess.CompletedProcess([], 0, "", "Get-CimInstance : Invalid class")
        for failure in (dict(side_effect=FileNotFoundError("powershell")), dict(return_value=cim_error)):
            with mock.patch.object(cc.subprocess, "run", **failure):
                with self.assertRaisesRegex(cc.Failed, "command line"):
                    cc.cancel(call)
            self.assertNotIn("rc", cc.read_meta(call))

    @unittest.skipUnless(cc.WINDOWS, "Windows tree kill")
    def test_failed_kill_leaves_the_call_cancellable(self):
        call = cc.prepare(self.args(), None)
        (call / "runner.pid").write_text(str(os.getpid()), encoding="utf-8")
        denied = subprocess.CompletedProcess([], 1, "", "access denied")
        for failure, said in ((dict(return_value=denied), "access denied"),
                              (dict(side_effect=FileNotFoundError("taskkill")), "cannot run taskkill")):
            with mock.patch.object(cc, "is_runner_of", return_value=True), \
                    mock.patch.object(cc.subprocess, "run", **failure):
                with self.assertRaisesRegex(cc.Failed, said):
                    cc.cancel(call)
            self.assertNotIn("rc", cc.read_meta(call))

    @unittest.skipUnless(cc.WINDOWS, "Windows pids are DWORDs")
    def test_alive_rejects_pids_a_dword_would_wrap(self):
        self.assertTrue(cc.alive(os.getpid()))
        self.assertFalse(cc.alive(os.getpid() + 2 ** 32))

    @unittest.skipUnless(cc.WINDOWS, "npm's .cmd shim")
    def test_cli_runs_an_npm_shim_through_node(self):
        npm = Path(self.tmp.name) / "npm"
        script = npm / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        script.parent.mkdir(parents=True)
        script.write_text("", encoding="utf-8")
        (npm / "node.exe").write_text("", encoding="utf-8")
        shim = npm / "codex.cmd"
        shim.write_text('@ECHO off\r\nendLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "%_prog%"  '
                        '"%dp0%\\node_modules\\@openai\\codex\\bin\\codex.js" %*\r\n', encoding="utf-8")
        with mock.patch.object(cc.shutil, "which", return_value=str(shim)):
            self.assertEqual([Path(p) for p in cc.cli("codex")], [npm / "node.exe", script])
        other = npm / "other.cmd"
        other.write_text("@echo off\r\nsomething %*\r\n", encoding="utf-8")
        with mock.patch.object(cc.shutil, "which", return_value=str(other)):
            self.assertEqual(cc.cli("other"), [str(other)])  # unknown layout: the shim itself

    def test_batch_arguments_cmd_would_reinterpret_are_refused(self):
        with mock.patch.object(cc, "WINDOWS", True):
            cc.check_batch(["C:/n/node.exe", "C:/t/a&b/out.md"])  # no shim: nothing to reinterpret
            cc.check_batch(["C:/n/codex.cmd", "-c", 'web_search="disabled"'])
            for bad in ("C:/t/a&b/out.md", "C:/t/%TEMP%/x", "a|b", "a^b", "a>b"):
                with self.assertRaisesRegex(cc.Failed, "cmd.exe"):
                    cc.check_batch(["C:/n/codex.CMD", "-o", bad])
        with mock.patch.object(cc, "WINDOWS", False):
            cc.check_batch(["/usr/bin/codex.cmd", "a&b"])  # POSIX starts no cmd.exe

    def test_alive_probes_without_harming_the_process(self):
        sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            self.assertTrue(cc.alive(sleeper.pid))
            time.sleep(0.5)
            self.assertIsNone(sleeper.poll())
        finally:
            sleeper.kill()
            sleeper.wait()
        # the Popen object still holds the exited process; it must not count as alive
        self.assertFalse(cc.alive(sleeper.pid))
        self.assertFalse(cc.alive(None))

    def test_cancel_never_signals_a_process_that_is_not_this_runner(self):
        call = cc.prepare(self.args(), None)
        stranger = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                    start_new_session=True)
        try:
            (call / "runner.pid").write_text(str(stranger.pid), encoding="utf-8")
            with mock.patch("sys.stderr"):
                self.assertEqual(cc.cancel(call), 1)
            self.assertIsNone(stranger.poll())
            self.assertIn("already gone", cc.read_meta(call)["error"])
            self.assertIn(str(call), [json.loads(line)["dir"] for line in
                                      (cc.ROOT / "calls.jsonl").read_text().splitlines()])
        finally:
            stranger.kill()
            stranger.wait()

    def test_cancel_without_a_detached_runner_is_refused(self):
        call = cc.prepare(self.args(), None)
        with self.assertRaises(cc.Failed):
            cc.cancel(call)

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

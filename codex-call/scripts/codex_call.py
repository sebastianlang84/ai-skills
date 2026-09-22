#!/usr/bin/env python3
"""One pinned way to call Codex: start a thread, ask a follow-up in it, wait for a detached call.

    codex_call.py new    [--cwd DIR] [--label L] [--model M] [--effort E] [--sandbox S] [--detach] PROMPT|-
    codex_call.py resume THREAD_ID [--label L] [--model M] [--effort E] [--sandbox S] [--detach] PROMPT|-
    codex_call.py wait   CALL_DIR [--timeout SECONDS]
    codex_call.py list   [-n N]
    codex_call.py selftest

PROMPT is a file path, or `-` for stdin. Without --detach the call blocks and prints its result;
with --detach it prints the call directory at once, and `wait` collects it.

Every flag below was measured against codex-cli 0.155.1 (2026-09-22):
- no `--ephemeral`: an ephemeral thread is not saved, so it cannot be resumed;
- `-c features.hooks=false`: this host's SessionEnd hook compacts the thread after every exec and
  holds its writer lock for minutes; a resume in that window fails with "already has an active
  writer";
- the model is repeated on resume, or Codex resumes under its configured default;
- `resume` accepts neither `-s` nor `-C`: the sandbox is set with `-c sandbox_mode=…`, because
  ~/.codex/config.toml defaults to danger-full-access;
- Codex exits 0 even when a turn fails (a refused model reports `turn.failed`), so success is
  decided from the event stream, not the exit code.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

MODEL = os.environ.get("CODEX_CALL_MODEL", "gpt-6-sol")
EFFORT = os.environ.get("CODEX_CALL_EFFORT", "medium")
ROOT = Path(os.environ.get("CODEX_CALL_ROOT", Path.home() / ".agents/state/codex-call"))
SANDBOXES = ("read-only", "workspace-write", "danger-full-access")
# One Bash tool call is capped at 600 s; a wait must return before that.
WAIT_TIMEOUT = 540
STILL_RUNNING = 3


class Failed(Exception):
    pass


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_meta(call: Path) -> dict:
    path = call / "meta.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Failed(f"not a codex-call directory: {call}")
    except json.JSONDecodeError as exc:
        raise Failed(f"unreadable {path}: {exc}")


def write_meta(call: Path, meta: dict) -> None:
    tmp = call / "meta.json.tmp"
    tmp.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    tmp.replace(call / "meta.json")


def codex_version(exe: str) -> str:
    try:
        return subprocess.run([exe, "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def command(meta: dict, exe: str, out: Path) -> list[str]:
    pins = ["-m", meta["model"], "-c", f"model_reasoning_effort={meta['effort']}",
            "-c", "features.hooks=false", "--skip-git-repo-check", "--json", "-o", str(out)]
    if meta["parent_thread"]:
        return [exe, "exec", "resume", meta["parent_thread"], *pins,
                "-c", f"sandbox_mode={meta['sandbox']}", "-"]
    return [exe, "exec", "-C", meta["cwd"], "-s", meta["sandbox"], *pins, "-"]


def outcome(events: str) -> tuple[str | None, str | None]:
    """(thread_id, error). error is None only for a turn that completed with an answer."""
    thread, answered, completed, error = None, False, False, None
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "thread.started" and thread is None:
            thread = event.get("thread_id")
        elif kind == "item.completed" and (event.get("item") or {}).get("type") == "agent_message":
            answered = True
        elif kind == "turn.completed":
            completed = True
        elif kind in ("turn.failed", "error"):
            detail = event.get("error") or event.get("message") or event
            error = str(detail.get("message") if isinstance(detail, dict) else detail)
    if error is None and not completed:
        error = "no turn.completed event"
    if error is None and not answered:
        error = "turn completed without an answer"
    return thread, error


def run(call: Path) -> int:
    """Execute one prepared call synchronously and record its end state in meta.json."""
    meta = read_meta(call)
    exe = shutil.which("codex")
    rc, error, thread = 1, None, meta.get("thread_id")
    try:
        if not exe:
            raise Failed("codex CLI not found on PATH")
        meta["codex_version"] = codex_version(exe)
        write_meta(call, meta)
        with (call / "prompt.md").open("rb") as stdin, \
                (call / "events.jsonl").open("wb") as stdout, \
                (call / "stderr.log").open("wb") as stderr:
            proc = subprocess.run(command(meta, exe, call / "last.md"), stdin=stdin,
                                  stdout=stdout, stderr=stderr, cwd=meta["cwd"])
        found, error = outcome((call / "events.jsonl").read_text(encoding="utf-8", errors="replace"))
        if error is None and proc.returncode != 0:
            error = f"codex exited {proc.returncode}"
        # Measured: resume reports thread.started with the resumed id, so a missing or different
        # id means the answer cannot be tied to the thread the caller asked for.
        if error is None and not found:
            error = "codex reported no thread id"
        if error is None and thread and found != thread:
            error = f"resumed {thread} but codex reported thread {found}"
        thread = thread or found
        last = call / "last.md"
        if error is None and (not last.exists() or not last.read_text(encoding="utf-8").strip()):
            error = "empty answer in last.md"
        if error is None:
            rc = 0
    except Exception as exc:  # recorded, never lost: wait reads the end state from meta.json
        error = str(exc)
    meta.update(thread_id=thread, rc=rc, error=error, finished=now())
    write_meta(call, meta)
    with (ROOT / "calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({k: meta.get(k) for k in (
            "started", "finished", "label", "thread_id", "parent_thread", "model", "effort",
            "sandbox", "cwd", "rc", "error")} | {"dir": str(call)}) + "\n")
    return rc


def alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def report(call: Path) -> int:
    meta = read_meta(call)
    if meta["rc"] != 0:
        tail = (call / "stderr.log").read_text(errors="replace")[-1500:] if (call / "stderr.log").exists() else ""
        print(f"FAILED: {meta['error']}\ncall: {call}\n{tail}".rstrip(), file=sys.stderr)
        return 1
    print(f"thread: {meta['thread_id']}\nresult: {call / 'last.md'}\n")
    print((call / "last.md").read_text(encoding="utf-8").rstrip())
    return 0


def runner_pid(call: Path, meta: dict) -> int | None:
    """A detached runner's pid lives in its own file, written only by the parent: meta.json has
    exactly one writer at a time, so the runner's end state cannot be overwritten by a stale copy."""
    try:
        return int((call / "runner.pid").read_text())
    except (FileNotFoundError, ValueError):
        return meta.get("pid")


def wait(call: Path, timeout: float) -> int:
    deadline = time.monotonic() + timeout
    while True:
        meta = read_meta(call)
        if "rc" in meta:
            return report(call)
        pid = runner_pid(call, meta)
        starting = pid is None and time.time() - call.stat().st_mtime < 30
        if not starting and not alive(pid):
            # Reread: the runner may have finished between the two reads.
            meta = read_meta(call)
            if "rc" in meta:
                return report(call)
            last = call / "last.md"
            partial = f"\npartial answer, unconfirmed: {last}" if last.exists() and last.stat().st_size else ""
            print(f"FAILED: runner {pid} is gone without an end state\ncall: {call}{partial}",
                  file=sys.stderr)
            return 1
        if time.monotonic() >= deadline:
            print(f"still running: {call}\nrun `wait {call}` again", file=sys.stderr)
            return STILL_RUNNING
        time.sleep(2)


def prepare(args, parent: str | None) -> Path:
    if args.sandbox not in SANDBOXES:
        raise Failed(f"--sandbox must be one of {', '.join(SANDBOXES)}")
    prompt = sys.stdin.read() if args.prompt == "-" else Path(args.prompt).read_text(encoding="utf-8")
    if not prompt.strip():
        raise Failed("empty prompt")
    ROOT.mkdir(parents=True, exist_ok=True)
    label = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.label)[:40] or "call"
    call = ROOT / f"{datetime.now():%Y%m%d-%H%M%S}-{label}"
    suffix = 1
    while call.exists():
        suffix += 1
        call = ROOT / f"{datetime.now():%Y%m%d-%H%M%S}-{label}-{suffix}"
    call.mkdir()
    (call / "prompt.md").write_text(prompt, encoding="utf-8")
    cwd = str(Path(args.cwd).resolve()) if getattr(args, "cwd", None) else str(call)
    write_meta(call, {"label": label, "started": now(), "model": args.model, "effort": args.effort,
                      "sandbox": args.sandbox, "cwd": cwd, "parent_thread": parent,
                      "thread_id": parent, "pid": None})
    return call


def start(args, parent: str | None) -> int:
    call = prepare(args, parent)
    if not args.detach:
        meta = read_meta(call)
        meta["pid"] = os.getpid()
        write_meta(call, meta)
        run(call)
        return report(call)
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_run", str(call)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=open(call / "runner.log", "wb"), start_new_session=True)
    (call / "runner.pid").write_text(str(proc.pid), encoding="utf-8")
    print(call)
    return 0


def selftest() -> int:
    """Prove the path the callers rely on: new, an immediate resume (the hook-lock case), and a
    read-only sandbox that survives the resume."""
    number = str(random.randint(1000, 9999))
    base = dict(label="selftest", model=MODEL, effort="low", sandbox="read-only", detach=False, cwd=None)

    def ask(parent, text):
        prompt = ROOT / "selftest-prompt.md"
        ROOT.mkdir(parents=True, exist_ok=True)
        prompt.write_text(text, encoding="utf-8")
        call = prepare(argparse.Namespace(prompt=str(prompt), **base), parent)
        run(call)
        return call, read_meta(call)

    def fail(step, meta):
        print(f"SELFTEST FAILED at {step}: {meta.get('error')}\ncall: see {ROOT}/calls.jsonl",
              file=sys.stderr)
        return 1

    first, meta = ask(None, f"Remember the number {number}. Reply only: OK")
    if meta["rc"] != 0 or not meta.get("thread_id"):
        return fail("new", meta)
    thread = meta["thread_id"]
    second, meta = ask(thread, "Which number did I ask you to remember? Reply with the number only.")
    if meta["rc"] != 0:
        return fail("resume", meta)
    answer = (second / "last.md").read_text(encoding="utf-8").strip()
    if answer != number:
        print(f"SELFTEST FAILED at resume: expected {number}, got {answer!r}", file=sys.stderr)
        return 1
    target = second / "sandbox-probe"
    third, meta = ask(thread, f"Run this shell command and report its output: "
                              f"sh -c 'echo x > {target} && echo WROTE || echo DENIED'")
    if meta["rc"] != 0:
        return fail("sandbox", meta)
    ran = any((json.loads(line).get("item") or {}).get("type") == "command_execution"
              for line in (third / "events.jsonl").read_text().splitlines() if line.startswith("{"))
    if not ran:
        print("SELFTEST FAILED at sandbox: the command was not executed, the check proves nothing",
              file=sys.stderr)
        return 1
    if target.exists():
        print(f"SELFTEST FAILED at sandbox: resume ran writable, {target} was written", file=sys.stderr)
        return 1
    record = {"verified": now(), "codex_version": meta.get("codex_version"), "model": MODEL,
              "thread_id": thread}
    (ROOT / "selftest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"selftest ok: {record['codex_version']}, {MODEL}, new + resume + read-only sandbox")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="codex_call.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--label", default="call")
        sp.add_argument("--model", default=MODEL)
        sp.add_argument("--effort", default=EFFORT)
        sp.add_argument("--sandbox", default="read-only")
        sp.add_argument("--detach", action="store_true")
        sp.add_argument("prompt")

    new = sub.add_parser("new")
    new.add_argument("--cwd")
    common(new)
    resume = sub.add_parser("resume")
    resume.add_argument("thread")
    common(resume)
    w = sub.add_parser("wait")
    w.add_argument("call")
    w.add_argument("--timeout", type=float, default=WAIT_TIMEOUT)
    ls = sub.add_parser("list")
    ls.add_argument("-n", type=int, default=20)
    sub.add_parser("selftest")
    r = sub.add_parser("_run")
    r.add_argument("call")

    args = p.parse_args(argv)
    try:
        if args.cmd == "new":
            return start(args, None)
        if args.cmd == "resume":
            return start(args, args.thread)
        if args.cmd == "wait":
            return wait(Path(args.call), args.timeout)
        if args.cmd == "list":
            log = ROOT / "calls.jsonl"
            lines = log.read_text().splitlines()[-args.n:] if log.exists() else []
            print("\n".join(lines))
            return 0
        if args.cmd == "selftest":
            return selftest()
        return run(Path(args.call))
    except Failed as exc:
        print(f"codex_call: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

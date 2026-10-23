#!/usr/bin/env python3
"""One pinned way to call Codex: start a thread, ask a follow-up in it, wait for a detached call.

    codex_call.py new    [--cwd DIR] [--label L] [--model M] [--effort E] [--sandbox S] [--search] [--detach] PROMPT|-
    codex_call.py resume THREAD_ID [--cwd DIR] [--label L] [--model M] [--effort E] [--sandbox S] [--search] [--detach] PROMPT|-
    codex_call.py wait   CALL_DIR [--timeout SECONDS]
    codex_call.py cancel CALL_DIR   (stops a detached call and its codex process)
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
import re
import signal
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

MODEL = os.environ.get("CODEX_CALL_MODEL", "gpt-6.1-sol")
EFFORT = os.environ.get("CODEX_CALL_EFFORT", "medium")
ROOT = Path(os.environ.get("CODEX_CALL_ROOT", Path.home() / ".agents/state/codex-call"))
SANDBOXES = ("read-only", "workspace-write", "danger-full-access")
# Banned on this machine (Sebastian, 2026-10-01); a call naming one fails before anything runs.
BANNED_MODELS = ("gpt-6-sol",)
# Never a default, only when Sebastian names it for this call; needs --on-request (Sebastian, 2026-10-24).
ON_REQUEST_MODELS = ("gpt-6-astra",)
# One Bash tool call is capped at 600 s; a wait must return before that.
WAIT_TIMEOUT = 540
STILL_RUNNING = 3
WINDOWS = os.name == "nt"


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


def cli(name: str) -> list[str] | None:
    """How to start a CLI, or None if it is not on PATH. On Windows npm installs a .cmd shim, which
    hands every argument to cmd.exe; cmd.exe acts on & | < > ^ % that Python's quoting cannot protect.
    So run node with the shim's script directly when the shim has npm's layout."""
    exe = shutil.which(name)
    if not exe or not (WINDOWS and exe.lower().endswith((".cmd", ".bat"))):
        return [exe] if exe else None
    shim = Path(exe)
    try:
        found = re.search(r'"%dp0%\\([^"]+\.[cm]?js)"', shim.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        found = None
    if found:
        script, node = shim.parent / found.group(1), shim.parent / "node.exe"
        node = str(node) if node.is_file() else shutil.which("node")
        if script.is_file() and node:
            return [node, str(script)]
    return [exe]


def check_batch(argv: list[str]) -> None:
    """Refuse an argument cmd.exe would reinterpret while argv still starts with a .cmd or .bat."""
    if WINDOWS and argv[0].lower().endswith((".cmd", ".bat")):
        bad = next((a for a in argv[1:] if set(a) & set("&|<>^%")), None)
        if bad is not None:
            raise Failed(f"cannot pass {bad!r} through {Path(argv[0]).name}: cmd.exe would reinterpret it")


def codex_version(prefix: list[str]) -> str:
    try:
        return subprocess.run([*prefix, "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def command(meta: dict, prefix: list[str], out: Path) -> list[str]:
    pins = ["-m", meta["model"], "-c", f"model_reasoning_effort={meta['effort']}",
            "-c", "features.hooks=false", "--skip-git-repo-check", "--json", "-o", str(out)]
    # `--search` (native web search) is a top-level flag; codex rejects it after `exec`.
    top = [*prefix, "--search"] if meta.get("search") else [*prefix]
    if meta["parent_thread"]:
        return [*top, "exec", "resume", meta["parent_thread"], *pins,
                "-c", f"sandbox_mode={meta['sandbox']}", "-"]
    return [*top, "exec", "-C", meta["cwd"], "-s", meta["sandbox"], *pins, "-"]


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
    prefix = cli("codex")
    rc, error, thread = 1, None, meta.get("thread_id")
    try:
        if not prefix:
            raise Failed("codex CLI not found on PATH")
        argv = command(meta, prefix, call / "last.md")
        check_batch(argv)
        meta["codex_version"] = codex_version(prefix)
        write_meta(call, meta)
        with (call / "prompt.md").open("rb") as stdin, \
                (call / "events.jsonl").open("wb") as stdout, \
                (call / "stderr.log").open("wb") as stderr:
            proc = subprocess.run(argv, stdin=stdin, stdout=stdout, stderr=stderr, cwd=meta["cwd"])
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
    finish(call, meta)
    return rc


def finish(call: Path, meta: dict) -> None:
    """Record a call's end state in meta.json and its one line in calls.jsonl."""
    write_meta(call, meta)
    with (ROOT / "calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({k: meta.get(k) for k in (
            "started", "finished", "label", "thread_id", "parent_thread", "model", "effort",
            "sandbox", "cwd", "rc", "error")} | {"dir": str(call)}) + "\n")


def alive(pid: int | None) -> bool:
    if not pid:
        return False
    if WINDOWS:
        return win_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def win_alive(pid: int) -> bool:
    """os.kill(pid, 0) is no probe on Windows: signal 0 is CTRL_C_EVENT, sent to a console process
    group, and it raises WinError 87 for a live pid outside this console. Open a handle instead."""
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    synchronize, query_limited, access_denied, invalid_parameter = 0x00100000, 0x1000, 5, 87
    if not 0 < pid <= 0xFFFFFFFF:
        return False  # no Windows pid; as a DWORD it would wrap onto some other process
    handle = k32.OpenProcess(synchronize | query_limited, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == invalid_parameter:  # no such process
            return False
        if error == access_denied:  # exists but belongs to someone else, like EPERM on POSIX
            return True
        raise Failed(f"cannot probe pid {pid}: {ctypes.FormatError(error)}")
    try:
        # an exited process stays openable while anyone holds a handle; it is signaled then
        state = k32.WaitForSingleObject(handle, 0)
        if state in (0, 0x102):  # WAIT_OBJECT_0: exited, WAIT_TIMEOUT: running
            return state == 0x102
        raise Failed(f"cannot probe pid {pid}: {ctypes.FormatError(ctypes.get_last_error())}")
    finally:
        k32.CloseHandle(handle)


def win_argv(pid: int) -> list[str]:
    """A process's argv as Windows parses its command line, [] if it has none we can read (it is
    gone, or another user's). A failed lookup raises, so a cancel stays retryable."""
    import ctypes
    from ctypes import wintypes
    # Stop: a CIM error otherwise exits 0 with empty stdout, which would read as "gone"
    query = ("$ErrorActionPreference = 'Stop'; "
             "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
             f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine")
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", query],
                              capture_output=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Failed(f"cannot read the command line of pid {pid}: {exc}")
    if proc.returncode != 0 or proc.stderr.strip():
        raise Failed(f"cannot read the command line of pid {pid}: {proc.stderr.strip()}")
    line = proc.stdout.strip().lstrip("﻿")
    if not line:
        return []
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = (wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int))
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    k32 = ctypes.WinDLL("kernel32")
    k32.LocalFree.argtypes = (ctypes.c_void_p,)
    count = ctypes.c_int()
    argv = shell32.CommandLineToArgvW(line, ctypes.byref(count))
    if not argv:
        raise Failed(f"cannot parse the command line of pid {pid}: {ctypes.FormatError(ctypes.get_last_error())}")
    try:
        return [argv[i] for i in range(count.value)]
    finally:
        k32.LocalFree(argv)


def report(call: Path) -> int:
    meta = read_meta(call)
    if meta["rc"] != 0:
        tail = (call / "stderr.log").read_text(encoding="utf-8", errors="replace")[-1500:] if (call / "stderr.log").exists() else ""
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
    stamp, suffix = f"{datetime.now():%Y%m%d-%H%M%S}", 1
    while True:
        # mkdir itself is the claim: two callers in the same second cannot both get one directory
        call = ROOT / (f"{stamp}-{label}" if suffix == 1 else f"{stamp}-{label}-{suffix}")
        try:
            call.mkdir()
            break
        except FileExistsError:
            suffix += 1
    (call / "prompt.md").write_text(prompt, encoding="utf-8")
    cwd = str(Path(args.cwd).resolve()) if getattr(args, "cwd", None) else str(call)
    write_meta(call, {"label": label, "started": now(), "model": args.model, "effort": args.effort,
                      "sandbox": args.sandbox, "search": bool(getattr(args, "search", False)), "cwd": cwd, "parent_thread": parent,
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


def cancel(call: Path) -> int:
    """Stop a detached call: its runner leads its own session, so the group holds codex too.
    Windows has no such group; there taskkill /T walks the tree runner → codex.cmd → node → codex."""
    call = call.resolve()  # the runner's argv holds the absolute path
    meta = read_meta(call)
    if "rc" in meta:
        return report(call)
    try:
        pid = int((call / "runner.pid").read_text())
    except (FileNotFoundError, ValueError):
        raise Failed(f"{call} has no detached runner to cancel")
    if not is_runner_of(pid, call):
        # The runner is gone and its pid may belong to someone else now: signal nothing.
        meta.update(rc=1, error="cancelled; runner already gone", finished=now())
        finish(call, meta)
        print(f"cancelled (runner already gone): {call}", file=sys.stderr)
        return 1
    if WINDOWS:
        kill_tree(pid)
    else:
        kill_group(pid)
    meta = read_meta(call)
    if "rc" not in meta:
        meta.update(rc=1, error="cancelled", finished=now())
        finish(call, meta)
    print(f"cancelled: {call}", file=sys.stderr)
    return 1


def kill_group(pid: int) -> None:
    for sig, grace in ((signal.SIGTERM, 10), (signal.SIGKILL, 5)):
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            break
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.2)
        else:
            continue
        break


def kill_tree(pid: int) -> None:
    # No SIGTERM for console processes: taskkill without /F only posts WM_CLOSE. /T finds the
    # children by parent pid, so it must run while the runner is still alive.
    try:
        proc = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                              encoding="oem", errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Failed(f"cannot run taskkill for runner {pid}: {exc}")
    said = (proc.stdout + proc.stderr).strip()
    deadline = time.monotonic() + 5
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(0.2)
    if alive(pid):
        # nothing recorded: the runner may still finish on its own, and cancel can be retried
        raise Failed(f"taskkill could not stop runner {pid}: {said}")
    if proc.returncode != 0:
        print(f"warning: taskkill exited {proc.returncode}, part of the tree may still run:\n{said}",
              file=sys.stderr)


def is_runner_of(pid: int, call: Path) -> bool:
    """True only if pid is alive, leads its own group (POSIX), and runs `_run` for this very call."""
    if WINDOWS:
        # no /proc and no process groups: compare the parsed command line, argument by argument
        if not alive(pid):
            return False
        argv = win_argv(pid)
        target = os.path.normcase(str(call))
        return any(flag == "_run" and os.path.normcase(str(Path(arg).resolve())) == target
                   for flag, arg in zip(argv, argv[1:]))
    try:
        argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        return os.getpgid(pid) == pid and b"_run" in argv and str(call).encode() in argv
    except (OSError, ProcessLookupError):
        return False


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
              for line in (third / "events.jsonl").read_text(encoding="utf-8", errors="replace").splitlines()
              if line.startswith("{"))
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
        sp.add_argument("--search", action="store_true", help="give Codex its native web search")
        sp.add_argument("--detach", action="store_true")
        sp.add_argument("--on-request", action="store_true",
                        help="the user named this on-request model for this call")
        sp.add_argument("prompt")

    new = sub.add_parser("new")
    new.add_argument("--cwd")
    common(new)
    resume = sub.add_parser("resume")
    resume.add_argument("thread")
    # resume rejects -C; --cwd here only sets the process directory the resumed turn runs in
    resume.add_argument("--cwd")
    common(resume)
    c = sub.add_parser("cancel")
    c.add_argument("call")
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
        if getattr(args, "model", None) in BANNED_MODELS:
            raise Failed(f"model {args.model} is banned on this machine; use gpt-6.1-sol or gpt-6-luna")
        if getattr(args, "model", None) in ON_REQUEST_MODELS and not args.on_request:
            raise Failed(f"model {args.model} runs only when the user names it for this call (--on-request)")
        if args.cmd == "new":
            return start(args, None)
        if args.cmd == "resume":
            return start(args, args.thread)
        if args.cmd == "wait":
            return wait(Path(args.call), args.timeout)
        if args.cmd == "list":
            log = ROOT / "calls.jsonl"
            lines = log.read_text(encoding="utf-8").splitlines()[-args.n:] if log.exists() else []
            print("\n".join(lines))
            return 0
        if args.cmd == "selftest":
            return selftest()
        if args.cmd == "cancel":
            return cancel(Path(args.call))
        if args.cmd == "_run":
            return run(Path(args.call))
        raise Failed(f"unknown command {args.cmd}")
    except Failed as exc:
        print(f"codex_call: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    # Every file here is UTF-8, but a redirected stream on Windows defaults to the ANSI code page:
    # printing an answer with characters outside cp1252 crashed, and a piped `-` prompt was misread.
    # Keep each stream's error handler: reconfigure would otherwise reset it to strict.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is not None:
            stream.reconfigure(encoding="utf-8", errors=stream.errors)
    sys.exit(main())

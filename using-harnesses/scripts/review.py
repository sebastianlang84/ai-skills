#!/usr/bin/env python3
"""review.py — send one adversarial review round to codex or claude with fixed, contained flags.

    review.sh <codex|claude> [--foreground] [--resume <id>] [--effort <level>] <brief-file> <artifact-file>...
    review.sh wait <dir> [--timeout <s>]  |  review.sh cancel <dir>
    review.sh --print-config | --get <KEY>

review.sh starts this file; both take the same arguments. Builds the payload from
../references/review-prompt.md (role lock, brief, rules, data clause, artifacts), refuses secrets and
`.env` inputs (exit 3), and runs the reviewer contained: codex in CODEX_HOME=~/.codex-review,
read-only, memories off, in an empty directory outside git that is also its HOME; claude with
--safe-mode --setting-sources project --tools "" in ~/.cache/using-harnesses/claude-review. --resume
continues only a session this script started. Models: defaults and
${XDG_CONFIG_HOME:-~/.config}/using-harnesses/models.conf, both through models_conf.py.
REVIEW_TIMEOUT may lower the 1800 s deadline. The only stdout line is a private directory (out.md,
session, err.txt, why, payload.md, raw log, rc). Every check runs before that line; the reviewer then
runs detached under its own runner and the call returns at once. `wait` prints "session: <id>", a
blank line and the answer, and exits with the round's status; it exits 75 while the round still runs.
--foreground blocks instead and exits with the round's status. Status: reviewer's own (124 =
deadline, 137 = deadline needed KILL, 143 = cancelled), 2 = usage, config or unsafe environment,
3 = payload refused, 4 = no answer or session id, 5 = answer lacks the closing ===REVIEW COMPLETE===
line. Details: ../references/review.md.

Runs on Linux and on Windows (Python from Git Bash, PowerShell or cmd). Windows differences: the
runner holds its reviewer in a job object that dies with it instead of a session, the reviewer home
is checked by its ACL instead of mode 600, and codex still lists ~/.agents/skills there (HOME does not
hide them; measured with codex-cli 0.160.0). Python 3.9, stdlib only; process helpers come from
codex_call.py next to this file.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_call  # noqa: E402  (alive, is_runner_of, kill_tree, WINDOWS)
import models_conf  # noqa: E402  (the one models.conf parser)

WINDOWS = codex_call.WINDOWS
REFS = HERE.parent / "references"
MARKER = "===REVIEW COMPLETE==="
WAIT_LIMIT = 540
STILL_RUNNING = 75
USAGE = ("usage: review.sh <codex|claude> [--foreground] [--resume <id>] [--effort <level>] "
         "<brief-file> <artifact-file>... | wait <dir> [--timeout <s>] | cancel <dir> | "
         "--print-config | --get <KEY>")
# Read by the runner; the checked values travel in a file, not through argv.
JOB = "job.json"
CLAUDE_UNSET = ("CLAUDE_CONFIG_DIR", "CLAUDE_CODE_PROJECT_DIR_NAME", "CLAUDE_CODE_RESUME_FROM_SESSION",
                "CLAUDE_CODE_SESSION_LOG", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
                "XDG_CACHE_HOME")
# Allowed besides the owner on a Windows reviewer login: SYSTEM and Administrators can read any file.
WIN_TRUSTED = ("S-1-5-18", "S-1-5-32-544")

SIG_RE = re.compile(
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|(^|[^A-Za-z0-9])(sk|pk|rk)-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}"
    rb"|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    rb"|[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", re.I)
# A credential-named assignment whose value is neither code nor a placeholder. A false rejection costs a
# resend, a false pass a leaked secret: short and punctuated values count.
KV_RE = re.compile(r'[A-Za-z0-9_]*(api[_-]?key|secret|password|passwd|pwd|token|credential)[A-Za-z0-9_]*["\']?'
                   r'\s*[:=]\s*(?:(["\'])((?:\\.|(?!\2)[^\\\r\n]){6,})\2|()([^\s"\'#;,(){}\[\]<>]{6,})(\(?))', re.I)
NAME_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*')
CHAIN_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+')
PLACEHOLDER_RE = re.compile(r'[*xX.<>-]+|<[^>]*>|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%\(?\w*\)?s|\{\w*\}'
                            r'|(changeme|example|redacted|placeholder|dummy|secret|password|token)', re.I)


class Exit(Exception):
    def __init__(self, code: int):
        self.code = code


def die(message: str, code: int = 2):
    print(f"review.sh: {message}", file=sys.stderr)
    raise Exit(code)


def usage():
    die(USAGE)


def tmp_root() -> str:
    return os.environ.get("TMPDIR") or ("/tmp" if not WINDOWS else tempfile.gettempdir())


def home() -> Path:
    value = os.environ.get("HOME") or (str(Path.home()) if WINDOWS else "")
    if not value:
        die("HOME is not set")
    return Path(value)


def shown(path: Path) -> str:
    """How a path is printed: forward slashes on Windows, so Git Bash and Python both accept it."""
    return path.as_posix() if WINDOWS else str(path)


def conf_values() -> dict[str, str]:
    """The effective models.conf values; a config error stops with models_conf.py's message, exit 2."""
    try:
        return models_conf.load()[0]
    except models_conf.ConfigError as exc:
        print(f"models_conf.py: {exc}", file=sys.stderr)
        raise Exit(2)


# --- ownership and process identity -------------------------------------------------------------

def win_acl(path: Path) -> dict:
    """{'me', 'owner', 'allow'} as SIDs, read through PowerShell (Get-Acl knows no POSIX modes)."""
    script = ("$ErrorActionPreference = 'Stop'; "
              "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
              "$s = [System.Security.Principal.SecurityIdentifier]; "
              "$a = Get-Acl -LiteralPath $env:REVIEW_ACL_PATH; "
              "[pscustomobject]@{ me = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; "
              "owner = $a.GetOwner($s).Value; "
              "allow = @($a.GetAccessRules($true, $true, $s) | Where-Object { $_.AccessControlType -eq 'Allow' } "
              "| ForEach-Object { $_.IdentityReference.Value }) } | ConvertTo-Json -Compress")
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                              capture_output=True, encoding="utf-8", errors="replace", timeout=60,
                              env={**os.environ, "REVIEW_ACL_PATH": str(path)})
        if proc.returncode != 0 or proc.stderr.strip():
            raise OSError(proc.stderr.strip() or f"exit {proc.returncode}")
        acl = json.loads(proc.stdout.strip().lstrip("﻿"))
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        die(f"cannot read the ACL of {path}: {exc}")
    acl["allow"] = acl.get("allow") or []
    if isinstance(acl["allow"], str):
        acl["allow"] = [acl["allow"]]
    return acl


def owned(path: Path) -> bool:
    if WINDOWS:
        acl = win_acl(path)
        return acl["owner"] == acl["me"]
    return path.stat().st_uid == os.geteuid()


def private_login(auth: Path) -> bool:
    """Yours and readable by nobody else: mode 600 on POSIX; on Windows no grant beyond you, SYSTEM
    and Administrators (git bash mounts noacl, so chmod 600 shows 644 there and proves nothing)."""
    if WINDOWS:
        acl = win_acl(auth)
        return acl["owner"] == acl["me"] and all(s in (acl["me"], *WIN_TRUSTED) for s in acl["allow"])
    st = auth.stat()
    return st.st_uid == os.geteuid() and (st.st_mode & 0o7777) == 0o600


def runner_of(call: Path) -> int | None:
    """The pid in call/pid if it names a live runner of exactly this call (its argv carries `_run` and
    this call's directory), so a forged pid file cannot point cancel at another process."""
    try:
        pid = int((call / "pid").read_text().strip())
    except (OSError, ValueError):
        return None
    try:
        return pid if codex_call.is_runner_of(pid, call) else None
    except codex_call.Failed as exc:
        die(str(exc))


def _k32():
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    return k32


def win_hold_runner(call: Path):
    """A handle on this call's runner, or None. Opened before the identity check, so the process that
    passes the check is the one held."""
    try:
        pid = int((call / "pid").read_text().strip())
    except (OSError, ValueError):
        return None
    if not 0 < pid <= 0xFFFFFFFF:
        return None
    k32 = _k32()
    handle = k32.OpenProcess(0x00100000 | 0x1000, False, pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    if runner_of(call) != pid:
        k32.CloseHandle(handle)
        return None
    return handle


def win_running(handle) -> bool:
    return _k32().WaitForSingleObject(handle, 0) == 0x102  # WAIT_TIMEOUT


def win_close(handle):
    _k32().CloseHandle(handle)


def session_members(sid: int) -> list[int]:
    """Every process whose session id is sid (pkill -s without procps)."""
    members = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
        except (OSError, IndexError):
            continue
        if int(fields[3]) == sid and int(entry.name) != os.getpid():
            members.append(int(entry.name))
    return members


def stop_session(sid: int, mode: str):
    """Stop every process of a runner's session, whatever its name (a CLI may re-exec as node or python).
    "live" only after runner_of proved the leader is this call's runner. "dead" when that runner is
    gone: Linux reuses no pid while a process still carries it as session id, so members of session sid
    are this call's leftovers exactly when no process sid exists; a live process with that pid is a
    reuse and nothing is signalled. On Windows the runner's job object takes its reviewer along when
    the runner dies, so "dead" has nothing left to stop."""
    if WINDOWS:
        if mode == "live":
            try:
                codex_call.kill_tree(sid)
            except codex_call.Failed as exc:
                die(str(exc))
        return
    if mode != "live" and codex_call.alive(sid):
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):  # KILL after a grace period: a reviewer may ignore TERM
        if Path("/proc").is_dir():
            for pid in session_members(sid):
                try:
                    os.kill(pid, sig)
                except OSError:
                    pass
        else:
            subprocess.run(["pkill", f"-{sig.name[3:]}", "-s", str(sid)], capture_output=True)
        if sig == signal.SIGTERM:
            time.sleep(2)


def remove_tree(path: Path):
    """Windows refuses to delete a directory that a dying process still has as its working directory:
    try for a few seconds there."""
    for _ in range(20 if WINDOWS else 1):
        shutil.rmtree(path, ignore_errors=True)
        if not os.path.lexists(path):
            return
        time.sleep(0.5)


def remove_neutral(call: Path):
    try:
        neutral = Path((call / "neutral").read_text(encoding="utf-8").strip())
    except OSError:
        return
    root = Path(tmp_root()).resolve()
    if neutral.parent == root and neutral.name.startswith("tmp."):
        remove_tree(neutral)


# --- wait and cancel ------------------------------------------------------------------------------

def last_line(path: Path) -> str:
    """The last non-blank line, trailing whitespace and CR forgiven: a quoted brief contains the marker too."""
    try:
        lines = path.read_bytes().decode("utf-8", "replace").split("\n")
    except OSError:
        return ""
    lines = [line for line in lines if line.strip()]
    return lines[-1].rstrip() if lines else ""


def collect(argv: list[str]) -> int:
    cmd = argv[0]
    if len(argv) < 2 or not argv[1]:
        usage()
    call, rest = Path(argv[1]), argv[2:]
    limit = WAIT_LIMIT
    if cmd == "wait" and rest:
        if not (len(rest) == 2 and rest[0] == "--timeout" and re.fullmatch(r"[0-9]{1,3}", rest[1])
                and int(rest[1]) <= WAIT_LIMIT):
            usage()
        limit = int(rest[1])
    elif rest:
        usage()
    if not (call.is_dir() and owned(call) and (call / "payload.md").is_file()):
        die(f"not a review.sh call directory: {argv[1]}")
    call = call.resolve()
    if cmd == "cancel":
        if (call / "rc").is_file():
            print(f"already ended with exit {(call / 'rc').read_text().strip()}")
            return 0
        pid = runner_of(call)
        if pid is None:
            die(f"no live runner of {argv[1]}; nothing stopped")
        stop_session(pid, "live")
        remove_neutral(call)
        (call / "rc").write_text("143\n")
        with (call / "why").open("a", encoding="utf-8") as why:
            why.write("review.sh: cancelled\n")
        print("cancelled")
        return 0
    end, held = time.monotonic() + limit, None
    try:
        while not (call / "rc").is_file():
            # A runner that died without publishing rc (SIGKILL, OOM) would otherwise read as running forever.
            if (call / "pid").is_file():
                if not WINDOWS:
                    gone = runner_of(call) is None
                else:
                    # The identity check costs a PowerShell call there: prove it once, then keep a handle,
                    # which also stops Windows from reusing the pid while this wait follows it.
                    held = held or win_hold_runner(call)
                    gone = held is None or not win_running(held)
            else:
                gone = time.time() - (call / "payload.md").stat().st_mtime > 60
            if gone:
                if (call / "rc").is_file():
                    break
                try:
                    stop_session(int((call / "pid").read_text().strip()), "dead")
                except (OSError, ValueError):
                    pass
                remove_neutral(call)
                with (call / "why").open("a", encoding="utf-8") as why:
                    why.write(f"review.sh: the runner died before it finished; see {shown(call)}/err.txt\n")
                (call / "rc").write_text("4\n")
                break
            if time.monotonic() >= end:
                print(f"still running: {argv[1]}", file=sys.stderr)
                return STILL_RUNNING
            time.sleep(2)
    finally:
        if held:
            win_close(held)
    rc_text = (call / "rc").read_text().strip()
    if not re.fullmatch(r"[0-9]+", rc_text):
        die(f"corrupt status in {argv[1]}/rc")
    rc = int(rc_text)
    if rc == 0:  # recheck what success means; never trust the status file alone
        session = call / "session"
        logs = [call / "log.jsonl", call / "log.json"]
        if not (nonempty(session) and any(nonempty(p) for p in logs) and last_line(call / "out.md") == MARKER):
            print(f"review.sh: status 0 without a complete answer, session and log in {argv[1]}", file=sys.stderr)
            return 4
        answer = (call / "out.md").read_bytes()
        out = sys.stdout.buffer
        out.write(f"session: {session.read_text(encoding='utf-8').strip()}\n\n".encode())
        out.write(answer if answer.endswith(b"\n") else answer + b"\n")
        out.flush()
    else:
        why = call / "why"
        if nonempty(why):
            sys.stderr.write(why.read_text(encoding="utf-8", errors="replace"))
    return rc


def nonempty(path: Path) -> bool:
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


# --- the payload ----------------------------------------------------------------------------------

def block(name: str) -> bytes | None:
    """The lines between <!-- BEGIN name --> and <!-- END name --> in review-prompt.md, or None."""
    begin, end = f"<!-- BEGIN {name} -->".encode(), f"<!-- END {name} -->".encode()
    out, on = [], False
    for line in (REFS / "review-prompt.md").read_bytes().split(b"\n"):
        line = line.rstrip(b"\r")
        if line == end and on:
            return b"".join(x + b"\n" for x in out)
        if on:
            out.append(line)
        if line == begin:
            on = True
    return None


def kv_hit(path: Path) -> bool:
    def harmless(m):
        q, qv, _, v, call = m.groups()[1:]
        if q:  # only a value that is a placeholder as a whole; passphrases with spaces count
            return bool(PLACEHOLDER_RE.fullmatch(qv))
        return bool(PLACEHOLDER_RE.fullmatch(v)) or (
            bool(NAME_RE.fullmatch(v)) if call else bool(CHAIN_RE.fullmatch(v)) and not re.search(r"[0-9]", v))
    with path.open(encoding="utf-8", errors="replace") as f:
        return any(not harmless(m) for line in f for m in KV_RE.finditer(line))


def secret_check(payload: Path) -> str:
    """'clean', 'secret' or 'failed'. Two stages on the exact copy that is sent; any error fails closed."""
    try:
        if any(SIG_RE.search(line) for line in payload.read_bytes().split(b"\n")):
            return "secret"
        return "secret" if kv_hit(payload) else "clean"
    except Exception:  # noqa: BLE001 — a crashing checker must refuse, never pass
        return "failed"


def first_message_opens_with(backend: str, path: Path, head: str) -> bool:
    """Does the stored session's first user message open with the role lock?"""
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict):
                continue
            if backend == "codex":
                p = e.get("payload") or {}
                if e.get("type") != "response_item" or p.get("type") != "message" or p.get("role") != "user":
                    continue
                c = p.get("content")
            else:
                if e.get("type") != "user":
                    continue
                c = (e.get("message") or {}).get("content")
            t = c if isinstance(c, str) else "".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
            if backend == "codex" and t.lstrip().startswith("<environment_context>"):
                continue
            return t.lstrip().startswith(head)
    return False


def inside_git(cwd: Path) -> bool:
    """codex reads AGENTS.md from the enclosing git root down to its working directory."""
    try:
        return subprocess.run(["git", "-C", str(cwd), "rev-parse", "--git-dir"],
                              capture_output=True).returncode == 0
    except OSError:
        return False


# --- start ----------------------------------------------------------------------------------------

def start(argv: list[str]) -> int:
    backend = argv[0] if argv else ""
    if backend not in ("codex", "claude"):
        usage()
    args, resume, effort, foreground = argv[1:], "", "", False
    while args:
        if args[0] == "--foreground":
            foreground, args = True, args[1:]
        elif args[0] in ("--resume", "--effort"):
            if len(args) < 2:
                usage()
            if args[0] == "--resume":
                resume = args[1]
            else:
                effort = args[1]
            args = args[2:]
        elif args[0].startswith("-"):
            usage()
        else:
            break
    if len(args) < 2:
        usage()
    conf, b = conf_values(), backend.upper()
    model, efforts = conf[f"{b}_MODEL"], conf[f"{b}_EFFORTS"]
    effort = effort or efforts.split(",")[0]
    if effort not in efforts.split(","):
        die(f"effort {effort} not allowed for {backend} (allowed: {efforts})")
    if resume and not re.fullmatch(r"[A-Za-z0-9-]{8,64}", resume):
        die("invalid resume id")
    brief, artifacts = args[0], args[1:]
    for f in (brief, *artifacts):
        if f.startswith("-"):
            usage()
        if not (os.path.isfile(f) and os.access(f, os.R_OK)):
            die(f"not a readable file: {f}")
        for n in (f, os.path.realpath(f)):  # the name given and the file it resolves to
            if ".env" in os.path.basename(n).lower():
                die(f"payload refused: {f} is or points to an excluded (.env) file", 3)
    deadline = os.environ.get("REVIEW_TIMEOUT", "1800")
    if not (re.fullmatch(r"[1-9][0-9]{0,3}", deadline) and int(deadline) <= 1800):
        die("REVIEW_TIMEOUT must be 1..1800 seconds")
    user_home = home()

    if not WINDOWS:
        os.umask(0o077)
    try:
        outdir = Path(tempfile.mkdtemp(prefix="review.", dir=tmp_root())).resolve()
    except OSError as exc:
        die(f"cannot create the call directory: {exc}")
    neutral: Path | None = None

    def fail(message: str, code: int):
        remove_tree(outdir)
        if neutral:
            remove_tree(neutral)
        die(message, code)

    head_block = block("role-lock")
    head = head_block.decode("utf-8", "replace").split("\n")[0] if head_block else ""
    if not head:
        fail("review-prompt.md has no role-lock block", 2)
    rules, data = block("rules"), block("data-clause")
    payload = outdir / "payload.md"
    try:
        if rules is None or data is None:
            raise OSError("block missing")
        parts = [head_block, b"\n", Path(brief).read_bytes(), b"\n\n", rules, b"\n", data]
        for f in artifacts:
            parts += [f"\n\n===== ARTIFACT: {os.path.basename(f)} =====\n".encode(), Path(f).read_bytes()]
        parts.append(b"\n\n===== END OF ARTIFACTS =====\n")
        payload.write_bytes(b"".join(parts))
    except OSError:
        fail("payload could not be assembled (review-prompt.md block or input missing)", 2)

    verdict = secret_check(payload)
    if verdict == "secret":
        fail("payload refused: it matches a secret pattern; redact or exclude it", 3)
    if verdict != "clean":
        fail("payload refused: the secret check failed to run", 3)

    stored = None
    if backend == "codex":
        reviewer_home = user_home / ".codex-review"
        auth = reviewer_home / "auth.json"
        if not auth.is_file() or auth.is_symlink():
            fail(f"no own reviewer login in {reviewer_home}; run once: CODEX_HOME={shown(reviewer_home)} "
                 "codex login --device-auth", 2)
        if not private_login(auth):
            fail(f"{auth} must be yours and readable by you alone"
                 + (" (mode 600)" if not WINDOWS else " (no grant to other users)"), 2)
        for name in ("AGENTS.md", "AGENTS.override.md"):
            if os.path.lexists(reviewer_home / name):
                fail(f"{reviewer_home / name} exists; the reviewer home must carry no instructions", 2)
        skills = reviewer_home / "skills"
        if os.path.lexists(skills):
            if skills.is_symlink() or (skills / ".system").is_symlink():
                fail(f"{skills} must not be a symlink", 2)
            try:
                extra = sorted(p for p in skills.iterdir() if p.name != ".system")
            except OSError:
                fail(f"cannot read {skills}", 2)
            if extra:
                fail(f"{extra[0]} is a user skill; the reviewer home must carry only built-in skills", 2)
        try:
            neutral = Path(tempfile.mkdtemp(prefix="tmp.", dir=tmp_root())).resolve()
        except OSError:
            fail("could not create a working directory", 2)
        cwd = neutral
        if resume:
            stored = next((p for p in sorted((reviewer_home / "sessions").rglob(f"rollout-*{resume}.jsonl"))
                           if p.is_file()), None)
    else:
        reviewer_home = None
        cwd = user_home / ".cache" / "using-harnesses" / "claude-review"
        try:
            cwd.mkdir(parents=True, exist_ok=True)
            cwd.chmod(0o700)
            cwd = cwd.resolve()
        except OSError:
            fail(f"cannot create {cwd}", 2)
        if resume:
            stored = next((p for p in sorted((user_home / ".claude" / "projects").glob(
                f"*-using-harnesses-claude-review/{resume}.jsonl")) if p.is_file()), None)
    if inside_git(cwd):
        fail(f"working directory {cwd} lies inside a git repository", 2)
    if resume:
        if stored is None:
            fail(f"session {resume} was not started by review.sh for {backend}; start a new one", 2)
        if not first_message_opens_with(backend, stored, head):
            fail(f"session {resume} does not open with the role lock; start a new one", 2)

    job = {"backend": backend, "model": model, "effort": effort, "resume": resume, "cwd": str(cwd),
           "home": str(reviewer_home) if reviewer_home else "", "deadline": int(deadline),
           "neutral": str(neutral) if neutral else ""}
    try:
        codex_call.check_batch(reviewer_command(job, outdir)[0])
    except codex_call.Failed as exc:
        fail(str(exc), 2)
    (outdir / JOB).write_text(json.dumps(job), encoding="utf-8")
    print(shown(outdir), flush=True)

    runner_proc = spawn_runner(outdir)
    if not foreground:
        return 0
    # --foreground runs the same runner and waits for it, so wait and cancel also work on it. The
    # runner leads a session of its own, so an interrupt of this process must stop it explicitly.
    caught = []

    def interrupt(signum, _frame):
        caught.append(signum)
        raise KeyboardInterrupt

    if not WINDOWS:
        for sig in (signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, interrupt)
    try:
        runner_proc.wait()
    except KeyboardInterrupt:
        # A second interrupt must not cut the cleanup short and leave the reviewer unsupervised.
        for sig in (signal.SIGINT, *(() if WINDOWS else (signal.SIGTERM, signal.SIGHUP))):
            signal.signal(sig, signal.SIG_IGN)
        stop_session(runner_proc.pid, "live")
        runner_proc.wait()
        remove_neutral(outdir)
        if not (outdir / "rc").is_file():
            publish(outdir, 128 + int(caught[0] if caught else signal.SIGINT), "review.sh: interrupted")
    rc_file = outdir / "rc"
    rc = int(rc_file.read_text().strip()) if rc_file.is_file() else 4
    why = outdir / "why"
    if nonempty(why):
        sys.stderr.write(why.read_text(encoding="utf-8", errors="replace"))
    return rc


def spawn_runner(outdir: Path) -> subprocess.Popen:
    """Start the runner in a session (POSIX) or process group (Windows) of its own, so the caller's
    tool call can return at once and cannot take the reviewer down."""
    argv = [sys.executable, str(Path(__file__).resolve()), "_run", str(outdir)]
    common = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                  stderr=(outdir / "err.txt").open("ab"), close_fds=True)
    if not WINDOWS:
        return subprocess.Popen(argv, start_new_session=True, **common)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    try:  # leave a caller's job, which may kill its members when the tool call ends
        return subprocess.Popen(argv, creationflags=flags | 0x01000000, **common)  # CREATE_BREAKAWAY_FROM_JOB
    except OSError:
        return subprocess.Popen(argv, creationflags=flags, **common)


# --- the runner -----------------------------------------------------------------------------------

def win_job_dies_with_me():
    """Put this process into a job that kills every member when its last handle closes, so a reviewer
    cannot outlive a runner that was killed. The handle stays open for the runner's lifetime."""
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", ctypes.c_uint64 * 6),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    job = k32.CreateJobObjectW(None, None)
    info = Extended()
    info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not (job and k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
            and k32.AssignProcessToJobObject(job, k32.GetCurrentProcess())):
        raise OSError(ctypes.FormatError(ctypes.get_last_error()))
    return job


def reviewer_command(job: dict, outdir: Path) -> tuple[list[str], dict, str]:
    backend, effort, model, resume = job["backend"], job["effort"], job["model"], job["resume"]
    if backend == "codex":
        # No tools at all: with a shell, read-only still lets codex read any file of the user (measured).
        common = ["--json", "--skip-git-repo-check", "--ignore-rules", "--ignore-user-config",
                  "--disable", "memories", "--disable", "shell_tool", "--disable", "unified_exec",
                  "--disable", "view_image", "--disable", "apps", "--disable", "plugins",
                  "--disable", "browser_use", "--disable", "computer_use", "--disable", "in_app_browser",
                  "-c", 'web_search="disabled"', "-m", model, "-c", f"model_reasoning_effort={effort}",
                  "-o", str(outdir / "out.md")]
        if not resume:
            args = ["exec", *common, "-C", job["cwd"], "-s", "read-only", "-"]
        else:
            args = ["exec", "resume", *common, "-c", 'sandbox_mode="read-only"', resume, "-"]
        # HOME=the empty cwd: codex also discovers user skills in $HOME/.agents/skills (measured, 0.160.1).
        env = {**os.environ, "HOME": job["cwd"], "CODEX_HOME": job["home"]}
        return [*(codex_call.cli("codex") or ["codex"]), *args], env, "log.jsonl"
    args = ["-p", "--safe-mode", "--setting-sources", "project", "--tools", "", "--output-format", "json",
            "--model", model, "--effort", effort]
    if resume:
        args += ["--resume", resume]
    env = {k: v for k, v in os.environ.items() if k not in CLAUDE_UNSET}
    return [*(codex_call.cli("claude") or ["claude"]), *args], env, "log.json"


def run_with_deadline(cmd: list[str], env: dict, cwd: str, payload: Path, log: Path, err: Path,
                      deadline: int) -> int:
    """The reviewer's exit status; 124 when the deadline stopped it, 137 when that took KILL.
    err.txt is appended to, so the runner's own messages before the reviewer stay readable."""
    with payload.open("rb") as stdin, log.open("wb") as stdout, err.open("ab") as stderr:
        try:
            proc = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env,
                                    **({} if WINDOWS else {"preexec_fn": os.setpgrp}))
        except OSError as exc:
            stderr.write(f"review.sh: cannot start {cmd[0]}: {exc}\n".encode())
            return 127
        try:
            rc = proc.wait(timeout=deadline)
        except subprocess.TimeoutExpired:
            if WINDOWS:
                try:
                    codex_call.kill_tree(proc.pid)
                except codex_call.Failed as exc:
                    stderr.write(f"review.sh: {exc}\n".encode())
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # The runner returns anyway: when it exits, its job object kills what is left.
                    stderr.write(b"review.sh: the reviewer survived taskkill; the runner's job object ends it\n")
                return 124
            for sig, grace in ((signal.SIGTERM, 10), (signal.SIGKILL, None)):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=grace)
                    return 124 if sig == signal.SIGTERM else 137
                except subprocess.TimeoutExpired:
                    continue
    return 128 - rc if rc < 0 else rc


def extract(backend: str, outdir: Path):
    """Session id (both) and answer (claude) from the raw log; raises with a reason."""
    sid = ""
    if backend == "codex":
        with (outdir / "log.jsonl").open(encoding="utf-8", errors="replace") as log:
            for line in log:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if isinstance(e, dict) and e.get("type") == "thread.started":
                    sid = str(e.get("thread_id") or "")
    else:
        d = json.loads((outdir / "log.json").read_text(encoding="utf-8", errors="replace"))
        if d.get("type") != "result" or d.get("subtype") != "success" or d.get("is_error"):
            raise ValueError("claude returned no successful result; see log.json")
        sid, r = str(d.get("session_id") or ""), (d.get("result") or "").strip()
        (outdir / "out.md").write_text(r + "\n" if r else "", encoding="utf-8")
    if not sid:
        raise ValueError("no session id in the reviewer's log")
    (outdir / "session").write_text(sid + "\n", encoding="utf-8")


def run_reviewer(outdir: Path) -> int:
    """Run the reviewer and leave its exit status in outdir/rc; the caller collects it with `wait`."""
    (outdir / "pid").write_text(f"{os.getpid()}\n")
    job = json.loads((outdir / JOB).read_text(encoding="utf-8"))
    neutral = Path(job["neutral"]) if job["neutral"] else None
    if neutral:
        (outdir / "neutral").write_text(f"{neutral}\n", encoding="utf-8")
    cmd, env, log = reviewer_command(job, outdir)
    err, why = outdir / "err.txt", outdir / "why"
    rc = run_with_deadline(cmd, env, job["cwd"], outdir / "payload.md", outdir / log, err, job["deadline"])
    if rc == 0:
        try:
            extract(job["backend"], outdir)
        except Exception as exc:  # noqa: BLE001 — recorded as "no answer or session id"
            with err.open("a", encoding="utf-8") as f:
                f.write(f"{exc}\n")
            rc = 4
    if rc == 0 and not nonempty(outdir / "out.md"):
        with why.open("a", encoding="utf-8") as f:
            f.write(f"review.sh: no answer; see {shown(outdir)}/err.txt\n")
        rc = 4
    if rc == 0 and last_line(outdir / "out.md") != MARKER:
        with why.open("a", encoding="utf-8") as f:
            f.write(f"review.sh: answer lacks the closing {MARKER} line; the round failed\n")
        rc = 5
    if neutral:
        remove_tree(neutral)
    return publish(outdir, rc)


def publish(outdir: Path, rc: int, why_line: str = "") -> int:
    if why_line:
        with (outdir / "why").open("a", encoding="utf-8") as f:
            f.write(why_line + "\n")
    (outdir / "rc.tmp").write_text(f"{rc}\n")
    (outdir / "rc.tmp").replace(outdir / "rc")
    return rc


def runner(outdir: Path) -> int:
    if WINDOWS:
        try:
            keep = win_job_dies_with_me()  # noqa: F841 — the handle closes when the runner exits
        except OSError as exc:
            # Without it a killed runner, or a reviewer that survives taskkill, would run unbounded.
            (outdir / "pid").write_text(f"{os.getpid()}\n")
            neutral = json.loads((outdir / JOB).read_text(encoding="utf-8"))["neutral"]
            if neutral:
                remove_tree(Path(neutral))
            return publish(outdir, 2, f"review.sh: cannot hold the reviewer in a job object, so nothing ran: {exc}")
    return run_reviewer(outdir)


def main(argv: list[str]) -> int:
    try:
        if argv and argv[0] in ("--get", "--print-config"):
            return models_conf.main(argv)
        if argv and argv[0] in ("wait", "cancel"):
            return collect(argv)
        if argv and argv[0] == "_run" and len(argv) == 2:
            return runner(Path(argv[1]))
        return start(argv)
    except Exit as exc:
        return exc.code


if __name__ == "__main__":
    # Every file here is UTF-8; a redirected stream on Windows defaults to the ANSI code page.
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:
            stream.reconfigure(encoding="utf-8", errors=stream.errors)
    sys.exit(main(sys.argv[1:]))

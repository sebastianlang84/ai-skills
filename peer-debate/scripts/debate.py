#!/usr/bin/env python3
"""peer-debate — relay two independent model instances through an argued question.

The orchestrating agent is the transport and the judge; this script only moves turns.

Python rather than shell on purpose: the only thing a debate needs beyond agy itself is an
interpreter, and this one runs the same way on Linux, macOS and Windows. A shell version needed
GNU coreutils for its turn deadline and GNU globbing to find a run, so it silently degraded
wherever those differ.

    debate.py init  <slug> <question-file>   create the run, put the question to both sides blind
    debate.py round <slug>                   one exchange: A answers B, then B answers A
    debate.py ask   <slug> A|B <message>     put one message to one side (orchestrator injection)
    debate.py show  <slug>                   print the transcript
    debate.py check                          report whether this machine can run a debate

Configuration, all optional, all environment variables:

    PEER_DEBATE_ROOT         where run directories are created   (default ~/peer-debates)
    PEER_DEBATE_MODEL        model both sides run                 (default agy:gemini-3.8-flash-medium)
    PEER_DEBATE_MODEL_A/_B   model for one side, overrides PEER_DEBATE_MODEL
    PEER_DEBATE_EFFORT       reasoning effort both sides run      (default medium)
    PEER_DEBATE_EFFORT_A/_B  effort for one side
    PEER_DEBATE_TIMEOUT      seconds per turn                     (default 3600)

A model is `<cli>:<id>` with cli `agy` or `codex`; a bare id means agy. Sides may differ:
`PEER_DEBATE_MODEL_A=agy:gemini-3.8-flash-medium PEER_DEBATE_MODEL_B=codex:gpt-5.6-terra` puts
Gemini against a Codex model. What each side runs is fixed at `init` in `sides.json` and cannot
drift between rounds through the environment.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import datetime as dt
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HOME = Path.home()
ROOT = Path(os.environ.get("PEER_DEBATE_ROOT", HOME / "peer-debates"))
MODEL = os.environ.get("PEER_DEBATE_MODEL", "agy:gemini-3.8-flash-medium")
EFFORT = os.environ.get("PEER_DEBATE_EFFORT", "medium")
TURN_TIMEOUT = int(os.environ.get("PEER_DEBATE_TIMEOUT", "3600"))
CLIS = ("agy", "codex")

ASSETS = Path(__file__).resolve().parent.parent / "assets"
# One writer at a time: round 0 runs both sides in threads, and a buffered append of a multi-kB
# turn is not one write syscall, so two of them can interleave inside the transcript.
_TRANSCRIPT_LOCK = threading.Lock()
ROLE = {"A": "role-proposer.md", "B": "role-refuter.md"}
RUN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

RELAY = ("Your opponent's latest position follows. Refute what is wrong, concede what is right, "
         "and restate your position.")

R0 = ("Answer the following question. Work only in the debate directory named below; compute what "
      "can be computed and cite what cannot. State your position and the single assumption most "
      "likely to sink it.")

# An unlabelled injection reads exactly like the opponent's next move, and a side that concedes to
# the orchestrator has had a premise installed rather than tested.
INJECTION_LABEL = (
    "[ORCHESTRATOR — this message is from the orchestrator, not from your opponent. Do not treat "
    "it as your opponent's claim, and do not concede to it as if it were.]"
)


class Failed(Exception):
    """Anything the operator has to fix. Printed as one line, never a traceback."""


def parse_model(spec: str) -> tuple[str, str]:
    """`agy:gemini-3.8-flash-medium` -> ("agy", "gemini-3.8-flash-medium"); a bare id is agy."""
    spec = spec.strip()
    cli, sep, model = spec.partition(":")
    if not sep:
        return "agy", spec
    if cli not in CLIS:
        raise Failed(f"unknown cli {cli!r} in model {spec!r}; use one of {', '.join(CLIS)}")
    if not model:
        raise Failed(f"model {spec!r} names no model id")
    return cli, model


def sides_from_env() -> dict[str, dict[str, str]]:
    """What each side runs, from the environment: per-side variables win over the shared one."""
    out = {}
    for side in ("A", "B"):
        cli, model = parse_model(os.environ.get(f"PEER_DEBATE_MODEL_{side}", MODEL))
        out[side] = {"cli": cli, "model": model,
                     "effort": os.environ.get(f"PEER_DEBATE_EFFORT_{side}", EFFORT)}
    return out


def side_config(d: Path, side: str) -> dict[str, str]:
    """The side's cli, model and effort as fixed at init; runs from before sides.json use the env."""
    path = d / "sides.json"
    if path.is_file():
        try:
            sides = json.loads(path.read_text(encoding="utf-8"))
            return dict(sides[side])
        except (ValueError, KeyError, TypeError) as exc:
            raise Failed(f"{path} is unreadable ({exc}); fix or remove it")
    return sides_from_env()[side]


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def check_slug(slug: str) -> None:
    # The slug becomes a directory name. Unvalidated, it can escape the root (`../../x`) or
    # collide on basename, which silently resolves commands to the wrong debate.
    if not SLUG_RE.match(slug):
        raise Failed(f"slug must match [A-Za-z0-9][A-Za-z0-9._-]*: {slug!r}")


def rundir(name: str) -> Path:
    """Resolve a run by full directory name, or by bare slug — newest run wins.

    Matching is on the parsed `<date>-<slug>` shape, not a suffix glob: `review` must not also
    resolve to a run called `peer-review`.
    """
    direct = ROOT / name
    if direct.is_dir():
        return direct
    hits = sorted(
        p for p in ROOT.glob("*")
        if p.is_dir() and (m := RUN_RE.match(p.name)) and m.group("slug") == name
    )
    if not hits:
        raise Failed(f"no such run: {name}")
    return hits[-1]


def parse_agy_result(stdout: str, stderr: str, side: str) -> tuple[str, str, str]:
    """Validate agy's headless JSON result and return reply, conversation id and usage stamp."""
    try:
        result = json.loads(stdout)
    except (TypeError, ValueError) as exc:
        raise Failed(f"side {side} returned invalid agy JSON ({exc}); nothing recorded")
    if not isinstance(result, dict):
        raise Failed(f"side {side} returned a non-object agy result; nothing recorded")
    if result.get("status") != "SUCCESS":
        raise Failed(f"side {side} returned agy status {result.get('status')!r}; nothing recorded")
    reply = result.get("response")
    conversation = result.get("conversation_id")
    if not isinstance(reply, str) or not reply.strip():
        tail = stderr.strip().splitlines()[-3:]
        detail = "\n  " + "\n  ".join(tail) if tail else ""
        raise Failed(f"side {side} returned an empty reply; nothing recorded{detail}")
    if not isinstance(conversation, str) or not conversation:
        raise Failed(f"side {side} returned no conversation_id; nothing recorded")
    usage = result.get("usage")
    if not isinstance(usage, dict):
        stamp = "usage=unavailable"
    else:
        stamp = (
            f"turns={result.get('num_turns', '?')} "
            f"in={usage.get('input_tokens', '?')} cached={usage.get('cache_read_tokens', '?')} "
            f"thinking={usage.get('thinking_tokens', '?')} out={usage.get('output_tokens', '?')} "
            f"total={usage.get('total_tokens', '?')} cumulative-for-this-side"
        )
    return reply.strip(), conversation, stamp


def parse_codex_result(stdout: str, stderr: str, side: str) -> tuple[str, str, str]:
    """Validate `codex exec --json` JSONL and return reply, thread id and usage stamp.

    Measured on codex-cli 0.152.1: `thread.started` carries the thread id, each assistant message
    is an `item.completed` with `item.type == "agent_message"`, `turn.completed` carries usage,
    and a refused model arrives as `error` plus `turn.failed` with exit status 0.
    """
    thread = None
    replies: list[str] = []
    usage = None
    errors: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "thread.started" and isinstance(event.get("thread_id"), str):
            thread = event["thread_id"]
        elif kind == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                replies.append(item["text"])
            elif item.get("type") == "error" and isinstance(item.get("message"), str):
                # Advisory (e.g. a model-mismatch note on resume); loud only if no reply follows.
                errors.append(item["message"])
        elif kind == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        elif kind in ("error", "turn.failed"):
            message = event.get("message") or (event.get("error") or {}).get("message")
            errors.append(str(message))
    if not thread:
        tail = stderr.strip().splitlines()[-3:]
        detail = "\n  " + "\n  ".join(tail) if tail else ""
        raise Failed(f"side {side} returned no codex thread id; nothing recorded{detail}")
    if not replies or not replies[-1].strip():
        detail = "\n  " + "\n  ".join(errors[-3:]) if errors else ""
        raise Failed(f"side {side} returned an empty reply; nothing recorded{detail}")
    if usage is None:
        stamp = "usage=unavailable"
    else:
        stamp = (
            f"in={usage.get('input_tokens', '?')} cached={usage.get('cached_input_tokens', '?')} "
            f"thinking={usage.get('reasoning_output_tokens', '?')} "
            f"out={usage.get('output_tokens', '?')} this-turn"
        )
    return replies[-1].strip(), thread, stamp


def agy_command(exe: str, work: Path, msg_file: Path, model: str, effort: str,
                conversation: str | None) -> list[str]:
    cmd = [exe]
    if conversation is not None:
        cmd.extend(["--conversation", conversation])
    cmd.extend([
        "--print", f"Read {msg_file}. It is this turn's complete message. Answer it.",
        "--add-dir", str(work),
        "--output-format", "json",
        "--model", model,
        "--effort", effort,
        "--mode", "accept-edits",
        # Headless agy soft-denies tools that would normally prompt. This private experiment host
        # deliberately gives both sides the full configured agy tool surface without interruptions.
        "--dangerously-skip-permissions",
        "--disable-slash-commands",
        "--print-timeout", f"{TURN_TIMEOUT}s",
    ])
    return cmd


def codex_command(exe: str, work: Path, msg_file: Path, model: str, effort: str,
                  thread: str | None) -> list[str]:
    cmd = [exe, "exec"]
    if thread is not None:
        # The model must be repeated on resume: without it codex resumes under its default model
        # and only notes the mismatch (measured 0.152.1).
        cmd.extend(["resume", thread])
    else:
        # `resume` accepts neither -C nor --add-dir nor --color (0.152.1); the working root is
        # remembered by the thread, and the process cwd is the side's directory either way.
        cmd.extend(["-C", str(work), "--add-dir", str(work), "--color", "never"])
    cmd.extend([
        "-m", model,
        "-c", f"model_reasoning_effort={effort}",
        # The SessionEnd hook on this host compacts the thread after every exec and holds its
        # writer lock for minutes; a resume in that window fails with "already has an active
        # writer". Hooks are therefore off for debate turns.
        "-c", "features.hooks=false",
        "--skip-git-repo-check",
        # Same grant as the agy side: full tools, no sandbox, no prompts. See tool-policy.md.
        "--dangerously-bypass-approvals-and-sandbox",
        "--json",
        f"Read {msg_file}. It is this turn's complete message. Answer it.",
    ])
    return cmd


def turn(run: str, side: str, message: str) -> str:
    """One turn against one side's persistent session. Returns the reply, records it."""
    if side not in ROLE:
        raise Failed(f"side must be A or B, not {side!r}")
    d = rundir(run)
    cfg = side_config(d, side)
    cli, model, effort = cfg["cli"], cfg["model"], cfg["effort"]

    # Each side works in its own directory. Sharing one made round 0 blind in name only: the
    # second side could read the first side's scripts and reply before answering.
    work = d / side
    work.mkdir(parents=True, exist_ok=True)

    exe = shutil.which(cli)
    if exe is None:
        raise Failed(f"{cli} is not on PATH — run `debate.py check`")

    conversation_file = d / f"conversation-{side}.txt"
    existing_conversation = None
    if conversation_file.is_file():
        existing_conversation = conversation_file.read_text(encoding="utf-8").strip()
        if not existing_conversation:
            raise Failed(f"side {side} has an empty conversation id file")

    # agy has no append-system-prompt flag. The role therefore enters the first user turn and is
    # retained by agy's conversation. Keeping the long payload in a file avoids argv limits.
    turn_message = message
    if existing_conversation is None:
        role = (ASSETS / ROLE[side]).read_text(encoding="utf-8")
        turn_message = (
            f"# Binding role instructions\n\n{role}\n\n"
            f"Your debate working directory is `{work}`. Use absolute paths under that directory "
            f"for every script, datum and result. Do not use {cli}'s scratch or brain directories.\n\n"
            f"# Turn message\n\n{message}"
        )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", dir=str(work),
                                     delete=False) as fh:
        fh.write(turn_message)
        msg_file = Path(fh.name)
    build = codex_command if cli == "codex" else agy_command
    cmd = build(exe, work, msg_file, model, effort, existing_conversation)
    try:
        # encoding is explicit: text=True alone decodes with the locale codec, and on a
        # cp1252 console every µ, — or ° in a reply raises or silently corrupts.
        proc = subprocess.run(cmd, cwd=work, stdin=subprocess.DEVNULL,
                              capture_output=True, encoding="utf-8", errors="replace",
                              timeout=TURN_TIMEOUT + 30)
    except subprocess.TimeoutExpired:
        raise Failed(f"side {side} hit the {TURN_TIMEOUT}s turn limit and was killed. The session "
                     f"may already hold this prompt, so its history and the transcript can differ; "
                     f"nothing was recorded here")
    except OSError as exc:
        raise Failed(f"could not run {cli} ({exc}) — run `debate.py check`")
    finally:
        msg_file.unlink(missing_ok=True)

    # A killed or failed turn must be loud and must not be recorded: a silently empty turn reads
    # downstream as a side that had nothing to say.
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise Failed(f"side {side} exited with status {proc.returncode}; nothing recorded"
                     + ("\n  " + "\n  ".join(tail) if tail else ""))
    parse = parse_codex_result if cli == "codex" else parse_agy_result
    reply, conversation, usage = parse(proc.stdout, proc.stderr, side)
    if existing_conversation is not None and conversation != existing_conversation:
        raise Failed(f"side {side} resumed {existing_conversation} but {cli} returned "
                     f"{conversation}; nothing recorded")

    conversation_tmp = d / f"conversation-{side}.txt.tmp"
    conversation_tmp.write_text(conversation + "\n", encoding="utf-8")
    conversation_tmp.replace(conversation_file)

    # Composed first, appended in one write, so two turns running at once cannot interleave.
    entry = (f"\n## {now()} -> {side}\n\n"
             f"<!-- cli={cli} model={model} effort={effort} {usage} -->\n\n{reply}\n")
    with _TRANSCRIPT_LOCK:
        with (d / "transcript.md").open("a", encoding="utf-8") as fh:
            fh.write(entry)
            fh.flush()
    tmp = d / f"last-{side}.md.tmp"
    tmp.write_text(reply + "\n", encoding="utf-8")
    tmp.replace(d / f"last-{side}.md")
    return reply


# Tools a debater is likely to reach for. What is absent shapes what it can honestly claim, so
# the answer belongs in the run rather than in the operator's head.
PROBED = ["agy", "codex", "python3", "git", "docker", "rg", "grep", "curl", "gnuplot", "sqlite3",
          "codemap", "ast-grep", "pandoc", "latexmk"]


def _local_ip() -> str:
    """The address this host would use to reach the network; no packet is sent."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 1))  # TEST-NET-1, unrouted by definition
            return sock.getsockname()[0]
    except OSError:
        return "no route to a network"


def _cli_version(cli: str, exe: str) -> str:
    args = [exe, "changelog"] if cli == "agy" else [exe, "--version"]
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=60).stdout
        first = out.strip().splitlines()
        return first[0].rstrip(":") if first else "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def machine_facts(sides: dict[str, dict[str, str]] | None = None) -> tuple[list[str], bool]:
    """What this machine is and what a debater can reach on it. Returns lines plus readiness."""
    ok = True
    sides = sides or sides_from_env()
    clis = sorted({cfg["cli"] for cfg in sides.values()})
    exes = {cli: shutil.which(cli) for cli in clis}
    # Today's date first: a model answers from a training cutoff and will otherwise assume a
    # wrong "now" — which silently decides any question about versions, prices or recency.
    lines = [
        f"date and time   {now()}  (this is the real current time, not your training cutoff)",
        f"platform        {platform.system()} {platform.release()} ({platform.machine()})",
        f"python          {sys.version.split()[0]} ({sys.executable})",
    ]
    for cli in clis:
        exe = exes[cli]
        lines.append(f"{cli:<15} {exe or f'NOT FOUND — install {cli} and put it on PATH'}")
        if exe:
            lines.append(f"{cli + ' version':<15} {_cli_version(cli, exe)}")
        ok &= bool(exe)
    for side, cfg in sides.items():
        lines.append(f"side {side}          {cfg['cli']}:{cfg['model']}, effort={cfg['effort']}")
    lines.extend([
        "execution       headless, full configured tools, no sandbox or prompts, on both clis",
        f"turn limit      {TURN_TIMEOUT}s",
        f"run root        {ROOT} {'(exists)' if ROOT.is_dir() else '(will be created)'}",
        "sessions        one conversation/thread id per side, stored in the run directory",
    ])
    roles_ok = all((ASSETS / r).is_file() for r in ROLE.values())
    lines.append(f"role prompts    {ASSETS} {'(ok)' if roles_ok else 'MISSING'}")
    ok &= roles_ok

    # Capacity, because a side that does not know it has 8 cores and 2 GB free will either
    # attempt a model that cannot run or refuse one that could.
    try:
        import multiprocessing
        cores = multiprocessing.cpu_count()
    except Exception:
        cores = "unknown"
    mem = "unknown"
    try:
        pages, size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
        mem = f"{pages * size / 2**30:.1f} GiB"
    except (ValueError, OSError, AttributeError):
        pass
    disk = "unknown"
    try:
        base = ROOT if ROOT.is_dir() else ROOT.parent
        disk = f"{shutil.disk_usage(base).free / 2**30:.1f} GiB free"
    except OSError:
        pass
    lines.append(f"capacity        {cores} cores, {mem} RAM, {disk} under the run root")
    lines.append(f"host            {socket.gethostname()} ({_local_ip()})")

    # Which numeric libraries exist decides whether a claim can be computed or only asserted.
    names = ("numpy", "scipy", "pandas", "matplotlib", "sympy", "networkx")
    probe = shutil.which("python3") or shutil.which("python")
    libs = None
    if probe:
        # Probe the interpreter a debater reaches through its shell, which need not be the one
        # running this script — a false "absent" tells a side a capability it has is missing.
        code = ("import importlib.util as u;"
                f"print(','.join(n for n in {names!r} if u.find_spec(n)))")
        try:
            out = subprocess.run([probe, "-c", code], capture_output=True, text=True, timeout=120)
            if out.returncode == 0:
                have = set(filter(None, out.stdout.strip().split(",")))
                libs = [n if n in have else f"{n}(absent)" for n in names]
        except (subprocess.SubprocessError, OSError):
            libs = None
    if libs is None:
        lines.append(f"python libs     unknown — could not probe {probe or 'any interpreter'}; "
                     f"check before assuming one is missing")
    else:
        lines.append(f"python libs     ({Path(probe).name}) " + ", ".join(libs))

    found = [c for c in PROBED if shutil.which(c)]
    missing = [c for c in PROBED if c not in found]
    lines.append("on PATH         " + ", ".join(found))
    lines.append("absent          " + (", ".join(missing) or "none of the probed set"))

    # agy lists its models; codex has no such command, so a wrong codex id surfaces only in
    # round 0 (as `turn.failed` — measured: gpt-5.4-terra is refused under a ChatGPT account).
    agy_models = {cfg["model"] for cfg in sides.values() if cfg["cli"] == "agy"}
    if agy_models and exes.get("agy"):
        try:
            proc = subprocess.run([exes["agy"], "models"], capture_output=True, text=True,
                                  timeout=120)
            listed = {line.split("\t", 1)[0] for line in proc.stdout.splitlines()}
            for model in sorted(agy_models):
                if proc.returncode == 0 and model in listed:
                    lines.append(f"model reachable {model} listed by agy")
                else:
                    lines.append(f"model reachable {model} NOT LISTED by agy — check the id")
                    ok = False
        except (subprocess.SubprocessError, OSError) as exc:
            lines.append(f"model reachable could not ask agy: {exc}")
            ok = False
    for cfg in sides.values():
        if cfg["cli"] == "codex":
            lines.append(f"model reachable {cfg['model']} not verifiable before round 0 (codex "
                         "lists no models)")
    return lines, ok


def cmd_check(_args) -> int:
    """Say whether this machine can run a debate, and name what is missing if not."""
    lines, ok = machine_facts()
    print("\n".join(lines))
    print("\n" + ("ready" if ok else "not ready — fix the lines above"))
    return 0 if ok else 1


def cmd_init(args) -> int:
    check_slug(args.slug)
    qfile = Path(args.question)
    if not qfile.is_file():
        raise Failed(f"no such question file: {qfile}")
    d = ROOT / f"{dt.date.today().isoformat()}-{args.slug}"
    if d.exists():
        raise Failed(f"run already exists: {d}")
    d.mkdir(parents=True)
    shutil.copyfile(qfile, d / "question.md")
    # Fixed here, read by every later turn: a model swapped through the environment mid-debate
    # would otherwise resume a Gemini conversation under a Codex id and fail, or worse, not.
    sides = sides_from_env()
    (d / "sides.json").write_text(json.dumps(sides, indent=2) + "\n", encoding="utf-8")
    (d / "transcript.md").write_text(
        f"# peer-debate: {args.slug}\n\nQuestion: see question.md\n", encoding="utf-8")

    # The machine is part of the question: a side that does not know what it can run will
    # either claim what it cannot verify, or fail to compute what it could have.
    facts, _ = machine_facts(sides)
    (d / "environment.md").write_text(
        "# The machine this debate runs on\n\n```\n" + "\n".join(facts) + "\n```\n",
        encoding="utf-8")
    for side in ("A", "B"):
        work = d / side
        work.mkdir()
        shutil.copyfile(d / "environment.md", work / "environment.md")

    prompt = (R0 + "\n\nWhat this machine is, and what you can reach on it, is recorded in "
              "`environment.md`. Read it before claiming a tool is unavailable.\n\n"
              + (d / "question.md").read_text(encoding="utf-8"))
    # Round 0 is blind on both sides, so nothing connects them and they run at once. Sequentially
    # this cost the slower side's wall clock plus the faster side's for nothing.
    with futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {side: pool.submit(turn, d.name, side, prompt) for side in ("A", "B")}
        errors = []
        for side, job in jobs.items():
            try:
                job.result()
            except Failed as exc:
                errors.append(f"round 0 failed on side {side}: {exc}")
    if errors:
        raise Failed("\n".join(errors))
    print(d)
    return 0


def cmd_round(args) -> int:
    d = rundir(args.slug)
    if not (d / "last-A.md").is_file() or not (d / "last-B.md").is_file():
        raise Failed("run round only after both sides answered round 0")
    turn(d.name, "A", RELAY + "\n\n" + (d / "last-B.md").read_text(encoding="utf-8"))
    print(turn(d.name, "B", RELAY + "\n\n" + (d / "last-A.md").read_text(encoding="utf-8")))
    return 0


def cmd_ask(args) -> int:
    print(turn(rundir(args.slug).name, args.side,
               INJECTION_LABEL + "\n\n" + args.message))
    return 0


def cmd_show(args) -> int:
    sys.stdout.write((rundir(args.slug) / "transcript.md").read_text(encoding="utf-8"))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="debate.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create the run, put the question to both sides blind")
    s.add_argument("slug"); s.add_argument("question"); s.set_defaults(fn=cmd_init)

    s = sub.add_parser("round", help="one exchange: A answers B, then B answers A")
    s.add_argument("slug"); s.set_defaults(fn=cmd_round)

    s = sub.add_parser("ask", help="put one message to one side (labelled as the orchestrator's)")
    s.add_argument("slug"); s.add_argument("side", choices=["A", "B"]); s.add_argument("message")
    s.set_defaults(fn=cmd_ask)

    s = sub.add_parser("show", help="print the transcript")
    s.add_argument("slug"); s.set_defaults(fn=cmd_show)

    s = sub.add_parser("check", help="report whether this machine can run a debate")
    s.set_defaults(fn=cmd_check)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except Failed as exc:
        print(f"peer-debate: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

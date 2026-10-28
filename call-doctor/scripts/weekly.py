#!/usr/bin/env python3
"""weekly.py — the weekly context-engineering analysis over all human agent sessions of a week.

    weekly.py [--days 7] [--out <dir>] [--evidence-only] [--no-kb]

Finds the Claude Code transcripts and Codex rollouts written in the window, keeps the sessions a
human drove (two or more own user messages; reviewer and worker runs are left out), and marks
signal hits: user messages that look like a correction ("nein", "falsch", "hab ich doch gesagt",
...) and interruptions. Around every hit it cuts an excerpt (the agent's turn before, its reaction
after) with collect.py's parser and redaction, then hands the evidence of each patient vendor to
the other vendor through using-harnesses' review.py, as call-doctor does for one session: Claude
sessions to codex, Codex sessions to claude. Each call is skipped when its subscription has less
than the reserve left (show-quota.py).

The doctor answers with findings as JSON. Every cited `S<k>:L<n>` is checked against the
evidence; a finding with no resolvable line drops to `schwach`. The report (German, findings
grouped by strength of evidence with counts, then every signal hit) goes to
<out>/<date>.md; evidence and raw answers to <out>/<date>/. Findings with `weg: ticket` become kb
tasks for the repo that owns the file (kb refuses a near-duplicate of an open ticket); those with
`weg: entscheidung` become one kb request to the curator. Python 3.9, stdlib.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect  # noqa: E402  (Bundle, parse_claude, parse_codex, redact, clip)

HOME = os.path.expanduser("~")
REFS = os.path.join(HERE, "..", "references")
REVIEW = os.path.join(HERE, "..", "..", "using-harnesses", "scripts", "review.py")
QUOTA = os.path.join(HOME, ".agents", "scripts", "show-quota.py")
DEFAULT_OUT = os.path.join(HOME, ".agents", "state", "kontext-woche")
BUDGET = 300 * 1024          # evidence per doctor call
SESSION_CAP = 180 * 1024     # one session's share of it
RESERVE = {"codex": 20, "claude": 15}   # percent of the weekly window that must stay free
# Projects of contained reviewer runs and experiment sandboxes: never a human session.
SKIP_PROJECT = re.compile(r"claude-review|-cache-|-state-market-digest-experiments|agentsmd-test")

SIGNAL = re.compile(
    r"\b(nein|falsch|stopp?|nicht so|so nicht|schon wieder|wieder (?:mal|nicht)|immer noch|wie (?:oft|gesagt)"
    r"|hab(?:e)? ich (?:doch|dir|schon|gesagt|geschrieben)|ich hab(?:e)? (?:dir|doch)"
    r"|(?:warum|wieso|weshalb) (?:hast|machst|fragst|schreibst|ignorierst) du|du sollst|verstehst du|kapier\w*"
    r"|ignorier\w*|vergessen|fuck\w*|schei(?:ß|ss)e?|wtf|bullshit|sinnlos|wahnsinn|wie kommst du|was soll (?:das|ein)"
    r"|merk(?:e)? dir|in zukunft|ab jetzt|künftig|nie wieder|jedes mal|wrong|why did you|i told you)\b|[!?]{3,}",
    re.I)
INTERRUPT = re.compile(r"^\[Request interrupted by user|^<turn_aborted>")
NOT_HUMAN = ("<command-name>", "<command-message>", "<local-command", "<task-notification>",
             "<side-sessions-event>", "<cross-session-message", "<ci-monitor-event>", "<bash-", "Caveat:",
             "This session is being continued from a previous conversation", "<user_shell_command>",
             "<environment_context>", "# AGENTS.md instructions")
REMINDER = re.compile(r"<system-reminder>[\s\S]*?</system-reminder>")
HUMAN_ENTRY = ("claude-desktop", "cli")   # sdk-cli is every claude -p and SDK run
GENERIC = ("System prompt", "Skill listing", "Output style", "mcp_instructions_delta", "language", "auto_mode",
           "model", "Developer message", "Environment context", "Codex base instructions")
BEFUND_KEYS = ("titel", "staerke", "ursache", "aenderung", "ort", "weg")
REF = re.compile(r"S(\d+):L(\d+)")


def own_text(kind: str, text: str) -> str | None:
    """The user's own words of a USER event, or None for harness-injected text."""
    if kind != "USER":
        return None
    t = REMINDER.sub("", text).strip()
    if not t or t.startswith(NOT_HUMAN):
        return None
    return t


def when(e: dict) -> dt.datetime | None:
    ts = e.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


class Session:
    def __init__(self, path: str, vendor: str):
        self.path, self.vendor = path, vendor
        self.cwd = self.entry = ""
        self.events: list[tuple[int, str, str]] = []
        self.loaded: list[str] = []
        self.users = 0
        self.hits: list[tuple[int, str, str]] = []   # (line, "korrektur"|"abbruch", text)
        self.key = ""
        self.cited: set[int] = set()   # lines the doctor saw in the evidence


def load(path: str, vendor: str, since: dt.datetime, seen: set) -> Session | None:
    """A human session with its signal hits in the window; `seen` drops a hit that a forked or
    resumed transcript already carried (same time, same text)."""
    raw = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict):
                raw.append((n, e))
    if not raw:
        return None
    s = Session(path, vendor)
    if vendor == "codex":
        meta = next((e.get("payload") or {} for _, e in raw[:5] if e.get("type") == "session_meta"), None)
        if meta is None or not isinstance(meta.get("source"), str) or meta.get("originator") == "codex_exec":
            return None   # exec workers, reviewers and subagents
        s.cwd, s.entry = meta.get("cwd") or "", f"{meta.get('originator')}"
    else:
        first = next((e for _, e in raw if e.get("cwd")), {})
        s.cwd, s.entry = first.get("cwd") or "", first.get("entrypoint") or ""
        if s.entry not in HUMAN_ENTRY:
            return None   # claude -p workers, nightshift, reviewers, apps on the SDK
    b = collect.Bundle()
    (collect.parse_codex if vendor == "codex" else collect.parse_claude)(raw, b)
    s.events = [ev for ev in b.events if ev[1] != "thinking"]
    s.loaded = sorted({t for t, _ in b.context if not t.startswith(GENERIC)})
    at = {n: when(e) for n, e in raw}
    for n, kind, txt in s.events:
        t = own_text(kind, txt)
        if t is None:
            continue
        stripped = t.lstrip()
        if not INTERRUPT.match(stripped):
            s.users += 1
        ts = at.get(n)
        if ts is None or ts < since or (ts, t[:300]) in seen:
            continue
        seen.add((ts, t[:300]))
        if INTERRUPT.match(stripped):
            s.hits.append((n, "abbruch", t))
        elif SIGNAL.search(t):
            s.hits.append((n, "korrektur", t))
    return s if s.users >= 2 and s.hits else None


def weight(hit: tuple[int, str, str]) -> int:
    """How strongly a hit reads as a correction; decides which hits get an excerpt first."""
    return len(SIGNAL.findall(hit[2])) + (hit[1] == "abbruch")


def excerpt(s: Session, hit_line: int) -> list[str]:
    """The agent turn before the hit (back to the previous user message, at most ten entries),
    the hit itself and the next three entries."""
    idx = next(i for i, ev in enumerate(s.events) if ev[0] == hit_line and ev[1] == "USER")
    start = idx
    while start > 0 and idx - start < 10 and s.events[start - 1][1] != "USER":
        start -= 1
    if start > 0 and s.events[start - 1][1] == "USER":
        start -= 1
    cap = {"USER": 1500, "ASSISTANT": 1500, "tool": 400, "result": 400, "COMPACTION": 400, "file": 200, "meta": 200}
    out = []
    for i in range(start, min(len(s.events), idx + 4)):
        n, kind, txt = s.events[i]
        if not txt.strip():
            continue
        out.append(f"L{n} {kind}: " + (collect.clip(txt, 4000) if i == idx else collect.clip(txt, cap.get(kind, 300))))
    return out


def evidence(sessions: list[Session]) -> tuple[str, dict[str, Session]]:
    parts, rest, keys = [], [], {}
    used = 0
    for s in sessions:
        keys[s.key] = s
        head = [f"## {s.key}: {s.vendor}, {s.entry}, cwd {s.cwd}",
                f"transcript: {s.path}; own user messages {s.users}; signal hits in window {len(s.hits)}",
                "loaded: " + ("; ".join(s.loaded) or "none recorded")]
        body, shown = [], set()
        for n, kind, txt in sorted(s.hits, key=lambda h: -weight(h)):
            block = [f"### {s.key}:L{n} ({kind})"] + [x for x in excerpt(s, n) if x not in shown]
            size = len("\n".join(block).encode())
            if used + size > BUDGET or len("\n".join(body).encode()) + size > SESSION_CAP:
                rest.append(f"{s.key}:L{n} ({kind}): {collect.clip(txt, 200)}")
                s.cited.add(n)
                continue
            shown.update(block[1:])
            s.cited.update(int(x[1:].split(" ", 1)[0]) for x in block[1:])
            body += [""] + block
            used += size
        parts += ["", *head, *body]
    if rest:
        parts += ["", "## Hits without excerpt", *rest]
    return collect.redact("# Evidence: one week of sessions\n" + "\n".join(parts) + "\n"), keys


def context_file(sessions: list[Session]) -> str:
    out = ["# Context on disk now", "", "## ~/.agents/AGENTS.md (global rules)",
           open(os.path.join(HOME, ".agents", "AGENTS.md"), encoding="utf-8").read(), "", "## Global skills"]
    for p in sorted(glob.glob(os.path.join(HOME, ".agents", "skills", "*", "SKILL.md"))):
        m = re.search(r"^description:\s*(.+)$", open(p, encoding="utf-8").read(), re.M)
        out.append(f"- {os.path.basename(os.path.dirname(p))} ({p}): {(m.group(1) if m else '').strip()}")
    repos: dict[str, int] = {}
    for s in sessions:
        top = git_top(s.cwd)
        if top and top != os.path.join(HOME, ".agents"):
            repos[top] = repos.get(top, 0) + len(s.hits)
    for top, _ in sorted(repos.items(), key=lambda x: -x[1])[:3]:
        p = os.path.join(top, "AGENTS.md")
        if os.path.isfile(p):
            out += ["", f"## {p}", collect.clip(open(p, encoding="utf-8", errors="replace").read(), 15000)]
    return collect.redact("\n".join(out) + "\n")


def git_top(path: str) -> str:
    d = path
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    if not d:
        return ""
    p = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def quota_free() -> dict[str, float | None]:
    try:
        q = json.loads(subprocess.run([sys.executable, QUOTA, "--json"], capture_output=True, text=True,
                                      timeout=120).stdout)
    except (ValueError, subprocess.SubprocessError, OSError):
        return {"codex": None, "claude": None}
    cx = next((w.get("usedPercent") for w in ((q.get("codex") or {}).get(k) for k in ("primary", "secondary"))
               if isinstance(w, dict) and w.get("windowDurationMins") == 7 * 24 * 60), None)
    cl = ((q.get("claude") or {}).get("seven_day") or {}).get("utilization")
    return {"codex": None if cx is None else 100 - cx, "claude": None if cl is None else 100 - cl}


def ask_doctor(doctor: str, work: str, files: list[str]) -> tuple[str | None, str]:
    """One foreground review.py round; returns (answer, problem)."""
    p = subprocess.run([sys.executable, REVIEW, doctor, "--foreground", "--effort", "medium",
                        "--rules", os.path.join(REFS, "weekly-rules.md"), *files],
                       capture_output=True, text=True, cwd=work)
    call = (p.stdout.strip().splitlines() or [""])[0]
    out = os.path.join(call, "out.md") if call else ""
    if p.returncode != 0 or not out or not os.path.isfile(out):
        return None, f"review.py {doctor} endete mit {p.returncode}: {(p.stderr or '').strip()[-400:]}"
    return open(out, encoding="utf-8").read(), ""


def parse_answer(answer: str) -> dict:
    blocks = re.findall(r"```json\s*\n([\s\S]*?)\n```", answer)
    if not blocks:
        raise ValueError("kein json-Block in der Antwort")
    d = json.loads(blocks[-1])
    if not isinstance(d, dict) or not isinstance(d.get("befunde"), list) or not isinstance(d.get("modellverhalten"), list):
        raise ValueError("befunde und modellverhalten fehlen oder sind keine Listen")
    for f in d["befunde"]:
        if not (isinstance(f, dict) and all(isinstance(f.get(k), str) and f[k].strip() for k in BEFUND_KEYS)
                and isinstance(f.get("belege"), list) and f["staerke"] in ("stark", "mittel", "schwach")
                and f["weg"] in ("ticket", "entscheidung")):
            raise ValueError(f"Befund ohne Pflichtfelder: {collect.clip(json.dumps(f, ensure_ascii=False), 200)}")
    return d


def resolve(ref: str, keys: dict[str, Session]) -> str | None:
    """The evidence line a reference points at, as `who: quote — transcript:line`, or None."""
    m = REF.fullmatch(ref.strip())
    if not m or f"S{m.group(1)}" not in keys:
        return None
    s, n = keys[f"S{m.group(1)}"], int(m.group(2))
    if n not in s.cited:
        return None
    # A line can hold several entries; harness-injected user text (reminders, notices) is no evidence.
    ev = next(((k, own_text(k, t) if k == "USER" else t) for ln, k, t in s.events
               if ln == n and (k != "USER" or own_text(k, t))), None)
    if ev is None:
        return None
    return f"{ref} ({s.vendor}, {s.cwd.replace(HOME, '~')}) {ev[0]}: „{collect.clip(' '.join(ev[1].split()), 300)}“ — {s.path}:{n}"


STRENGTH = (("stark", "Starke Belege"), ("mittel", "Mittlere Belege"), ("schwach", "Schwache Belege"))


def render(date: str, since: str, sessions: list[Session], results: list[dict], notes: list[str]) -> tuple[str, list[dict]]:
    findings = []
    for r in results:
        for f in r["data"].get("befunde", []):
            belege = [resolve(x, r["keys"]) for x in f.get("belege", [])]
            f["_belege"] = [x for x in belege if x]
            f["_fehlend"] = [x for x, y in zip(f.get("belege", []), belege) if not y]
            st = f.get("staerke") if f.get("staerke") in ("stark", "mittel", "schwach") else "schwach"
            f["staerke"] = st if f["_belege"] else "schwach"
            f["_vendor"] = r["vendor"]
            findings.append(f)
    hits = sum(len(s.hits) for s in sessions)
    out = [f"# Kontext-Woche {date}", "",
           f"Zeitraum {since} bis {date}. {len(sessions)} Sitzungen mit Signal, {hits} Signal-Treffer, "
           f"{len(findings)} Befunde (Diagnose jeweils durch den anderen Anbieter, Belege vom Skript geprüft).", ""]
    out += [f"Hinweis: {x}" for x in notes] + ([""] if notes else [])
    nr = 0
    for key, label in STRENGTH:
        group = [f for f in findings if f["staerke"] == key]
        out += [f"## {label} ({len(group)})", ""]
        for f in group:
            nr += 1
            f["_nr"] = nr
            out += [f"{nr}. **{f.get('titel', '').strip()}**",
                    f"   Ursache: {f.get('ursache', '').strip()}",
                    f"   Änderung: {f.get('aenderung', '').strip()}",
                    f"   Ort: {f.get('ort', '').strip()}",
                    f"   Weg: {'Entscheidung durch Sebastian – ' + f.get('grund_entscheidung', '').strip() if f.get('weg') == 'entscheidung' else 'Ticket für die zuständige Sitzung'}"]
            out += [f"   Beleg: {b}" for b in f["_belege"]]
            if f["_fehlend"]:
                out.append(f"   Nicht im Beleg auffindbar: {', '.join(f['_fehlend'])}")
            out.append("")
        if not group:
            out += ["Keine.", ""]
    mv = [(m, r["keys"]) for r in results for m in r["data"].get("modellverhalten", [])]
    out += [f"## Modellverhalten, kein Kontextproblem ({len(mv)})", ""]
    for i, (m, keys) in enumerate(mv, 1):
        out.append(f"{i}. **{m.get('titel', '').strip()}**: {m.get('erklaerung', '').strip()}")
        out += [f"   Beleg: {b}" for b in (resolve(x, keys) for x in m.get("belege", [])) if b]
    if not mv:
        out.append("Keine.")
    out += ["", f"## Alle Signal-Treffer ({hits})", "",
            "Stichwort-Treffer, ungeprüft; viele sind keine Korrektur.", ""]
    i = 0
    for s in sessions:
        out.append(f"{s.key}: {s.vendor}, {s.cwd.replace(HOME, '~')}, {len(s.hits)} Treffer — {s.path}")
        for n, kind, txt in s.hits:
            i += 1
            out.append(f"{i}. L{n} {kind}: „{collect.clip(' '.join(collect.redact(txt).split()), 200)}“")
        out.append("")
    return collect.redact("\n".join(out)), findings


def kb(args: list[str], note: str = "") -> tuple[int, str]:
    p = subprocess.run(["kb", *args], input=note, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def still_open(ticket: str) -> bool:
    rc, out = kb(["show", ticket])
    m = re.search(r"^status: (\S+)", out, re.M)
    return rc == 0 and bool(m) and m.group(1) not in ("done", "abandoned")


def file_tickets(date: str, report: str, findings: list[dict], filed_path: str) -> tuple[list[str], bool]:
    """kb tasks for clear changes, one curator request for decisions. A finding goes to kb only when
    every cited line was in the evidence and its file exists; one open ticket per file across weeks
    (`filed_path` maps the file to its ticket). Returns the log and whether kb failed."""
    try:
        filed = json.load(open(filed_path, encoding="utf-8"))
    except (OSError, ValueError):
        filed = {}
    rc, tok = kb(["start", "--as", "kontext-woche"])
    if rc != 0:
        return [f"kb nicht erreichbar: {tok[-200:]}"], True
    tok = tok.split()[-1]
    log, decide, failed = [], [], False
    for f in findings:
        ort = os.path.realpath(os.path.expanduser(f["ort"].strip()))
        repo = os.path.basename(git_top(ort)) if os.path.isfile(ort) else ""
        if f["_fehlend"] or not f["_belege"] or not repo:
            why = "Beleg nicht im Auszug" if f["_fehlend"] or not f["_belege"] else "Datei existiert nicht"
            log.append(f"Befund {f['_nr']}: nicht ans Board ({why})")
            continue
        key = f"{f['weg']}:{ort}"
        old = filed.get(key)
        if old and still_open(old["id"]):
            # The same file, maybe another cause: append it, never drop it.
            rc, _ = kb(["note", "--session", tok, old["id"]], collect.redact(
                f"Kontext-Woche {date}, Befund {f['_nr']}: {f['titel']}\nÄnderung: {f['aenderung']}\n"
                + (f"Grund für die Entscheidung: {f.get('grund_entscheidung', '')}\n" if f["weg"] == "entscheidung" else "")
                + f"Bericht: {report}"))
            failed |= rc != 0
            log.append(f"Befund {f['_nr']}: an das offene Ticket {old['id']} angehängt")
            continue
        if f["weg"] == "entscheidung":
            decide.append((f, key))
            continue
        note = (f"Aus der Kontext-Woche {date}, Befund {f['_nr']} ({f['staerke']}): {report}\n"
                f"Änderung: {f['aenderung']}\nOrt: {ort}\n" + "\n".join(f["_belege"]))
        rc, out = kb(["add", "--session", tok, "--todo", "--repo", repo, "--label", "kontext-woche", "--stdin",
                      collect.clip("Kontext: " + f["titel"], 110)], collect.redact(note))
        if rc == 0:
            filed[key] = {"id": out.split()[-1], "date": date}
        failed |= rc not in (0, 2)
        log.append(f"Befund {f['_nr']}: " + ("Ticket " + out.split()[-1] if rc == 0 else
                                             "ähnliches Ticket offen, nicht neu angelegt" if rc == 2 else f"kb-Fehler {rc}"))
    if decide:
        note = f"Bericht: {report}\nZur Entscheidung:\n" + "\n".join(
            f"Befund {f['_nr']}: {f['titel']} – {f.get('grund_entscheidung', '')}" for f, _ in decide)
        rc, out = kb(["add", "--session", tok, "--type", "request", "--to", "curator", "--label", "kontext-woche",
                      "--new", "--stdin", f"Kontext-Woche {date}: {len(decide)} Änderungen zur Entscheidung"],
                     collect.redact(note))
        if rc == 0:
            filed.update({key: {"id": out.split()[-1], "date": date} for _, key in decide})
        failed |= rc != 0
        log.append("Anfrage an den Kurator: " + (out.split()[-1] if rc == 0 else f"kb-Fehler {rc}: {out[-200:]}"))
    kb(["end", "--session", tok])
    with open(filed_path, "w", encoding="utf-8") as fh:
        json.dump(filed, fh, ensure_ascii=False, indent=1)
    return log, failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--evidence-only", action="store_true", help="write the evidence, call no doctor")
    ap.add_argument("--no-kb", action="store_true", help="write no kb ticket or request")
    a = ap.parse_args()

    os.umask(0o077)
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=a.days)
    date, since_d = now.astimezone().date().isoformat(), since.astimezone().date().isoformat()
    work = os.path.join(a.out, date)
    os.makedirs(work, mode=0o700, exist_ok=True)
    os.chmod(a.out, 0o700)

    found = [(p, "claude") for p in glob.glob(f"{HOME}/.claude/projects/*/*.jsonl")
             if not SKIP_PROJECT.search(os.path.basename(os.path.dirname(p)))]
    found += [(p, "codex") for p in glob.glob(f"{HOME}/.codex/sessions/**/rollout-*.jsonl", recursive=True)]
    found = [(p, v) for p, v in found if os.path.getmtime(p) >= since.timestamp()]
    seen: set = set()
    found.sort(key=lambda x: os.path.getmtime(x[0]))
    sessions = [s for s in (load(p, v, since, seen) for p, v in found) if s]
    sessions.sort(key=lambda s: -len(s.hits))
    for i, s in enumerate(sessions, 1):
        s.key = f"S{i}"

    kbrep = os.path.join(work, "kb-report.md")
    rc, rep = kb(["report", "--days", str(a.days)])
    failed = rc != 0
    with open(kbrep, "w", encoding="utf-8") as f:
        f.write(collect.redact(collect.clip(rep if rc == 0 else "kb report nicht verfügbar", 10000)) + "\n")
    notes_kb = [] if rc == 0 else ["kb report nicht verfügbar; die Board-Nutzung fehlt in der Diagnose."]
    ctx = os.path.join(work, "context.md")
    with open(ctx, "w", encoding="utf-8") as f:
        f.write(context_file(sessions))

    free = quota_free()
    results, notes = [], [f"{len(found)} Transkripte im Zeitraum gelesen, {len(sessions)} davon menschliche Sitzungen mit Signal."] + notes_kb
    for vendor, doctor in (("claude", "codex"), ("codex", "claude")):
        group = [s for s in sessions if s.vendor == vendor]
        if not group:
            continue
        doc, keys = evidence(group)
        ev = os.path.join(work, f"evidence-{vendor}.md")
        with open(ev, "w", encoding="utf-8") as f:
            f.write(doc)
        counts = (f"{len(group)} {vendor} sessions with signal, "
                  f"{sum(len(s.hits) for s in group)} hits ({sum(k == 'abbruch' for s in group for _, k, _ in s.hits)} interruptions).")
        brief = os.path.join(work, f"brief-{vendor}.md")
        with open(brief, "w", encoding="utf-8") as f:
            f.write(open(os.path.join(REFS, "weekly-brief.md"), encoding="utf-8").read().format(
                vendor=vendor, since=since_d, until=date, counts=counts))
        if a.evidence_only:
            continue
        left = free.get(doctor)
        if left is None or left < RESERVE[doctor]:
            notes.append(f"Diagnose der {vendor}-Sitzungen übersprungen: " + (
                f"Kontingent von {doctor} nicht abrufbar." if left is None else f"{doctor} hat nur {left:.0f} % der Woche frei."))
            failed |= left is None
            continue
        answer, problem = ask_doctor(doctor, work, [brief, ev, ctx, kbrep])
        if answer is None:
            notes.append(f"Diagnose der {vendor}-Sitzungen fehlgeschlagen: {problem}")
            failed = True
            continue
        with open(os.path.join(work, f"answer-{vendor}.md"), "w", encoding="utf-8") as f:
            f.write(answer)
        try:
            results.append({"vendor": vendor, "keys": keys, "data": parse_answer(answer)})
        except ValueError as exc:
            notes.append(f"Antwort zu den {vendor}-Sitzungen unlesbar ({exc}); Rohtext in {work}/answer-{vendor}.md")
            failed = True
    if a.evidence_only:
        print(work)
        return 0

    report = os.path.join(a.out, f"{date}.md")
    text, findings = render(date, since_d, sessions, results, notes)
    if findings and not a.no_kb:
        log, kb_failed = file_tickets(date, report, findings, os.path.join(a.out, "filed.json"))
        failed |= kb_failed
        text += "\n## Tickets\n\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(log, 1)) + "\n"
    with open(report, "w", encoding="utf-8") as f:
        f.write(text)
    print(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

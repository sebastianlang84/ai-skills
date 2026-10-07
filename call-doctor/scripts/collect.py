#!/usr/bin/env python3
"""collect.py — build the doctor's evidence file from one agent session transcript.

    collect.py [--session <path|id>] [--focus <from>-<to>]... [--budget <KB>]
               [--extra <file>]... <out-file>

Reads a Claude Code transcript (~/.claude/projects/<dir>/<id>.jsonl) or a Codex rollout
(~/.codex/sessions/**/rollout-*<id>.jsonl) and writes one Markdown file with:
  1. the context the harness loaded (instruction files, memory index, skill listing, invoked
     skills, hook context, output style, system prompt, developer messages) as recorded in the
     transcript; a re-injection that changed is shown as a diff;
  2. a timeline, one entry per transcript line, prefixed `L<n>` (the physical JSONL line, so a
     finding can be checked with `sed -n '<n>p' <transcript>`), with compaction boundaries;
  3. any --extra files the caller adds (a system map, a rule file the session should have read).
Entries inside a --focus range are never cut; everything else is cut, then omitted, until the
file fits the budget (default 300 KB). Omitted ranges are marked, and the header says when the
evidence is incomplete. Every text is redacted before it is cut. Sidechain (subagent) entries
are left out. Without --session it uses the calling session ($CODEX_THREAD_ID or
$CLAUDE_CODE_SESSION_ID; with both set, --session is required).
Prints `vendor: claude|codex` (the patient's vendor), then the output path. Python 3.9, stdlib.
"""
from __future__ import annotations

import argparse
import difflib
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")

# A superset of the payload check in using-harnesses/scripts/review.sh.
SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----|$)"
    r"|(?<![A-Za-z0-9])(sk|pk|rk)-[A-Za-z0-9_-]{8,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|gh[pousr]_[A-Za-z0-9]{10,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(\.[A-Za-z0-9_-]+)?"
    r"|(?<=://)[^/\s:@]+:[^/\s@]+(?=@)",
    re.I,
)
# Credential-named key, then a separator, then the whole value: a quoted string or a bare word.
KV = re.compile(
    r"((?<![A-Za-z0-9_-])[A-Za-z0-9_-]{0,40}(api[_-]?key|secret|password|passwd|pwd|token|credential)[A-Za-z0-9_-]{0,40}"
    r"[\"']?[ \t]*[:=][ \t]*)(\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'|[^\s\"',;]+)",
    re.I,
)
# An Authorization header or an auth scheme followed by its credential.
BEARER = re.compile(r"\b(authorization[ \t]*[:=][ \t]*|Bearer[ \t]+|Basic[ \t]+|Token[ \t]+)[^\s\"',;]+([ \t]+[^\s\"',;]+)?", re.I)
EMAIL = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,}")


def redact(text: str) -> str:
    text = SECRET.sub("[REDACTED]", text)
    text = BEARER.sub(lambda m: m.group(1).rstrip() + " [REDACTED]", text)
    text = KV.sub(lambda m: m.group(1) + "[REDACTED]", text)
    return EMAIL.sub("[EMAIL]", text)


def find_session(ref: str | None) -> str:
    if not ref:
        cx, cl = os.environ.get("CODEX_THREAD_ID"), os.environ.get("CLAUDE_CODE_SESSION_ID")
        if cx and cl:
            sys.exit("collect.py: both CODEX_THREAD_ID and CLAUDE_CODE_SESSION_ID are set "
                     "(nested harness); pass --session")
        ref = cx or cl
    if not ref:
        sys.exit("collect.py: no --session and no CLAUDE_CODE_SESSION_ID/CODEX_THREAD_ID in the environment")
    if os.path.isfile(ref):
        return ref
    if not re.fullmatch(r"[A-Za-z0-9-]{8,64}", ref):
        sys.exit(f"collect.py: not a file or session id: {ref}")
    hits = glob.glob(f"{HOME}/.claude/projects/*/{ref}.jsonl") + glob.glob(
        f"{HOME}/.codex/sessions/**/rollout-*{ref}.jsonl", recursive=True)
    if not hits:
        sys.exit(f"collect.py: no transcript for session {ref}")
    return max(hits, key=os.path.getmtime)


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for c in content or []:
        if isinstance(c, dict):
            out.append(c.get("text") or c.get("thinking") or "")
        elif isinstance(c, str):
            out.append(c)
    return "\n".join(x for x in out if x)


def clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + f" […+{len(s) - n}]"


class Bundle:
    def __init__(self):
        self.meta: list[str] = []
        self.context: dict[tuple[str, str], list[int]] = {}  # (title, content) -> lines seen
        self.events: list[tuple[int, str, str]] = []  # (line, kind, redacted text)

    def ctx(self, title: str, body: str, n: int):
        """Record one injected context block; an identical re-injection only adds its line."""
        body = redact(body or "").strip()
        if body:
            self.context.setdefault((title, body), []).append(n)

    def ev(self, n: int, kind: str, text: str):
        self.events.append((n, kind, redact(text or "")))


def parse_claude(lines, b: Bundle):
    line_of = {e.get("uuid"): n for n, e in lines if e.get("uuid")}
    for n, e in lines:
        if e.get("isSidechain"):
            continue
        t = e.get("type")
        if t == "system" and e.get("subtype") == "compact_boundary":
            m = e.get("compactMetadata") or {}
            kept = [line_of.get(u) for u in (m.get("preservedMessages") or {}).get("uuids") or []]
            kept = ", ".join(f"L{x}" for x in sorted(x for x in kept if x)) or "none recorded"
            b.ev(n, "COMPACTION", f"{m.get('trigger')} compaction, {m.get('preTokens')} -> {m.get('postTokens')} "
                 f"tokens; earlier turns were replaced by a summary, except preserved messages: {kept}")
            continue
        if t == "attachment":
            a = e.get("attachment") or {}
            at = a.get("type")
            if at == "instructions":
                for f in a.get("files") or []:
                    b.ctx(f"{f.get('type')}: {f.get('path')}", f.get("content") or "", n)
            elif at == "skill_listing":
                b.ctx("Skill listing", a.get("content") or "", n)
            elif at == "invoked_skills":
                for s in a.get("skills") or []:
                    b.ctx(f"Invoked skill: {s.get('name')}", s.get("content") or "", n)
            elif at == "hook_additional_context":
                c = a.get("content")
                b.ctx(f"Hook context ({a.get('hookName')})", "\n".join(c) if isinstance(c, list) else str(c or ""), n)
            elif at == "output_style_instructions":
                st = a.get("style") or {}
                b.ctx(f"Output style: {st.get('name')}", st.get("prompt") or "", n)
            elif at == "prompt_snapshot":
                b.ctx("System prompt", text_of(a.get("systemPrompt")), n)
            elif at in ("mcp_instructions_delta", "language", "auto_mode", "model"):
                b.ctx(at, json.dumps({k: v for k, v in a.items() if k != "type"}, ensure_ascii=False), n)
            elif at == "file":
                fc = (a.get("content") or {}).get("file") or {}
                b.ev(n, "file", f"auto-attached {a.get('filename')}: {fc.get('content') or ''}")
            elif at == "environment" and not b.meta:
                b.meta.append("environment: " + redact(json.dumps(a.get("snapshot"), ensure_ascii=False))[:600])
            continue
        if t not in ("user", "assistant"):
            continue
        content = (e.get("message") or {}).get("content")
        if t == "user":
            if isinstance(content, str):
                b.ev(n, "meta" if e.get("isMeta") else "USER", content)
                continue
            for c in content or []:
                if c.get("type") == "tool_result":
                    r = c.get("content")
                    b.ev(n, "result", r if isinstance(r, str) else text_of(r))
                elif c.get("type") == "text":
                    b.ev(n, "meta" if e.get("isMeta") else "USER", c.get("text") or "")
        else:
            for c in content or []:
                ct = c.get("type")
                if ct == "text":
                    b.ev(n, "ASSISTANT", c.get("text") or "")
                elif ct == "thinking":
                    b.ev(n, "thinking", c.get("thinking") or "")
                elif ct == "tool_use":
                    b.ev(n, "tool", f"{c.get('name')} {json.dumps(c.get('input'), ensure_ascii=False)}")


def parse_codex(lines, b: Bundle):
    for n, e in lines:
        t, p = e.get("type"), e.get("payload") or {}
        if t == "compacted":
            b.ev(n, "COMPACTION", "context compacted; earlier turns were replaced by a summary "
                 "(which messages were kept is not recorded here)")
            continue
        if t == "session_meta":
            b.meta.append(f"cwd: {p.get('cwd')}  cli: {p.get('cli_version')}  source: {p.get('source')}")
            bi = p.get("base_instructions")
            b.ctx("Codex base instructions", bi.get("text", "") if isinstance(bi, dict) else str(bi or ""), n)
            continue
        if t == "turn_context" and len(b.meta) < 2:
            b.meta.append(f"model: {p.get('model')}  effort: {p.get('effort')}")
            continue
        if t != "response_item":
            continue
        pt = p.get("type")
        if pt == "message":
            role, txt = p.get("role"), text_of(p.get("content"))
            if role == "developer":
                b.ctx("Developer message", txt, n)
            elif role == "user" and txt.lstrip().startswith("# AGENTS.md instructions"):
                b.ctx("AGENTS.md (as loaded)", txt, n)
            elif role == "user" and txt.lstrip().startswith("<environment_context>"):
                b.ctx("Environment context", txt, n)
            else:
                b.ev(n, "USER" if role == "user" else "ASSISTANT", txt)
        elif pt in ("function_call", "custom_tool_call"):
            b.ev(n, "tool", f"{p.get('name')} {p.get('arguments') or p.get('input') or ''}")
        elif pt in ("function_call_output", "custom_tool_call_output"):
            o = p.get("output")
            b.ev(n, "result", o if isinstance(o, str) else json.dumps(o, ensure_ascii=False))
        elif pt == "reasoning":
            s = " ".join(x.get("text", "") for x in p.get("summary") or [] if isinstance(x, dict))
            if s:
                b.ev(n, "thinking", s)


KINDS = ("USER", "COMPACTION", "ASSISTANT", "thinking", "tool", "result", "file", "meta")
# Limits outside the focus ranges, from generous to terse; the first level that fits wins.
# 0 omits the entry; the last levels omit whole kinds.
LEVELS = [dict(zip(KINDS, v)) for v in (
    (8000, 4000, 2500, 1200, 600, 500, 600, 400),
    (6000, 2000, 1200, 500, 300, 200, 200, 200),
    (4000, 1000, 600, 200, 160, 100, 100, 120),
    (3000, 600, 300, 0, 100, 60, 0, 0),
    (3000, 600, 300, 0, 0, 0, 0, 0),
    (2000, 600, 0, 0, 0, 0, 0, 0),
)]


def render_timeline(events, lim, focus) -> tuple[str, int, int]:
    """Return the timeline, the number of omitted and of cut entries; an omitted run becomes one marker.
    Entries inside a focus range are never cut."""
    out, run = [], []

    def flush():
        if run:
            out.append(f"[L{run[0]}–L{run[-1]}: {len(run)} entries omitted]")

    omitted = cut = 0
    for n, kind, txt in events:
        if not txt.strip():
            continue
        cap = None if any(a <= n <= z for a, z in focus) else lim[kind]
        if cap == 0:
            run.append(n)
            omitted += 1
            continue
        flush()
        run = []
        if cap is not None and len(txt.strip()) > cap:
            cut += 1
        out.append(f"L{n} {kind}: {txt.strip() if cap is None else clip(txt, cap)}")
    flush()
    return "\n".join(out), omitted, cut


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--session")
    ap.add_argument("--focus", action="append", default=[], help="line range kept in full, e.g. 4320-4340")
    ap.add_argument("--budget", type=int, default=300, help="target size in KB (default 300)")
    ap.add_argument("--extra", action="append", default=[], help="add a file (repeatable)")
    ap.add_argument("out")
    a = ap.parse_args()
    focus = []
    for r in a.focus:
        m = re.fullmatch(r"L?(\d+)(?:-L?(\d+))?", r)
        if not m:
            sys.exit(f"collect.py: bad --focus range {r}")
        focus.append((int(m.group(1)), int(m.group(2) or m.group(1))))

    path = find_session(a.session)
    lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict):
                lines.append((n, e))
    codex = any(e.get("type") == "session_meta" for _, e in lines[:5])
    b = Bundle()
    (parse_codex if codex else parse_claude)(lines, b)

    ctx = ["", "## Loaded context (as recorded in the transcript)",
           "At a COMPACTION line earlier turns were replaced by a summary, except the preserved messages it "
           "lists; whether a block injected before it stayed in view is otherwise unknown."]
    last: dict[str, str] = {}
    ctx_cut = 0
    for (title, body), seen in b.context.items():
        at = ", ".join(f"L{x}" for x in seen)
        if title in last:  # a changed re-injection: show only what changed
            diff = difflib.unified_diff(last[title].splitlines(), body.splitlines(), lineterm="", n=1)
            diff = "\n".join(list(diff)[2:])
            ctx_cut += len(diff.strip()) > 8000
            ctx += ["", f"### {title}, changed ({len(body)} chars; injected at {at}); diff to the previous version",
                    clip(diff, 8000)]
        else:
            ctx_cut += len(body) > 30000
            ctx += ["", f"### {title} ({len(body)} chars; injected at {at})", clip(body, 30000)]
        last[title] = body
    extras = []
    for x in a.extra:
        if os.path.basename(x).lower().startswith(".env"):
            sys.exit(f"collect.py: refusing .env file {x}")
        try:
            body = open(x, encoding="utf-8", errors="replace").read()
        except OSError as exc:
            sys.exit(f"collect.py: cannot read --extra {x}: {exc.strerror}")
        body = redact(body)
        ctx_cut += len(body.strip()) > 40000
        extras += ["", f"## Extra file: {x}", clip(body, 40000)]

    head = [f"# Evidence: {'Codex' if codex else 'Claude Code'} session",
            f"transcript: {path}  ({os.path.getsize(path)} bytes, {len(lines)} JSON lines)"] + b.meta
    budget = a.budget * 1024
    fixed = len("\n".join(head + ctx + extras).encode()) + 600
    for lim in LEVELS:
        tl, omitted, cut = render_timeline(b.events, lim, focus)
        if fixed + len(tl.encode()) <= budget:
            break
    if omitted or cut or ctx_cut:
        head.append(f"EVIDENCE INCOMPLETE: {omitted} timeline entries omitted, {cut} cut, {ctx_cut} context "
                    f"or extra blocks cut to fit "
                    f"{a.budget} KB; focus ranges ({', '.join(a.focus) or 'none'}) are kept in full. A claim "
                    "about an omitted or cut range is UNVERIFIED.")
    note = f"(limits outside focus: {lim}; `[…+N]` marks cut characters)"
    doc = "\n".join(head + ctx + ["", "## Timeline", note, "", tl] + extras) + "\n"
    if len(doc.encode()) > budget:
        print(f"collect.py: evidence is {len(doc.encode()) // 1024} KB, over the {a.budget} KB budget",
              file=sys.stderr)
    fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(redact(doc))
    print(f"vendor: {'codex' if codex else 'claude'}")
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

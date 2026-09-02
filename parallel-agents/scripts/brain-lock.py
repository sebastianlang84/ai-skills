#!/usr/bin/env python3
"""Short-lived, kernel-backed write locks for files in the shared Brain.

Agents acquire every Brain path they will edit in one call, then release the returned token after
the edit and lint. A detached holder process owns POSIX advisory locks; the kernel releases them
when it exits, and a TTL bounds abandoned holders.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import select
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

DEFAULT_TTL = 15 * 60
MAX_TTL = 60 * 60
READY_TIMEOUT = 3.0


def brain_root() -> Path:
    return Path(os.environ.get("BRAIN_LOCK_ROOT", "~/.agents/brain")).expanduser().resolve()


def state_root() -> Path:
    return Path(
        os.environ.get("BRAIN_LOCK_STATE", "~/.agents/state/parallel-agents/brain-locks")
    ).expanduser()


def proc_start(pid: int) -> str | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return None
    return fields[19] if len(fields) > 19 else None


def alive(pid: int, started: str | None) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return not started or proc_start(pid) == started


def owner_name(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for key in ("CODEX_THREAD_ID", "CLAUDE_SESSION_ID", "PI_SESSION_ID"):
        if os.environ.get(key):
            return f"{key.lower()}:{os.environ[key]}"
    return f"process:{os.getppid()}"


def normalize_paths(raw_paths: list[str]) -> list[str]:
    root = brain_root()
    out: set[str] = set()
    for raw in raw_paths:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = root / path
        path = path.resolve(strict=False)
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(f"outside Brain: {raw}") from exc
        if rel in ("", ".") or rel.startswith(".git/"):
            raise ValueError(f"not a Brain entry: {raw}")
        out.add(rel)
    if not out:
        raise ValueError("at least one Brain path is required")
    return sorted(out)


def lock_file(rel: str) -> Path:
    digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()
    return state_root() / "paths" / f"{digest}.lock"


def token_file(token: str) -> Path:
    return state_root() / "holders" / f"{token}.json"


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def holder(token: str, ttl: float, owner: str, paths: list[str]) -> int:
    handles = []
    metadata: dict = {}
    stop = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        for rel in paths:
            path = lock_file(rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("a+", encoding="utf-8")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.seek(0)
                try:
                    current = json.loads(handle.read() or "{}")
                except json.JSONDecodeError:
                    current = {}
                print("BLOCKED\t" + json.dumps({"path": rel, "holder": current}), flush=True)
                return 2
            handles.append((rel, handle))

        now = time.time()
        metadata = {
            "token": token,
            "owner": owner,
            "pid": os.getpid(),
            "proc_start": proc_start(os.getpid()),
            "acquired_at": now,
            "expires_at": now + ttl,
            "paths": paths,
        }
        for _rel, handle in handles:
            handle.seek(0)
            handle.truncate()
            json.dump(metadata, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
        write_json_atomic(token_file(token), metadata)
        print("READY\t" + json.dumps(metadata), flush=True)

        deadline = time.monotonic() + ttl
        while not stop and time.monotonic() < deadline:
            time.sleep(min(0.2, max(0.01, deadline - time.monotonic())))
        return 0
    finally:
        current = read_json(token_file(token))
        if current.get("pid") == os.getpid():
            token_file(token).unlink(missing_ok=True)
        for _rel, handle in handles:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
            except OSError:
                pass


def acquire(paths: list[str], ttl: float, owner: str | None) -> int:
    if ttl <= 0 or ttl > MAX_TTL:
        print(f"TTL must be greater than 0 and at most {MAX_TTL} seconds", file=sys.stderr)
        return 2
    try:
        normalized = normalize_paths(paths)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    token = uuid.uuid4().hex
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_hold",
        "--token",
        token,
        "--ttl",
        str(ttl),
        "--owner",
        owner_name(owner),
        *normalized,
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    assert process.stdout is not None
    ready, _, _ = select.select([process.stdout], [], [], READY_TIMEOUT)
    if not ready:
        process.terminate()
        print("Brain lock holder did not start", file=sys.stderr)
        return 2
    line = process.stdout.readline().rstrip("\n")
    process.stdout.close()
    if line.startswith("READY\t"):
        print(f"acquired {', '.join(normalized)}")
        print(f"token {token}")
        print(f"release: {Path(__file__).resolve()} release {token}")
        return 0
    process.wait(timeout=READY_TIMEOUT)
    if line.startswith("BLOCKED\t"):
        detail = json.loads(line.split("\t", 1)[1])
        holder_info = detail.get("holder") or {}
        remaining = max(0, int(float(holder_info.get("expires_at") or 0) - time.time()))
        print(
            f"locked: {detail.get('path')} by {holder_info.get('owner', 'unknown')} "
            f"for up to {remaining}s",
            file=sys.stderr,
        )
    else:
        assert process.stderr is not None
        print(process.stderr.read().strip() or "Brain lock holder failed", file=sys.stderr)
    return 2


def release(token: str) -> int:
    if not token or any(ch not in "0123456789abcdef" for ch in token):
        print("invalid token", file=sys.stderr)
        return 2
    metadata = read_json(token_file(token))
    if not metadata:
        print("lock already released or expired")
        return 0
    pid = int(metadata.get("pid") or 0)
    if not pid or not alive(pid, metadata.get("proc_start")):
        token_file(token).unlink(missing_ok=True)
        print("removed expired lock metadata")
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    deadline = time.monotonic() + 2.0
    while token_file(token).exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    print(f"released {token}")
    return 0


def status() -> int:
    holders = state_root() / "holders"
    rows = []
    for path in sorted(holders.glob("*.json")) if holders.exists() else []:
        value = read_json(path)
        pid = int(value.get("pid") or 0)
        if not pid or not alive(pid, value.get("proc_start")):
            path.unlink(missing_ok=True)
            continue
        rows.append(value)
    if not rows:
        print("no active Brain write locks")
        return 0
    for row in rows:
        remaining = max(0, int(float(row["expires_at"]) - time.time()))
        print(f"{row['token']}  {row['owner']}  {remaining}s  {', '.join(row['paths'])}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    take = commands.add_parser("acquire", help="atomically lock Brain paths")
    take.add_argument("paths", nargs="+")
    take.add_argument("--ttl", type=float, default=DEFAULT_TTL)
    take.add_argument("--owner")
    give = commands.add_parser("release", help="release a lock token")
    give.add_argument("token")
    commands.add_parser("status", help="list live lock holders")
    hold = commands.add_parser("_hold", help=argparse.SUPPRESS)
    hold.add_argument("paths", nargs="+")
    hold.add_argument("--token", required=True)
    hold.add_argument("--ttl", type=float, required=True)
    hold.add_argument("--owner", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "acquire":
        return acquire(args.paths, args.ttl, args.owner)
    if args.command == "release":
        return release(args.token)
    if args.command == "status":
        return status()
    return holder(args.token, args.ttl, args.owner, args.paths)


if __name__ == "__main__":
    raise SystemExit(main())

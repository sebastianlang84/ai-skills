#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("~/.config/tool-update-checker/tools.toml").expanduser()
USER_AGENT = "tool-update-checker/0.1"


@dataclass
class Result:
    name: str
    kind: str
    installed: str
    latest: str
    status: str
    note: str = ""


def run(cmd: list[str], *, cwd: str | None = None, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def expand_path(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def load_config(path: Path) -> list[dict[str, Any]]:
    with path.open("rb") as f:
        data = tomllib.load(f)
    tools = data.get("tool")
    if not isinstance(tools, list):
        raise ValueError(f"Config {path} must contain one or more [[tool]] entries")
    return tools


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value.strip()


def npm_installed_version(package: str) -> str | None:
    proc = run(["npm", "-g", "ls", package, "--depth=0", "--json"])
    data = parse_json(proc.stdout or "{}")
    if not isinstance(data, dict):
        return None
    deps = data.get("dependencies") or {}
    dep = deps.get(package) or {}
    version = dep.get("version")
    return version if isinstance(version, str) and version else None


def npm_latest_version(package: str) -> str:
    proc = run(["npm", "view", package, "version", "--json"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "npm view failed")
    value = parse_json(proc.stdout)
    if isinstance(value, str) and value:
        return value
    raise RuntimeError("npm returned no version")


def check_npm_global(tool: dict[str, Any]) -> Result:
    name = str(tool["name"])
    package = str(tool["package"])
    installed = npm_installed_version(package)
    latest = npm_latest_version(package)
    if not installed:
        return Result(name, "npm-global", "missing", latest, "missing", package)
    status = "up-to-date" if installed == latest else "update-available"
    return Result(name, "npm-global", installed, latest, status, package)


def git_current_branch(path: Path) -> str:
    proc = run(["git", "-C", str(path), "branch", "--show-current"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git branch failed")
    branch = proc.stdout.strip()
    if not branch:
        raise RuntimeError("repository is detached; set branch explicitly in config")
    return branch


def git_head_sha(path: Path) -> tuple[str, str]:
    short_proc = run(["git", "-C", str(path), "rev-parse", "--short=12", "HEAD"])
    full_proc = run(["git", "-C", str(path), "rev-parse", "HEAD"])
    if short_proc.returncode != 0 or full_proc.returncode != 0:
        raise RuntimeError(short_proc.stderr.strip() or full_proc.stderr.strip() or "git rev-parse failed")
    return short_proc.stdout.strip(), full_proc.stdout.strip()


def git_remote_sha(path: Path, remote: str, branch: str) -> str:
    proc = run(["git", "-C", str(path), "ls-remote", "--heads", remote, f"refs/heads/{branch}"], timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git ls-remote failed")
    line = proc.stdout.strip().splitlines()
    if not line:
        raise RuntimeError(f"remote branch not found: {remote}/{branch}")
    sha = line[0].split()[0].strip()
    if not sha:
        raise RuntimeError(f"unable to parse remote SHA for {remote}/{branch}")
    return sha


def git_remote_url(path: Path, remote: str) -> str:
    proc = run(["git", "-C", str(path), "remote", "get-url", remote])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git remote get-url failed")
    return proc.stdout.strip()


def check_git_repo(tool: dict[str, Any]) -> Result:
    name = str(tool["name"])
    path = expand_path(str(tool["path"]))
    if not path.exists():
        return Result(name, "git-repo", "missing", "unknown", "missing", str(path))
    branch = str(tool.get("branch") or git_current_branch(path))
    remote = str(tool.get("remote") or "origin")
    local_short, local_full = git_head_sha(path)
    remote_full = git_remote_sha(path, remote, branch)
    remote_url = git_remote_url(path, remote)
    remote_short = remote_full[:12]
    status = "up-to-date" if local_full == remote_full else "remote-changed"
    note = f"{remote}/{branch} {remote_url}"
    return Result(name, "git-repo", f"{branch}@{local_short}", f"{branch}@{remote_short}", status, note)


def github_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def github_latest_release_or_tag(repo: str) -> str:
    latest_release_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        data = github_json(latest_release_url)
        tag = data.get("tag_name")
        if isinstance(tag, str) and tag:
            return tag
    except urllib.error.HTTPError as e:
        if e.code not in (404, 403):
            raise RuntimeError(f"GitHub API error {e.code}") from e
        if e.code == 403:
            raise RuntimeError("GitHub API rate limit or access denied") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"GitHub request failed: {e}") from e

    tags_url = f"https://api.github.com/repos/{repo}/tags?per_page=1"
    try:
        tags = github_json(tags_url)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"GitHub request failed: {e}") from e

    if isinstance(tags, list) and tags:
        name = tags[0].get("name")
        if isinstance(name, str) and name:
            return name
    raise RuntimeError("No release or tag found")


def check_github_release(tool: dict[str, Any]) -> Result:
    name = str(tool["name"])
    repo = str(tool["repo"])
    current = str(tool.get("current") or "unknown")
    latest = github_latest_release_or_tag(repo)
    if current == "unknown":
        status = "info"
    else:
        status = "up-to-date" if current == latest else "update-available"
    return Result(name, "github-release", current, latest, status, repo)


CHECKERS = {
    "npm-global": check_npm_global,
    "git-repo": check_git_repo,
    "github-release": check_github_release,
}


def check_tool(tool: dict[str, Any]) -> Result:
    kind = tool.get("kind")
    name = str(tool.get("name") or kind or "unnamed")
    if kind not in CHECKERS:
        return Result(name, str(kind), "unknown", "unknown", "error", f"unsupported kind: {kind}")
    try:
        return CHECKERS[str(kind)](tool)
    except Exception as e:  # noqa: BLE001
        return Result(name, str(kind), "unknown", "unknown", "error", str(e))


def filter_tools(tools: list[dict[str, Any]], groups: list[str]) -> list[dict[str, Any]]:
    if not groups:
        return tools
    wanted = set(groups)
    filtered: list[dict[str, Any]] = []
    for tool in tools:
        tool_groups = tool.get("groups") or []
        if not isinstance(tool_groups, list):
            continue
        if wanted.intersection(str(g) for g in tool_groups):
            filtered.append(tool)
    return filtered


def to_table(results: list[Result]) -> str:
    rows = [[r.name, r.kind, r.installed, r.latest, r.status, r.note] for r in results]
    headers = ["Name", "Kind", "Installed", "Latest", "Status", "Note"]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def fmt(row: list[str]) -> str:
        return " | ".join(value.ljust(widths[i]) for i, value in enumerate(row))

    sep = "-+-".join("-" * width for width in widths)
    lines = [fmt(headers), sep]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines)


def to_markdown(results: list[Result]) -> str:
    rows = [[r.name, r.kind, r.installed, r.latest, r.status, r.note] for r in results]
    headers = ["Name", "Kind", "Installed", "Latest", "Status", "Note"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        safe = [value.replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local tools for available updates")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to tools.toml")
    parser.add_argument("--format", choices=["table", "markdown", "json"], default="table")
    parser.add_argument("--group", action="append", default=[], help="Only check tools that belong to this group; repeatable")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = expand_path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        tools = load_config(config_path)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to load config: {e}", file=sys.stderr)
        return 2

    tools = filter_tools(tools, args.group)
    if not tools:
        print("No tools matched the selected config/group filters.", file=sys.stderr)
        return 2

    results = [check_tool(tool) for tool in tools]

    if args.format == "json":
        print(json.dumps([asdict(r) for r in results], indent=2))
    elif args.format == "markdown":
        print(to_markdown(results))
    else:
        print(to_table(results))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

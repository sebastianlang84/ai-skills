#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- BEGIN SKILL LIST -->"
END = "<!-- END SKILL LIST -->"
ZERO_SHA = "0" * 40


def git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc


def git_lines(args: list[str]) -> list[str]:
    return [line for line in git(args).stdout.splitlines() if line]


class View:
    def __init__(self, treeish: str | None = None) -> None:
        self.treeish = treeish

    def read_text(self, path: str) -> str:
        if self.treeish is None:
            return (ROOT / path).read_text(encoding="utf-8")
        proc = git(["show", f"{self.treeish}:{path}"], check=False)
        if proc.returncode != 0:
            raise FileNotFoundError(path)
        return proc.stdout

    def exists(self, path: str) -> bool:
        if self.treeish is None:
            return (ROOT / path).exists()
        return git(["cat-file", "-e", f"{self.treeish}:{path}"], check=False).returncode == 0

    def skill_dirs(self) -> list[str]:
        if self.treeish is None:
            return sorted(
                p.name
                for p in ROOT.iterdir()
                if p.is_dir() and not p.is_symlink() and not p.name.startswith(".")
                and (p / "SKILL.md").exists()
            )
        names: set[str] = set()
        for path in git_lines(["ls-tree", "-r", "--name-only", self.treeish]):
            parts = path.split("/")
            if len(parts) == 2 and parts[1] == "SKILL.md" and not parts[0].startswith("."):
                names.add(parts[0])
        return sorted(names)


def parse_frontmatter(text: str, path: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError(f"{path} has no YAML frontmatter")
    values: dict[str, str] = {}
    current: str | None = None
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t")) and current:
            values[current] += " " + line.strip().strip('"\'')
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[current] = value
    return values


def expected_skill_block(view: View) -> str:
    lines = [START]
    for skill in view.skill_dirs():
        meta = parse_frontmatter(view.read_text(f"{skill}/SKILL.md"), f"{skill}/SKILL.md")
        name = meta.get("name", "")
        description = " ".join((meta.get("description") or "").split())
        if name != skill:
            raise ValueError(f"{skill}/SKILL.md name is {name!r}, expected {skill!r}")
        if not description:
            raise ValueError(f"{skill}/SKILL.md has empty description")
        lines.append(f"- `{skill}` — {description}")
    lines.append(END)
    return "\n".join(lines)


def check_readme(view: View) -> list[str]:
    errors: list[str] = []
    try:
        text = view.read_text("README.md")
    except FileNotFoundError:
        return ["README.md is missing"]
    expected = expected_skill_block(view)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    match = pattern.search(text)
    if not match:
        errors.append(f"README.md must contain generated skill-list markers {START} / {END}")
        return errors
    if match.group(0).strip() != expected.strip():
        errors.append("README.md skill list is stale. Update the block between BEGIN/END SKILL LIST markers.")
    return errors


def check_changelog_exists(view: View) -> list[str]:
    try:
        text = view.read_text("CHANGELOG.md")
    except FileNotFoundError:
        return ["CHANGELOG.md is missing"]
    if "## [Unreleased]" not in text:
        return ["CHANGELOG.md must contain a ## [Unreleased] section"]
    return []


def changed_files_for_range(range_spec: str) -> list[str]:
    return git_lines(["diff", "--name-only", range_spec])


def changed_files_for_staged() -> list[str]:
    return git_lines(["diff", "--cached", "--name-only"])


def is_relevant_change(path: str, view: View) -> bool:
    if path == "CHANGELOG.md":
        return False
    if path == "README.md" or path.startswith(("_scripts/", ".github/", ".githooks/")):
        return True
    if path.startswith("skills/"):
        return True
    first = path.split("/", 1)[0]
    return view.exists(f"{first}/SKILL.md") or path.endswith("/SKILL.md")


def check_changelog_touched(files: list[str], view: View) -> list[str]:
    if not files:
        return []
    relevant = [f for f in files if is_relevant_change(f, view)]
    if relevant and "CHANGELOG.md" not in files:
        sample = ", ".join(relevant[:5])
        return [f"CHANGELOG.md must be updated when skill/repo metadata changes. Relevant changes: {sample}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ai-skills README/CHANGELOG metadata gates")
    parser.add_argument("--tree", help="Validate README/CHANGELOG content from a Git tree-ish instead of the working tree")
    parser.add_argument("--range", help="Git revision range to check for changelog enforcement, e.g. origin/main..HEAD")
    parser.add_argument("--staged", action="store_true", help="Validate staged index content and staged changelog enforcement")
    args = parser.parse_args()

    treeish = args.tree
    files: list[str] = []
    if args.staged:
        treeish = git(["write-tree"]).stdout.strip()
        files = changed_files_for_staged()
    elif args.range:
        files = changed_files_for_range(args.range)

    view = View(treeish)
    errors: list[str] = []
    try:
        errors.extend(check_readme(view))
        errors.extend(check_changelog_exists(view))
        errors.extend(check_changelog_touched(files, view))
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    if errors:
        print("ai-skills metadata check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("ai-skills metadata check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

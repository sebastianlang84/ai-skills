#!/usr/bin/env python3
"""models_conf.py — the one parser of the per-user models.conf of using-harnesses.

    models_conf.py --get <KEY>       print the effective value of one key
    models_conf.py --print-config    print every key with its source, then the file path

The file is ${XDG_CONFIG_HOME:-~/.config}/using-harnesses/models.conf (format:
../references/models.conf.example). It is read as bytes and never executed. A NUL byte, bytes that
are not UTF-8, an unknown key or a bad value stop with exit 2 instead of being skipped, because a
skipped line silently runs a model the user did not choose. A banned model id stops the same way.
review.sh calls this file. Python 3.9, stdlib only.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DEFAULTS = {
    "CODEX_MODEL": "gpt-6.1-sol",
    "CODEX_EFFORTS": "medium,high",
    "CLAUDE_MODEL": "claude-opus-5-5",
    "CLAUDE_EFFORTS": "medium",
}
# Never configured or called on this machine (Sebastian, 2026-10-01).
BANNED = ("gpt-6-sol", "gpt-6-astra")
# Levels each harness accepts; an *_EFFORTS list must stay inside them.
LEVELS = {
    "CODEX": ("low", "medium", "high", "xhigh", "max", "ultra"),
    "CLAUDE": ("low", "medium", "high", "xhigh", "max"),
}
_SKIP = re.compile(r"[ \t\f\v]*(#.*)?")
_LINE = re.compile(r"([A-Z_]+)=([^ \t\f\v\r]+)")
_LIST = re.compile(r"[a-z]+(,[a-z]+)*")
_ID = re.compile(r"[A-Za-z0-9._/-]+")


class ConfigError(Exception):
    """A models.conf that must be fixed before anything runs."""


def conf_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.environ.get("HOME") or str(Path.home()), ".config")
    return Path(base) / "using-harnesses" / "models.conf"


def load(path: Path | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """Return (values, sources); a missing file gives the defaults with source 'default'."""
    path = path or conf_path()
    values, sources = dict(DEFAULTS), dict.fromkeys(DEFAULTS, "default")
    if not path.is_file():
        return values, sources
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"{path}: cannot read: {exc.strerror}") from exc
    if b"\0" in raw:
        raise ConfigError(f"{path}: contains a NUL byte")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path}: not UTF-8 (invalid byte at offset {exc.start})") from exc
    for line in text.split("\n"):
        line = line[:-1] if line.endswith("\r") else line
        if _SKIP.fullmatch(line):
            continue
        m = _LINE.fullmatch(line)
        if not m:
            raise ConfigError(f"{path}: not a KEY=value line: {line}")
        key, value = m.groups()
        if key not in DEFAULTS:
            raise ConfigError(f"{path}: unknown key {key}")
        if key.endswith("_EFFORTS"):
            if not _LIST.fullmatch(value):
                raise ConfigError(f"{path}: {key}: bad list {value}")
            for level in value.split(","):
                if level not in LEVELS[key.split("_")[0]]:
                    raise ConfigError(f"{path}: {key}: unsupported level {level}")
        elif not _ID.fullmatch(value):
            raise ConfigError(f"{path}: {key}: bad id {value}")
        elif value.lower() in BANNED:
            raise ConfigError(f"{path}: {key}: {value} is banned on this machine")
        values[key], sources[key] = value, "file"
    return values, sources


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")
    try:
        if len(argv) == 2 and argv[0] == "--get":
            if argv[1] not in DEFAULTS:
                raise ConfigError("--get takes one key: " + " ".join(DEFAULTS))
            print(load()[0][argv[1]])
        elif argv == ["--print-config"]:
            values, sources = load()
            for key in DEFAULTS:
                print(f"{key}={values[key]}\t({sources[key]})")
            print(f"# file: {conf_path()}")
        else:
            raise ConfigError("usage: models_conf.py --get <KEY> | --print-config")
    except ConfigError as exc:
        print(f"models_conf.py: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

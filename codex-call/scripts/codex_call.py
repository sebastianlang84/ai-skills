#!/usr/bin/env python3
"""Compatibility starter: codex_call.py moved to ../../using-codex/scripts/codex_call.py.

Kept for callers with the old path (market-digest's quality loop). Remove once nothing uses it.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parents[2] / "using-codex" / "scripts" / "codex_call.py"
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")

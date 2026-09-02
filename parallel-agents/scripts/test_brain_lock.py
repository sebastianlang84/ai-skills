#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("brain-lock.py")


class BrainLockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.brain = base / "brain"
        self.state = base / "state"
        self.brain.mkdir()
        (self.brain / "a.md").write_text("a\n", encoding="utf-8")
        (self.brain / "b.md").write_text("b\n", encoding="utf-8")
        self.env = os.environ | {
            "BRAIN_LOCK_ROOT": str(self.brain),
            "BRAIN_LOCK_STATE": str(self.state),
        }
        self.tokens: list[str] = []

    def tearDown(self) -> None:
        for token in self.tokens:
            self.invoke("release", token)
        self.temp.cleanup()

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, str(SCRIPT), *args),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def acquire(self, *paths: str, ttl: str = "5") -> subprocess.CompletedProcess[str]:
        result = self.invoke("acquire", "--ttl", ttl, *paths)
        match = re.search(r"^token ([0-9a-f]+)$", result.stdout, re.MULTILINE)
        if match:
            self.tokens.append(match.group(1))
        return result

    def test_same_path_blocks_until_release(self) -> None:
        first = self.acquire("a.md")
        self.assertEqual(first.returncode, 0, first.stderr)
        blocked = self.acquire("a.md")
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("locked: a.md", blocked.stderr)
        token = self.tokens.pop()
        self.assertEqual(self.invoke("release", token).returncode, 0)
        self.assertEqual(self.acquire("a.md").returncode, 0)

    def test_multi_path_acquire_is_atomic(self) -> None:
        self.assertEqual(self.acquire("a.md").returncode, 0)
        blocked = self.acquire("a.md", "b.md")
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(self.acquire("b.md").returncode, 0)

    def test_different_paths_can_be_held_together(self) -> None:
        self.assertEqual(self.acquire("a.md").returncode, 0)
        self.assertEqual(self.acquire("b.md").returncode, 0)
        status = self.invoke("status")
        self.assertIn("a.md", status.stdout)
        self.assertIn("b.md", status.stdout)

    def test_ttl_releases_abandoned_holder(self) -> None:
        self.assertEqual(self.acquire("a.md", ttl="0.25").returncode, 0)
        time.sleep(0.4)
        self.assertEqual(self.acquire("a.md").returncode, 0)

    def test_path_outside_brain_is_rejected(self) -> None:
        result = self.acquire(str(Path(self.temp.name) / "outside.md"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside Brain", result.stderr)


if __name__ == "__main__":
    unittest.main()

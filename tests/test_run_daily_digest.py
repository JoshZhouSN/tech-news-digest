#!/usr/bin/env python3
"""Tests for run-daily-digest.py."""

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
MODULE_PATH = SCRIPTS_DIR / "run-daily-digest.py"

spec = importlib.util.spec_from_file_location("run_daily_digest", MODULE_PATH)
run_daily_digest = importlib.util.module_from_spec(spec)
sys.modules["run_daily_digest"] = run_daily_digest
spec.loader.exec_module(run_daily_digest)


class TestRunDailyDigest(unittest.TestCase):
    def test_build_pipeline_command_uses_target_sources(self):
        args = Namespace(
            defaults=Path("/tmp/defaults"),
            config=Path("/tmp/config"),
            archive_dir=Path("/tmp/archive"),
            hours=48,
            freshness="pd",
            only="twitter,github,trending,reddit,web",
            twitter_backend="bird",
        )

        cmd = run_daily_digest.build_pipeline_command(args, Path("/tmp/merged.json"))

        self.assertIn("--only", cmd)
        self.assertIn("twitter,github,trending,reddit,web", cmd)
        self.assertIn("--twitter-backend", cmd)
        self.assertIn("bird", cmd)
        self.assertIn("--force", cmd)


if __name__ == "__main__":
    unittest.main()

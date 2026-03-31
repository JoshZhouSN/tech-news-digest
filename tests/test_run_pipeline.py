#!/usr/bin/env python3
"""Tests for run-pipeline.py summary behavior."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
MODULE_PATH = SCRIPTS_DIR / "run-pipeline.py"

spec = importlib.util.spec_from_file_location("run_pipeline", MODULE_PATH)
run_pipeline = importlib.util.module_from_spec(spec)
sys.modules["run_pipeline"] = run_pipeline
spec.loader.exec_module(run_pipeline)


class TestRunStepCounts(unittest.TestCase):
    def test_reads_total_articles_from_merged_output_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "merged.json"
            output_path.write_text(
                json.dumps(
                    {
                        "output_stats": {
                            "total_articles": 82,
                        }
                    }
                )
            )

            completed = mock.Mock(returncode=0, stderr="")
            with mock.patch.object(run_pipeline.subprocess, "run", return_value=completed):
                result = run_pipeline.run_step(
                    "Merge",
                    "merge-sources.py",
                    [],
                    output_path,
                )

        self.assertEqual(result["count"], 82)


if __name__ == "__main__":
    unittest.main()

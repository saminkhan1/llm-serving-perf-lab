from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from lsp.artifacts.models import ARTIFACT_SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]


class BenchmarkRunSmokeTests(unittest.TestCase):
    def test_run_dry_run_writes_valid_artifacts(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m1-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "m1-smoke"

        result = subprocess.run(
            [
                "python3",
                "-m",
                "lsp.cli.main",
                "run",
                "--backend-config",
                "configs/backends/vllm_dev.yaml",
                "--workload-config",
                "configs/workloads/mixed_short_long.yaml",
                "--output-dir",
                str(temp_root),
                "--run-id",
                "m1-smoke",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), str(run_dir))

        validation = subprocess.run(
            ["python3", "-m", "lsp.cli.main", "validate-artifact", str(run_dir)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"run_id": "m1-smoke"', validation.stdout)

        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["mode"], "dry-run")
        self.assertTrue(metadata["synthetic"])
        self.assertIn("synthetic", " ".join(metadata["notes"]).lower())
        self.assertEqual(metadata["schema_version"], ARTIFACT_SCHEMA_VERSION)

        metrics_rows = (run_dir / "metrics.parquet").read_text(encoding="utf-8").strip()
        requests_rows = (run_dir / "requests.parquet").read_text(encoding="utf-8").strip()
        self.assertTrue(metrics_rows)
        self.assertTrue(requests_rows)

    def test_make_reproduce_m1_alias(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m1-repro-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "repro-m1"

        result = subprocess.run(
            [
                "make",
                "reproduce",
                "RUN=m1",
                f"REPRO_OUTPUT_DIR={temp_root}",
                "REPRO_RUN_ID=repro-m1",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("--dry-run", result.stdout)

        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["mode"], "dry-run")
        self.assertTrue(metadata["synthetic"])
        self.assertEqual(metadata["schema_version"], ARTIFACT_SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()

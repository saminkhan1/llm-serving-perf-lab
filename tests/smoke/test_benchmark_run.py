from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

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

        self.assertGreater(pq.read_table(run_dir / "metrics.parquet").num_rows, 0)
        self.assertGreater(pq.read_table(run_dir / "requests.parquet").num_rows, 0)

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

    def test_real_mode_requires_explicit_hardware_metadata(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m2-hardware-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        backend_config = temp_root / "backend.json"
        backend_config.write_text(
            json.dumps(
                {
                    "backend": "vllm",
                    "mode": "serve",
                    "model_id": "fake/local-test-model",
                    "host": "127.0.0.1",
                    "port": 18080,
                    "launch": {
                        "attach_mode": "external",
                        "startup_timeout_seconds": 0.2,
                        "healthcheck_interval_seconds": 0.05,
                        "request_timeout_seconds": 0.1,
                    },
                    "metrics": {
                        "scrape_endpoint": "http://127.0.0.1:18080/metrics",
                        "scrape_interval_seconds": 1,
                    },
                    "artifacts": {
                        "capture_runtime_metadata": True,
                        "write_plots": True,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                "python3",
                "-m",
                "lsp.cli.main",
                "run",
                "--backend-config",
                str(backend_config),
                "--workload-config",
                "configs/workloads/chat_short.yaml",
                "--output-dir",
                str(temp_root),
                "--run-id",
                "missing-hardware",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("backend config.hardware", result.stderr)
        self.assertFalse((temp_root / "missing-hardware").exists())


if __name__ == "__main__":
    unittest.main()

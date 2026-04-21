from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeRunSmokeTests(unittest.TestCase):
    def test_cli_help(self) -> None:
        result = subprocess.run(
            ["python3", "-m", "lsp.cli.main", "--help"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("fake-run", result.stdout)

    def test_fake_run_writes_valid_artifacts(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m0-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "smoke-run"
        result = subprocess.run(
            [
                "python3",
                "-m",
                "lsp.cli.main",
                "fake-run",
                "--backend-config",
                "configs/backends/vllm_dev.yaml",
                "--workload-config",
                "configs/workloads/chat_short.yaml",
                "--output-dir",
                str(temp_root),
                "--run-id",
                "smoke-run",
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
        self.assertIn('"run_id": "smoke-run"', validation.stdout)


if __name__ == "__main__":
    unittest.main()

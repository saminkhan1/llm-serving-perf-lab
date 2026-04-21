from __future__ import annotations

import json
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq
import pytest
import yaml

from lsp.artifacts.models import ARTIFACT_SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
FAKE_SERVER = REPO_ROOT / "tests" / "support" / "fake_vllm_server.py"
SOCKETS_ALLOWED = True

try:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.close()
except PermissionError:
    SOCKETS_ALLOWED = False


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _write_backend_config(temp_root: Path, port: int, command: list[str] | None) -> Path:
    config_path = temp_root / "backend.yaml"
    config = {
        "backend": "vllm",
        "mode": "serve",
        "model_id": "fake/local-test-model",
        "host": "127.0.0.1",
        "port": port,
        "launch": {
            "command": command,
            "startup_timeout_seconds": 0.6,
            "healthcheck_interval_seconds": 0.05,
            "request_timeout_seconds": 0.5,
        },
        "metrics": {
            "scrape_endpoint": f"http://127.0.0.1:{port}/metrics",
            "scrape_interval_seconds": 1,
        },
        "artifacts": {
            "capture_runtime_metadata": True,
            "write_plots": True,
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config_path


class RealBenchmarkSmokeTests(unittest.TestCase):
    @pytest.mark.network
    @unittest.skipUnless(SOCKETS_ALLOWED, "local sockets are not permitted in this environment")
    def test_real_mode_run_against_fake_backend(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m2-real-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "m2-real-smoke"
        port = _free_port()
        backend_config = _write_backend_config(
            temp_root,
            port,
            ["python3", str(FAKE_SERVER), "--port", str(port), "--mode", "healthy"],
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
                "m2-real-smoke",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), str(run_dir))

        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "success")
        self.assertEqual(metadata["mode"], "serve")
        self.assertFalse(metadata["synthetic"])
        self.assertEqual(metadata["schema_version"], ARTIFACT_SCHEMA_VERSION)
        self.assertIn("fake local backend", " ".join(metadata["notes"]).lower())
        self.assertEqual(metadata["backend_version"], "fake-vllm/0.2.0")

        system_info = json.loads((run_dir / "system_info.json").read_text(encoding="utf-8"))
        runtime_metadata = system_info["runtime_metadata"]
        self.assertEqual(runtime_metadata["version_payload"]["implementation"], "fake-vllm")

        metrics_rows = pq.read_table(run_dir / "metrics.parquet").to_pylist()
        metric_names = {row.get("metric_name") for row in metrics_rows}
        self.assertIn("vllm:time_to_first_token_seconds", metric_names)
        self.assertIn("client_request_latency_seconds", metric_names)
        self.assertFalse(
            any(row.get("missing") is True for row in metrics_rows if row.get("metric_name"))
        )

    def test_real_mode_failure_writes_visible_artifact(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m2-fail-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "m2-failure"
        port = 18082
        backend_config = _write_backend_config(temp_root, port, command=None)

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
                "m2-failure",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr.splitlines()[0], str(run_dir))

        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "failed")
        self.assertIn("launch_timeout", str(metadata["failure_reason"]))
        report_text = (run_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("failure_reason", report_text)


if __name__ == "__main__":
    unittest.main()

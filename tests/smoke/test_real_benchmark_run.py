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
    return _write_backend_config_with_target(
        temp_root=temp_root,
        command=command,
        host="127.0.0.1",
        port=port,
        base_url=None,
    )


def _write_backend_config_with_target(
    *,
    temp_root: Path,
    command: list[str] | None,
    host: str | None,
    port: int | None,
    base_url: str | None,
) -> Path:
    config_path = temp_root / "backend.yaml"
    config = {
        "backend": "vllm",
        "mode": "serve",
        "model_id": "fake/local-test-model",
        "hardware": {
            "provider": "test",
            "accelerator": "fake-local-gpu",
            "accelerator_count": 1,
        },
        "launch": {
            "command": command,
            "startup_timeout_seconds": 0.6,
            "healthcheck_interval_seconds": 0.05,
            "request_timeout_seconds": 0.5,
        },
        "artifacts": {
            "capture_runtime_metadata": True,
            "write_plots": True,
        },
    }
    if base_url is not None:
        config["base_url"] = base_url
        config["metrics"] = {
            "scrape_endpoint": f"{base_url.rstrip('/')}/metrics",
            "scrape_interval_seconds": 1,
        }
    else:
        assert host is not None
        assert port is not None
        config["host"] = host
        config["port"] = port
        config["metrics"] = {
            "scrape_endpoint": f"http://{host}:{port}/metrics",
            "scrape_interval_seconds": 1,
        }
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config_path


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


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
        self.assertEqual(metadata["hardware_profile"], "fake-local-gpu x1 via test")
        self.assertEqual(metadata["hardware_metadata"]["provider"], "test")
        self.assertIn("fake local backend", " ".join(metadata["notes"]).lower())
        self.assertEqual(metadata["backend_version"], "fake-vllm/0.2.0")

        system_info = json.loads((run_dir / "system_info.json").read_text(encoding="utf-8"))
        runtime_metadata = system_info["runtime_metadata"]
        self.assertEqual(runtime_metadata["version_payload"]["implementation"], "fake-vllm")

        metrics_rows = pq.read_table(run_dir / "metrics.parquet").to_pylist()
        metric_names = {row.get("metric_name") for row in metrics_rows}
        self.assertTrue(
            any(
                isinstance(name, str) and name.startswith("vllm:time_to_first_token_seconds_")
                for name in metric_names
            )
        )
        self.assertIn("client_request_latency_seconds", metric_names)
        self.assertFalse(
            any(row.get("missing") is True for row in metrics_rows if row.get("metric_name"))
        )

    @pytest.mark.network
    @unittest.skipUnless(SOCKETS_ALLOWED, "local sockets are not permitted in this environment")
    def test_real_mode_run_against_external_base_url_backend(self) -> None:
        temp_root = Path(
            tempfile.mkdtemp(prefix="lsp-m2-real-external-", dir=REPO_ROOT / "artifacts")
        )
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        run_dir = temp_root / "m2-real-external"
        port = _free_port()
        server = subprocess.Popen(
            ["python3", str(FAKE_SERVER), "--port", str(port), "--mode", "healthy"],
            cwd=REPO_ROOT,
            text=True,
        )
        self.addCleanup(lambda: _stop_process(server))
        backend_config = _write_backend_config_with_target(
            temp_root=temp_root,
            command=None,
            host=None,
            port=None,
            base_url=f"http://127.0.0.1:{port}",
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
                "m2-real-external",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), str(run_dir))

        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "success")
        self.assertFalse(metadata["synthetic"])
        self.assertEqual(metadata["backend_version"], "fake-vllm/0.2.0")
        self.assertEqual(metadata["hardware_profile"], "fake-local-gpu x1 via test")
        self.assertEqual(metadata["runtime_metadata"]["base_url"], f"http://127.0.0.1:{port}")

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
        self.assertEqual(metadata["hardware_profile"], "fake-local-gpu x1 via test")
        self.assertIn("launch_timeout", str(metadata["failure_reason"]))
        report_text = (run_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("failure_reason", report_text)


if __name__ == "__main__":
    unittest.main()

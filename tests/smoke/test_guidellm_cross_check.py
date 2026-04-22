from __future__ import annotations

import json
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

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


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _write_backend_config(temp_root: Path, *, base_url: str) -> Path:
    config_path = temp_root / "backend.yaml"
    config = {
        "backend": "vllm",
        "mode": "serve",
        "model_id": "gpt2",
        "hardware": {
            "provider": "test",
            "accelerator": "fake-local-gpu",
            "accelerator_count": 1,
        },
        "launch": {
            "command": None,
            "startup_timeout_seconds": 0.6,
            "healthcheck_interval_seconds": 0.05,
            "request_timeout_seconds": 0.5,
        },
        "metrics": {
            "scrape_endpoint": f"{base_url.rstrip('/')}/metrics",
            "scrape_interval_seconds": 1,
        },
        "base_url": base_url,
        "artifacts": {
            "capture_runtime_metadata": True,
            "write_plots": True,
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config_path


def _write_workload_config(temp_root: Path) -> Path:
    config_path = temp_root / "workload.yaml"
    config = {
        "workload_id": "guidellm_local_smoke",
        "seed": 7,
        "kind": "synthetic",
        "request_count": 5,
        "arrival": {
            "distribution": "poisson",
            "rate_per_second": 2.0,
        },
        "prompt_tokens": {
            "distribution": "lognormal",
            "median": 10,
            "p95": 20,
        },
        "output_tokens": {
            "distribution": "lognormal",
            "median": 3,
            "p95": 6,
        },
        "prefix_reuse": {
            "enabled": False,
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config_path


class GuideLLMCrossCheckSmokeTests(unittest.TestCase):
    @pytest.mark.network
    @unittest.skipUnless(SOCKETS_ALLOWED, "local sockets are not permitted in this environment")
    @unittest.skipUnless(shutil.which("guidellm"), "guidellm must be installed for the smoke test")
    def test_cross_check_guidellm_executes_against_fake_backend(self) -> None:
        temp_root = Path(
            tempfile.mkdtemp(prefix="lsp-guidellm-smoke-", dir=REPO_ROOT / "artifacts")
        )
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        port = _free_port()
        server = subprocess.Popen(
            ["python3", str(FAKE_SERVER), "--port", str(port), "--mode", "healthy"],
            cwd=REPO_ROOT,
            text=True,
        )
        self.addCleanup(lambda: _stop_process(server))
        output_dir = temp_root / "guidellm"
        backend_config = _write_backend_config(temp_root, base_url=f"http://127.0.0.1:{port}")
        workload_config = _write_workload_config(temp_root)

        result = subprocess.run(
            [
                "python3",
                "-m",
                "lsp.cli.main",
                "cross-check-guidellm",
                "--backend-config",
                str(backend_config),
                "--workload-config",
                str(workload_config),
                "--output-dir",
                str(output_dir),
                "--execute",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        execution = json.loads(
            (output_dir / "repo_cross_check_execution.json").read_text(encoding="utf-8")
        )
        self.assertEqual(execution["status"], "completed")
        self.assertEqual(execution["timeout_seconds"], 600)
        self.assertEqual(execution["artifact_validation"]["status"], "passed")
        self.assertTrue((output_dir / "benchmark.json").exists())
        self.assertTrue((output_dir / "benchmark.csv").exists())
        benchmark = json.loads((output_dir / "benchmark.json").read_text(encoding="utf-8"))
        summary = benchmark["benchmarks"][0]["scheduler_state"]
        self.assertEqual(summary["created_requests"], 5)
        self.assertEqual(summary["processed_requests"], 5)
        self.assertEqual(summary["successful_requests"], 5)


if __name__ == "__main__":
    unittest.main()

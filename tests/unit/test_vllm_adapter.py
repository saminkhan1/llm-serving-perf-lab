from __future__ import annotations

import json
import shutil
import socket
import tempfile
import unittest
from pathlib import Path
from typing import cast

import pytest

from lsp.backends import BackendLifecycleError, build_vllm_adapter
from lsp.config.loader import load_config
from lsp.config.models import BackendConfig

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


def _write_backend_config(
    *,
    temp_root: Path,
    port: int | None,
    command: list[str] | None,
    base_url: str | None = None,
) -> Path:
    config_path = temp_root / "backend.yaml"
    config = {
        "backend": "vllm",
        "mode": "serve",
        "model_id": "fake/local-test-model",
        "launch": {
            "command": command,
            "startup_timeout_seconds": 0.4,
            "healthcheck_interval_seconds": 0.05,
            "request_timeout_seconds": 0.3,
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
        assert port is not None
        config["host"] = "127.0.0.1"
        config["port"] = port
        config["metrics"] = {
            "scrape_endpoint": f"http://127.0.0.1:{port}/metrics",
            "scrape_interval_seconds": 1,
        }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path


class VLLMAdapterLifecycleTests(unittest.TestCase):
    def test_process_exit_is_visible(self) -> None:
        temp_root = Path(
            tempfile.mkdtemp(prefix="lsp-m2-adapter-exit-", dir=REPO_ROOT / "artifacts")
        )
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        config_path = _write_backend_config(
            temp_root=temp_root,
            port=18081,
            command=["python3", "-c", "raise SystemExit(3)"],
        )

        config_document = load_config(config_path)
        self.assertIsInstance(config_document, BackendConfig)
        config = cast(BackendConfig, config_document)
        adapter = build_vllm_adapter(config)

        with self.assertRaises(BackendLifecycleError) as ctx:
            adapter.launch()
        self.assertEqual(ctx.exception.phase, "launch_process_exit")
        self.assertIn("exit_code=3", str(ctx.exception))

    @pytest.mark.network
    @unittest.skipUnless(SOCKETS_ALLOWED, "local sockets are not permitted in this environment")
    def test_healthcheck_failure_is_visible(self) -> None:
        temp_root = Path(
            tempfile.mkdtemp(prefix="lsp-m2-adapter-health-", dir=REPO_ROOT / "artifacts")
        )
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        port = _free_port()
        config_path = _write_backend_config(
            temp_root=temp_root,
            port=port,
            command=["python3", str(FAKE_SERVER), "--port", str(port), "--mode", "bad-health"],
        )

        config_document = load_config(config_path)
        self.assertIsInstance(config_document, BackendConfig)
        config = cast(BackendConfig, config_document)
        adapter = build_vllm_adapter(config)

        try:
            with self.assertRaises(BackendLifecycleError) as ctx:
                adapter.launch()
            self.assertEqual(ctx.exception.phase, "healthcheck_failed")
            self.assertIn("/health", str(ctx.exception))
        finally:
            adapter.stop()

    def test_base_url_target_builds_expected_endpoints(self) -> None:
        temp_root = Path(
            tempfile.mkdtemp(prefix="lsp-m2-adapter-base-url-", dir=REPO_ROOT / "artifacts")
        )
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        config_path = _write_backend_config(
            temp_root=temp_root,
            port=None,
            command=None,
            base_url="https://example.modal.run/vllm",
        )

        config_document = load_config(config_path)
        self.assertIsInstance(config_document, BackendConfig)
        config = cast(BackendConfig, config_document)
        adapter = build_vllm_adapter(config)

        self.assertEqual(adapter.base_url, "https://example.modal.run/vllm")
        self.assertEqual(adapter.health_url, "https://example.modal.run/vllm/health")
        self.assertEqual(adapter.version_url, "https://example.modal.run/vllm/version")
        self.assertEqual(adapter.completions_url, "https://example.modal.run/vllm/v1/completions")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from lsp.config.loader import load_config
from lsp.config.models import BackendConfig, WorkloadConfig
from lsp.m2_scaffolding import (
    build_guidellm_cross_check_plan,
    build_vllm_launch_plan,
    check_m2_readiness,
    execute_guidellm_cross_check,
    probe_vllm_target,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class M2ScaffoldingTests(unittest.TestCase):
    def test_vllm_launch_plan_uses_repo_template(self) -> None:
        config_document = load_config(REPO_ROOT / "configs" / "backends" / "vllm_dev.yaml")
        config = cast(BackendConfig, config_document)

        plan = build_vllm_launch_plan(config)

        self.assertEqual(plan["attach_mode"], "external")
        self.assertEqual(plan["base_url"], "http://127.0.0.1:8000")
        self.assertTrue(bool(plan["has_command_template"]))
        self.assertIn("vllm.entrypoints.openai.api_server", str(plan["command_shell"]))
        self.assertEqual(config.resolved["hardware"]["provider"], "local")

    def test_vllm_launch_plan_supports_base_url_targets(self) -> None:
        config_document = load_config(
            REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        )
        config = cast(BackendConfig, config_document)

        plan = build_vllm_launch_plan(config)

        self.assertEqual(
            plan["base_url"],
            "https://your-workspace-name--example-vllm-inference-serve.modal.run",
        )
        self.assertNotIn("host", plan)
        self.assertNotIn("port", plan)
        self.assertFalse(bool(plan["has_command_template"]))

    def test_guidellm_cross_check_plan_is_explicitly_external(self) -> None:
        backend_document = load_config(REPO_ROOT / "configs" / "backends" / "vllm_dev.yaml")
        workload_document = load_config(REPO_ROOT / "configs" / "workloads" / "chat_short.yaml")
        backend = cast(BackendConfig, backend_document)
        workload = cast(WorkloadConfig, workload_document)

        plan = build_guidellm_cross_check_plan(
            backend=backend,
            workload=workload,
            output_dir=REPO_ROOT / "artifacts",
        )

        self.assertEqual(plan["tool"], "guidellm")
        self.assertEqual(plan["request_count"], int(workload.resolved["request_count"]))
        self.assertIn("--max-requests", plan["command"])
        self.assertIn("external cross-check scaffolding", " ".join(plan["notes"]).lower())

    def test_guidellm_cross_check_plan_uses_external_base_url(self) -> None:
        backend_document = load_config(
            REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        )
        workload_document = load_config(REPO_ROOT / "configs" / "workloads" / "chat_short.yaml")
        backend = cast(BackendConfig, backend_document)
        workload = cast(WorkloadConfig, workload_document)

        plan = build_guidellm_cross_check_plan(
            backend=backend,
            workload=workload,
            output_dir=REPO_ROOT / "artifacts",
        )

        self.assertEqual(
            plan["target"],
            "https://your-workspace-name--example-vllm-inference-serve.modal.run",
        )

    def test_probe_vllm_target_reports_metrics_and_hardware(self) -> None:
        backend_document = load_config(
            REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        )
        backend = cast(BackendConfig, backend_document)

        class FakeAdapter:
            base_url = "https://example.modal.run"
            scrape_endpoint = "https://example.modal.run/metrics"

            def healthcheck(self) -> None:
                return None

            def fetch_runtime_metadata(self) -> tuple[str | None, dict[str, object]]:
                return "vllm/0.8.0", {"version_payload": {"version": "0.8.0"}}

            def collect_metrics(self) -> list[dict[str, object]]:
                return [
                    {
                        "metric_kind": "official",
                        "metric_name": "vllm:time_to_first_token_seconds",
                        "semantic_name": "vllm:time_to_first_token_seconds",
                        "missing": False,
                    },
                    {
                        "metric_kind": "official",
                        "metric_name": None,
                        "semantic_name": "queue_depth",
                        "missing": True,
                    },
                ]

        with patch("lsp.m2_scaffolding.build_vllm_adapter", return_value=FakeAdapter()):
            probe = probe_vllm_target(backend)

        self.assertEqual(probe["status"], "ok")
        self.assertEqual(probe["backend_version"], "vllm/0.8.0")
        self.assertEqual(probe["hardware_profile"], "replace-with-modal-gpu-sku x1 via modal")
        self.assertEqual(probe["official_metrics_present"], 1)
        self.assertEqual(probe["official_metrics_missing"], ["queue_depth"])

    def test_execute_guidellm_cross_check_writes_plan_and_logs(self) -> None:
        backend_document = load_config(REPO_ROOT / "configs" / "backends" / "vllm_dev.yaml")
        workload_document = load_config(REPO_ROOT / "configs" / "workloads" / "chat_short.yaml")
        backend = cast(BackendConfig, backend_document)
        workload = cast(WorkloadConfig, workload_document)
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-guidellm-plan-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        bin_dir = temp_root / "bin"
        bin_dir.mkdir()
        fake_guidellm = bin_dir / "guidellm"
        fake_guidellm.write_text(
            "#!/bin/sh\n" "echo guidellm-ok\n" "echo guidellm-stderr 1>&2\n",
            encoding="utf-8",
        )
        fake_guidellm.chmod(fake_guidellm.stat().st_mode | stat.S_IXUSR)
        output_dir = temp_root / "guidellm"
        plan = build_guidellm_cross_check_plan(
            backend=backend,
            workload=workload,
            output_dir=output_dir,
        )

        with patch.dict(os.environ, {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}):
            returncode = execute_guidellm_cross_check(plan, cwd=REPO_ROOT)

        self.assertEqual(returncode, 0)
        execution = json.loads(
            (output_dir / "repo_cross_check_execution.json").read_text(encoding="utf-8")
        )
        persisted_plan = json.loads(
            (output_dir / "repo_cross_check_plan.json").read_text(encoding="utf-8")
        )
        self.assertEqual(execution["status"], "completed")
        self.assertEqual(persisted_plan["tool"], "guidellm")
        self.assertIn("guidellm-ok", (output_dir / "repo_cross_check_stdout.log").read_text())
        self.assertIn(
            "guidellm-stderr",
            (output_dir / "repo_cross_check_stderr.log").read_text(),
        )

    def test_check_m2_readiness_reports_placeholder_and_missing_guidellm(self) -> None:
        backend_document = load_config(
            REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        )
        backend = cast(BackendConfig, backend_document)

        with (
            patch("lsp.m2_scaffolding._tool_available") as tool_available,
            patch("lsp.m2_scaffolding._modal_current_profile", return_value="saminkhan1"),
        ):
            tool_available.side_effect = lambda name: name == "modal"
            report = check_m2_readiness(backend)

        self.assertEqual(report["status"], "blocked")
        blocked_ids = {item["id"] for item in report["checks"] if item["status"] == "blocked"}
        self.assertIn("backend.base_url", blocked_ids)
        self.assertIn("backend.metrics_endpoint", blocked_ids)
        self.assertIn("backend.hardware", blocked_ids)
        self.assertIn("tool.guidellm", blocked_ids)

    def test_check_m2_readiness_reports_ready_when_inputs_are_real(self) -> None:
        backend_document = load_config(
            REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        )
        backend = cast(BackendConfig, backend_document)
        backend.resolved["base_url"] = "https://real-workspace--vllm.modal.run"
        backend.resolved["metrics"][
            "scrape_endpoint"
        ] = "https://real-workspace--vllm.modal.run/metrics"
        backend.resolved["hardware"]["accelerator"] = "NVIDIA L4"

        with (
            patch("lsp.m2_scaffolding._tool_available", return_value=True),
            patch("lsp.m2_scaffolding._modal_current_profile", return_value="saminkhan1"),
        ):
            report = check_m2_readiness(backend)

        self.assertEqual(report["status"], "ready")

from __future__ import annotations

import unittest
from pathlib import Path
from typing import cast

from lsp.config.loader import load_config
from lsp.config.models import BackendConfig, WorkloadConfig
from lsp.m2_scaffolding import build_guidellm_cross_check_plan, build_vllm_launch_plan

REPO_ROOT = Path(__file__).resolve().parents[2]


class M2ScaffoldingTests(unittest.TestCase):
    def test_vllm_launch_plan_uses_repo_template(self) -> None:
        config_document = load_config(REPO_ROOT / "configs" / "backends" / "vllm_dev.yaml")
        config = cast(BackendConfig, config_document)

        plan = build_vllm_launch_plan(config)

        self.assertEqual(plan["attach_mode"], "external")
        self.assertTrue(bool(plan["has_command_template"]))
        self.assertIn("vllm.entrypoints.openai.api_server", str(plan["command_shell"]))

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

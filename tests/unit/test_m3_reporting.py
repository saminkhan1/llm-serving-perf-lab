from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from lsp.reporting import (
    build_m3_reporting_checkpoint,
    render_m3_reporting_report,
    render_m3_result_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HERO_RUN_DIR = REPO_ROOT / "artifacts" / "m2-qwen-l40s-modal-chat-short-20260423-r2"


class M3ReportingTests(unittest.TestCase):
    def test_build_m3_reporting_checkpoint_reads_hero_artifact(self) -> None:
        checkpoint = build_m3_reporting_checkpoint(HERO_RUN_DIR)

        self.assertEqual(
            checkpoint.question_answered,
            (
                "Can the repo produce one real, reproducible, cross-checked vLLM baseline "
                "on a single-GPU Modal deployment?"
            ),
        )
        self.assertEqual(checkpoint.request_count, 500)
        self.assertEqual(checkpoint.response_count, 500)
        self.assertEqual(checkpoint.total_metric_rows, 920)
        self.assertEqual(checkpoint.official_metric_rows, 420)
        self.assertEqual(checkpoint.official_metrics_missing, [])
        self.assertAlmostEqual(checkpoint.client_latency.p95_seconds, 1.316456, places=6)
        self.assertIsNotNone(checkpoint.guide_summary)
        guide = checkpoint.guide_summary
        assert guide is not None
        self.assertEqual(guide.successful_requests, 500)
        self.assertAlmostEqual(guide.ttft_median_ms, 187.18385696411133, places=6)
        self.assertAlmostEqual(guide.ttft_p95_ms, 266.2920951843262, places=6)
        self.assertEqual(
            checkpoint.stable_repro_command,
            (
                "make reproduce RUN=m2-real "
                "REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml "
                "REPRO_WORKLOAD=configs/workloads/chat_short.yaml "
                "REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260423-r2"
            ),
        )

    def test_rendered_outputs_match_tracked_files(self) -> None:
        checkpoint = build_m3_reporting_checkpoint(HERO_RUN_DIR)

        expected_report = (HERO_RUN_DIR / "m3_report.md").read_text(encoding="utf-8")
        expected_summary = (HERO_RUN_DIR / "m3_summary.md").read_text(encoding="utf-8")

        self.assertEqual(render_m3_reporting_report(checkpoint), expected_report)
        self.assertEqual(render_m3_result_summary(checkpoint), expected_summary)

    def test_cli_build_m3_report_writes_outputs(self) -> None:
        temp_root = Path(tempfile.mkdtemp(prefix="lsp-m3-report-", dir=REPO_ROOT / "artifacts"))
        self.addCleanup(lambda: shutil.rmtree(temp_root, ignore_errors=True))
        report_path = temp_root / "report.md"
        summary_path = temp_root / "summary.md"

        result = subprocess.run(
            [
                "python3",
                "-m",
                "lsp.cli.main",
                "build-m3-report",
                "--run-dir",
                str(HERO_RUN_DIR),
                "--report-path",
                str(report_path),
                "--summary-path",
                str(summary_path),
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        manifest = json.loads(result.stdout)
        self.assertEqual(manifest["report_path"], str(report_path))
        self.assertEqual(manifest["summary_path"], str(summary_path))
        self.assertIn("M3 Reporting Checkpoint", report_path.read_text(encoding="utf-8"))
        self.assertIn("M3 Result Summary", summary_path.read_text(encoding="utf-8"))

    def test_readme_references_m3_outputs(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("m3_report.md", readme)
        self.assertIn("m3_summary.md", readme)
        self.assertIn("REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml", readme)
        self.assertIn("The next required work order is M4 SGLang + PD baseline.", readme)


if __name__ == "__main__":
    unittest.main()

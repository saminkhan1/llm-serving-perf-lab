from __future__ import annotations

import unittest
from pathlib import Path

from lsp.config.loader import load_config, validate_example_configs
from lsp.config.models import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]


class ConfigLoaderTests(unittest.TestCase):
    def test_validate_example_configs(self) -> None:
        results = validate_example_configs(REPO_ROOT)
        self.assertIn("configs/backends/vllm_dev.yaml", results)
        self.assertIn("configs/backends/vllm_modal_example.yaml", results)
        self.assertEqual(results["configs/workloads/chat_short.yaml"], "workload")

    def test_unknown_keys_fail_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_backend_unknown_key.yaml"
        with self.assertRaises(ValidationError):
            load_config(config_path)

    def test_missing_required_keys_fail_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_backend_missing_required.yaml"
        with self.assertRaisesRegex(ValidationError, "missing required keys: port"):
            load_config(config_path)

    def test_conflicting_endpoint_modes_fail_validation(self) -> None:
        config_path = (
            REPO_ROOT / "tests" / "fixtures" / "invalid_backend_conflicting_endpoint_modes.yaml"
        )
        with self.assertRaisesRegex(ValidationError, "either base_url or host/port"):
            load_config(config_path)

    def test_modal_backend_config_validates(self) -> None:
        config_path = REPO_ROOT / "configs" / "backends" / "vllm_modal_example.yaml"
        config = load_config(config_path)
        self.assertEqual(config.kind, "backend")
        self.assertEqual(config.to_dict()["resolved"]["hardware"]["provider"], "modal")

    def test_invalid_hardware_metadata_fails_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_backend_hardware_bad_count.yaml"
        with self.assertRaisesRegex(ValidationError, "accelerator_count must be > 0"):
            load_config(config_path)

    def test_base_url_with_path_fails_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_backend_base_url_with_path.yaml"
        with self.assertRaisesRegex(ValidationError, "must be the endpoint root"):
            load_config(config_path)

    def test_metrics_endpoint_mismatch_fails_validation(self) -> None:
        config_path = (
            REPO_ROOT / "tests" / "fixtures" / "invalid_backend_metrics_endpoint_mismatch.yaml"
        )
        with self.assertRaisesRegex(ValidationError, "must equal base_url \\+ '/metrics'"):
            load_config(config_path)

    def test_invalid_enum_fails_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_threshold_bad_enum.yaml"
        with self.assertRaisesRegex(ValidationError, "comparison_mode must be one of"):
            load_config(config_path)

    def test_impossible_thresholds_fail_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_threshold_impossible.yaml"
        with self.assertRaisesRegex(ValidationError, "impossible thresholds"):
            load_config(config_path)

    def test_impossible_budget_fails_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_experiment_impossible_budget.yaml"
        with self.assertRaisesRegex(
            ValidationError,
            "max_consecutive_failures cannot exceed max_runs",
        ):
            load_config(config_path)


if __name__ == "__main__":
    unittest.main()

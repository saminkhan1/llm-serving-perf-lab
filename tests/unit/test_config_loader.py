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
        self.assertEqual(results["configs/workloads/chat_short.yaml"], "workload")

    def test_unknown_keys_fail_validation(self) -> None:
        config_path = REPO_ROOT / "tests" / "fixtures" / "invalid_backend_unknown_key.yaml"
        with self.assertRaises(ValidationError):
            load_config(config_path)


if __name__ == "__main__":
    unittest.main()

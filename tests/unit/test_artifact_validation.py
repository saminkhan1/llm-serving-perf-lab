from __future__ import annotations

import json
import unittest
from pathlib import Path

from lsp.artifacts.models import validate_artifact_dir
from lsp.config.models import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]


class ArtifactValidationTests(unittest.TestCase):
    def test_missing_metrics_file_fails(self) -> None:
        run_dir = REPO_ROOT / "tests" / "fixtures" / "invalid_artifact_missing_metrics"
        with self.assertRaisesRegex(
            ValidationError,
            "artifact directory missing required files: metrics.parquet",
        ):
            validate_artifact_dir(run_dir)

    def test_valid_fixture_artifact_passes(self) -> None:
        run_dir = REPO_ROOT / "tests" / "fixtures" / "valid_artifact"
        bundle = validate_artifact_dir(run_dir)
        self.assertEqual(bundle.metadata.run_id, "fixture-run")
        payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "success")


if __name__ == "__main__":
    unittest.main()

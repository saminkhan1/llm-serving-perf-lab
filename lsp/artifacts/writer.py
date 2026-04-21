from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lsp.artifacts.models import ArtifactBundle, RunMetadata, validate_artifact_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_synthetic_parquet_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    # M0 keeps the fake path synthetic: parquet-named files contain deterministic row JSON.
    serialized = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(serialized, encoding="utf-8")


def write_artifact_bundle(
    run_dir: Path,
    metadata: RunMetadata,
    backend_config: dict[str, Any],
    system_info: dict[str, Any],
    scorecard: dict[str, Any],
    requests: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    report_lines: list[str],
) -> ArtifactBundle:
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "plots").mkdir()

    write_json(run_dir / "run.json", metadata.to_dict())
    write_json(run_dir / "backend_config_resolved.json", backend_config)
    write_json(run_dir / "system_info.json", system_info)
    write_json(run_dir / "scorecard.json", scorecard)
    write_synthetic_parquet_rows(run_dir / "requests.parquet", requests)
    write_synthetic_parquet_rows(run_dir / "responses.parquet", responses)
    write_synthetic_parquet_rows(run_dir / "metrics.parquet", metrics)
    (run_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return validate_artifact_dir(run_dir)

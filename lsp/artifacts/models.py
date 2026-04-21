from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pyarrow.parquet as pq

from lsp.config.models import ValidationError

ARTIFACT_SCHEMA_VERSION = "artifact.v2"


@dataclass(frozen=True)
class RunMetadata:
    schema_version: str
    run_id: str
    status: str
    mode: str
    backend: str
    backend_version: str
    model_id: str
    workload_id: str
    policy_id: str
    seed: int
    start_time_utc: str
    end_time_utc: str
    git_commit: str
    git_dirty: bool
    hardware_profile: str
    synthetic: bool
    repro_command: str
    notes: list[str]
    hardware_metadata: dict[str, object] | None = None
    failure_reason: str | None = None
    runtime_metadata: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactBundle:
    run_dir: Path
    metadata: RunMetadata


def _parquet_row_count(path: Path) -> int:
    try:
        table = pq.read_table(path)  # type: ignore[no-untyped-call]
    except Exception as exc:  # pragma: no cover - exact pyarrow errors are version-specific
        raise ValidationError(f"invalid parquet file: {path.name}") from exc
    return int(table.num_rows)


def validate_artifact_dir(run_dir: Path) -> ArtifactBundle:
    required = [
        "run.json",
        "backend_config_resolved.json",
        "system_info.json",
        "scorecard.json",
        "report.md",
        "requests.parquet",
        "responses.parquet",
        "metrics.parquet",
    ]
    missing = [name for name in required if not (run_dir / name).exists()]
    if missing:
        joined = ", ".join(missing)
        raise ValidationError(f"artifact directory missing required files: {joined}")

    plots_dir = run_dir / "plots"
    if not plots_dir.exists() or not plots_dir.is_dir():
        raise ValidationError("artifact directory missing plots/ directory")

    run_path = run_dir / "run.json"
    metadata_raw = json.loads(run_path.read_text(encoding="utf-8"))
    if metadata_raw.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ValidationError("artifact schema_version mismatch")
    if not metadata_raw.get("repro_command"):
        raise ValidationError("artifact repro_command must be non-empty")
    if metadata_raw.get("status") == "success":
        if _parquet_row_count(run_dir / "metrics.parquet") <= 0:
            raise ValidationError("successful run must write non-empty metrics.parquet")

    return ArtifactBundle(
        run_dir=run_dir,
        metadata=RunMetadata(**metadata_raw),
    )

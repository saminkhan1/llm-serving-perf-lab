from __future__ import annotations

import platform
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from lsp.artifacts.models import ARTIFACT_SCHEMA_VERSION, ArtifactBundle, RunMetadata
from lsp.artifacts.writer import write_artifact_bundle
from lsp.config.loader import load_config
from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig


def _git_commit(repo_root: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return commit, dirty


def _build_fake_rows(
    workload: WorkloadConfig,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    row_count = int(workload.resolved.get("request_count", 3))
    row_count = min(row_count, 5)
    requests: list[dict[str, object]] = []
    responses: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    for index in range(row_count):
        prompt_hash = sha256(
            f"{workload.workload_id}:{workload.seed}:{index}".encode("utf-8")
        ).hexdigest()[:16]
        requests.append(
            {
                "request_id": f"req-{index:03d}",
                "arrival_timestamp_ms": index * 50,
                "prompt": f"SYNTHETIC_FAKE_PROMPT::{prompt_hash}",
                "max_new_tokens": 32,
                "tags": ["synthetic", "fake_run", workload.workload_id],
            }
        )
        responses.append(
            {
                "request_id": f"req-{index:03d}",
                "status": "ok",
                "output_text": f"SYNTHETIC_FAKE_RESPONSE::{prompt_hash}",
                "output_tokens": 16 + index,
            }
        )
        metrics.append(
            {
                "request_id": f"req-{index:03d}",
                "ttft_ms": 20 + index,
                "latency_ms": 55 + index * 3,
                "tokens_per_second": 120.0 - index,
                "metric_source": "synthetic_fake_backend",
            }
        )
    return requests, responses, metrics


def run_fake_benchmark(
    *,
    backend_config_path: Path,
    workload_config_path: Path,
    output_dir: Path,
    run_id: str | None,
    argv: list[str],
) -> ArtifactBundle:
    repo_root = Path.cwd()
    backend = load_config(backend_config_path)
    workload = load_config(workload_config_path)
    if not isinstance(backend, BackendConfig):
        raise ValidationError("fake-run requires a backend config")
    if not isinstance(workload, WorkloadConfig):
        raise ValidationError("fake-run requires a workload config")

    start_time = datetime.now(UTC)
    resolved_run_id = run_id or f"fake-{workload.workload_id}-{workload.seed}"
    run_dir = output_dir / resolved_run_id
    if run_dir.exists():
        raise ValidationError(f"artifact run directory already exists: {run_dir}")

    commit, dirty = _git_commit(repo_root)
    requests, responses, metrics = _build_fake_rows(workload)
    end_time = datetime.now(UTC)

    metadata = RunMetadata(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        run_id=resolved_run_id,
        status="success",
        mode="fake",
        backend=backend.backend,
        backend_version="synthetic-m0",
        model_id=backend.model_id,
        workload_id=workload.workload_id,
        policy_id="none",
        seed=workload.seed,
        start_time_utc=start_time.isoformat(),
        end_time_utc=end_time.isoformat(),
        git_commit=commit,
        git_dirty=dirty,
        hardware_profile=f"{platform.system()}-{platform.machine()}",
        synthetic=True,
        repro_command=f"python3 -m lsp.cli.main {' '.join(argv)}",
        notes=[
            "Synthetic fake backend path for M0 foundation only.",
            "This artifact does not represent a real serving benchmark.",
        ],
    )

    scorecard = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "summary": "Synthetic fake run completed successfully.",
        "synthetic": True,
        "request_count": len(requests),
        "metrics_present": len(metrics),
    }
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "synthetic": True,
    }
    report_lines = [
        "# Fake Run Report",
        "",
        "This report comes from the M0 synthetic fake backend path.",
        "It validates repo wiring and artifact structure only.",
        "",
        f"- run_id: `{resolved_run_id}`",
        f"- backend: `{backend.backend}`",
        f"- workload: `{workload.workload_id}`",
        f"- request_rows: `{len(requests)}`",
        f"- metric_rows: `{len(metrics)}`",
    ]

    return write_artifact_bundle(
        run_dir=run_dir,
        metadata=metadata,
        backend_config=backend.resolved,
        system_info=system_info,
        scorecard=scorecard,
        requests=requests,
        responses=responses,
        metrics=metrics,
        report_lines=report_lines,
    )

from __future__ import annotations

import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from lsp.artifacts.models import ARTIFACT_SCHEMA_VERSION, ArtifactBundle, RunMetadata
from lsp.artifacts.writer import write_artifact_bundle
from lsp.config.loader import load_config
from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig
from lsp.workloads import NormalizedRequest, generate_requests


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


def _build_synthetic_backend_rows(
    requests: list[NormalizedRequest],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    responses: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    for index, request in enumerate(requests):
        output_tokens = max(1, request.max_new_tokens - (index % 3))
        ttft_ms = 12 + (request.prompt_token_count // 64) + (index % 5)
        latency_ms = ttft_ms + output_tokens * 3
        responses.append(
            {
                "request_id": request.request_id,
                "status": "synthetic_ok",
                "output_text": (
                    "SYNTHETIC_DRY_RUN_RESPONSE "
                    f"request_id={request.request_id} output_tokens={output_tokens}"
                ),
                "output_tokens": output_tokens,
                "synthetic": True,
            }
        )
        metrics.append(
            {
                "request_id": request.request_id,
                "ttft_ms": ttft_ms,
                "latency_ms": latency_ms,
                "tokens_per_second": round(output_tokens / max(latency_ms / 1000, 0.001), 3),
                "queue_depth": index % 4,
                "metric_source": "synthetic_dry_run",
                "synthetic": True,
            }
        )
    return responses, metrics


def run_benchmark(
    *,
    backend_config_path: Path,
    workload_config_path: Path,
    output_dir: Path,
    run_id: str | None,
    argv: list[str],
    dry_run: bool,
) -> ArtifactBundle:
    if not dry_run:
        raise ValidationError(
            "M1 runner supports --dry-run only; real backend integration starts in M2"
        )

    repo_root = Path.cwd()
    backend = load_config(backend_config_path)
    workload = load_config(workload_config_path)
    if not isinstance(backend, BackendConfig):
        raise ValidationError("run requires a backend config")
    if not isinstance(workload, WorkloadConfig):
        raise ValidationError("run requires a workload config")

    start_time = datetime.now(UTC)
    resolved_run_id = run_id or f"dry-run-{workload.workload_id}-{workload.seed}"
    run_dir = output_dir / resolved_run_id
    if run_dir.exists():
        raise ValidationError(f"artifact run directory already exists: {run_dir}")

    commit, dirty = _git_commit(repo_root)
    requests = generate_requests(workload)
    responses, metrics = _build_synthetic_backend_rows(requests)
    end_time = datetime.now(UTC)

    metadata = RunMetadata(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        run_id=resolved_run_id,
        status="success",
        mode="dry-run",
        backend=backend.backend,
        backend_version="synthetic-m1-dry-run",
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
            "Synthetic dry-run benchmark path for M1 harness validation.",
            "No real backend serving, GPU metrics, or network calls are performed.",
        ],
    )

    scorecard = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "summary": "Synthetic dry-run benchmark completed successfully.",
        "synthetic": True,
        "request_count": len(requests),
        "response_count": len(responses),
        "metric_rows": len(metrics),
    }
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "synthetic": True,
        "mode": "dry-run",
    }
    report_lines = [
        "# M1 Dry-Run Benchmark Report",
        "",
        "This report comes from the deterministic M1 dry-run harness.",
        "It validates workload generation, replay, and artifact writing only.",
        "",
        f"- run_id: `{resolved_run_id}`",
        f"- backend: `{backend.backend}`",
        f"- workload: `{workload.workload_id}`",
        f"- request_rows: `{len(requests)}`",
        f"- response_rows: `{len(responses)}`",
        f"- metric_rows: `{len(metrics)}`",
    ]

    return write_artifact_bundle(
        run_dir=run_dir,
        metadata=metadata,
        backend_config=backend.resolved,
        system_info=system_info,
        scorecard=scorecard,
        requests=[request.to_dict() for request in requests],
        responses=responses,
        metrics=metrics,
        report_lines=report_lines,
    )

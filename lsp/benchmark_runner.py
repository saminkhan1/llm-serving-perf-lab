from __future__ import annotations

import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from lsp.artifacts.models import ARTIFACT_SCHEMA_VERSION, ArtifactBundle, RunMetadata
from lsp.artifacts.writer import write_artifact_bundle
from lsp.backends import BackendLifecycleError, build_vllm_adapter
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


class BenchmarkRunFailed(RuntimeError):
    def __init__(self, bundle: ArtifactBundle, message: str) -> None:
        super().__init__(message)
        self.bundle = bundle


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _build_real_report_lines(
    *,
    run_id: str,
    backend: BackendConfig,
    workload: WorkloadConfig,
    request_count: int,
    response_count: int,
    metric_rows: int,
    official_missing: list[str],
    latency_seconds: list[float],
    runtime_metadata: dict[str, object],
    notes: list[str],
) -> list[str]:
    p50 = _percentile(latency_seconds, 0.50)
    p95 = _percentile(latency_seconds, 0.95)
    p99 = _percentile(latency_seconds, 0.99)

    lines = [
        "# M2 Real-Mode Benchmark Report",
        "",
        "This report exercises the M2 controller path against a structured HTTP backend.",
        (
            "Interpret measured results only in the context of the tested backend, "
            "model, hardware, and workload."
        ),
        "",
        f"- run_id: `{run_id}`",
        f"- backend: `{backend.backend}`",
        f"- workload: `{workload.workload_id}`",
        f"- request_rows: `{request_count}`",
        f"- response_rows: `{response_count}`",
        f"- metric_rows: `{metric_rows}`",
        (
            f"- median_client_latency_seconds: `{median(latency_seconds):.6f}`"
            if latency_seconds
            else "- median_client_latency_seconds: `n/a`"
        ),
        (
            f"- p50_client_latency_seconds: `{p50:.6f}`"
            if p50 is not None
            else "- p50_client_latency_seconds: `n/a`"
        ),
        (
            f"- p95_client_latency_seconds: `{p95:.6f}`"
            if p95 is not None
            else "- p95_client_latency_seconds: `n/a`"
        ),
        (
            f"- p99_client_latency_seconds: `{p99:.6f}`"
            if p99 is not None
            else "- p99_client_latency_seconds: `n/a`"
        ),
        (
            f"- official_metrics_missing: `{', '.join(official_missing)}`"
            if official_missing
            else "- official_metrics_missing: `none`"
        ),
    ]

    version_payload = runtime_metadata.get("version_payload")
    if isinstance(version_payload, dict):
        lines.append(f"- version_payload: `{version_payload}`")
    for note in notes:
        lines.append(f"- note: {note}")
    return lines


def _write_failure_artifact(
    *,
    run_dir: Path,
    run_id: str,
    backend: BackendConfig,
    workload: WorkloadConfig,
    argv: list[str],
    start_time: datetime,
    end_time: datetime,
    commit: str,
    dirty: bool,
    failure_reason: str,
    notes: list[str],
    runtime_metadata: dict[str, object],
) -> ArtifactBundle:
    metadata = RunMetadata(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        run_id=run_id,
        status="failed",
        mode="serve",
        backend=backend.backend,
        backend_version=str(runtime_metadata.get("backend_version") or "unknown"),
        model_id=backend.model_id,
        workload_id=workload.workload_id,
        policy_id="none",
        seed=workload.seed,
        start_time_utc=start_time.isoformat(),
        end_time_utc=end_time.isoformat(),
        git_commit=commit,
        git_dirty=dirty,
        hardware_profile=f"{platform.system()}-{platform.machine()}",
        synthetic=False,
        repro_command=f"python3 -m lsp.cli.main {' '.join(argv)}",
        notes=notes,
        failure_reason=failure_reason,
        runtime_metadata=runtime_metadata,
    )
    scorecard = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "summary": "Real-mode benchmark failed before completion.",
        "status": "failed",
        "failure_reason": failure_reason,
    }
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "mode": "serve",
        "runtime_metadata": runtime_metadata,
        "failure_reason": failure_reason,
    }
    report_lines = [
        "# M2 Real-Mode Benchmark Failure",
        "",
        f"- run_id: `{run_id}`",
        f"- backend: `{backend.backend}`",
        f"- workload: `{workload.workload_id}`",
        f"- failure_reason: `{failure_reason}`",
    ]
    report_lines.extend(f"- note: {note}" for note in notes)
    return write_artifact_bundle(
        run_dir=run_dir,
        metadata=metadata,
        backend_config=backend.resolved,
        system_info=system_info,
        scorecard=scorecard,
        requests=[],
        responses=[],
        metrics=[],
        report_lines=report_lines,
    )


def _run_real_benchmark(
    *,
    backend: BackendConfig,
    workload: WorkloadConfig,
    run_dir: Path,
    resolved_run_id: str,
    argv: list[str],
    commit: str,
    dirty: bool,
) -> ArtifactBundle:
    adapter = build_vllm_adapter(backend)
    requests = generate_requests(workload)
    start_time = datetime.now(UTC)
    runtime_metadata: dict[str, object] = {}
    notes: list[str] = []

    try:
        launch_info = adapter.launch()
        runtime_metadata = dict(launch_info.runtime_metadata)
        runtime_metadata["backend_version"] = launch_info.version or "unknown"
        runtime_metadata["scrape_endpoint"] = launch_info.scrape_endpoint
        if "fake" in json_like(runtime_metadata).lower():
            notes.append(
                "This run used a controller-verified fake local backend and is not "
                "a claimed real vLLM benchmark artifact."
            )

        responses: list[dict[str, object]] = []
        metrics: list[dict[str, object]] = []
        latency_seconds: list[float] = []
        for request_payload in requests:
            started = time.perf_counter()
            response = adapter.submit(request_payload)
            elapsed = time.perf_counter() - started
            latency_seconds.append(elapsed)
            responses.append(
                {
                    "request_id": response.request_id,
                    "status": response.status,
                    "output_text": response.output_text,
                    "output_tokens": response.output_tokens,
                    "finish_reason": response.finish_reason,
                    "synthetic": False,
                }
            )
            metrics.append(
                {
                    "metric_kind": "derived",
                    "metric_name": "client_request_latency_seconds",
                    "semantic_name": "client_request_latency_seconds",
                    "request_id": response.request_id,
                    "value": elapsed,
                    "missing": False,
                    "metric_source": "client_timer",
                }
            )

        metrics.extend(adapter.collect_metrics())
        end_time = datetime.now(UTC)
        official_missing = sorted(
            str(row["semantic_name"])
            for row in metrics
            if row.get("metric_kind") == "official" and row.get("missing") is True
        )

        metadata = RunMetadata(
            schema_version=ARTIFACT_SCHEMA_VERSION,
            run_id=resolved_run_id,
            status="success",
            mode="serve",
            backend=backend.backend,
            backend_version=str(runtime_metadata.get("backend_version") or "unknown"),
            model_id=backend.model_id,
            workload_id=workload.workload_id,
            policy_id="none",
            seed=workload.seed,
            start_time_utc=start_time.isoformat(),
            end_time_utc=end_time.isoformat(),
            git_commit=commit,
            git_dirty=dirty,
            hardware_profile=f"{platform.system()}-{platform.machine()}",
            synthetic=False,
            repro_command=f"python3 -m lsp.cli.main {' '.join(argv)}",
            notes=notes,
            runtime_metadata=runtime_metadata,
        )
        scorecard = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "summary": "Real-mode benchmark completed successfully.",
            "status": "success",
            "request_count": len(requests),
            "response_count": len(responses),
            "metric_rows": len(metrics),
            "official_metrics_missing": official_missing,
        }
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "mode": "serve",
            "runtime_metadata": runtime_metadata,
            "official_metrics_missing": official_missing,
        }
        report_lines = _build_real_report_lines(
            run_id=resolved_run_id,
            backend=backend,
            workload=workload,
            request_count=len(requests),
            response_count=len(responses),
            metric_rows=len(metrics),
            official_missing=official_missing,
            latency_seconds=latency_seconds,
            runtime_metadata=runtime_metadata,
            notes=notes,
        )
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
    except BackendLifecycleError as exc:
        end_time = datetime.now(UTC)
        notes.append("Lifecycle failure was recorded into the artifact bundle.")
        bundle = _write_failure_artifact(
            run_dir=run_dir,
            run_id=resolved_run_id,
            backend=backend,
            workload=workload,
            argv=argv,
            start_time=start_time,
            end_time=end_time,
            commit=commit,
            dirty=dirty,
            failure_reason=str(exc),
            notes=notes,
            runtime_metadata=runtime_metadata,
        )
        raise BenchmarkRunFailed(bundle, str(exc)) from exc
    finally:
        adapter.stop()


def json_like(payload: object) -> str:
    return str(payload)


def run_benchmark(
    *,
    backend_config_path: Path,
    workload_config_path: Path,
    output_dir: Path,
    run_id: str | None,
    argv: list[str],
    dry_run: bool,
) -> ArtifactBundle:
    repo_root = Path.cwd()
    backend = load_config(backend_config_path)
    workload = load_config(workload_config_path)
    if not isinstance(backend, BackendConfig):
        raise ValidationError("run requires a backend config")
    if not isinstance(workload, WorkloadConfig):
        raise ValidationError("run requires a workload config")

    start_time = datetime.now(UTC)
    resolved_run_id = run_id or f"dry-run-{workload.workload_id}-{workload.seed}"
    if not dry_run:
        resolved_run_id = run_id or f"real-{workload.workload_id}-{workload.seed}"
    run_dir = output_dir / resolved_run_id
    if run_dir.exists():
        raise ValidationError(f"artifact run directory already exists: {run_dir}")

    commit, dirty = _git_commit(repo_root)
    if not dry_run:
        return _run_real_benchmark(
            backend=backend,
            workload=workload,
            run_dir=run_dir,
            resolved_run_id=resolved_run_id,
            argv=argv,
            commit=commit,
            dirty=dirty,
        )

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

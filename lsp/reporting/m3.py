from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, cast

import pyarrow.parquet as pq

from lsp.artifacts.models import RunMetadata, validate_artifact_dir
from lsp.config.models import ValidationError


@dataclass(frozen=True)
class LatencySummary:
    count: int
    median_seconds: float
    p50_seconds: float
    p95_seconds: float
    p99_seconds: float


@dataclass(frozen=True)
class GuideLLMSummary:
    request_count: int
    successful_requests: int
    errored_requests: int
    incomplete_requests: int
    ttft_median_ms: float
    ttft_p95_ms: float
    request_latency_median_seconds: float
    request_latency_p95_seconds: float
    mean_requests_per_second: float


@dataclass(frozen=True)
class PortfolioCheckpoint:
    run_dir: Path
    metadata: RunMetadata
    backend_config_path: str | None
    workload_config_path: str | None
    output_dir: str | None
    request_count: int
    response_count: int
    total_metric_rows: int
    official_metric_rows: int
    official_metrics_missing: list[str]
    client_latency: LatencySummary
    guide_summary: GuideLLMSummary | None
    question_answered: str
    caveats: list[str]
    stable_repro_command: str | None
    cross_check_command: str | None


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * percentile)))
    return float(ordered[index])


def _extract_client_latency_summary(metrics_path: Path) -> tuple[LatencySummary, int, int]:
    rows = pq.read_table(metrics_path).to_pylist()  # type: ignore[no-untyped-call]
    values = [
        float(row["value"])
        for row in rows
        if row.get("metric_name") == "client_request_latency_seconds"
        and isinstance(row.get("value"), (float, int))
    ]
    if not values:
        raise ValidationError("artifact metrics.parquet is missing client_request_latency_seconds")
    official_metric_rows = sum(1 for row in rows if row.get("metric_kind") == "official")
    return (
        LatencySummary(
            count=len(values),
            median_seconds=float(median(values)),
            p50_seconds=_percentile(values, 0.50),
            p95_seconds=_percentile(values, 0.95),
            p99_seconds=_percentile(values, 0.99),
        ),
        len(rows),
        official_metric_rows,
    )


def _extract_stat(metric_block: dict[str, Any], name: str) -> dict[str, Any]:
    section = metric_block.get(name)
    if not isinstance(section, dict):
        raise ValidationError(f"GuideLLM benchmark is missing metric block: {name}")
    successful = section.get("successful")
    if not isinstance(successful, dict):
        raise ValidationError(f"GuideLLM benchmark is missing successful metric block: {name}")
    return successful


def _extract_percentile_value(
    metric_block: dict[str, Any], name: str, percentile_key: str
) -> float:
    stats = _extract_stat(metric_block, name)
    percentiles = stats.get("percentiles")
    if not isinstance(percentiles, dict):
        raise ValidationError(f"GuideLLM benchmark is missing percentiles for metric: {name}")
    value = percentiles.get(percentile_key)
    if not isinstance(value, (float, int)):
        raise ValidationError(
            f"GuideLLM benchmark is missing percentile {percentile_key} for metric: {name}"
        )
    return float(value)


def _extract_mean_value(metric_block: dict[str, Any], name: str) -> float:
    stats = _extract_stat(metric_block, name)
    value = stats.get("mean")
    if not isinstance(value, (float, int)):
        raise ValidationError(f"GuideLLM benchmark is missing mean for metric: {name}")
    return float(value)


def _extract_median_value(metric_block: dict[str, Any], name: str) -> float:
    stats = _extract_stat(metric_block, name)
    value = stats.get("median")
    if not isinstance(value, (float, int)):
        raise ValidationError(f"GuideLLM benchmark is missing median for metric: {name}")
    return float(value)


def _extract_guidellm_summary(guidellm_dir: Path) -> GuideLLMSummary | None:
    benchmark_path = guidellm_dir / "benchmark.json"
    execution_path = guidellm_dir / "repo_cross_check_execution.json"
    if not benchmark_path.exists() or not execution_path.exists():
        return None

    benchmark = _load_json(benchmark_path)
    execution = _load_json(execution_path)
    benchmarks = benchmark.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValidationError("GuideLLM benchmark.json is missing benchmarks")
    benchmark_entry = cast(dict[str, Any], benchmarks[0])
    metric_block = benchmark_entry.get("metrics")
    if not isinstance(metric_block, dict):
        raise ValidationError("GuideLLM benchmark.json is missing metrics")

    validation = execution.get("artifact_validation")
    if not isinstance(validation, dict):
        raise ValidationError(
            "GuideLLM repo_cross_check_execution.json is missing artifact_validation"
        )
    summary = validation.get("summary")
    if not isinstance(summary, dict):
        raise ValidationError("GuideLLM repo_cross_check_execution.json is missing summary")

    request_count = summary.get("created_requests")
    successful = summary.get("successful_requests")
    errored = summary.get("errored_requests")
    incomplete = summary.get("incomplete_entry_count")
    if not isinstance(request_count, int):
        raise ValidationError("GuideLLM summary missing created_requests")
    if not isinstance(successful, int):
        raise ValidationError("GuideLLM summary missing successful_requests")
    if not isinstance(errored, int):
        raise ValidationError("GuideLLM summary missing errored_requests")
    if not isinstance(incomplete, int):
        raise ValidationError("GuideLLM summary missing incomplete_entry_count")

    return GuideLLMSummary(
        request_count=request_count,
        successful_requests=successful,
        errored_requests=errored,
        incomplete_requests=incomplete,
        ttft_median_ms=_extract_median_value(metric_block, "time_to_first_token_ms"),
        ttft_p95_ms=_extract_percentile_value(metric_block, "time_to_first_token_ms", "p95"),
        request_latency_median_seconds=_extract_median_value(metric_block, "request_latency"),
        request_latency_p95_seconds=_extract_percentile_value(
            metric_block, "request_latency", "p95"
        ),
        mean_requests_per_second=_extract_mean_value(metric_block, "requests_per_second"),
    )


def _derive_repo_paths(metadata: RunMetadata) -> tuple[str | None, str | None, str | None]:
    tokens = shlex.split(metadata.repro_command)
    if "run" not in tokens:
        return None, None, None

    def _value_after(flag: str) -> str | None:
        if flag not in tokens:
            return None
        index = tokens.index(flag)
        next_index = index + 1
        if next_index >= len(tokens):
            return None
        return tokens[next_index]

    return (
        _value_after("--backend-config"),
        _value_after("--workload-config"),
        _value_after("--output-dir"),
    )


def _derive_make_repro_command(
    metadata: RunMetadata,
    backend_config_path: str | None,
    workload_config_path: str | None,
) -> str | None:
    if metadata.mode != "serve":
        return None
    if backend_config_path is None or workload_config_path is None:
        return None
    return (
        "make reproduce RUN=m2-real "
        f"REPRO_BACKEND={backend_config_path} "
        f"REPRO_WORKLOAD={workload_config_path} "
        f"REPRO_RUN_ID={metadata.run_id}"
    )


def _derive_cross_check_command(
    *,
    backend_config_path: str | None,
    workload_config_path: str | None,
    guidellm_dir: Path,
) -> str | None:
    if backend_config_path is None or workload_config_path is None:
        return None
    return (
        "uv run lsp cross-check-guidellm "
        f"--backend-config {backend_config_path} "
        f"--workload-config {workload_config_path} "
        f"--output-dir {_display_path(guidellm_dir)} "
        "--execute"
    )


def _display_backend_name(backend: str) -> str:
    mapping = {
        "vllm": "vLLM",
        "sglang": "SGLang",
    }
    return mapping.get(backend, backend)


def _display_path(path: Path) -> str:
    cwd = Path.cwd().resolve()
    try:
        return path.resolve().relative_to(cwd).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _question_answered(metadata: RunMetadata) -> str:
    provider = None
    if metadata.hardware_metadata is not None:
        raw_provider = metadata.hardware_metadata.get("provider")
        if isinstance(raw_provider, str):
            provider = raw_provider
    if provider == "modal":
        return (
            "Can the repo produce one real, reproducible, cross-checked "
            f"{_display_backend_name(metadata.backend)} baseline on a single-GPU Modal deployment?"
        )
    return (
        "Can the repo produce one real, reproducible, cross-checked "
        f"{_display_backend_name(metadata.backend)} baseline on `{metadata.hardware_profile}`?"
    )


def _build_caveats(
    *,
    metadata: RunMetadata,
    guide_summary: GuideLLMSummary | None,
) -> list[str]:
    caveats = [
        (
            f"Bound to {metadata.hardware_profile}, {metadata.model_id}, and "
            f"{metadata.workload_id}. It does not generalize beyond that setup."
        )
    ]
    if metadata.git_dirty:
        caveats.append("The stored artifact records `git_dirty: true`.")
    if guide_summary is not None:
        caveats.append(
            "The GuideLLM cross-check uses a synthetic token summary rather than an exact "
            "controller trace replay."
        )
    provider = None
    if metadata.hardware_metadata is not None:
        raw_provider = metadata.hardware_metadata.get("provider")
        if isinstance(raw_provider, str):
            provider = raw_provider
    if provider == "modal":
        caveats.append(
            "Modal endpoints can cold-start; treat a failed first probe as warmup only if a "
            "subsequent probe passes before the benchmark run."
        )
    return caveats


def build_m3_portfolio_checkpoint(run_dir: Path) -> PortfolioCheckpoint:
    bundle = validate_artifact_dir(run_dir)
    scorecard = _load_json(run_dir / "scorecard.json")
    request_count = scorecard.get("request_count")
    response_count = scorecard.get("response_count")
    missing_metrics = scorecard.get("official_metrics_missing")
    if not isinstance(request_count, int):
        raise ValidationError("scorecard.json is missing request_count")
    if not isinstance(response_count, int):
        raise ValidationError("scorecard.json is missing response_count")
    if not isinstance(missing_metrics, list) or not all(
        isinstance(item, str) for item in missing_metrics
    ):
        raise ValidationError("scorecard.json is missing official_metrics_missing")

    client_latency, total_metric_rows, official_metric_rows = _extract_client_latency_summary(
        run_dir / "metrics.parquet"
    )
    metadata = bundle.metadata
    backend_config_path, workload_config_path, output_dir = _derive_repo_paths(metadata)
    guide_summary = _extract_guidellm_summary(run_dir / "guidellm")

    return PortfolioCheckpoint(
        run_dir=run_dir,
        metadata=metadata,
        backend_config_path=backend_config_path,
        workload_config_path=workload_config_path,
        output_dir=output_dir,
        request_count=request_count,
        response_count=response_count,
        total_metric_rows=total_metric_rows,
        official_metric_rows=official_metric_rows,
        official_metrics_missing=list(missing_metrics),
        client_latency=client_latency,
        guide_summary=guide_summary,
        question_answered=_question_answered(metadata),
        caveats=_build_caveats(metadata=metadata, guide_summary=guide_summary),
        stable_repro_command=_derive_make_repro_command(
            metadata,
            backend_config_path,
            workload_config_path,
        ),
        cross_check_command=_derive_cross_check_command(
            backend_config_path=backend_config_path,
            workload_config_path=workload_config_path,
            guidellm_dir=run_dir / "guidellm",
        ),
    )


def _fmt_seconds(value: float) -> str:
    return f"{value:.3f}"


def _fmt_ms(value: float) -> str:
    return f"{value:.1f}"


def _fmt_rps(value: float) -> str:
    return f"{value:.2f}"


def render_m3_portfolio_report(checkpoint: PortfolioCheckpoint) -> str:
    metadata = checkpoint.metadata
    lines = [
        "# M3 Portfolio Checkpoint A",
        "",
        (
            "This report packages the first stored real benchmark into a reviewer-friendly "
            "artifact that can be audited from repo state plus saved outputs."
        ),
        "",
        "## Question",
        "",
        checkpoint.question_answered,
        "",
        "## Setup",
        "",
        f"- Backend: `{_display_backend_name(metadata.backend)}` `{metadata.backend_version}`",
        f"- Hardware: `{metadata.hardware_profile}`",
        f"- Model: `{metadata.model_id}`",
        f"- Workload: `{metadata.workload_id}`",
        f"- Run ID: `{metadata.run_id}`",
        f"- Requests: `{checkpoint.request_count}`",
        "",
        "## Measured Result",
        "",
        (
            "- Controller path completed "
            f"`{checkpoint.response_count}/{checkpoint.request_count}` requests."
        ),
        (
            "- Client latency p50 / p95 / p99: "
            f"`{_fmt_seconds(checkpoint.client_latency.p50_seconds)} / "
            f"{_fmt_seconds(checkpoint.client_latency.p95_seconds)} / "
            f"{_fmt_seconds(checkpoint.client_latency.p99_seconds)} s`."
        ),
        (
            "- Official metric rows captured: "
            f"`{checkpoint.official_metric_rows}` with `"
            f"{len(checkpoint.official_metrics_missing)}` required metrics missing."
        ),
        f"- Total metric rows written: `{checkpoint.total_metric_rows}`.",
    ]

    if checkpoint.guide_summary is not None:
        guide = checkpoint.guide_summary
        lines.extend(
            [
                "",
                "## External Cross-Check",
                "",
                (
                    "- Saved GuideLLM run completed "
                    f"`{guide.successful_requests}/{guide.request_count}` requests "
                    f"with `{guide.errored_requests}` errored and "
                    f"`{guide.incomplete_requests}` incomplete entries."
                ),
                (
                    "- Median / p95 TTFT: "
                    f"`{_fmt_ms(guide.ttft_median_ms)} / {_fmt_ms(guide.ttft_p95_ms)} ms`."
                ),
                (
                    "- Median / p95 request latency: "
                    f"`{_fmt_seconds(guide.request_latency_median_seconds)} / "
                    f"{_fmt_seconds(guide.request_latency_p95_seconds)} s`."
                ),
                f"- Mean throughput: `{_fmt_rps(guide.mean_requests_per_second)} req/s`.",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is enough to claim that the repo can stand up one real vLLM target, "
                "drive a bounded workload end to end, collect official `/metrics`, and preserve "
                "an external cross-check next to the artifact."
            ),
            (
                "It is not enough to claim a serving optimization, a PD advantage, routing "
                "effectiveness, regression protection, profiler depth, or production readiness."
            ),
            "",
            "## Reproduce",
            "",
            "Primary benchmark:",
            "```bash",
            checkpoint.stable_repro_command or metadata.repro_command,
            "```",
        ]
    )
    if checkpoint.cross_check_command is not None:
        lines.extend(
            [
                "",
                "GuideLLM cross-check:",
                "```bash",
                checkpoint.cross_check_command,
                "```",
            ]
        )

    lines.extend(
        [
            "",
            "## Evidence Files",
            "",
            f"- `artifacts/{metadata.run_id}/run.json`",
            f"- `artifacts/{metadata.run_id}/scorecard.json`",
            f"- `artifacts/{metadata.run_id}/metrics.parquet`",
            f"- `artifacts/{metadata.run_id}/report.md`",
        ]
    )
    if checkpoint.guide_summary is not None:
        lines.extend(
            [
                f"- `artifacts/{metadata.run_id}/guidellm/benchmark.json`",
                f"- `artifacts/{metadata.run_id}/guidellm/repo_cross_check_execution.json`",
            ]
        )

    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in checkpoint.caveats)
    lines.append("")
    return "\n".join(lines)


def render_m3_result_summary(checkpoint: PortfolioCheckpoint) -> str:
    metadata = checkpoint.metadata
    caveat_summary = "; ".join(caveat.rstrip(".") for caveat in checkpoint.caveats)
    lines = [
        "# M3 Result Summary",
        "",
        f"- Question answered: {checkpoint.question_answered}",
        (
            "- Answer: yes. The controller path completed "
            f"`{checkpoint.response_count}/{checkpoint.request_count}` requests on "
            f"`{metadata.hardware_profile}` with `{metadata.model_id}` and "
            f"`{metadata.workload_id}`, at client latency p50 / p95 / p99 "
            f"`{_fmt_seconds(checkpoint.client_latency.p50_seconds)} / "
            f"{_fmt_seconds(checkpoint.client_latency.p95_seconds)} / "
            f"{_fmt_seconds(checkpoint.client_latency.p99_seconds)} s`."
        ),
    ]
    if checkpoint.guide_summary is not None:
        guide = checkpoint.guide_summary
        lines.append(
            (
                "- Cross-check: the saved GuideLLM run also completed "
                f"`{guide.successful_requests}/{guide.request_count}` requests and reported "
                f"median / p95 TTFT `{_fmt_ms(guide.ttft_median_ms)} / "
                f"{_fmt_ms(guide.ttft_p95_ms)} ms` with mean throughput "
                f"`{_fmt_rps(guide.mean_requests_per_second)} req/s`."
            )
        )
    lines.append("- Caveats: " + caveat_summary + ".")
    lines.extend(
        [
            "",
            "```bash",
            checkpoint.stable_repro_command or metadata.repro_command,
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_m3_report_outputs(
    *,
    run_dir: Path,
    report_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, str]:
    checkpoint = build_m3_portfolio_checkpoint(run_dir)
    resolved_report_path = report_path or run_dir / "m3_report.md"
    resolved_summary_path = summary_path or run_dir / "m3_summary.md"
    resolved_report_path.write_text(
        render_m3_portfolio_report(checkpoint),
        encoding="utf-8",
    )
    resolved_summary_path.write_text(
        render_m3_result_summary(checkpoint),
        encoding="utf-8",
    )
    return {
        "run_dir": str(run_dir),
        "report_path": str(resolved_report_path),
        "summary_path": str(resolved_summary_path),
    }

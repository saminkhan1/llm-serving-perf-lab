from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsp.backends import build_vllm_adapter
from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig
from lsp.workloads import generate_requests

GUIDELLM_EXECUTION_TIMEOUT_SECONDS = 600
GUIDELLM_ARTIFACT_VALIDATION_EXIT_CODE = 3
GUIDELLM_ENVIRONMENT = {
    "GUIDELLM__MP_CONTEXT_TYPE": "spawn",
    "GUIDELLM__MAX_WORKER_PROCESSES": "1",
}
GUIDELLM_OUTPUT_FILES = ("benchmark.json", "benchmark.csv")


def _ensure_vllm_backend(config: BackendConfig) -> None:
    if config.backend != "vllm":
        raise ValidationError("M2 scaffolding requires a vllm backend config")


def _string_list(value: object, *, context: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValidationError(f"{context} must be a non-empty string list")
    return [str(item) for item in value]


def _resolve_base_url(payload: dict[str, Any]) -> str:
    configured = payload.get("base_url")
    if isinstance(configured, str) and configured:
        return configured.rstrip("/")
    return f"http://{payload['host']}:{payload['port']}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def _modal_current_profile() -> str | None:
    if not _tool_available("modal"):
        return None
    result = subprocess.run(
        ["modal", "profile", "current"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    profile = result.stdout.strip()
    return profile or None


def build_vllm_launch_plan(config: BackendConfig) -> dict[str, Any]:
    _ensure_vllm_backend(config)
    hardware_profile, hardware_metadata = describe_backend_hardware(config, require_explicit=False)
    launch = config.resolved["launch"]
    attach_mode = str(
        launch.get("attach_mode") or ("spawn" if launch.get("command") else "external")
    )

    command: list[str] | None = None
    if "command" in launch and launch["command"] is not None:
        command = _string_list(launch["command"], context="vllm backend config.launch.command")

    command_template: list[str] | None = None
    if "command_template" in launch and launch["command_template"] is not None:
        command_template = _string_list(
            launch["command_template"],
            context="vllm backend config.launch.command_template",
        )

    resolved = command or command_template
    plan = {
        "backend": config.backend,
        "model_id": config.model_id,
        "attach_mode": attach_mode,
        "base_url": _resolve_base_url(config.resolved),
        "metrics_endpoint": config.resolved["metrics"]["scrape_endpoint"],
        "has_spawn_command": command is not None,
        "has_command_template": command_template is not None,
        "command": resolved,
        "command_shell": shlex.join(resolved) if resolved else None,
        "hardware_profile": hardware_profile,
        "hardware_metadata": hardware_metadata,
        "notes": [
            (
                "Attach mode 'external' means this repo expects you to start vLLM "
                "outside the benchmark command."
            ),
            (
                "Replace launch.command if you want the benchmark runner to spawn "
                "and stop the server itself."
            ),
        ],
    }
    if "host" in config.resolved:
        plan["host"] = config.resolved["host"]
    if "port" in config.resolved:
        plan["port"] = config.resolved["port"]
    return plan


def describe_backend_hardware(
    config: BackendConfig,
    *,
    require_explicit: bool,
) -> tuple[str | None, dict[str, object] | None]:
    raw_hardware = config.resolved.get("hardware")
    if raw_hardware is None:
        if require_explicit:
            raise ValidationError(
                "real benchmark runs require backend config.hardware with provider, "
                "accelerator, and accelerator_count"
            )
        return None, None
    if not isinstance(raw_hardware, dict):
        raise ValidationError("backend config.hardware must be an object")

    accelerator = str(raw_hardware["accelerator"])
    accelerator_count = int(raw_hardware["accelerator_count"])
    provider = str(raw_hardware["provider"])
    summary = f"{accelerator} x{accelerator_count} via {provider}"

    extras: list[str] = []
    instance_type = raw_hardware.get("instance_type")
    if isinstance(instance_type, str) and instance_type:
        extras.append(f"instance={instance_type}")
    region = raw_hardware.get("region")
    if isinstance(region, str) and region:
        extras.append(f"region={region}")
    if extras:
        summary = f"{summary} ({', '.join(extras)})"

    return summary, dict(raw_hardware)


def _mean_int(values: list[int]) -> int:
    if not values:
        return 0
    return max(1, round(sum(values) / len(values)))


def _guidellm_environment() -> dict[str, str]:
    return dict(GUIDELLM_ENVIRONMENT)


def _coerce_subprocess_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _coerce_non_negative_int(value: object, *, context: str) -> int:
    if isinstance(value, bool):
        raise ValidationError(f"{context} must be a non-negative integer")
    if isinstance(value, int):
        integer = value
    elif isinstance(value, float) and value.is_integer():
        integer = int(value)
    else:
        raise ValidationError(f"{context} must be a non-negative integer")
    if integer < 0:
        raise ValidationError(f"{context} must be a non-negative integer")
    return integer


def _count_request_entries(value: object, *, context: str) -> int:
    if not isinstance(value, list):
        raise ValidationError(f"{context} must be a list")
    return len(value)


def _summarize_guidellm_benchmark_report(report: dict[str, Any]) -> dict[str, int]:
    benchmarks = report.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValidationError("GuideLLM benchmark report must contain at least one benchmark")

    summary = {
        "benchmark_count": len(benchmarks),
        "created_requests": 0,
        "processed_requests": 0,
        "successful_requests": 0,
        "errored_requests": 0,
        "cancelled_requests": 0,
        "successful_entry_count": 0,
        "errored_entry_count": 0,
        "incomplete_entry_count": 0,
    }

    for index, benchmark in enumerate(benchmarks):
        if not isinstance(benchmark, dict):
            raise ValidationError(f"GuideLLM benchmark[{index}] must be an object")
        scheduler_state = benchmark.get("scheduler_state")
        requests = benchmark.get("requests")
        if not isinstance(scheduler_state, dict):
            raise ValidationError(f"GuideLLM benchmark[{index}].scheduler_state must be an object")
        if not isinstance(requests, dict):
            raise ValidationError(f"GuideLLM benchmark[{index}].requests must be an object")

        summary["created_requests"] += _coerce_non_negative_int(
            scheduler_state.get("created_requests"),
            context=f"GuideLLM benchmark[{index}].scheduler_state.created_requests",
        )
        summary["processed_requests"] += _coerce_non_negative_int(
            scheduler_state.get("processed_requests"),
            context=f"GuideLLM benchmark[{index}].scheduler_state.processed_requests",
        )
        summary["successful_requests"] += _coerce_non_negative_int(
            scheduler_state.get("successful_requests"),
            context=f"GuideLLM benchmark[{index}].scheduler_state.successful_requests",
        )
        summary["errored_requests"] += _coerce_non_negative_int(
            scheduler_state.get("errored_requests"),
            context=f"GuideLLM benchmark[{index}].scheduler_state.errored_requests",
        )
        summary["cancelled_requests"] += _coerce_non_negative_int(
            scheduler_state.get("cancelled_requests"),
            context=f"GuideLLM benchmark[{index}].scheduler_state.cancelled_requests",
        )
        summary["successful_entry_count"] += _count_request_entries(
            requests.get("successful"),
            context=f"GuideLLM benchmark[{index}].requests.successful",
        )
        summary["errored_entry_count"] += _count_request_entries(
            requests.get("errored"),
            context=f"GuideLLM benchmark[{index}].requests.errored",
        )
        summary["incomplete_entry_count"] += _count_request_entries(
            requests.get("incomplete"),
            context=f"GuideLLM benchmark[{index}].requests.incomplete",
        )

    return summary


def validate_guidellm_cross_check_artifact(
    plan: dict[str, Any],
    *,
    output_dir: Path,
) -> dict[str, Any]:
    expected_output_files = plan.get("output_files", list(GUIDELLM_OUTPUT_FILES))
    if not isinstance(expected_output_files, list) or not all(
        isinstance(item, str) and item for item in expected_output_files
    ):
        raise ValidationError("cross-check plan output_files must be a non-empty string list")

    missing_output_files = [
        name for name in expected_output_files if not (output_dir / name).is_file()
    ]
    if missing_output_files:
        return {
            "status": "artifact_invalid",
            "failure_reason": (
                "GuideLLM exited successfully but did not write the required output files: "
                + ", ".join(missing_output_files)
            ),
            "missing_output_files": missing_output_files,
        }

    benchmark_path = output_dir / GUIDELLM_OUTPUT_FILES[0]
    try:
        benchmark_report = json.loads(benchmark_path.read_text(encoding="utf-8"))
        summary = _summarize_guidellm_benchmark_report(benchmark_report)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return {
            "status": "artifact_invalid",
            "failure_reason": (
                "GuideLLM exited successfully but the benchmark artifact could not be "
                f"validated: {type(exc).__name__}: {exc}"
            ),
        }

    validation: dict[str, Any] = {
        "status": "passed",
        "summary": summary,
        "validated_output_files": list(expected_output_files),
    }
    issues: list[str] = []

    expected_request_count = plan.get("request_count")
    if isinstance(expected_request_count, int) and expected_request_count > 0:
        validation["expected_request_count"] = expected_request_count
        if summary["created_requests"] != expected_request_count:
            issues.append(
                f"created_requests={summary['created_requests']} expected={expected_request_count}"
            )

    if summary["processed_requests"] != summary["created_requests"]:
        issues.append(
            "processed_requests="
            f"{summary['processed_requests']} created_requests={summary['created_requests']}"
        )
    if summary["successful_requests"] != summary["successful_entry_count"]:
        issues.append(
            "successful_requests="
            f"{summary['successful_requests']} "
            f"successful_entries={summary['successful_entry_count']}"
        )
    if summary["errored_requests"] != summary["errored_entry_count"]:
        issues.append(
            "errored_requests="
            f"{summary['errored_requests']} errored_entries={summary['errored_entry_count']}"
        )
    if summary["processed_requests"] != (
        summary["successful_requests"] + summary["errored_requests"] + summary["cancelled_requests"]
    ):
        processed_component_total = (
            summary["successful_requests"]
            + summary["errored_requests"]
            + summary["cancelled_requests"]
        )
        issues.append(
            "processed_requests="
            f"{summary['processed_requests']} "
            f"successful+errored+cancelled={processed_component_total}"
        )
    if summary["errored_requests"] != 0:
        issues.append(f"errored_requests={summary['errored_requests']}")
    if summary["cancelled_requests"] != 0:
        issues.append(f"cancelled_requests={summary['cancelled_requests']}")
    if summary["incomplete_entry_count"] != 0:
        issues.append(f"incomplete_entries={summary['incomplete_entry_count']}")

    if issues:
        validation["status"] = "artifact_incomplete"
        validation["failure_reason"] = (
            "GuideLLM exited successfully but wrote an incomplete benchmark artifact: "
            + "; ".join(issues)
        )
        validation["issues"] = issues

    return validation


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def build_guidellm_cross_check_plan(
    *,
    backend: BackendConfig,
    workload: WorkloadConfig,
    output_dir: Path,
) -> dict[str, Any]:
    _ensure_vllm_backend(backend)
    requests = generate_requests(workload)
    prompt_tokens = [request.prompt_token_count for request in requests]
    output_tokens = [request.max_new_tokens for request in requests]
    avg_prompt_tokens = _mean_int(prompt_tokens)
    avg_output_tokens = _mean_int(output_tokens)
    data_arg = f"prompt_tokens={avg_prompt_tokens},output_tokens={avg_output_tokens}"
    target = _resolve_base_url(backend.resolved)
    resolved_output_dir = output_dir.resolve()
    hardware_profile, hardware_metadata = describe_backend_hardware(backend, require_explicit=False)
    command = [
        "guidellm",
        "benchmark",
        "run",
        "--target",
        target,
        "--backend",
        "openai_http",
        "--model",
        backend.model_id,
        "--request-format",
        "/v1/completions",
        "--profile",
        "synchronous",
        "--max-requests",
        str(len(requests)),
        "--data-num-workers",
        "0",
        "--output-dir",
        str(resolved_output_dir),
        "--outputs",
        GUIDELLM_OUTPUT_FILES[0],
        "--outputs",
        GUIDELLM_OUTPUT_FILES[1],
        "--disable-console-interactive",
        "--data",
        data_arg,
    ]
    return {
        "tool": "guidellm",
        "tool_available": shutil.which("guidellm") is not None,
        "workload_id": workload.workload_id,
        "request_count": len(requests),
        "target": target,
        "output_dir": str(resolved_output_dir),
        "hardware_profile": hardware_profile,
        "hardware_metadata": hardware_metadata,
        "data": {
            "mode": "synthetic_token_summary",
            "avg_prompt_tokens": avg_prompt_tokens,
            "avg_output_tokens": avg_output_tokens,
            "source_seed": workload.seed,
        },
        "command": command,
        "command_shell": shlex.join(command),
        "environment": _guidellm_environment(),
        "timeout_seconds": GUIDELLM_EXECUTION_TIMEOUT_SECONDS,
        "output_files": list(GUIDELLM_OUTPUT_FILES),
        "notes": [
            (
                "This is external cross-check scaffolding only; it does not "
                "fabricate a benchmark result."
            ),
            (
                "The generated GuideLLM command uses synthetic token sizes derived from the repo "
                "workload config, not a byte-for-byte replay of the repo request trace."
            ),
            (
                "GuideLLM 0.6.x expects `guidellm benchmark run` with an explicit "
                "`--backend openai_http`, `--model`, and `--request-format /v1/completions` "
                "for this cross-check shape."
            ),
            (
                "The plan writes explicit `benchmark.json` and `benchmark.csv` outputs because "
                "GuideLLM 0.6.0 does not reliably resolve bare `json`/`csv` aliases when "
                "`--output-dir` is used."
            ),
            (
                "Execution exports `GUIDELLM__MP_CONTEXT_TYPE=spawn` and "
                "`GUIDELLM__MAX_WORKER_PROCESSES=1` to avoid a local multiprocessing "
                "shutdown hang observed with the installed GuideLLM 0.6.0 CLI on macOS."
            ),
            (
                "Execution treats a zero exit code as insufficient proof by itself; the saved "
                "GuideLLM artifact must also close all expected requests cleanly."
            ),
        ],
    }


def probe_vllm_target(config: BackendConfig) -> dict[str, Any]:
    _ensure_vllm_backend(config)
    adapter = build_vllm_adapter(config)
    hardware_profile, hardware_metadata = describe_backend_hardware(config, require_explicit=False)

    adapter.healthcheck()
    version, runtime_metadata = adapter.fetch_runtime_metadata()
    metrics = adapter.collect_metrics()
    official_missing = sorted(
        str(row["semantic_name"])
        for row in metrics
        if row.get("metric_kind") == "official" and row.get("missing") is True
    )
    official_present = sum(
        1 for row in metrics if row.get("metric_kind") == "official" and row.get("missing") is False
    )

    return {
        "status": "ok",
        "backend": config.backend,
        "model_id": config.model_id,
        "base_url": adapter.base_url,
        "metrics_endpoint": adapter.scrape_endpoint,
        "backend_version": version,
        "runtime_metadata": runtime_metadata,
        "hardware_profile": hardware_profile,
        "hardware_metadata": hardware_metadata,
        "official_metrics_present": official_present,
        "official_metrics_missing": official_missing,
        "metric_rows": len(metrics),
        "notes": [
            "This probe checks reachability, runtime metadata, and official metrics exposure.",
            "It does not submit workload traffic or claim a benchmark result.",
        ],
    }


def check_m2_readiness(config: BackendConfig) -> dict[str, Any]:
    _ensure_vllm_backend(config)
    hardware_profile, hardware_metadata = describe_backend_hardware(config, require_explicit=True)
    if hardware_profile is None:
        raise ValidationError("real benchmark runs require resolved hardware metadata")

    checks: list[dict[str, str]] = []
    base_url = _resolve_base_url(config.resolved)
    metrics_endpoint = str(config.resolved["metrics"]["scrape_endpoint"])
    provider = str((hardware_metadata or {}).get("provider") or "")
    accelerator = str((hardware_metadata or {}).get("accelerator") or "")

    def add_check(*, check_id: str, status: str, message: str) -> None:
        checks.append({"id": check_id, "status": status, "message": message})

    if "your-workspace-name--example-vllm-inference-serve.modal.run" in base_url:
        add_check(
            check_id="backend.base_url",
            status="blocked",
            message="Replace the example Modal base_url with the deployed endpoint root.",
        )
    else:
        add_check(
            check_id="backend.base_url",
            status="ok",
            message="Backend base_url is set to a non-example endpoint root.",
        )

    if "your-workspace-name--example-vllm-inference-serve.modal.run" in metrics_endpoint:
        add_check(
            check_id="backend.metrics_endpoint",
            status="blocked",
            message=(
                "Replace the example metrics.scrape_endpoint with the deployed endpoint "
                "/metrics URL."
            ),
        )
    else:
        add_check(
            check_id="backend.metrics_endpoint",
            status="ok",
            message="Metrics endpoint is set to a non-example URL.",
        )

    if accelerator.startswith("replace-with-"):
        add_check(
            check_id="backend.hardware",
            status="blocked",
            message="Replace the placeholder hardware.accelerator with the actual tested GPU SKU.",
        )
    else:
        add_check(
            check_id="backend.hardware",
            status="ok",
            message=f"Hardware metadata is explicit: {hardware_profile}.",
        )

    if _tool_available("guidellm"):
        add_check(
            check_id="tool.guidellm",
            status="ok",
            message="GuideLLM executable is available for the official cross-check.",
        )
    else:
        add_check(
            check_id="tool.guidellm",
            status="blocked",
            message="GuideLLM executable is not installed in PATH.",
        )

    if provider == "modal":
        if not _tool_available("modal"):
            add_check(
                check_id="tool.modal",
                status="blocked",
                message="Modal CLI is not installed in PATH.",
            )
        else:
            profile = _modal_current_profile()
            if profile is None:
                add_check(
                    check_id="tool.modal_auth",
                    status="blocked",
                    message="Modal CLI is installed but no current profile is configured.",
                )
            else:
                add_check(
                    check_id="tool.modal_auth",
                    status="ok",
                    message=f"Modal CLI is configured with current profile `{profile}`.",
                )

    blocked = [item for item in checks if item["status"] == "blocked"]
    return {
        "status": "ready" if not blocked else "blocked",
        "backend": config.backend,
        "model_id": config.model_id,
        "base_url": base_url,
        "metrics_endpoint": metrics_endpoint,
        "hardware_profile": hardware_profile,
        "checks": checks,
        "recommended_commands": [
            "make verify-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml",
            "make smoke-guidellm",
            "make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml",
            (
                "make reproduce RUN=m2-real "
                "REPRO_BACKEND=configs/backends/vllm_modal_example.yaml "
                "REPRO_WORKLOAD=configs/workloads/chat_short.yaml "
                "REPRO_RUN_ID=<run_id>"
            ),
            (
                "uv run lsp cross-check-guidellm "
                "--backend-config configs/backends/vllm_modal_example.yaml "
                "--workload-config configs/workloads/chat_short.yaml "
                "--output-dir artifacts/<run_id>/guidellm --execute"
            ),
        ],
    }


def execute_guidellm_cross_check(plan: dict[str, Any], *, cwd: Path) -> int:
    command = plan["command"]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ValidationError("cross-check plan does not contain a runnable command")

    output_dir = Path(str(plan["output_dir"]))
    if not output_dir.is_absolute():
        output_dir = cwd / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    persisted_plan = dict(plan)
    persisted_plan["output_dir"] = str(output_dir)
    _write_json(output_dir / "repo_cross_check_plan.json", persisted_plan)

    executable = str(command[0])
    if shutil.which(executable) is None:
        _write_json(
            output_dir / "repo_cross_check_execution.json",
            {
                "status": "not_executable",
                "tool": executable,
                "output_dir": str(output_dir),
                "failure_reason": (
                    "GuideLLM executable not found. Install it separately before "
                    "running the cross-check."
                ),
            },
        )
        raise ValidationError(
            "GuideLLM executable not found. Install it separately before running the cross-check."
        )

    started_at = datetime.now(UTC).isoformat()
    env = os.environ.copy()
    raw_environment = plan.get("environment")
    if raw_environment is not None:
        if not isinstance(raw_environment, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in raw_environment.items()
        ):
            raise ValidationError("cross-check plan environment must be a string-to-string map")
        env.update(raw_environment)
    timeout_seconds = plan.get("timeout_seconds", GUIDELLM_EXECUTION_TIMEOUT_SECONDS)
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        raise ValidationError("cross-check plan timeout_seconds must be a positive integer")
    try:
        process = subprocess.Popen(
            command,
            cwd=output_dir,
            env=env,
            start_new_session=(os.name == "posix"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except OSError as exc:
        _write_json(
            output_dir / "repo_cross_check_execution.json",
            {
                "status": "execution_error",
                "tool": executable,
                "output_dir": str(output_dir),
                "started_at_utc": started_at,
                "failure_reason": f"{type(exc).__name__}: {exc}",
            },
        )
        raise
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_subprocess_output(exc.stdout)
        stderr = _coerce_subprocess_output(exc.stderr)
        _terminate_process_group(process)
        finished_at = datetime.now(UTC).isoformat()
        (output_dir / "repo_cross_check_stdout.log").write_text(stdout, encoding="utf-8")
        (output_dir / "repo_cross_check_stderr.log").write_text(stderr, encoding="utf-8")
        _write_json(
            output_dir / "repo_cross_check_execution.json",
            {
                "status": "timed_out",
                "tool": executable,
                "output_dir": str(output_dir),
                "started_at_utc": started_at,
                "finished_at_utc": finished_at,
                "returncode": 124,
                "timeout_seconds": timeout_seconds,
                "stdout_log": "repo_cross_check_stdout.log",
                "stderr_log": "repo_cross_check_stderr.log",
                "failure_reason": (
                    "GuideLLM did not exit before the configured timeout and the "
                    "repo terminated the local process group."
                ),
            },
        )
        return 124

    finished_at = datetime.now(UTC).isoformat()
    (output_dir / "repo_cross_check_stdout.log").write_text(stdout, encoding="utf-8")
    (output_dir / "repo_cross_check_stderr.log").write_text(stderr, encoding="utf-8")
    tool_returncode = int(process.returncode)
    artifact_validation: dict[str, Any] | None = None
    status = "completed" if tool_returncode == 0 else "failed"
    failure_reason: str | None = (
        None if tool_returncode == 0 else f"GuideLLM exited with return code {tool_returncode}."
    )
    returncode = tool_returncode

    if tool_returncode == 0:
        artifact_validation = validate_guidellm_cross_check_artifact(plan, output_dir=output_dir)
        if artifact_validation["status"] != "passed":
            status = str(artifact_validation["status"])
            failure_reason = str(artifact_validation["failure_reason"])
            returncode = GUIDELLM_ARTIFACT_VALIDATION_EXIT_CODE

    _write_json(
        output_dir / "repo_cross_check_execution.json",
        {
            "status": status,
            "tool": executable,
            "output_dir": str(output_dir),
            "started_at_utc": started_at,
            "finished_at_utc": finished_at,
            "returncode": returncode,
            "tool_returncode": tool_returncode,
            "timeout_seconds": timeout_seconds,
            "stdout_log": "repo_cross_check_stdout.log",
            "stderr_log": "repo_cross_check_stderr.log",
            "failure_reason": failure_reason,
            "artifact_validation": artifact_validation,
        },
    )
    return returncode


def format_plan_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)

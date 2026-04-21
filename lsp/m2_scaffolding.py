from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsp.backends import build_vllm_adapter
from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig
from lsp.workloads import generate_requests


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
    hardware_profile, hardware_metadata = describe_backend_hardware(backend, require_explicit=False)
    command = [
        "guidellm",
        "benchmark",
        "--target",
        target,
        "--request-type",
        "completions",
        "--profile",
        "synchronous",
        "--max-requests",
        str(len(requests)),
        "--data",
        data_arg,
    ]
    return {
        "tool": "guidellm",
        "tool_available": shutil.which("guidellm") is not None,
        "workload_id": workload.workload_id,
        "request_count": len(requests),
        "target": target,
        "output_dir": str(output_dir),
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
                "GuideLLM documentation describes `guidellm benchmark --target ... --request-type "
                "completions --data ...` and allows `--max-requests` to bound a run."
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
    try:
        result = subprocess.run(
            command,
            cwd=output_dir,
            check=False,
            capture_output=True,
            text=True,
        )
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

    finished_at = datetime.now(UTC).isoformat()
    (output_dir / "repo_cross_check_stdout.log").write_text(result.stdout, encoding="utf-8")
    (output_dir / "repo_cross_check_stderr.log").write_text(result.stderr, encoding="utf-8")
    _write_json(
        output_dir / "repo_cross_check_execution.json",
        {
            "status": "completed" if result.returncode == 0 else "failed",
            "tool": executable,
            "output_dir": str(output_dir),
            "started_at_utc": started_at,
            "finished_at_utc": finished_at,
            "returncode": int(result.returncode),
            "stdout_log": "repo_cross_check_stdout.log",
            "stderr_log": "repo_cross_check_stderr.log",
        },
    )
    return int(result.returncode)


def format_plan_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)

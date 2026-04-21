from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig
from lsp.workloads import generate_requests


def _ensure_vllm_backend(config: BackendConfig) -> None:
    if config.backend != "vllm":
        raise ValidationError("M2 scaffolding requires a vllm backend config")


def _string_list(value: object, *, context: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValidationError(f"{context} must be a non-empty string list")
    return [str(item) for item in value]


def build_vllm_launch_plan(config: BackendConfig) -> dict[str, Any]:
    _ensure_vllm_backend(config)
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
    return {
        "backend": config.backend,
        "model_id": config.model_id,
        "attach_mode": attach_mode,
        "host": config.resolved["host"],
        "port": config.resolved["port"],
        "base_url": f"http://{config.resolved['host']}:{config.resolved['port']}",
        "metrics_endpoint": config.resolved["metrics"]["scrape_endpoint"],
        "has_spawn_command": command is not None,
        "has_command_template": command_template is not None,
        "command": resolved,
        "command_shell": shlex.join(resolved) if resolved else None,
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
    target = f"http://{backend.resolved['host']}:{backend.resolved['port']}"
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


def execute_guidellm_cross_check(plan: dict[str, Any], *, cwd: Path) -> int:
    command = plan["command"]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ValidationError("cross-check plan does not contain a runnable command")
    if shutil.which(command[0]) is None:
        raise ValidationError(
            "GuideLLM executable not found. Install it separately before running the cross-check."
        )
    output_dir = Path(str(plan["output_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, cwd=output_dir if output_dir.is_dir() else cwd, check=False)
    return int(result.returncode)


def format_plan_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)

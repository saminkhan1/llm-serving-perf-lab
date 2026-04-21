from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from lsp.backends.base import (
    BackendAdapter,
    BackendLaunchInfo,
    BackendLifecycleError,
    BackendResponse,
)
from lsp.config.models import BackendConfig, ValidationError
from lsp.metrics.prometheus import parse_prometheus_metrics
from lsp.workloads import NormalizedRequest


def _http_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    timeout_seconds: float,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url=url, data=data, method=method, headers=headers)
    with request.urlopen(req, timeout=timeout_seconds) as response:
        status = int(response.status)
        body = response.read().decode("utf-8")
    if not body:
        return status, {}
    decoded = json.loads(body)
    if not isinstance(decoded, dict):
        raise BackendLifecycleError(
            phase="invalid_json",
            message="endpoint returned non-object JSON payload",
            details={"url": url},
        )
    return status, decoded


def _http_text(*, url: str, timeout_seconds: float) -> tuple[int, str]:
    req = request.Request(url=url, method="GET")
    with request.urlopen(req, timeout=timeout_seconds) as response:
        return int(response.status), response.read().decode("utf-8")


@dataclass(frozen=True)
class _LaunchSettings:
    command: list[str] | None
    cwd: str | None
    env: dict[str, str]
    startup_timeout_seconds: float
    healthcheck_interval_seconds: float
    request_timeout_seconds: float


class VLLMAdapter(BackendAdapter):
    def __init__(self, config: BackendConfig) -> None:
        if config.backend != "vllm":
            raise ValidationError("VLLMAdapter requires a vllm backend config")

        self.config = config
        self.payload = config.resolved
        self.base_url = f"http://{self.payload['host']}:{self.payload['port']}"
        self.health_url = f"{self.base_url}/health"
        self.version_url = f"{self.base_url}/version"
        self.completions_url = f"{self.base_url}/v1/completions"
        metrics = self.payload["metrics"]
        self.scrape_endpoint = str(metrics["scrape_endpoint"])
        self.settings = self._parse_launch_settings()
        self.process: subprocess.Popen[str] | None = None
        self._launch_started = False

    def _parse_launch_settings(self) -> _LaunchSettings:
        launch = self.payload["launch"]
        command = launch.get("command")
        cwd = launch.get("cwd")
        env = launch.get("env") or {}
        startup_timeout = launch.get("startup_timeout_seconds", 30.0)
        health_interval = launch.get("healthcheck_interval_seconds", 0.25)
        request_timeout = launch.get("request_timeout_seconds", 10.0)

        if command is not None:
            if (
                not isinstance(command, list)
                or not command
                or not all(isinstance(item, str) and item for item in command)
            ):
                raise ValidationError(
                    "vllm backend config.launch.command must be a non-empty string list"
                )
        if cwd is not None and (not isinstance(cwd, str) or not cwd):
            raise ValidationError("vllm backend config.launch.cwd must be a non-empty string")
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in env.items()
        ):
            raise ValidationError("vllm backend config.launch.env must be a mapping of strings")
        if not isinstance(startup_timeout, (int, float)) or startup_timeout <= 0:
            raise ValidationError("vllm backend config.launch.startup_timeout_seconds must be > 0")
        if not isinstance(health_interval, (int, float)) or health_interval <= 0:
            raise ValidationError(
                "vllm backend config.launch.healthcheck_interval_seconds must be > 0"
            )
        if not isinstance(request_timeout, (int, float)) or request_timeout <= 0:
            raise ValidationError("vllm backend config.launch.request_timeout_seconds must be > 0")

        return _LaunchSettings(
            command=command,
            cwd=cwd,
            env=dict(env),
            startup_timeout_seconds=float(startup_timeout),
            healthcheck_interval_seconds=float(health_interval),
            request_timeout_seconds=float(request_timeout),
        )

    def launch(self) -> BackendLaunchInfo:
        if self.settings.command is not None:
            env = os.environ.copy()
            env.update(self.settings.env)
            self.process = subprocess.Popen(
                self.settings.command,
                cwd=self.settings.cwd,
                env=env,
                text=True,
            )
            self._launch_started = True

        deadline = time.monotonic() + self.settings.startup_timeout_seconds
        last_error: BackendLifecycleError | None = None

        while time.monotonic() < deadline:
            if self.process is not None:
                exit_code = self.process.poll()
                if exit_code is not None:
                    raise BackendLifecycleError(
                        phase="launch_process_exit",
                        message="backend process exited before it became healthy",
                        details={"exit_code": exit_code},
                    )
            try:
                self.healthcheck()
                version, runtime_metadata = self._fetch_runtime_metadata()
                runtime_metadata["launch"] = self._build_launch_metadata()
                return BackendLaunchInfo(
                    base_url=self.base_url,
                    scrape_endpoint=self.scrape_endpoint,
                    version=version,
                    runtime_metadata=runtime_metadata,
                )
            except BackendLifecycleError as exc:
                last_error = exc
                time.sleep(self.settings.healthcheck_interval_seconds)

        if last_error is not None and last_error.phase == "healthcheck_failed":
            raise last_error
        raise BackendLifecycleError(
            phase="launch_timeout",
            message="backend did not become healthy before startup timeout",
            details={
                "base_url": self.base_url,
                "startup_timeout_seconds": self.settings.startup_timeout_seconds,
            },
        )

    def _build_launch_metadata(self) -> dict[str, Any]:
        launch = self.payload["launch"]
        metadata: dict[str, Any] = {
            "command": self.settings.command,
            "cwd": self.settings.cwd,
            "configured_launch": {key: value for key, value in launch.items() if key != "env"},
        }
        if self.process is not None:
            metadata["pid"] = self.process.pid
        return metadata

    def healthcheck(self) -> None:
        try:
            status, payload = _http_json(
                method="GET",
                url=self.health_url,
                payload=None,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        except error.HTTPError as exc:
            raise BackendLifecycleError(
                phase="healthcheck_failed",
                message="health endpoint returned a non-200 response",
                details={"status": exc.code, "url": self.health_url},
            ) from exc
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BackendLifecycleError(
                phase="launch_timeout",
                message="health endpoint is not reachable yet",
                details={"url": self.health_url, "error": type(exc).__name__},
            ) from exc

        if status != 200:
            raise BackendLifecycleError(
                phase="healthcheck_failed",
                message="health endpoint did not return HTTP 200",
                details={"status": status, "url": self.health_url},
            )

        state = payload.get("status")
        if state not in (None, "ok", "healthy", "ready"):
            raise BackendLifecycleError(
                phase="healthcheck_failed",
                message="health endpoint reported an unhealthy state",
                details={"status": state, "url": self.health_url},
            )

    def _fetch_runtime_metadata(self) -> tuple[str | None, dict[str, Any]]:
        runtime_metadata: dict[str, Any] = {"base_url": self.base_url}
        try:
            status, payload = _http_json(
                method="GET",
                url=self.version_url,
                payload=None,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            runtime_metadata["version_endpoint_error"] = type(exc).__name__
            return None, runtime_metadata

        runtime_metadata["version_endpoint_status"] = status
        runtime_metadata["version_payload"] = payload
        version = payload.get("version")
        if isinstance(version, str) and version:
            return version, runtime_metadata
        implementation = payload.get("implementation")
        if isinstance(implementation, str) and implementation:
            return implementation, runtime_metadata
        return None, runtime_metadata

    def submit(self, request_payload: NormalizedRequest) -> BackendResponse:
        payload = {
            "model": self.config.model_id,
            "prompt": request_payload.prompt,
            "max_tokens": request_payload.max_new_tokens,
            "temperature": request_payload.decoding_params["temperature"],
            "top_p": request_payload.decoding_params["top_p"],
        }
        try:
            status, response_payload = _http_json(
                method="POST",
                url=self.completions_url,
                payload=payload,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BackendLifecycleError(
                phase="request_failed",
                message="completion request failed",
                details={"request_id": request_payload.request_id, "error": type(exc).__name__},
            ) from exc

        choices = response_payload.get("choices")
        if status != 200 or not isinstance(choices, list) or not choices:
            raise BackendLifecycleError(
                phase="request_failed",
                message="completion endpoint returned an invalid response",
                details={"request_id": request_payload.request_id, "status": status},
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise BackendLifecycleError(
                phase="request_failed",
                message="completion endpoint choice payload must be an object",
                details={"request_id": request_payload.request_id},
            )

        usage = response_payload.get("usage")
        output_tokens = None
        if isinstance(usage, dict):
            completion_tokens = usage.get("completion_tokens")
            if isinstance(completion_tokens, int):
                output_tokens = completion_tokens

        output_text = first_choice.get("text")
        if not isinstance(output_text, str):
            raise BackendLifecycleError(
                phase="request_failed",
                message="completion endpoint choice.text must be a string",
                details={"request_id": request_payload.request_id},
            )

        finish_reason = first_choice.get("finish_reason")
        return BackendResponse(
            request_id=request_payload.request_id,
            status="ok",
            output_text=output_text,
            output_tokens=output_tokens,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
            raw_response=response_payload,
        )

    def collect_metrics(self) -> list[dict[str, Any]]:
        try:
            status, body = _http_text(
                url=self.scrape_endpoint,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise BackendLifecycleError(
                phase="metrics_failed",
                message="metrics scrape failed",
                details={"scrape_endpoint": self.scrape_endpoint, "error": type(exc).__name__},
            ) from exc
        if status != 200:
            raise BackendLifecycleError(
                phase="metrics_failed",
                message="metrics scrape returned a non-200 response",
                details={"scrape_endpoint": self.scrape_endpoint, "status": status},
            )
        return parse_prometheus_metrics(body, scrape_endpoint=self.scrape_endpoint)

    def stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None


def build_vllm_adapter(config: BackendConfig) -> VLLMAdapter:
    return VLLMAdapter(config)

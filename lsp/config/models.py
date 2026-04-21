from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, ClassVar


class ValidationError(ValueError):
    """Raised when repo configs fail schema validation."""


def _require_keys(
    payload: dict[str, Any],
    *,
    required: set[str],
    allowed: set[str],
    context: str,
) -> None:
    missing = sorted(required - payload.keys())
    unknown = sorted(payload.keys() - allowed)
    if missing:
        raise ValidationError(f"{context} missing required keys: {', '.join(missing)}")
    if unknown:
        raise ValidationError(f"{context} contains unknown keys: {', '.join(unknown)}")


def _ensure_type(value: Any, expected: type[Any] | tuple[type[Any], ...], context: str) -> None:
    if not isinstance(value, expected):
        raise ValidationError(f"{context} has invalid type {type(value).__name__}")


def _ensure_positive_int(value: Any, context: str) -> int:
    _ensure_type(value, int, context)
    if value <= 0:
        raise ValidationError(f"{context} must be > 0")
    return int(value)


def _ensure_non_negative_number(value: Any, context: str) -> float:
    _ensure_type(value, (int, float), context)
    number = float(value)
    if number < 0:
        raise ValidationError(f"{context} must be >= 0")
    return number


@dataclass(frozen=True)
class ConfigDocument:
    kind: ClassVar[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendConfig(ConfigDocument):
    kind: ClassVar[str] = "backend"
    backend: str
    mode: str
    model_id: str
    resolved: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BackendConfig":
        backend = payload.get("backend")
        if backend == "vllm":
            _require_keys(
                payload,
                required={
                    "backend",
                    "mode",
                    "model_id",
                    "host",
                    "port",
                    "launch",
                    "metrics",
                    "artifacts",
                },
                allowed={
                    "backend",
                    "mode",
                    "model_id",
                    "host",
                    "port",
                    "launch",
                    "metrics",
                    "artifacts",
                },
                context="vllm backend config",
            )
            _ensure_type(payload["host"], str, "vllm backend config.host")
            _ensure_positive_int(payload["port"], "vllm backend config.port")
            _ensure_type(payload["launch"], dict, "vllm backend config.launch")
            _ensure_type(payload["metrics"], dict, "vllm backend config.metrics")
            _ensure_type(payload["artifacts"], dict, "vllm backend config.artifacts")
        elif backend == "sglang":
            _require_keys(
                payload,
                required={
                    "backend",
                    "mode",
                    "model_id",
                    "router",
                    "workers",
                    "transfer",
                    "artifacts",
                },
                allowed={
                    "backend",
                    "mode",
                    "model_id",
                    "router",
                    "workers",
                    "transfer",
                    "artifacts",
                },
                context="sglang backend config",
            )
            _ensure_type(payload["router"], dict, "sglang backend config.router")
            _ensure_type(payload["workers"], dict, "sglang backend config.workers")
            _ensure_type(payload["transfer"], dict, "sglang backend config.transfer")
            _ensure_type(payload["artifacts"], dict, "sglang backend config.artifacts")
            workers = payload["workers"]
            for role in ("prefill", "decode"):
                if role not in workers:
                    raise ValidationError(f"sglang backend config.workers missing role: {role}")
        else:
            raise ValidationError("backend config.backend must be one of: vllm, sglang")

        mode = payload.get("mode")
        if not isinstance(mode, str) or not mode:
            raise ValidationError("backend config.mode must be a non-empty string")
        model_id = payload.get("model_id")
        if not isinstance(model_id, str) or not model_id:
            raise ValidationError("backend config.model_id must be a non-empty string")

        return cls(backend=backend, mode=mode, model_id=model_id, resolved=payload)


@dataclass(frozen=True)
class WorkloadConfig(ConfigDocument):
    kind: ClassVar[str] = "workload"
    workload_id: str
    seed: int
    workload_kind: str
    resolved: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkloadConfig":
        kind = payload.get("kind")
        if kind == "synthetic":
            _require_keys(
                payload,
                required={
                    "workload_id",
                    "seed",
                    "kind",
                    "request_count",
                    "arrival",
                    "prompt_tokens",
                    "output_tokens",
                    "prefix_reuse",
                },
                allowed={
                    "workload_id",
                    "seed",
                    "kind",
                    "request_count",
                    "arrival",
                    "prompt_tokens",
                    "output_tokens",
                    "prefix_reuse",
                },
                context="synthetic workload config",
            )
            _ensure_positive_int(
                payload["request_count"],
                "synthetic workload config.request_count",
            )
        elif kind == "workload_shaped":
            _require_keys(
                payload,
                required={
                    "workload_id",
                    "seed",
                    "kind",
                    "mixture",
                    "arrival",
                    "prefix_reuse",
                    "notes",
                },
                allowed={
                    "workload_id",
                    "seed",
                    "kind",
                    "mixture",
                    "arrival",
                    "prefix_reuse",
                    "notes",
                },
                context="workload_shaped workload config",
            )
            mixture = payload["mixture"]
            _ensure_type(mixture, list, "workload_shaped workload config.mixture")
            if not mixture:
                raise ValidationError("workload_shaped workload config.mixture must be non-empty")
        else:
            raise ValidationError("workload config.kind must be one of: synthetic, workload_shaped")

        workload_id = payload.get("workload_id")
        if not isinstance(workload_id, str) or not workload_id:
            raise ValidationError("workload config.workload_id must be a non-empty string")
        seed = _ensure_positive_int(payload.get("seed"), "workload config.seed")
        return cls(workload_id=workload_id, seed=seed, workload_kind=kind, resolved=payload)


@dataclass(frozen=True)
class PolicyConfig(ConfigDocument):
    kind: ClassVar[str] = "policy"
    policy_id: str
    resolved: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PolicyConfig":
        _require_keys(
            payload,
            required={"policy_id", "kind", "allowed_signals", "decision_order", "fallback"},
            allowed={"policy_id", "kind", "allowed_signals", "decision_order", "fallback"},
            context="policy config",
        )
        _ensure_type(payload["allowed_signals"], list, "policy config.allowed_signals")
        _ensure_type(payload["decision_order"], list, "policy config.decision_order")
        _ensure_type(payload["fallback"], dict, "policy config.fallback")
        policy_id = payload["policy_id"]
        _ensure_type(policy_id, str, "policy config.policy_id")
        return cls(policy_id=policy_id, resolved=payload)


@dataclass(frozen=True)
class ThresholdConfig(ConfigDocument):
    kind: ClassVar[str] = "thresholds"
    threshold_set_id: str
    resolved: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ThresholdConfig":
        _require_keys(
            payload,
            required={"threshold_set_id", "comparison_mode", "metrics"},
            allowed={"threshold_set_id", "comparison_mode", "metrics"},
            context="threshold config",
        )
        metrics = payload["metrics"]
        _ensure_type(metrics, dict, "threshold config.metrics")
        for metric_name, values in metrics.items():
            _ensure_type(values, dict, f"threshold config.metrics.{metric_name}")
            for key, raw_value in values.items():
                _ensure_non_negative_number(
                    raw_value,
                    f"threshold config.metrics.{metric_name}.{key}",
                )
        threshold_set_id = payload["threshold_set_id"]
        _ensure_type(threshold_set_id, str, "threshold config.threshold_set_id")
        return cls(threshold_set_id=threshold_set_id, resolved=payload)


@dataclass(frozen=True)
class ExperimentConfig(ConfigDocument):
    kind: ClassVar[str] = "experiment"
    experiment_id: str
    resolved: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExperimentConfig":
        _require_keys(
            payload,
            required={
                "experiment_id",
                "baseline",
                "objective",
                "search_space",
                "budget",
                "approval_policy",
                "reporting",
            },
            allowed={
                "experiment_id",
                "baseline",
                "objective",
                "search_space",
                "budget",
                "approval_policy",
                "reporting",
            },
            context="experiment config",
        )
        _ensure_type(payload["baseline"], dict, "experiment config.baseline")
        _ensure_type(payload["objective"], dict, "experiment config.objective")
        _ensure_type(payload["search_space"], dict, "experiment config.search_space")
        budget = payload["budget"]
        _ensure_type(budget, dict, "experiment config.budget")
        for key in ("max_runs", "max_wall_clock_minutes", "max_consecutive_failures"):
            _ensure_positive_int(budget.get(key), f"experiment config.budget.{key}")
        experiment_id = payload["experiment_id"]
        _ensure_type(experiment_id, str, "experiment config.experiment_id")
        return cls(experiment_id=experiment_id, resolved=payload)

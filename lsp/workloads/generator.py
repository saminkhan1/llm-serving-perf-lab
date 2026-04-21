from __future__ import annotations

import math
import random
from hashlib import sha256
from typing import Any

from lsp.config.models import ValidationError, WorkloadConfig

from .models import NormalizedRequest

_P95_Z_SCORE = 1.6448536269514722


def _sample_lognormal(rng: random.Random, spec: dict[str, Any], context: str) -> int:
    if spec.get("distribution") != "lognormal":
        raise ValidationError(f"{context}.distribution must be lognormal")
    median = spec.get("median")
    p95 = spec.get("p95")
    if not isinstance(median, (int, float)) or not isinstance(p95, (int, float)):
        raise ValidationError(f"{context} must define numeric median and p95")
    if median <= 0 or p95 < median:
        raise ValidationError(f"{context} must satisfy 0 < median <= p95")
    mu = math.log(float(median))
    sigma = math.log(float(p95) / float(median)) / _P95_Z_SCORE if p95 > median else 0.0
    return max(1, int(round(rng.lognormvariate(mu, sigma))))


def _sample_mixture(rng: random.Random, mixture: list[dict[str, Any]]) -> dict[str, Any]:
    total_weight = 0.0
    normalized: list[tuple[float, dict[str, Any]]] = []
    for component in mixture:
        weight = component.get("weight")
        if not isinstance(weight, (int, float)) or weight <= 0:
            raise ValidationError("workload_shaped mixture weights must be > 0")
        total_weight += float(weight)
        normalized.append((total_weight, component))
    threshold = rng.random() * total_weight
    for cutoff, component in normalized:
        if threshold <= cutoff:
            return component
    return normalized[-1][1]


def _next_arrival_ms(
    rng: random.Random,
    arrival: dict[str, Any],
    index: int,
    current_ms: int,
) -> int:
    distribution = arrival.get("distribution") or arrival.get("pattern")
    if distribution == "poisson":
        rate = arrival.get("rate_per_second") or arrival.get("base_rate_per_second")
        if not isinstance(rate, (int, float)) or rate <= 0:
            raise ValidationError("arrival poisson rate must be > 0")
        delta_ms = int(round(rng.expovariate(float(rate)) * 1000))
        return current_ms + delta_ms
    if distribution == "bursty_poisson":
        base_rate = arrival.get("base_rate_per_second")
        burst_multiplier = arrival.get("burst_multiplier")
        burst_duration = arrival.get("burst_duration_seconds")
        burst_every = arrival.get("burst_every_seconds")
        positive_values = (base_rate, burst_multiplier, burst_duration, burst_every)
        if not all(isinstance(value, (int, float)) and value > 0 for value in positive_values):
            raise ValidationError("bursty arrival fields must be positive numbers")
        assert isinstance(base_rate, (int, float))
        assert isinstance(burst_multiplier, (int, float))
        assert isinstance(burst_duration, (int, float))
        assert isinstance(burst_every, (int, float))
        typed_base_rate = float(base_rate)
        typed_burst_multiplier = float(burst_multiplier)
        typed_burst_duration = int(burst_duration)
        typed_burst_every = int(burst_every)
        in_burst = (index % typed_burst_every) < typed_burst_duration
        active_rate = typed_base_rate * (typed_burst_multiplier if in_burst else 1.0)
        delta_ms = int(round(rng.expovariate(active_rate) * 1000))
        return current_ms + delta_ms
    raise ValidationError("arrival distribution must be one of: poisson, bursty_poisson")


def _build_prompt(
    *,
    workload_id: str,
    request_id: str,
    prompt_token_count: int,
    prefix_key: str,
    profile_name: str,
) -> str:
    prompt_hash = sha256(
        f"{workload_id}:{request_id}:{prompt_token_count}:{prefix_key}:{profile_name}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return (
        "SYNTHETIC_PROMPT "
        f"workload={workload_id} profile={profile_name} tokens={prompt_token_count} "
        f"prefix={prefix_key} body={prompt_hash}"
    )


def _prefix_key(
    rng: random.Random,
    prefix_reuse: dict[str, Any],
    index: int,
    workload_id: str,
) -> str:
    enabled = prefix_reuse.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValidationError("prefix_reuse.enabled must be a boolean")
    if not enabled:
        return f"{workload_id}-unique-{index:04d}"
    reuse_probability = prefix_reuse.get("reuse_probability", 0.0)
    if not isinstance(reuse_probability, (int, float)) or not 0 <= float(reuse_probability) <= 1:
        raise ValidationError("prefix_reuse.reuse_probability must be between 0 and 1")
    pool_size = prefix_reuse.get("prefix_pool_size", 8)
    if not isinstance(pool_size, int) or pool_size <= 0:
        raise ValidationError("prefix_reuse.prefix_pool_size must be a positive integer")
    if rng.random() <= float(reuse_probability):
        return f"{workload_id}-shared-{rng.randrange(pool_size):02d}"
    return f"{workload_id}-unique-{index:04d}"


def generate_requests(config: WorkloadConfig) -> list[NormalizedRequest]:
    rng = random.Random(config.seed)
    arrival_ms = 0
    requests: list[NormalizedRequest] = []
    payload = config.resolved
    request_count = int(payload["request_count"])
    prefix_reuse = payload["prefix_reuse"]

    for index in range(request_count):
        arrival_ms = _next_arrival_ms(rng, payload["arrival"], index, arrival_ms)
        request_id = f"{config.workload_id}-{config.seed}-{index:05d}"
        if config.workload_kind == "synthetic":
            profile_name = config.workload_id
            prompt_tokens = _sample_lognormal(
                rng,
                payload["prompt_tokens"],
                "synthetic workload config.prompt_tokens",
            )
            output_tokens = _sample_lognormal(
                rng,
                payload["output_tokens"],
                "synthetic workload config.output_tokens",
            )
        else:
            component = _sample_mixture(rng, payload["mixture"])
            profile_name = str(component.get("name", "mixture_component"))
            prompt_tokens = _sample_lognormal(
                rng,
                {
                    "distribution": "lognormal",
                    "median": component.get("prompt_tokens_median"),
                    "p95": component.get("prompt_tokens_p95"),
                },
                f"workload_shaped mixture {profile_name} prompt_tokens",
            )
            output_tokens = _sample_lognormal(
                rng,
                {
                    "distribution": "lognormal",
                    "median": component.get("output_tokens_median"),
                    "p95": component.get("output_tokens_p95"),
                },
                f"workload_shaped mixture {profile_name} output_tokens",
            )
        prefix_key = _prefix_key(rng, prefix_reuse, index, config.workload_id)
        requests.append(
            NormalizedRequest(
                request_id=request_id,
                prompt=_build_prompt(
                    workload_id=config.workload_id,
                    request_id=request_id,
                    prompt_token_count=prompt_tokens,
                    prefix_key=prefix_key,
                    profile_name=profile_name,
                ),
                prompt_token_count=prompt_tokens,
                arrival_timestamp_ms=arrival_ms,
                max_new_tokens=output_tokens,
                decoding_params={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "synthetic": True,
                },
                tags={
                    "workload_id": config.workload_id,
                    "profile_name": profile_name,
                    "prefix_key": prefix_key,
                    "workload_kind": config.workload_kind,
                },
            )
        )

    return requests

from __future__ import annotations

import re

_METRIC_LINE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>\S+)(?:\s+\S+)?$"
)
_LABEL_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:[^"\\]|\\.)*)"')

_EXPECTED_METRICS: dict[str, list[str]] = {
    "ttft_seconds": ["vllm:time_to_first_token_seconds"],
    "time_per_output_token_seconds": ["vllm:time_per_output_token_seconds"],
    "e2e_request_latency_seconds": ["vllm:e2e_request_latency_seconds"],
    "requests_running": ["vllm:requests_running"],
    "queue_depth": ["vllm:requests_waiting"],
    "gpu_cache_usage_perc": ["vllm:gpu_cache_usage_perc"],
    "gpu_memory_usage_bytes": ["vllm:gpu_memory_usage_bytes"],
    "prompt_throughput_tokens_per_second": ["vllm:avg_prompt_throughput_toks_per_s"],
    "generation_throughput_tokens_per_second": ["vllm:avg_generation_throughput_toks_per_s"],
    "request_success_total": ["vllm:request_success_total"],
    "request_error_total": ["vllm:request_error_total"],
    "request_timeout_total": ["vllm:request_timeout_total"],
}


def _parse_labels(raw_labels: str | None) -> dict[str, str]:
    if not raw_labels:
        return {}
    labels: dict[str, str] = {}
    for match in _LABEL_RE.finditer(raw_labels):
        labels[match.group(1)] = match.group(2).encode("utf-8").decode("unicode_escape")
    return labels


def parse_prometheus_metrics(body: str, *, scrape_endpoint: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_metric_names: set[str] = set()

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _METRIC_LINE_RE.match(stripped)
        if match is None:
            continue
        value_text = match.group("value")
        try:
            value = float(value_text)
        except ValueError:
            continue
        metric_name = match.group("name")
        seen_metric_names.add(metric_name)
        rows.append(
            {
                "metric_kind": "official",
                "metric_name": metric_name,
                "semantic_name": metric_name,
                "labels": _parse_labels(match.group("labels")),
                "value": value,
                "missing": False,
                "scrape_endpoint": scrape_endpoint,
                "metric_source": "official_prometheus",
            }
        )

    for semantic_name, candidates in _EXPECTED_METRICS.items():
        if any(candidate in seen_metric_names for candidate in candidates):
            continue
        rows.append(
            {
                "metric_kind": "official",
                "metric_name": None,
                "semantic_name": semantic_name,
                "labels": {},
                "value": None,
                "missing": True,
                "missing_candidates": candidates,
                "missing_reason": "not_exposed_by_scrape_endpoint",
                "scrape_endpoint": scrape_endpoint,
                "metric_source": "official_prometheus",
            }
        )

    return rows

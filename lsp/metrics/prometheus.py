from __future__ import annotations

import re

_METRIC_LINE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>\S+)(?:\s+\S+)?$"
)
_LABEL_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:[^"\\]|\\.)*)"')

_EXPECTED_METRICS: dict[str, list[str]] = {
    "ttft_seconds": ["vllm:time_to_first_token_seconds"],
    "time_per_output_token_seconds": [
        "vllm:request_time_per_output_token_seconds",
        "vllm:time_per_output_token_seconds",
    ],
    "e2e_request_latency_seconds": ["vllm:e2e_request_latency_seconds"],
    "requests_running": ["vllm:num_requests_running", "vllm:requests_running"],
    "queue_depth": ["vllm:num_requests_waiting", "vllm:requests_waiting"],
    "gpu_cache_usage_perc": ["vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"],
    # Current vLLM production metrics document this counter without the OpenMetrics
    # text-format suffix; Prometheus scrapes expose it as *_total.
    "request_success_total": ["vllm:request_success", "vllm:request_success_total"],
}


def _has_metric_family(metric_names: set[str], candidate: str) -> bool:
    if candidate in metric_names:
        return True
    prefix = f"{candidate}_"
    return any(metric_name.startswith(prefix) for metric_name in metric_names)


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
        if any(_has_metric_family(seen_metric_names, candidate) for candidate in candidates):
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

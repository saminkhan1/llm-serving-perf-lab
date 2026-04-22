from __future__ import annotations

import unittest

from lsp.metrics import parse_prometheus_metrics


class PrometheusMetricsTests(unittest.TestCase):
    def test_missing_metrics_follow_current_core_contract(self) -> None:
        body = "\n".join(
            [
                "# TYPE vllm:time_to_first_token_seconds histogram",
                'vllm:time_to_first_token_seconds_bucket{le="0.5",model_name="demo"} 1',
                'vllm:time_to_first_token_seconds_sum{model_name="demo"} 0.123',
                'vllm:time_to_first_token_seconds_count{model_name="demo"} 1',
                "# TYPE vllm:num_requests_waiting gauge",
                "vllm:num_requests_waiting 2",
                "",
            ]
        )

        rows = parse_prometheus_metrics(body, scrape_endpoint="http://127.0.0.1:8000/metrics")

        present_rows = [
            row for row in rows if row["metric_name"] == "vllm:time_to_first_token_seconds_count"
        ]
        self.assertEqual(len(present_rows), 1)
        self.assertFalse(bool(present_rows[0]["missing"]))
        self.assertEqual(present_rows[0]["labels"], {"model_name": "demo"})

        missing_rows = [row for row in rows if row["missing"] is True]
        semantic_names = {str(row["semantic_name"]) for row in missing_rows}
        self.assertIn("time_per_output_token_seconds", semantic_names)
        self.assertIn("e2e_request_latency_seconds", semantic_names)
        self.assertIn("requests_running", semantic_names)
        self.assertIn("gpu_cache_usage_perc", semantic_names)
        self.assertIn("request_success_total", semantic_names)
        self.assertNotIn("queue_depth", semantic_names)
        self.assertNotIn("gpu_memory_usage_bytes", semantic_names)
        self.assertNotIn("prompt_throughput_tokens_per_second", semantic_names)
        self.assertNotIn("generation_throughput_tokens_per_second", semantic_names)
        self.assertNotIn("request_error_total", semantic_names)
        self.assertNotIn("request_timeout_total", semantic_names)

    def test_histogram_families_and_v019_aliases_count_as_present(self) -> None:
        body = "\n".join(
            [
                "# TYPE vllm:time_to_first_token_seconds histogram",
                'vllm:time_to_first_token_seconds_bucket{le="0.5"} 1',
                "vllm:time_to_first_token_seconds_sum 0.31",
                "vllm:time_to_first_token_seconds_count 1",
                "# TYPE vllm:e2e_request_latency_seconds histogram",
                'vllm:e2e_request_latency_seconds_bucket{le="1.0"} 1',
                "vllm:e2e_request_latency_seconds_sum 0.72",
                "vllm:e2e_request_latency_seconds_count 1",
                "# TYPE vllm:request_time_per_output_token_seconds histogram",
                'vllm:request_time_per_output_token_seconds_bucket{le="0.1"} 1',
                "vllm:request_time_per_output_token_seconds_sum 0.03",
                "vllm:request_time_per_output_token_seconds_count 1",
                "# TYPE vllm:num_requests_running gauge",
                "vllm:num_requests_running 1",
                "# TYPE vllm:num_requests_waiting gauge",
                "vllm:num_requests_waiting 0",
                "# TYPE vllm:kv_cache_usage_perc gauge",
                "vllm:kv_cache_usage_perc 0.5",
                "# TYPE vllm:request_success_total counter",
                "vllm:request_success_total 1",
            ]
        )

        rows = parse_prometheus_metrics(body, scrape_endpoint="http://127.0.0.1:8000/metrics")

        missing_rows = [row for row in rows if row["missing"] is True]
        semantic_names = {str(row["semantic_name"]) for row in missing_rows}
        self.assertNotIn("ttft_seconds", semantic_names)
        self.assertNotIn("e2e_request_latency_seconds", semantic_names)
        self.assertNotIn("time_per_output_token_seconds", semantic_names)
        self.assertNotIn("requests_running", semantic_names)
        self.assertNotIn("queue_depth", semantic_names)
        self.assertNotIn("gpu_cache_usage_perc", semantic_names)
        self.assertNotIn("request_success_total", semantic_names)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from lsp.metrics import parse_prometheus_metrics


class PrometheusMetricsTests(unittest.TestCase):
    def test_missing_metrics_are_preserved_explicitly(self) -> None:
        body = "\n".join(
            [
                "# TYPE vllm:time_to_first_token_seconds gauge",
                'vllm:time_to_first_token_seconds{model_name="demo"} 0.123',
                "# TYPE vllm:requests_waiting gauge",
                "vllm:requests_waiting 2",
                "",
            ]
        )

        rows = parse_prometheus_metrics(body, scrape_endpoint="http://127.0.0.1:8000/metrics")

        present_rows = [
            row for row in rows if row["metric_name"] == "vllm:time_to_first_token_seconds"
        ]
        self.assertEqual(len(present_rows), 1)
        self.assertFalse(bool(present_rows[0]["missing"]))
        self.assertEqual(present_rows[0]["labels"], {"model_name": "demo"})

        missing_rows = [row for row in rows if row["missing"] is True]
        semantic_names = {str(row["semantic_name"]) for row in missing_rows}
        self.assertIn("gpu_memory_usage_bytes", semantic_names)
        self.assertIn("request_timeout_total", semantic_names)
        self.assertIn("request_error_total", semantic_names)


if __name__ == "__main__":
    unittest.main()

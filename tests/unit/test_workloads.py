from __future__ import annotations

import unittest
from pathlib import Path

from lsp.config.loader import load_config
from lsp.config.models import WorkloadConfig
from lsp.workloads import generate_requests

REPO_ROOT = Path(__file__).resolve().parents[2]


class WorkloadGenerationTests(unittest.TestCase):
    def test_same_seed_replays_same_request_stream(self) -> None:
        config = load_config(REPO_ROOT / "configs" / "workloads" / "mixed_short_long.yaml")
        self.assertIsInstance(config, WorkloadConfig)

        first = [request.to_dict() for request in generate_requests(config)]
        second = [request.to_dict() for request in generate_requests(config)]

        self.assertEqual(first, second)

    def test_different_seed_changes_request_stream(self) -> None:
        first = load_config(REPO_ROOT / "configs" / "workloads" / "chat_short.yaml")
        second = load_config(REPO_ROOT / "tests" / "fixtures" / "chat_short_alt_seed.yaml")
        self.assertIsInstance(first, WorkloadConfig)
        self.assertIsInstance(second, WorkloadConfig)

        first_requests = [request.to_dict() for request in generate_requests(first)]
        second_requests = [request.to_dict() for request in generate_requests(second)]

        self.assertNotEqual(first_requests, second_requests)

    def test_required_m1_workload_profiles_exist_and_generate(self) -> None:
        expected = {
            "chat_short",
            "context_long",
            "mixed_short_long",
            "bursty_chat",
            "prefix_reuse_heavy",
            "sharegpt_like",
        }

        seen: set[str] = set()
        for path in sorted((REPO_ROOT / "configs" / "workloads").glob("*.yaml")):
            config = load_config(path)
            if not isinstance(config, WorkloadConfig):
                continue
            if config.workload_id not in expected:
                continue
            seen.add(config.workload_id)
            requests = generate_requests(config)
            self.assertGreater(len(requests), 0)
            self.assertEqual(requests[0].tags["workload_id"], config.workload_id)

        self.assertEqual(seen, expected)


if __name__ == "__main__":
    unittest.main()

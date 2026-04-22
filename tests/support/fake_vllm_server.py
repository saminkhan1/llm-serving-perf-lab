from __future__ import annotations

import argparse
import json
import signal
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class ServerState:
    mode: str
    model_id: str = "fake/local-test-model"
    prompt_tokens_total: int = 0
    generation_tokens_total: int = 0
    request_success_total: int = 0


def _metrics_payload(state: ServerState) -> str:
    return "\n".join(
        [
            "# TYPE vllm:time_to_first_token_seconds histogram",
            'vllm:time_to_first_token_seconds_bucket{le="0.05"} 1',
            "vllm:time_to_first_token_seconds_sum 0.012",
            "vllm:time_to_first_token_seconds_count 1",
            "# TYPE vllm:request_time_per_output_token_seconds histogram",
            'vllm:request_time_per_output_token_seconds_bucket{le="0.01"} 1',
            "vllm:request_time_per_output_token_seconds_sum 0.004",
            "vllm:request_time_per_output_token_seconds_count 1",
            "# TYPE vllm:e2e_request_latency_seconds histogram",
            'vllm:e2e_request_latency_seconds_bucket{le="0.05"} 1',
            "vllm:e2e_request_latency_seconds_sum 0.028",
            "vllm:e2e_request_latency_seconds_count 1",
            "# TYPE vllm:num_requests_running gauge",
            "vllm:num_requests_running 0",
            "# TYPE vllm:num_requests_waiting gauge",
            "vllm:num_requests_waiting 0",
            "# TYPE vllm:kv_cache_usage_perc gauge",
            "vllm:kv_cache_usage_perc 0.125",
            "# TYPE vllm:request_success_total counter",
            f"vllm:request_success_total {float(state.request_success_total):.1f}",
            "# TYPE vllm:prompt_tokens_total counter",
            f"vllm:prompt_tokens_total {float(state.prompt_tokens_total):.1f}",
            "# TYPE vllm:generation_tokens_total counter",
            f"vllm:generation_tokens_total {float(state.generation_tokens_total):.1f}",
            "",
        ]
    )


def build_handler(state: ServerState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _write_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                if state.mode == "healthy":
                    self._write_json(200, {"status": "ok"})
                else:
                    self._write_json(503, {"status": "not_ready"})
                return
            if self.path == "/version":
                self._write_json(
                    200,
                    {
                        "implementation": "fake-vllm",
                        "version": "fake-vllm/0.2.0",
                    },
                )
                return
            if self.path == "/v1/models":
                self._write_json(
                    200,
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": state.model_id,
                                "object": "model",
                                "created": 0,
                                "owned_by": "llm-serving-perf-lab",
                            }
                        ],
                    },
                )
                return
            if self.path == "/metrics":
                body = _metrics_payload(state).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404, "not found")

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/completions":
                self.send_error(404, "not found")
                return
            raw_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(raw_length).decode("utf-8"))
            prompt = str(payload.get("prompt", ""))
            max_tokens = int(payload.get("max_tokens", 1))
            completion_tokens = max(1, min(max_tokens, 8))
            state.request_success_total += 1
            state.prompt_tokens_total += max(1, len(prompt.split()))
            state.generation_tokens_total += completion_tokens
            response = {
                "id": f"cmpl-{state.request_success_total:04d}",
                "object": "text_completion",
                "model": state.model_id,
                "choices": [
                    {
                        "text": f"FAKE_COMPLETION tokens={completion_tokens}",
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": max(1, len(prompt.split())),
                    "completion_tokens": completion_tokens,
                    "total_tokens": max(1, len(prompt.split())) + completion_tokens,
                },
            }
            self._write_json(200, response)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--mode", choices=["healthy", "bad-health"], default="healthy")
    args = parser.parse_args()

    state = ServerState(mode=args.mode)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), build_handler(state))

    def _stop_server(*_: object) -> None:
        server.shutdown()

    signal.signal(signal.SIGTERM, _stop_server)
    signal.signal(signal.SIGINT, _stop_server)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

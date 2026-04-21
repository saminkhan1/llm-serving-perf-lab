from __future__ import annotations

import argparse
import json
import signal
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class ServerState:
    mode: str
    prompt_tokens_total: int = 0
    generation_tokens_total: int = 0
    request_success_total: int = 0


def _metrics_payload(state: ServerState) -> str:
    request_errors = 0.0
    request_timeouts = 0.0
    return "\n".join(
        [
            "# TYPE vllm:time_to_first_token_seconds gauge",
            "vllm:time_to_first_token_seconds 0.012",
            "# TYPE vllm:time_per_output_token_seconds gauge",
            "vllm:time_per_output_token_seconds 0.004",
            "# TYPE vllm:e2e_request_latency_seconds gauge",
            "vllm:e2e_request_latency_seconds 0.028",
            "# TYPE vllm:requests_running gauge",
            "vllm:requests_running 0",
            "# TYPE vllm:requests_waiting gauge",
            "vllm:requests_waiting 0",
            "# TYPE vllm:gpu_cache_usage_perc gauge",
            "vllm:gpu_cache_usage_perc 12.5",
            "# TYPE vllm:gpu_memory_usage_bytes gauge",
            "vllm:gpu_memory_usage_bytes 1048576",
            "# TYPE vllm:avg_prompt_throughput_toks_per_s gauge",
            "vllm:avg_prompt_throughput_toks_per_s 512.0",
            "# TYPE vllm:avg_generation_throughput_toks_per_s gauge",
            "vllm:avg_generation_throughput_toks_per_s 256.0",
            "# TYPE vllm:request_success_total counter",
            f"vllm:request_success_total {float(state.request_success_total):.1f}",
            "# TYPE vllm:prompt_tokens_total counter",
            f"vllm:prompt_tokens_total {float(state.prompt_tokens_total):.1f}",
            "# TYPE vllm:generation_tokens_total counter",
            f"vllm:generation_tokens_total {float(state.generation_tokens_total):.1f}",
            "# TYPE vllm:request_error_total counter",
            f"vllm:request_error_total {request_errors:.1f}",
            "# TYPE vllm:request_timeout_total counter",
            f"vllm:request_timeout_total {request_timeouts:.1f}",
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

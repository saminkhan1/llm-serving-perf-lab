# M2 Real-Mode Benchmark Report

This report exercises the M2 controller path against a structured HTTP backend.
Interpret measured results only in the context of the tested backend, model, hardware, and workload.

- run_id: `m2-qwen-l40s-modal-chat-short-20260421-r3`
- backend: `vllm`
- hardware: `L40S x1 via modal`
- workload: `chat_short`
- request_rows: `500`
- response_rows: `500`
- metric_rows: `925`
- median_client_latency_seconds: `0.664248`
- p50_client_latency_seconds: `0.665260`
- p95_client_latency_seconds: `1.140493`
- p99_client_latency_seconds: `1.412930`
- official_metrics_missing: `generation_throughput_tokens_per_second, gpu_memory_usage_bytes, prompt_throughput_tokens_per_second, request_error_total, request_timeout_total`
- hardware_note: Deployed from scripts/modal_vllm_m2.py for the first real M2 baseline.
- hardware_note: Bound to one Modal-hosted L40S replica serving Qwen/Qwen2.5-1.5B-Instruct.
- hardware_note: Benchmark validity assumes the Modal app stays pinned to a single replica during the run.
- version_payload: `{'version': '0.19.0'}`

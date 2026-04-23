# M2 Real-Mode Benchmark Report

This report exercises the M2 controller path against a structured HTTP backend.
Interpret measured results only in the context of the tested backend, model, hardware, and workload.

- run_id: `m2-qwen-l40s-modal-chat-short-20260423-r2`
- backend: `vllm`
- hardware: `L40S x1 via modal`
- workload: `chat_short`
- request_rows: `500`
- response_rows: `500`
- metric_rows: `920`
- median_client_latency_seconds: `0.779643`
- p50_client_latency_seconds: `0.779981`
- p95_client_latency_seconds: `1.316456`
- p99_client_latency_seconds: `1.650834`
- official_metrics_missing: `none`
- hardware_note: Deployed from scripts/modal_vllm_m2.py.
- hardware_note: Benchmark intent is a single-container single-GPU M2 baseline.
- version_payload: `{'version': '0.19.0'}`

# M3 Reporting Checkpoint

This report packages the first stored real benchmark into a reviewer-friendly artifact that can be audited from repo state plus saved outputs.

## Question

Can the repo produce one real, reproducible, cross-checked vLLM baseline on a single-GPU Modal deployment?

## Setup

- Backend: `vLLM` `0.19.0`
- Hardware: `L40S x1 via modal`
- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Workload: `chat_short`
- Run ID: `m2-qwen-l40s-modal-chat-short-20260423-r2`
- Requests: `500`

## Measured Result

- Controller path completed `500/500` requests.
- Client latency p50 / p95 / p99: `0.780 / 1.316 / 1.651 s`.
- Official metric rows captured: `420` with `0` required metrics missing.
- Total metric rows written: `920`.

## External Cross-Check

- Saved GuideLLM run completed `500/500` requests with `0` errored and `0` incomplete entries.
- Median / p95 TTFT: `187.2 / 266.3 ms`.
- Median / p95 request latency: `0.799 / 0.999 s`.
- Mean throughput: `1.21 req/s`.

## Interpretation

This is enough to claim that the repo can stand up one real vLLM target, drive a bounded workload end to end, collect official `/metrics`, and preserve an external cross-check next to the artifact.
It is not enough to claim a serving optimization, a PD advantage, routing effectiveness, regression protection, profiler depth, or production readiness.

## Reproduce

Primary benchmark:
```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260423-r2
```

GuideLLM cross-check:
```bash
uv run lsp cross-check-guidellm --backend-config configs/backends/vllm_modal_m2_qwen_l40s.yaml --workload-config configs/workloads/chat_short.yaml --output-dir artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm --execute
```

## Evidence Files

- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/run.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/scorecard.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/metrics.parquet`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/report.md`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/benchmark.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/repo_cross_check_execution.json`

## Caveats

- Bound to L40S x1 via modal, Qwen/Qwen2.5-1.5B-Instruct, and chat_short. It does not generalize beyond that setup.
- The stored artifact records `git_dirty: true`.
- The GuideLLM cross-check uses a synthetic token summary rather than an exact controller trace replay.
- Modal endpoints can cold-start; treat a failed first probe as warmup only if a subsequent probe passes before the benchmark run.

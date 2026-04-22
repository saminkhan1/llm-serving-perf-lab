# Artifact Index

Use this file to point reviewers at the smallest number of artifacts needed to audit the repo's current proof state.

## Current hero artifacts

| Artifact ID | Milestone | Status | Question Answered | Hardware | Model | Workload | Repro Command | Primary Report | Raw Data | Caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `m2-qwen-l40s-modal-chat-short-20260421-r3` | M2 | hero | Can the repo produce one real vLLM baseline with official metrics capture and one completed GuideLLM cross-check on a single-GPU Modal deployment? | `Modal L40S x1` | `Qwen/Qwen2.5-1.5B-Instruct` | `chat_short` | `make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260421-r3` | `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/report.md` | `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/metrics.parquet`, `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/guidellm/benchmark.json` | Bound to tested hardware / model / workload. The `official_metrics_missing` field in this report predates the 2026-04-21 metric-contract cleanup. |

### `m2-qwen-l40s-modal-chat-short-20260421-r3`

Question:
- Can the repo produce one real, reproducible, cross-checked M2 baseline on a single-GPU Modal deployment?

Finding:
- On `Modal L40S x1` with `Qwen/Qwen2.5-1.5B-Instruct` and `chat_short`, the baseline completed `500/500` requests with median client latency `0.664248s`, p95 `1.140493s`, and a GuideLLM cross-check that also closed `500/500` successfully.

Reproduction:
```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260421-r3
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/guidellm \
  --execute
```

Files:
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/run.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/report.md`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/scorecard.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/metrics.parquet`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/guidellm/repo_cross_check_execution.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/guidellm/benchmark.json`

Caveats:
- Hardware-specific: only `Modal L40S x1` was tested.
- Workload-specific: only `chat_short` was used for this artifact.
- Model-specific: only `Qwen/Qwen2.5-1.5B-Instruct` was served.
- Historical note: the report's `official_metrics_missing` field was written before the repo removed stale non-core metric expectations on 2026-04-21.

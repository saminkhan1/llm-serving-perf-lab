# Artifact Index

Use this file to point reviewers at the smallest number of artifacts needed to audit the repo's current proof state.

## Current hero artifacts

| Artifact ID | Milestone | Status | Question Answered | Hardware | Model | Workload | Repro Command | Primary Report | Raw Data | Caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `m2-qwen-l40s-modal-chat-short-20260423-r2` | M2 | hero | Can the repo produce one real, reproducible, cross-checked vLLM baseline on a single-GPU Modal deployment? | `L40S x1 via modal` | `Qwen/Qwen2.5-1.5B-Instruct` | `chat_short` | `make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260423-r2` | `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/report.md` | `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/metrics.parquet`, `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/benchmark.json` | Bound to one Modal-hosted L40S, one model, one workload; artifact records `git_dirty: true`; GuideLLM uses a synthetic token summary; Modal cold-start probe timeouts require a later clean passing probe. |

## Hero summary

### `m2-qwen-l40s-modal-chat-short-20260423-r2`

Question:
- Can the repo produce one real, reproducible, cross-checked vLLM baseline on a single-GPU Modal deployment?

Finding:
- On `L40S x1 via modal` with `Qwen/Qwen2.5-1.5B-Instruct` and `chat_short`, the controller path completed `500/500` requests with p50/p95/p99 client latency `0.780 / 1.316 / 1.651 s` and `920` official `/metrics` rows with no required official metrics missing. The stored GuideLLM cross-check also completed `500/500` requests and reported median TTFT `187.2 ms`, p95 TTFT `266.3 ms`, and mean throughput `1.21 req/s`.

Reproduction:
```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260423-r2
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_m2_qwen_l40s.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm \
  --execute
```

Files:
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/run.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/report.md`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/scorecard.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/metrics.parquet`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/repo_cross_check_execution.json`
- `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/benchmark.json`

Caveats:
- Bound to one Modal-hosted `L40S x1`, `Qwen/Qwen2.5-1.5B-Instruct`, and `chat_short`; it does not generalize beyond that setup.
- The hero artifact records `git_dirty: true`; a clean-checkout rerun would reduce packaging caveats but is not part of this M2 evidence claim.
- The GuideLLM cross-check is useful as an official-tool comparison, but it replays a synthetic token summary rather than the exact controller request trace.
- Modal cold start can make a first probe time out; that is only acceptable as warmup behavior when a subsequent probe passes cleanly before evidence is produced.

# M3 Result Summary

- Question answered: Can the repo produce one real, reproducible, cross-checked vLLM baseline on a single-GPU Modal deployment?
- Answer: yes. The controller path completed `500/500` requests on `L40S x1 via modal` with `Qwen/Qwen2.5-1.5B-Instruct` and `chat_short`, at client latency p50 / p95 / p99 `0.780 / 1.316 / 1.651 s`.
- Cross-check: the saved GuideLLM run also completed `500/500` requests and reported median / p95 TTFT `187.2 / 266.3 ms` with mean throughput `1.21 req/s`.
- Caveats: Bound to L40S x1 via modal, Qwen/Qwen2.5-1.5B-Instruct, and chat_short. It does not generalize beyond that setup; The stored artifact records `git_dirty: true`; The GuideLLM cross-check uses a synthetic token summary rather than an exact controller trace replay; Modal endpoints can cold-start; treat a failed first probe as warmup only if a subsequent probe passes before the benchmark run.

```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=m2-qwen-l40s-modal-chat-short-20260423-r2
```

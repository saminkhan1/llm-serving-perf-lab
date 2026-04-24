# llm-serving-perf-lab

Compact LLM serving performance lab focused on reproducible benchmarks, official serving metrics, and auditable artifact packs.

> [!WARNING]
> Status as of 2026-04-23: M3 reporting checkpoint complete. This checkout contains a fresh real vLLM artifact pack at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/`, a standalone M3 report at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_report.md`, a concise result summary at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_summary.md`, and a completed GuideLLM cross-check at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/`.
> Public claims must stay bounded to one Modal-hosted `L40S x1`, `Qwen/Qwen2.5-1.5B-Instruct`, and `chat_short` workload. The artifact records `git_dirty: true`, and the GuideLLM cross-check uses a synthetic token summary rather than exact trace replay.

Current status: M3 reporting checkpoint is complete with a stored real baseline, standalone report, concise summary, and saved official-tool cross-check.
The next required work order is M4 SGLang + PD baseline.

## Highlighted state

- **Current hero artifact:** `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/` with [standalone report](artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_report.md), [concise summary](artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_summary.md), and sibling GuideLLM output under `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/`.
- **What remains risky:** the stored hero artifact came from a dirty checkout, the GuideLLM cross-check uses a synthetic token summary, and Modal cold start can make a first probe time out before a later clean warm probe passes. The result is only one bounded baseline and does not support performance-win, routing, PD, regression, profiler, or production-readiness claims.

## Highlighted finding

- **M2 baseline:** On `L40S x1 via modal` with `Qwen/Qwen2.5-1.5B-Instruct` and `chat_short`, the stored controller run completed `500/500` requests with p50/p95/p99 client latency `0.780 / 1.316 / 1.651 s`, `420` official `/metrics` rows, `920` total metric rows, and no required official metrics missing. The saved GuideLLM cross-check also completed `500/500` requests and reported median TTFT `187.2 ms`, p95 TTFT `266.3 ms`, and mean throughput `1.21 req/s`.
- **Primary caveat:** the GuideLLM cross-check uses a synthetic token summary derived from the repo workload config rather than a byte-for-byte replay of the controller trace; the current hero artifact was generated from a dirty checkout; and Modal cold-start probe timeouts should be treated as warmup behavior only when a subsequent probe passes cleanly.

## Reproduce The Hero Artifact

Audit the stored artifact:

```bash
uv run lsp validate-artifact artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2
```

Produce a fresh equivalent run with a non-colliding run id:

```bash
RUN_ID=m2-qwen-l40s-modal-chat-short-repro-$(date +%Y%m%d-%H%M%S)
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID="$RUN_ID"
uv run lsp cross-check-guidellm --backend-config configs/backends/vllm_modal_m2_qwen_l40s.yaml --workload-config configs/workloads/chat_short.yaml --output-dir "artifacts/$RUN_ID/guidellm" --execute
```

## Why this repo exists

The goal is to build a small but serious inference-performance lab that eventually demonstrates:
- real backend bring-up for vLLM and SGLang
- workload-shaped benchmark discipline
- reproducible artifact packs and regression checks
- profiler-backed performance investigation
- public writeups with bounded, hardware-specific claims

## What exists today

Current implemented scope:
- Python package and CLI scaffold (`lsp`)
- strict YAML config validation for backend, workload, policy, threshold, and experiment configs
- deterministic workload generation for M1 workload families
- zero-GPU synthetic fake-run and dry-run benchmark paths for smoke testing repo wiring
- real-mode vLLM adapter path with official Prometheus `/metrics` ingestion and failure artifacts
- official metric expectations aligned with current documented vLLM production metrics rather than deprecated throughput gauges
- explicit backend hardware metadata capture for real-mode artifact credibility
- external `base_url` target support for Modal or other HTTPS vLLM deployments
- external endpoint validation that rejects non-root `base_url` values such as `/v1` and mismatched `/metrics` targets before the real run
- repo-owned vLLM launch-plan rendering from `configs/backends/vllm_dev.yaml`
- endpoint probe for health, runtime metadata, and official metrics exposure
- external GuideLLM cross-check scaffolding plus plan/log capture for M2 verification
- stored real M2 artifact pack and saved GuideLLM cross-check for a single-GPU Modal L40S baseline
- unit and smoke tests
- example configs for future milestones

## What does not exist yet

To keep claims honest, this repo does not yet provide:
- PD comparison studies
- regression gate examples
- profiler-backed optimization reports
- routing studies
- public writeups
- upstream contributions
- a clean-checkout rerun of the current M2 hero artifact for stronger artifact claims

## Quickstart

Requirements:
- Python 3.12+
- `uv`

Setup:

```bash
make install
```

Verify the current repo state:

```bash
make verify-m2
make smoke
make reproduce RUN=m1 REPRO_RUN_ID=demo-m1
```

Prepare for an external Modal-backed M2 run after filling the placeholder config:

```bash
make verify-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
```

Validate a generated artifact directory:

```bash
uv run lsp validate-artifact artifacts/<run_id>
```

Reproduce the current stable aliases:

```bash
make reproduce RUN=m0 REPRO_RUN_ID=demo-m0
make reproduce RUN=m1 REPRO_RUN_ID=demo-m1
make reproduce RUN=configs/workloads/sharegpt_like.yaml REPRO_RUN_ID=demo-sharegpt
make reproduce RUN=m2-real REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=demo-m2-real
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=demo-m2-modal
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_m2_qwen_l40s.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=demo-m2-modal-live
```

`make reproduce RUN=m2-real` is a real-mode path.
It requires a reachable vLLM endpoint or a host where you can turn the repo launch template into a working local server command.
The stable `make` entrypoint now runs `check-m2-readiness` first so placeholder Modal URLs, `/v1` base URLs, mismatched metrics endpoints, and missing cross-check tooling fail before workload traffic starts.
A real M2 claim only becomes valid once the resulting artifact directory is stored and auditable from repo state.

For a Modal-backed M2 run, fill in `configs/backends/vllm_modal_example.yaml` with the deployed `https://...modal.run` URL from Modal's official vLLM example, then use `REPRO_BACKEND=configs/backends/vllm_modal_example.yaml`.
Also replace the placeholder `hardware` block before the real run so the artifact names the tested GPU explicitly.
The repo expects `base_url` to be the endpoint root and now validates that `metrics.scrape_endpoint` is exactly `<base_url>/metrics`, because it derives `/health`, `/version`, and `/v1/completions` from that root.
Use `make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml` before the remote run to catch leftover placeholders and missing local tooling such as GuideLLM.

Inspect the repo-owned M2 launch and cross-check scaffolding directly:

```bash
uv run lsp render-vllm-launch --backend-config configs/backends/vllm_dev.yaml
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_dev.yaml \
  --workload-config configs/workloads/chat_short.yaml
uv run lsp render-vllm-launch --backend-config configs/backends/vllm_modal_example.yaml
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml
uv run lsp check-m2-readiness --backend-config configs/backends/vllm_modal_example.yaml
uv run lsp probe-vllm-target --backend-config configs/backends/vllm_modal_example.yaml
```

## CLI

```bash
uv run lsp --help
uv run lsp validate-config configs/backends/vllm_dev.yaml
uv run lsp validate-config configs/backends/vllm_modal_example.yaml
uv run lsp validate-examples
uv run lsp render-vllm-launch --backend-config configs/backends/vllm_dev.yaml
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_dev.yaml \
  --workload-config configs/workloads/chat_short.yaml
uv run lsp render-vllm-launch --backend-config configs/backends/vllm_modal_example.yaml
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml
uv run lsp run \
  --backend-config configs/backends/vllm_dev.yaml \
  --workload-config configs/workloads/mixed_short_long.yaml \
  --output-dir artifacts \
  --run-id demo-dry-run \
  --dry-run
uv run lsp fake-run \
  --backend-config configs/backends/vllm_dev.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts \
  --run-id demo-run
uv run lsp validate-artifact artifacts/demo-run
```

## Modal M2 Path

Use `configs/backends/vllm_modal_example.yaml` as the starting point for a real external HTTPS target.
Fill in the placeholder endpoint and hardware fields first.
The shortest repo-owned path is:

```bash
make verify-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=<run_id>
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/<run_id>/guidellm \
  --execute
```

After a fresh real run and completed cross-check exist in `artifacts/<run_id>/`, keep the run id, command invocation, backend config, workload config, and caveats with the artifact.

## Artifact contract

A successful run artifact is expected to contain:
- `run.json`
- `backend_config_resolved.json`
- `system_info.json`
- `scorecard.json`
- `report.md`
- `requests.parquet`
- `responses.parquet`
- `metrics.parquet`
- `plots/`

When the external GuideLLM cross-check is executed into `artifacts/<run_id>/guidellm`, the repo also persists:
- `repo_cross_check_plan.json`
- `repo_cross_check_execution.json`
- `repo_cross_check_stdout.log`
- `repo_cross_check_stderr.log`

The repo writes real parquet files for request, response, and metrics tables.
Nested fields such as maps/lists are serialized into JSON strings inside parquet cells to keep the artifact writer deterministic and lightweight.

## Development checks

```bash
make lint
make format-check
make typecheck
make test
make verify-m2
```

## Repository layout

- `configs/` — validated example configs
- `lsp/` — package source for config loading, artifact writing, and CLI behavior
- `tests/` — unit and smoke coverage
- `artifacts/` — generated run outputs; most ad hoc runs are gitignored, while the current M2 hero artifact is intentionally tracked

## Roadmap

M1 execution is complete.
M2 has a fresh artifact-backed baseline.
M3 reporting checkpoint is complete.
The next required stop is M4 SGLang + PD baseline.

## Public-sharing guidance

If you post progress publicly right now, keep the framing honest:
- this is an open-source inference-performance lab with one stored real vLLM baseline and one saved GuideLLM cross-check
- the safe measured claim today is limited to the stored Modal `L40S x1`, `Qwen/Qwen2.5-1.5B-Instruct`, and `chat_short` artifact
- official metrics ingestion follows the current documented core vLLM production metrics
- do not generalize the measured latency or throughput beyond that artifact; call out that the artifact records `git_dirty: true`
- do not claim PD, routing, regression, or profiler depth yet

## License

MIT — see `LICENSE`.

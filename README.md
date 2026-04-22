# llm-serving-perf-lab

Compact LLM serving performance lab focused on reproducibility, artifact quality, and hiring-signal-first systems work.

> [!WARNING]
> Status as of 2026-04-21: Silver / interview-supporting. The repo now has one real M2 baseline artifact and one completed GuideLLM cross-check for `Qwen/Qwen2.5-1.5B-Instruct` on `Modal L40S x1` with `chat_short`.
> Claims are safe only for that tested hardware / model / workload tuple. This is not yet a Gold-level portfolio centerpiece: PD, regression, profiling, routing, public writeup, and upstream artifacts are still missing.

Current status: M2 is complete for one bounded setup and the next required stop is M3 packaging quality.
The repo now contains a real-mode vLLM adapter path, current-core official `/metrics` ingestion, runtime metadata capture, support for external HTTPS `base_url` targets, a repo-owned Modal vLLM launch template, an external GuideLLM cross-check path, and real parquet artifact writing.
The current hero artifact lives at `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3`; the paired cross-check lives at `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/guidellm`.

## Highlighted finding

- **M2 baseline:** On `Modal L40S x1` serving `Qwen/Qwen2.5-1.5B-Instruct` with `chat_short`, the repo baseline completed `500/500` requests with median client latency `0.664248s`, p95 `1.140493s`, and a GuideLLM cross-check that also closed `500/500` successfully. See `docs/18-artifact-index.md` and `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3/report.md`.

Important note:
- the `official_metrics_missing` line inside the April 21, 2026 `r3` report predates the repo's 2026-04-21 metric-contract cleanup
- current repo code no longer treats those stale names as required official vLLM metrics
- the measured latency and request-completion results from that artifact remain valid

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
- synthetic fake-run and dry-run benchmark paths for smoke testing repo wiring
- real-mode vLLM adapter path with official Prometheus `/metrics` ingestion and failure artifacts
- official metric expectations aligned with current documented vLLM production metrics rather than deprecated throughput gauges
- explicit backend hardware metadata capture for real-mode artifact credibility
- external `base_url` target support for Modal or other HTTPS vLLM deployments
- repo-owned vLLM launch-plan rendering from `configs/backends/vllm_dev.yaml`
- endpoint probe for health, runtime metadata, and official metrics exposure
- external GuideLLM cross-check scaffolding plus plan/log capture for M2 verification
- one real Modal-backed M2 artifact pack and matching GuideLLM cross-check under `artifacts/`
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
- broad performance claims beyond the tested M2 tuple

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
make verify-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
make smoke
make reproduce RUN=m1 REPRO_RUN_ID=demo-m1
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
```

`make reproduce RUN=m2-real` is a real-mode path.
It requires a reachable vLLM endpoint or a host where you can turn the repo launch template into a working local server command.
The repo now includes one successful external-Modal example under `artifacts/m2-qwen-l40s-modal-chat-short-20260421-r3`, but reproducing it still requires real endpoint and GPU access.

For a Modal-backed M2 run, fill in `configs/backends/vllm_modal_example.yaml` with the deployed `https://...modal.run` URL from Modal's official vLLM example, then use `REPRO_BACKEND=configs/backends/vllm_modal_example.yaml`.
Also replace the placeholder `hardware` block before the real run so the artifact names the tested GPU explicitly.
The repo expects `base_url` to be the endpoint root, not `/v1`, because it derives `/health`, `/version`, `/v1/completions`, and reads `/metrics` from `metrics.scrape_endpoint`.
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

Use `configs/backends/vllm_modal_example.yaml` for a real external HTTPS target and follow [docs/16-modal-m2-runbook.md](/Users/saminkhan1/Documents/llm-serving-perf-lab/docs/16-modal-m2-runbook.md:1).
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

The current completed example is indexed in `docs/18-artifact-index.md`.

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

The repo now writes real parquet files for request, response, and metrics tables.
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

- `docs/` — project contract, milestones, acceptance gates, and public-writeup guidance
- `configs/` — validated example configs
- `lsp/` — package source for config loading, artifact writing, and CLI behavior
- `tests/` — unit and smoke coverage
- `artifacts/` — generated run outputs (gitignored except placeholder)

## Roadmap

Planned execution order lives in `docs/03-milestones.md`.
M2 execution is complete for one bounded setup.
The next required stop is M3 packaging quality, then M4 PD work.

## Public-sharing guidance

If you post progress publicly right now, keep the framing honest:
- this is an open-source inference-performance lab with one bounded real M2 baseline
- the safe claim today is a real vLLM baseline plus external cross-check for `Qwen/Qwen2.5-1.5B-Instruct` on `Modal L40S x1` with `chat_short`
- official metrics ingestion now follows the current documented core vLLM production metrics
- do not generalize beyond that tested tuple
- do not claim PD, routing, regression, or profiler depth yet

## License

MIT — see `LICENSE`.

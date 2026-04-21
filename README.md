# llm-serving-perf-lab

Compact LLM serving performance lab focused on reproducibility, artifact quality, and hiring-signal-first systems work.

> [!WARNING]
> Status as of 2026-04-21: portfolio-in-progress. M2 scaffolding exists, but there is still no checked-in real vLLM artifact pack, no completed official-tool cross-check, and no measured performance finding that is safe to lead with publicly.
> Until [docs/19-proof-readiness-checklist.md](/Users/saminkhan1/Documents/llm-serving-perf-lab/docs/19-proof-readiness-checklist.md:1) reaches at least Silver, treat this repo as evidence of engineering judgment and lab discipline, not completed inference/performance proof.

Current status: M2 repo scaffolding is in place, but M2 is not complete on this machine.
The repo now contains a real-mode vLLM adapter path, official `/metrics` ingestion, runtime metadata capture, support for external HTTPS `base_url` targets, a repo-owned vLLM launch template, an external GuideLLM cross-check plan, and real parquet artifact writing.
This machine still does not have a real vLLM deployment, GuideLLM, or GPU access, so no real vLLM baseline artifact or official-tool cross-check result is claimed here.

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
- external `base_url` target support for Modal or other HTTPS vLLM deployments
- repo-owned vLLM launch-plan rendering from `configs/backends/vllm_dev.yaml`
- external GuideLLM cross-check scaffolding for M2 verification
- unit and smoke tests
- example configs for future milestones

## What does not exist yet

To keep claims honest, this repo does not yet provide:
- a checked-in real vLLM artifact pack produced on this machine
- a completed GuideLLM cross-check result produced on this machine
- measured performance claims
- PD comparison studies
- profiler-backed optimization reports

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
On this machine that runtime dependency is missing, so the command is reproducible as repo scaffolding but not expected to succeed locally.

For a Modal-backed M2 run, fill in `configs/backends/vllm_modal_example.yaml` with the deployed `https://...modal.run` URL from Modal's official vLLM example, then use `REPRO_BACKEND=configs/backends/vllm_modal_example.yaml`.
The repo expects `base_url` to be the endpoint root, not `/v1`, because it derives `/health`, `/version`, `/v1/completions`, and reads `/metrics` from `metrics.scrape_endpoint`.

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
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=<run_id>
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/<run_id>/guidellm \
  --execute
```

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
This repo is still working through M2: the remaining blocker is producing a real vLLM artifact pack and official-tool cross-check on a machine that actually has the required runtime.

## Public-sharing guidance

If you post progress publicly right now, keep the framing honest:
- this is an open-source inference-performance lab in progress
- deterministic synthetic workload generation and artifact-writing harnesses are complete
- no real benchmark claims are being made yet
- measured findings start only once real backend integration lands in M2

## License

MIT — see `LICENSE`.

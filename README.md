# llm-serving-perf-lab

Compact LLM serving performance lab focused on reproducibility, artifact quality, and hiring-signal-first systems work.

Current status: M1 deterministic workload generation plus a dry-run benchmark harness is complete.
This repo now provides validated workload configs, seeded synthetic request generation, artifact writing, and clearly labeled dry-run and fake-run paths.
It does not yet contain real vLLM or SGLang benchmark results, so it should be shared as an in-progress open-source build log, not as a finished performance portfolio.

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
- artifact bundle writer plus validation checks
- deterministic workload generation for M1 workload families
- synthetic fake-run and dry-run benchmark paths for smoke testing repo wiring
- unit and smoke tests
- example configs for future milestones

## What does not exist yet

To keep claims honest, this repo does not yet provide:
- real serving runs
- official backend metrics ingestion
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

Verify the current M1 state:

```bash
make verify-m1
make smoke
make reproduce RUN=m1 REPRO_RUN_ID=demo-m1
```

Validate a generated artifact directory:

```bash
uv run lsp validate-artifact artifacts/<run_id>
```

Reproduce the current synthetic milestones with stable aliases:

```bash
make reproduce RUN=m0 REPRO_RUN_ID=demo-m0
make reproduce RUN=m1 REPRO_RUN_ID=demo-m1
make reproduce RUN=configs/workloads/sharegpt_like.yaml REPRO_RUN_ID=demo-sharegpt
```

`make reproduce` is intentionally limited to the current M0/M1 synthetic paths.
It does not run a real backend and must not be presented as measured M2+ evidence.

## CLI

```bash
uv run lsp --help
uv run lsp validate-config configs/backends/vllm_dev.yaml
uv run lsp validate-examples
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

Note: the M0 fake-run path and the M1 `run --dry-run` path both write deterministic JSON rows into `.parquet`-named files only to exercise the artifact contract. These are synthetic scaffolding paths, not a real parquet-format claim or real benchmark result.

## Development checks

```bash
make lint
make format-check
make typecheck
make test
make verify-m1
```

## Repository layout

- `docs/` — project contract, milestones, acceptance gates, and public-writeup guidance
- `configs/` — validated example configs
- `lsp/` — package source for config loading, artifact writing, and CLI behavior
- `tests/` — unit and smoke coverage
- `artifacts/` — generated run outputs (gitignored except placeholder)

## Roadmap

Planned execution order lives in `docs/03-milestones.md`.
The next work order after M1 is M2: real vLLM integration plus official metrics ingestion.

## Public-sharing guidance

If you post progress publicly right now, keep the framing honest:
- this is an open-source inference-performance lab in progress
- deterministic synthetic workload generation and artifact-writing harnesses are complete
- no real benchmark claims are being made yet
- measured findings start only once real backend integration lands in M2

## License

MIT — see `LICENSE`.

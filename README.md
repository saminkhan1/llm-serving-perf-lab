# llm-serving-perf-lab

Compact LLM serving performance lab focused on reproducibility, artifact quality, and hiring-signal-first systems work.

Current status: M0 foundation is complete.
This repo currently provides the validated scaffold for future benchmark work: config schemas, artifact schema, CLI, and a clearly labeled synthetic fake-run path.
It does not yet contain real vLLM or SGLang benchmark results, so it should be shared as an in-progress open-source build log, not as a finished performance portfolio.

## Why this repo exists

The goal is to build a small but serious inference-performance lab that eventually demonstrates:
- real backend bring-up for vLLM and SGLang
- workload-shaped benchmark discipline
- reproducible artifact packs and regression checks
- profiler-backed performance investigation
- public writeups with bounded, hardware-specific claims

## What exists today

M0 foundation is implemented and validated:
- Python package and CLI scaffold (`lsp`)
- strict YAML config validation for backend, workload, policy, threshold, and experiment configs
- artifact bundle writer plus validation checks
- synthetic fake-run path for smoke testing repo wiring
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

Verify the current M0 state:

```bash
make verify-m0
make smoke
uv run lsp fake-run \
  --backend-config configs/backends/vllm_dev.yaml \
  --workload-config configs/workloads/chat_short.yaml
```

Validate a generated artifact directory:

```bash
uv run lsp validate-artifact artifacts/<run_id>
```

## CLI

```bash
uv run lsp --help
uv run lsp validate-config configs/backends/vllm_dev.yaml
uv run lsp validate-examples
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

Note: in M0, the fake-run path writes deterministic JSON rows into `.parquet`-named files only to exercise the artifact contract. This is synthetic scaffolding, not a real data format claim.

## Development checks

```bash
make lint
make format-check
make typecheck
make test
make verify-m0
```

## Repository layout

- `docs/` — project contract, milestones, acceptance gates, and public-writeup guidance
- `configs/` — validated example configs
- `lsp/` — package source for config loading, artifact writing, and CLI behavior
- `tests/` — unit and smoke coverage
- `artifacts/` — generated run outputs (gitignored except placeholder)

## Roadmap

Planned execution order lives in `docs/03-milestones.md`.
The next work order after M0 is M1: deterministic workload generation plus benchmark-harness artifact writing.

## Public-sharing guidance

If you post progress publicly right now, keep the framing honest:
- this is an open-source inference-performance lab in progress
- M0 foundation is complete and validated
- no real benchmark claims are being made yet
- measured findings will start once real backend integration lands

## License

MIT — see `LICENSE`.

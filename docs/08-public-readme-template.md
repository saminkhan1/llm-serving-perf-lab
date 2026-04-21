# Public README Template

Use this structure when the repo is ready to be shown publicly.

---

# llm-serving-perf-lab

Production-style LLM inference performance lab for mixed-workload serving, prefill/decode tradeoff studies, routing, rollout safety, and profiler-backed optimization.

## What this repo proves

This repo is designed to show:
- real serving-stack bring-up
- workload-shaped benchmark discipline
- PD tradeoff measurement
- routing and rollout logic
- profiler-backed performance debugging
- bounded, reproducible experiment search

## Highlighted findings

Lead with 3 findings, not a feature list.

Example format:
- **PD tradeoff:** On `[hardware]` with `[model]` and `[workload]`, PD reduced `[metric]` by `[x%]` while leaving `[other metric]` unchanged / worse.
- **Routing:** A cache-aware policy improved `[metric]` by `[x%]` vs round-robin on `[workload]`.
- **Regression gate:** A candidate with `[fault / degraded config]` was correctly blocked by the compare engine due to `[metrics]`.

## Backends

Required:
- vLLM
- SGLang

Optional:
- TensorRT-LLM

## Quickstart

```bash
make install
make smoke
lsp validate-config configs/...
lsp run --config configs/...
lsp compare --baseline <run_id> --candidate <run_id>
make reproduce RUN=<run_id>
```

## Proof artifacts

Link directly to:
- baseline report
- PD study
- routing study
- regression gate example
- profiler-backed optimization note
- topology study
- upstream contribution

## Architecture

Briefly describe:
- adapters
- workloads
- metrics
- regression
- routing
- profiling
- sweep runner

Keep this short. The artifacts matter more than the architecture section.

## Reproducibility

For every highlighted result, provide:
- config path
- run id
- exact command
- hardware / model / backend version
- caveats

## Caveats

Include what the repo does **not** prove:
- not a production fleet
- results bounded to tested hardware/model/workload
- optional components may be incomplete

## Upstream contributions

List:
- issue / PR title
- link
- what was discovered or improved

## Why this project exists

One paragraph only:
This repo exists to study realistic LLM serving behavior under mixed workloads and to package the results as reproducible engineering artifacts rather than screenshots or claims.

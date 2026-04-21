# Architecture Contract

## System layers

The repository should have these core layers:

1. backend adapters
2. workload generation / replay
3. metrics ingestion
4. regression and comparison
5. routing / policy plane
6. profiling / reporting
7. bounded experiment runner

The key difference from a generic platform is that every layer exists to support **measured inference results**.

## Repository layout

```text
llm-serving-perf-lab/
  README.md
  AGENTS.md
  pyproject.toml
  Makefile
  docs/
  configs/
    backends/
    workloads/
    policies/
    thresholds/
    experiments/
  lsp/
    cli/
    config/
    artifacts/
    backends/
      base.py
      vllm_adapter.py
      sglang_adapter.py
      trtllm_adapter.py        # optional stretch
    workloads/
    metrics/
    regression/
    routing/
    profiling/
    reporting/
    agentops/
    utils/
  tests/
    unit/
    integration/
    smoke/
  artifacts/
```

## Core contracts

### Backend adapter contract

Every adapter must implement:
- launch
- stop
- healthcheck
- submit
- collect_metrics

Rules:
- prefer structured endpoints over fragile log scraping
- dry-run mode is required
- resolved launch settings must be written to artifacts
- version / runtime metadata must be captured

### Workload contract

Every request should include:
- request id
- prompt
- arrival timestamp
- max new tokens
- decoding params
- tags

Required workload families:
- `chat_short`
- `context_long`
- `mixed_short_long`
- `bursty_chat`
- `prefix_reuse_heavy`
- `sharegpt_like` or equivalent workload-shaped profile

### Metrics contract

Required metrics for serious runs:
- TTFT
- ITL / TPOT
- p50 / p95 / p99 end-to-end latency
- requests/sec
- tokens/sec
- queue depth
- running requests or best equivalent
- GPU memory usage or best available proxy
- KV-cache usage / hits when supported
- error rate / timeout rate

Rules:
- use official backend metrics first
- derived metrics must be labeled as derived
- missing metrics must be visible, not silently backfilled

### Artifact contract

Each run should write an immutable artifact directory with at least:
- `run.json`
- `requests.parquet`
- `responses.parquet`
- `metrics.parquet`
- `backend_config_resolved.json`
- `system_info.json`
- `scorecard.json`
- `report.md`
- `plots/`
- `profiler/` when enabled

Required metadata:
- run id
- git sha or dirty marker
- backend
- backend version
- mode
- model id
- hardware profile
- workload id
- policy id
- seed
- start and end time
- status
- repro command

### Routing signal contract

Allowed online signals:
- prompt length bucket
- estimated decode length heuristic
- prefix hash / cache reuse hint
- queue depth by worker
- recent TTFT / ITL EWMA
- memory headroom
- worker role
- backend / hardware capability tag

Forbidden online signals:
- actual completion length
- future arrivals
- offline oracle labels
- any data unavailable at request time

### Regression contract

Given a baseline and candidate:
- compute relative deltas
- apply config-driven thresholds
- emit PASS / WARN / FAIL
- explain the top deltas in machine-readable and markdown form

### Profiling contract

Profiling must be:
- opt-in
- normalizable into artifacts
- referenced from reports
- non-fatal when tools are absent

### Bounded sweep contract

The sweep runner exists to automate benchmark experiments, not code writing.

It must enforce:
- max runs
- wall-clock budget
- max consecutive failures
- explicit objective
- explicit tie-breakers
- append-only ledger

Selected winners must be reproducible from:
- base config
- config deltas
- command list
- objective
- artifacts

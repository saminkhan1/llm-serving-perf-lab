# Acceptance Tests

## Global gates

Every milestone must pass the relevant subset of:
```bash
ruff check .
black --check .
mypy lsp
pytest -m "not gpu and not network"
```

GPU-backed integration can add stricter jobs later.

## Gate 1 — config safety

Must fail on:
- unknown keys
- missing required keys
- invalid enums
- impossible thresholds
- impossible budgets
- invalid external endpoint layout such as `base_url` set to `/v1` or a metrics URL that does not match the target server's `/metrics` endpoint

## Gate 2 — artifact validity

Every serious run artifact must include:
- metadata
- repro command
- git sha or dirty marker
- status
- non-empty metrics unless failure is explicit
- schema version markers

## Gate 3 — no silent degradation

New code may not:
- swallow launch failures
- emit fake metrics in real mode
- hide missing profiler data
- mark incomplete runs as success
- silently change metric definitions

## Gate 4 — deterministic replay

The following must be reproducible from seed and config:
- synthetic workload generation
- routing simulator decisions
- bounded sweep candidate enumeration

## Gate 5 — claim discipline

Public-facing reports may not:
- generalize beyond tested hardware/model/workload
- omit caveats for tradeoff studies
- claim wins without baseline comparison
- hide negative results that materially change interpretation

## Milestone-specific checks

### M0
- fake run artifact validates
- sample configs validate
- CLI help works

### M1
- same seed yields same request stream
- workload-shaped profile exists
- runner writes artifacts

### M2
- vLLM lifecycle failures are visible
- official metrics ingestion works
- one real run completes
- one result is cross-checked against official benchmarking path

### M3
- README draft section includes measured numbers and repro command
- early report can stand on its own

### M4
- PD launch validates required roles
- artifacts record endpoints and roles
- PD and non-PD runs are comparable

### M5
- PASS/WARN/FAIL semantics are tested
- one bad candidate fails
- synthetic fault annotations appear in report output

### M6
- profiler capture is opt-in
- missing profiler tools do not crash runs
- parsed profiler summaries land in artifacts

### M7
- simulator uses only allowed signals
- decision logs include reason codes
- replay is deterministic

### M8
- live routing logs worker choice and reason
- fallback behavior is explicit
- policy version is recorded

### M9
- no sweep exceeds budget
- repeated failures trigger watchdog stop
- best-run selection uses declared objective only

### M10
- optimization note includes baseline, candidate, hardware, model
- profiler evidence is attached
- at least one caveat is documented

### M11
- topology assumptions are explicit
- concurrency or worker-count axis is present
- claim is bounded to tested setup

### M12
- optional backend does not break the clarity of the main story

### M13
- quickstart works from clean checkout
- upstream link is present
- public writeup is based on repo-generated artifacts

## Reproducibility contract

Any result used in applications must be reproducible through a stable command such as:
```bash
make reproduce RUN=<run_id or config>
```

For the current M0/M1 synthetic state, the stable baseline commands are:
```bash
make reproduce RUN=m0
make reproduce RUN=m1
```

For M2 real-mode bring-up, the stable repo entrypoint is:
```bash
make reproduce RUN=m2-real REPRO_WORKLOAD=configs/workloads/chat_short.yaml
```

For external HTTPS deployments such as Modal, use the same entrypoint with an explicit backend config:
```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml
```

That command is only a reproducible repo entrypoint, not a guarantee that the local machine has the required vLLM, GPU, or external cross-check dependencies.
It now performs a readiness precheck first so obvious placeholder or malformed external endpoint configs fail before workload traffic starts.

If a result cannot be reproduced from repo state and stored artifacts, it does not count.

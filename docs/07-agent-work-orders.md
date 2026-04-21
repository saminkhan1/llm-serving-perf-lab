# Agent Work Orders

Use these as milestone-bounded prompts for coding agents.

## Global instructions for every work order

You are working inside `llm-serving-perf-lab`.

Read first:
- `docs/00-start-here.md`
- `docs/01-hiring-signal-charter.md`
- `docs/05-architecture.md`
- `docs/06-acceptance-tests.md`

Non-negotiable rules:
1. Do not work on future milestones.
2. Prefer smaller deterministic implementations.
3. Add tests unless truly impossible; if impossible, explain why precisely.
4. Label all mocks, dry-runs, and synthetic paths clearly.
5. Do not add dashboards or notebook-only logic.
6. Optimize for artifact quality and reproducibility.
7. If a milestone produces a report, write it.
8. If a result is ambiguous, state the ambiguity instead of smoothing it over.

## Work order A — M0 foundation

### Goal
Create repo skeleton, config schemas, artifact schema, CLI scaffold, and smoke-testable fake path.

### Deliverables
- repo structure
- pyproject
- schema definitions
- config loader
- artifact writer
- CLI scaffold
- smoke tests
- root `AGENTS.md`

### Definition of done
- fake run emits valid artifacts
- smoke tests pass

---

## Work order B — M1 workload engine + benchmark harness

### Goal
Implement deterministic workloads and artifact-writing benchmark runner.

### Required workloads
- `chat_short`
- `context_long`
- `mixed_short_long`
- `bursty_chat`
- `prefix_reuse_heavy`
- `sharegpt_like` or equivalent

### Definition of done
- same seed reproduces same request stream
- runner writes requests, responses, metrics, and report

---

## Work order C — M2 vLLM baseline + official metrics

### Goal
Implement vLLM adapter, real run path, and official metrics ingestion.

### Deliverables
- vLLM adapter
- lifecycle handling
- `/metrics` ingestion
- runtime metadata capture
- baseline config
- one real artifact pack path

### Constraints
- official metrics first
- no fragile log parsing if structured metrics exist
- dry-run must remain GPU-free

### Current execution choice
- stand up the first real endpoint from Modal's official vLLM example before changing repo code again
- prefer one small ungated model for the first proof run, currently `Qwen/Qwen2.5-1.5B-Instruct`
- prefer `1x L40S` for the first Modal attempt because it is a simpler single-GPU fit than jumping to larger spend
- use repo-side checks in this order once the endpoint exists:
  - `make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml`
  - `make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml`
  - `make reproduce RUN=m2-real ...`
  - `uv run lsp cross-check-guidellm ... --execute`
- treat the external GPU-backed benchmark run as the final M2 step, not as setup work to mix with local repo changes

### Definition of done
- one real run completes
- artifacts include repro command and caveats

---

## Work order D — M3 Portfolio Checkpoint A

### Goal
Turn the first real benchmark into a public-quality artifact.

### Deliverables
- polished benchmark report
- README draft section with measured numbers
- reproduction command
- concise summary of result and caveats

### Definition of done
- result is understandable in under two minutes

---

## Work order E — M4 SGLang + PD baseline

### Goal
Implement SGLang adapter and produce PD vs non-PD comparison.

### Deliverables
- standard serving mode
- PD launch mode
- endpoint / role capture
- comparison script
- study report

### Constraints
- honest tradeoff analysis required
- do not claim generic throughput gains

### Definition of done
- PD and non-PD study is reproducible and caveated

---

## Work order F — M5 regression gate + fault injection

### Goal
Implement compare engine, thresholds, PASS/WARN/FAIL, and labeled synthetic faults.

### Definition of done
- one bad candidate fails
- report shows fault annotations clearly

---

## Work order G — M6 profiling integration

### Goal
Integrate Nsight Systems, optionally Nsight Compute, and write normalized profiler summaries.

### Definition of done
- profiled run produces parsable artifacts
- no-profiler environment still works cleanly

---

## Work order H — M7 routing simulator

### Goal
Build offline routing simulator using request-time signals only.

### Definition of done
- at least 5 policies compared
- reason-coded decisions
- deterministic replay

---

## Work order I — M8 live routing / control plane

### Goal
Integrate live policy selection into dispatch path.

### Definition of done
- live runs record chosen worker and why

---

## Work order J — M9 bounded sweep runner

### Goal
Implement bounded experiment runner for benchmark configs.

### Definition of done
- best candidate is selected from explicit objective and budgeted search
- chosen config is reproducible from artifacts alone

---

## Work order K — M10 kernel/runtime artifact

### Goal
Produce one profiler-backed hot-path improvement or tuning study.

### Definition of done
- before/after metrics plus profiler evidence
- caveat or counterexample included

---

## Work order L — M11 communication/topology artifact

### Goal
Produce one topology-aware or communication-related systems study.

### Definition of done
- explicit topology assumptions
- scaling or concurrency axis
- bounded claims

---

## Work order M — M12 optional TensorRT-LLM

### Goal
Optionally add TensorRT-LLM without weakening the main repo narrative.

### Definition of done
- backend adds credibility without becoming the main story

---

## Work order N — M13 upstream + public release

### Goal
Package the repo for applications.

### Deliverables
- upstream link
- final README
- technical writeup
- artifact index
- application checklist output

### Definition of done
- clean-checkout quickstart works
- public materials are based on repo-generated evidence

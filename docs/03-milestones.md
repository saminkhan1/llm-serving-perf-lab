# Milestones

## Strict execution order

1. M0 foundation
2. M1 workload engine + benchmark harness
3. M2 vLLM baseline + official metrics
4. M3 Portfolio Checkpoint A
5. M4 SGLang + PD baseline
6. M5 regression gate + fault injection
7. M6 profiling integration
8. M7 routing simulator
9. M8 live routing / control plane
10. M9 bounded sweep runner
11. M10 kernel/runtime optimization artifact
12. M11 communication/topology artifact
13. M12 optional TensorRT-LLM
14. M13 upstream + public release + application checkpoint

Do not skip checkpoints.

---

## M0 — foundation

### Goal
Create the repo skeleton, config schema, artifact schema, CLI, and smoke-testable fake path.

### Deliverables
- repo layout
- pyproject and tooling
- schema validation
- artifact writer
- CLI scaffold
- smoke tests
- root `AGENTS.md`

### Done when
- fake run emits a valid artifact directory
- schema examples validate
- smoke tests pass

---

## M1 — workload engine + benchmark harness

### Goal
Implement deterministic workload generation and a benchmark runner that supports dry-run and fake backends first.

### Required workload families
- `chat_short`
- `context_long`
- `mixed_short_long`
- `bursty_chat`
- `prefix_reuse_heavy`
- one workload-shaped profile such as `sharegpt_like`

### Deliverables
- seeded request generation
- normalized request schema
- minimal reporting
- request/response/metrics artifact writing
- at least one workload-shaped config

### Done when
- same seed reproduces same request stream
- runner writes valid artifacts
- at least one workload-shaped profile exists

---

## M2 — vLLM baseline + official metrics

### Goal
Bring up vLLM for real, ingest official metrics, and establish the first trustworthy baseline.

### Required priorities
1. real run before feature breadth
2. official `/metrics` ingestion before custom approximations
3. one benchmark cross-check using official vLLM tooling or GuideLLM-compatible flow

### Deliverables
- vLLM adapter
- launch and lifecycle handling
- `/metrics` ingestion
- runtime metadata capture
- baseline config
- one real artifact pack

### Done when
- one real end-to-end benchmark run completes
- artifact includes run metadata, metrics, report, and repro command
- at least one result is cross-checked against official benchmarking flow

### Stop-and-package gate after M2
Before any M4 work starts, update:
- README status and measured-findings draft
- artifact index entry using `docs/18-artifact-index-template.md`
- proof-readiness state in `docs/19-proof-readiness-checklist.md`
- claim wording in `docs/10-application-packaging.md` if the new artifact changes what is safe to say

---

## M3 — Portfolio Checkpoint A

### Goal
Force an early public-quality artifact before more platform work.

### Required output
- one polished benchmark report
- one concise result summary
- one README draft section with measured numbers
- one artifact reproduction command
- one artifact-index entry
- one proof-readiness status update

### Done when
- a skeptical engineer can understand the result in under two minutes
- the result is reproducible from repo + artifact data
- no unsupported claims remain in the text

Do not continue until this checkpoint is met.

---

## M4 — SGLang + PD baseline

### Goal
Add SGLang, then produce a real PD vs non-PD comparison.

### Required priorities
1. non-PD serving first
2. PD on a tested setup second
3. honest writeup of where PD helps and where it does not

### Deliverables
- SGLang adapter
- standard serving mode
- PD mode with explicit prefill/decode roles
- endpoint and role capture in artifacts
- one PD comparison study

### Done when
- PD and non-PD runs are comparable with one command
- study explicitly records workload, hardware, and caveats
- result avoids overclaiming throughput gains

---

## M5 — regression gate + fault injection

### Goal
Build pass/warn/fail comparison logic before deeper routing or low-level optimization breadth.

### Deliverables
- compare engine
- threshold schema
- PASS / WARN / FAIL output
- slow-worker fault
- queue-inflation fault
- memory-pressure proxy or explicit alternative
- report annotations

### Done when
- one known-bad candidate fails
- one injected fault shows up in report output
- comparison output is legible to a reviewer

---

## M6 — profiling integration

### Goal
Make profiling a normal part of the workflow before chasing sophisticated optimizations.

### Deliverables
- Nsight Systems wrapper
- optional Nsight Compute wrapper
- parser outputs
- normalized profiler summaries in artifacts

### Done when
- a profiled run emits normalized parsed summaries
- runs still work when profiler is unavailable
- profiler outputs can be linked directly from a report

### Stop-and-package gate after M6
Before any M7 work starts, update:
- README findings block or draft findings block
- technical writeup draft for the profiler-backed note
- artifact index entry for the profiled run
- proof-readiness checklist and application-facing copy to reflect what is now safe to claim

---

## M7 — routing simulator

### Goal
Build offline routing evaluation using request-time signals only.

### Deliverables
- signal extraction
- baseline policies
- cache-aware policy
- hybrid policy
- decision logs with reason codes
- evaluation summary

### Done when
- simulator compares at least 5 policies on one trace
- all decisions are reproducible from trace + seed
- no future-information leakage exists

---

## M8 — live routing / control plane

### Goal
Integrate live policy selection into request submission after offline logic is trustworthy.

### Deliverables
- worker-state view
- online signal snapshots
- dispatch-time policy hook
- structured reason codes
- visible fallback behavior

### Done when
- live runs log chosen worker and reason
- missing state is handled explicitly
- artifacts record the policy version used

---

## M9 — bounded sweep runner

### Goal
Add bounded automation for serving experiments, not for code generation.

### Deliverables
- objective abstraction
- bounded search space
- approval policy
- watchdog / loop detection
- ledger
- experiment manifest artifact

### Done when
- a bounded sweep chooses a best candidate
- stop conditions are enforced
- chosen candidate is reproducible from artifacts alone

---

## M10 — kernel/runtime optimization artifact

### Goal
Produce one profiler-backed hot-path improvement or well-scoped tuning study.

### Examples
- Triton kernel tuning
- runtime scheduling change
- batching-related improvement
- operator-level hot-path reduction

### Done when
- before/after metrics are shown
- profiler evidence is attached
- at least one counterexample or limitation is documented

---

## M11 — communication/topology artifact

### Goal
Produce one communication or topology study that looks like real systems evaluation.

### Examples
- NCCL setting study
- NVLink / PCIe aware placement
- PD role placement analysis
- concurrency vs worker-count scaling
- transfer-delay impact study

### Done when
- hardware topology assumptions are explicit
- concurrency or scale axis is present
- claims are limited to tested setup

---

## M12 — optional TensorRT-LLM

### Goal
Only after the strong proof artifacts exist, optionally add TensorRT-LLM as extra credibility.

### Done when
- it does not dilute the clarity of the main story
- the repo still leads with measured proof, not backend count

---

## M13 — upstream + public release + application checkpoint

### Goal
Package the repo so it reads well in hiring funnels.

### Deliverables
- one upstream contribution or serious issue/design note
- final README
- technical writeup
- artifact index
- application packaging assets
- completed proof-readiness checklist

### Done when
- clean-checkout quickstart works
- upstream link is recorded
- README highlights proof artifacts above feature list
- application checklist is satisfied

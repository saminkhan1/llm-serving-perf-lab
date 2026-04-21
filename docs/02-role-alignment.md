# Role Alignment

This document exists to keep the project aligned with what current inference / performance roles actually reward.

## What the roles tend to reward

### OpenAI-style inference roles
Signal:
- high-volume, low-latency, high-availability serving
- visibility into bottlenecks and instability
- CUDA / NCCL / NVLink / HPC familiarity
- production distributed systems
- performance, latency, throughput, efficiency

What your repo should show:
- real serving baseline
- artifacted bottleneck visibility
- one kernel/runtime or scheduler hot-path study
- clean reproducibility
- debugging discipline

### OpenAI-style workload / bring-up roles
Signal:
- repeatable benchmark and stress harnesses
- whole-system behavior across CPU, GPU, memory, networking
- pass/fail and regression detection
- platform bring-up and validation

What your repo should show:
- benchmark harness with actionable outputs
- regression gates
- topology / scaling study
- clear boundary of claims

### Anthropic-style inference / cloud inference roles
Signal:
- intelligent request routing
- batching and caching strategies
- large-scale distributed systems
- orchestration across heterogeneous accelerators
- observability on real serving workloads

What your repo should show:
- routing simulator
- live routing hook
- cache-aware policy
- explicit reason codes
- metrics-first evaluation

### Anthropic-style inference deployment roles
Signal:
- deployment and validation automation
- resource-constrained rollout logic
- observability on deploy state
- safe launch sequencing

What your repo should show:
- compare engine
- canary-style pass/warn/fail logic
- rollout-safe judgment
- visible synthetic faults
- reproducible baseline/candidate diffs

### Google-style kernel / performance roles
Signal:
- CUDA / Triton or equivalent low-level work
- understanding of attention, MoE, low precision, accelerator behavior
- benchmarking infrastructure
- developer tooling and documentation
- open-source signal

What your repo should show:
- profiler-backed hot-path analysis
- one low-level improvement or well-scoped tuning study
- benchmark infra that others can run
- good docs
- upstream issue or PR

## Project components ranked by hiring signal

### Highest signal
1. Reproducible benchmark harness with real backend runs
2. SGLang PD study with honest tradeoff analysis
3. Regression gate that blocks a bad candidate
4. Profiler-backed optimization artifact
5. Routing policy win with reason-coded decisions
6. Upstream contribution or serious issue with minimal repro
7. Strong README with measured wins and reproduction commands

### Medium signal
- bounded sweep runner
- optional TensorRT-LLM adapter
- polished architecture diagrams
- containerization depth beyond what is needed

### Low signal if done before the high-signal items
- fancy dashboards
- broad backend abstraction without real measurements
- lots of knobs with no artifact quality
- agent branding
- generic blog language

## Mid-level reality check

This project can meaningfully improve your candidacy and can absolutely help you win interviews.

It does **not** magically replace years of professional experience on its own.

So the project must do two things:
1. prove strong technical judgment through artifacts
2. minimize anything that makes it look like an academic or speculative side project

## If you only had time for four things

Do these:
1. vLLM baseline with official metrics and a clean artifact pack
2. SGLang PD study with one honest conclusion
3. regression gate + fault injection
4. profiler-backed optimization note

If those four are excellent, the repo can already become useful in applications.

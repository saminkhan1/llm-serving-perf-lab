# Role Alignment

Checked: 2026-04-21

This document exists to keep the project aligned with what current inference / performance roles actually reward.

Use `docs/17-job-mapping-2026.md` as the dated appendix when updating README copy, artifact summaries, or application-facing language. This page holds the stable thesis; the appendix holds the current public-role evidence map.

## Primary target roles

Optimize this repo first for:
- inference systems
- workload / performance engineering
- inference deployment / launch engineering
- cloud inference / routing / cost-efficiency roles

This maps most directly to the current role shapes at:
- OpenAI Model Inference
- OpenAI Workload Enablement
- Anthropic Inference
- Anthropic Cloud Inference
- Anthropic Inference Deployment
- Anthropic Inference Routing and Performance
- Google Software Engineer III, AI/ML, GPU Inference, Optimization

## Secondary / stretch target roles

Treat these as stretch alignment, not the main ROI story:
- kernel / accelerator bring-up
- deep compiler / runtime optimization
- heterogeneous cluster scheduling / supercomputing roles
- physical-AI infra roles centered on large training fleets

Those roles usually require more evidence in:
- low-level kernel work
- collective communication tuning
- new hardware bring-up
- multi-accelerator or multi-cluster placement
- upstream-facing systems debugging

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

### Meta / physical-AI-style infra roles
Signal:
- placement and scheduling decisions under resource constraints
- heterogeneous hardware awareness
- topology and communication reasoning
- operational tooling that keeps ML systems usable by researchers

What your repo should show:
- explicit placement and routing logic
- topology / worker-count or transfer-delay study
- reproducible operational artifacts instead of prose-only claims
- clear accounting of hardware, model, workload, and limits

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

## Inbound-interest bar

If the goal is inbound recruiter or hiring-manager interest for frontier-lab-style inference roles, assume the repo must reach at least:
- one real vLLM artifact pack
- one honest SGLang PD study
- one regression gate artifact
- one profiler-backed optimization artifact
- one routing or placement study
- one upstream issue / PR
- one README / writeup that leads with measured findings

Anything less can still help in interviews, but is less likely to read as a top-of-stack proof-of-work project.

## If you only had time for four things

Do these:
1. vLLM baseline with official metrics and a clean artifact pack
2. SGLang PD study with one honest conclusion
3. regression gate + fault injection
4. profiler-backed optimization note

If those four are excellent, the repo can already become useful in applications.

## 2026 evidence rule

When a current role page emphasizes:
- throughput / latency / high-availability serving
- bottleneck visibility and instability debugging
- repeatable benchmarks and regression detection
- routing, deployment automation, or heterogeneous accelerator judgment

answer with one artifact, not one paragraph.

The practical mapping is:
- real vLLM artifact pack for serving-stack credibility
- GuideLLM or official-tool cross-check for result validation
- regression gate for rollout and launch-engineering signal
- profiler-backed note for depth
- routing study for systems judgment

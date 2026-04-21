# Hiring-Signal Charter

## Mission

Build a **production-style LLM inference performance lab** that proves, in one coherent repository, that you can:

1. bring up real serving stacks
2. run realistic and reproducible benchmarks
3. reason about prefill/decode tradeoffs
4. build routing and rollout logic with explicit constraints
5. observe and debug performance regressions
6. produce at least one low-level optimization artifact with profiler evidence
7. communicate results clearly enough for engineers and hiring managers to trust them

## Primary thesis

> **SLA-aware LLM serving optimization under mixed workloads**  
> with **observability-first evaluation**, **PD tradeoff analysis**,  
> **cache-aware routing**, **regression-aware rollout gating**,  
> and **bounded experiment search**.

## Target role families

This project is optimized to resonate with:
- inference systems roles
- workload / performance engineering roles
- ML systems infrastructure roles
- kernel / runtime adjacent performance roles
- cloud inference / inference deployment roles

## What this repo must prove

### Systems depth
- real backend bring-up
- realistic failure handling
- structured artifact writing
- repeatable test harnesses

### Inference depth
- latency / throughput / cache / queue tradeoffs
- PD analysis
- batching / routing / scheduling reasoning
- hardware- and workload-shaped measurement

### Operational judgment
- pass/warn/fail regression gates
- canary-style comparison logic
- visible synthetic faults
- explicit fallbacks and reason codes

### Engineering maturity
- tests
- bounded scope
- caveats
- upstream contribution or high-quality upstream issue
- clear docs and reproduction instructions

## What this repo is not

It is not:
- a new model
- a training repo
- a generic AI agent
- a dashboard-first SaaS
- a speculative research platform
- a benchmark screenshot collection
- a compiler project
- a wrapper around blog-post numbers

## Stack policy

### Required
- vLLM
- SGLang

### Optional stretch
- TensorRT-LLM

TensorRT-LLM should only become required after the repo already has:
- one vLLM baseline artifact pack
- one SGLang PD study
- one regression gate example
- one profiler-backed runtime note

## Workload policy

The repo must include both:
- deterministic synthetic workloads
- at least one workload-shaped benchmark inspired by real serving behavior

The repo may use synthetic prompts, but it must model behaviors such as:
- short interactive chat
- long-context requests
- burstiness
- prefix reuse
- mixed short/long interference

## Artifact policy

Every serious result must have:
- config
- seed
- backend version
- model id
- hardware description
- command invocation
- metrics
- report
- caveats

If any of those are missing, the result does not count as a portfolio artifact.

## Public narrative

The repo should be described as:

> a compact inference-performance lab for LLM serving: benchmark discipline, PD tradeoff studies, routing decisions, rollout safety, and profiler-backed optimization.

Do **not** lead with:
- “agentic experimentation”
- “autonomous research”
- “frontier AI platform”
- “general inference orchestration platform”

Those stories are broader and weaker for the target roles.

## Final recruiting narrative

A strong reviewer should be able to say:

> This person did not just run benchmarks.  
> They stood up real backends, evaluated workload-shaped serving behavior, studied PD tradeoffs, built routing and regression logic, found at least one hot path with profiling, and packaged the results like an engineer who understands production constraints.

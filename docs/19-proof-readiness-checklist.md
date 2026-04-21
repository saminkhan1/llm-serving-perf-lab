# Proof Readiness Checklist

Checked: 2026-04-21

This document is the public-claim gate.

If the answer is "no" for the current stage, downgrade the wording in:
- `README.md`
- `docs/10-application-packaging.md`
- resume bullets
- LinkedIn copy

## Current default state

Until the first real M2 artifact pack lands, the repo is:
- portfolio-in-progress
- useful for interview discussion
- not yet safe to lead with as measured inference-performance proof

## Stage gates

### Bronze — not ready to lead with

Required state:
- plans, scaffolding, or synthetic-only outputs

Safe wording:
- repo-in-progress
- deterministic benchmark harness
- real-mode bring-up path exists
- no measured claims yet

Not safe:
- throughput / latency wins
- serving-stack credibility claims
- routing claims
- regression-safety claims
- profiler-depth claims

### Silver — interview-supporting

Required:
- one real vLLM artifact pack
- one official-tool or GuideLLM cross-check
- one README measured-findings section
- one artifact-index entry

Safe wording:
- real serving baseline exists
- official metrics were captured
- results are reproducible from repo state plus artifacts

Still not safe:
- profiler-backed optimization claims
- routing-effectiveness claims
- "portfolio centerpiece" positioning

### Gold — safe to lead with

Required:
- all Silver requirements
- one SGLang PD study
- one regression gate example
- one profiler-backed optimization artifact
- one public writeup
- one upstream issue or PR

Safe wording:
- compact inference-performance lab
- measured PD tradeoff analysis
- rollout-safe performance tooling
- profiler-backed optimization note

### Platinum — strongest version

Required:
- all Gold requirements
- one routing study
- one topology / communication study
- consistently clean docs with caveats and negative results

Safe wording:
- stronger systems-judgment and infra-adjacent story

## Exact application gate

Do not make this repo the lead project in applications until:
- Silver is complete at minimum

Do not expect meaningful inbound interest from inference / performance hiring teams until:
- Gold is complete

## Final check before public posting

Answer yes to all:
- Can I link one real artifact pack directly?
- Can I show the exact repro command?
- Can I name the hardware, model, and workload without hand-waving?
- Can I point to one bounded claim and one caveat?
- Can a skeptical engineer verify the result in under two minutes?

If any answer is no, keep the repo framed as in progress.

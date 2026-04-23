# Proof Readiness Checklist

Checked: 2026-04-23

This document is the public-claim gate.
If the answer is "no" for the current stage, downgrade the wording in:
- `README.md`
- `docs/10-application-packaging.md`
- resume bullets
- LinkedIn copy

## Current default state

The repo is currently at Silver:
- stored real M2 artifact pack present at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/`
- M3 packaging outputs present at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_report.md` and `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/m3_summary.md`
- completed GuideLLM cross-check present at `artifacts/m2-qwen-l40s-modal-chat-short-20260423-r2/guidellm/`
- bounded measured claims are now safe for one Modal-hosted `L40S x1`, `Qwen/Qwen2.5-1.5B-Instruct`, and `chat_short` setup
- `configs/backends/vllm_modal_example.yaml` remains a placeholder example, while `configs/backends/vllm_modal_m2_qwen_l40s.yaml` is the current concrete repo config for the stored Modal baseline
- the current hero artifact records `git_dirty: true`, and the GuideLLM cross-check uses a synthetic token summary rather than exact trace replay
- Modal cold-start probe timeouts are not failures by themselves, but the evidence path requires a subsequent clean probe before the benchmark run
- the next required work order is M4 SGLang + PD baseline

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
- one real vLLM artifact pack checked into or otherwise directly accessible from repo state
- one official-tool or GuideLLM cross-check saved next to that artifact
- one README measured-findings section grounded in those files
- one artifact-index entry pointing to those files

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

# Application Packaging

Checked: 2026-04-22

This document turns the project into something usable in applications.

Pair it with:
- `docs/17-job-mapping-2026.md` for current role-language alignment
- `docs/18-artifact-index.md` for current public artifact linking
- `docs/19-proof-readiness-checklist.md` for the current safe-to-claim gate

## Reality check

A strong project can:
- improve recruiter response rates
- make your resume bullets much stronger
- create better technical interview discussions
- help offset missing direct inference-role experience

A strong project usually cannot, by itself, fully replace years of proven production experience.

So the goal is not magic. The goal is to create the strongest possible **evidence bundle**.

## Readiness bars

### Bronze — not ready
You have plans, scaffolding, or synthetic-only runs.

Do not lead with the repo.

### Silver — interview-supporting
You have:
- one real vLLM artifact pack
- one official-tool or GuideLLM cross-check
- one README section with measured numbers
- one artifact-index entry

This is enough to include the project, but it should not be the top line of your candidacy yet.

### Gold — strong portfolio centerpiece
You have:
- all Silver requirements
- one SGLang PD study
- one regression gate example
- one profiler-backed optimization artifact
- one public writeup
- one upstream issue / PR
- clean reproduction commands

At Gold, the repo can absolutely be a lead project in applications.

For the specific target roles of this repo, Gold is the practical minimum bar before expecting meaningful inbound interest.

### Platinum — exceptional independent signal
You have:
- all Gold requirements
- one routing policy study
- one topology / communication study
- consistently strong docs
- clear negative results and caveats
- optional extra backend only if it adds clarity

This is the strongest version of the project.

## Current public framing at Bronze

Use wording like:

> Repo-in-progress. The codebase has real-mode vLLM benchmark wiring, official metrics ingestion, runtime metadata capture, external HTTPS target support, and a GuideLLM cross-check path, but the current checkout does not include a stored real M2 artifact pack yet. Claims should stay at capability level until a fresh real run and saved cross-check outputs are restored.

Current note:
- `configs/backends/vllm_modal_example.yaml` is a placeholder example and must be filled with a live endpoint plus real hardware metadata before any public M2 claim is safe

If that sentence becomes false, update it immediately.

## GitHub copy

README headline:

> Production-style LLM inference performance lab for reproducible serving benchmarks, prefill/decode tradeoff analysis, regression gating, routing decisions, and profiler-backed optimization.

Short repository description:

> Compact inference-performance lab focused on reproducible artifacts, measured serving tradeoffs, and rollout-safe performance tooling.

README findings block template after the first real artifact:

At Silver, one bounded measured finding plus one clear caveat is enough.
Expand to three findings only after more real artifacts exist.

> Highlighted findings
>
> - vLLM baseline: On `[hardware]` with `[model]` and `[workload]`, the baseline sustained `[throughput metric]` at `[tail latency metric]`, with official `/metrics` captured and an external cross-check preserved next to the artifact.
> - PD tradeoff: On `[hardware]` with `[model]` and `[workload]`, PD changed `[metric]` by `[x%]` while worsening or leaving `[other metric]` unchanged; the writeup states exactly where it helped and where it did not.
> - Regression gate: A candidate configured with `[fault / bad setting]` was blocked by the compare engine due to `[metrics]`, preventing a bad rollout.

## LinkedIn copy

Headline:

> ML Systems / Inference Performance Engineer | Reproducible LLM serving benchmarks, PD tradeoff analysis, profiling, and rollout-safe performance tooling

Project description:

> Built an open-source LLM serving performance lab focused on real backend bring-up, workload-shaped benchmarking, official metrics ingestion, profiler-backed optimization, regression gating, and cache-aware routing. The repo is packaged as a compact inference-systems evidence bundle rather than a generic AI platform.

## Resume bullet templates

Use bullets like:
- Built a production-style LLM inference performance lab around **vLLM** and **SGLang** to evaluate mixed-workload serving, prefill/decode tradeoffs, routing, and regression gating.
- Implemented reproducible benchmark harnesses and artifacted comparisons for TTFT, ITL, p95/p99 latency, throughput, queue depth, cache usage, and error rate across controlled serving experiments.
- Added a compare engine with config-driven PASS/WARN/FAIL thresholds and synthetic fault injection to catch serving regressions before rollout.
- Produced profiler-backed performance analysis and a documented optimization study with before/after measurements and caveats.
- Contributed an upstream issue / PR with minimal repro based on findings from the project.

## Recruiter pitch

Use a short version:
> I built a reproducible LLM inference performance lab around vLLM and SGLang, focused on realistic serving benchmarks, PD tradeoff studies, routing decisions, regression gating, and profiler-backed optimization.

## Hiring-manager pitch

Use:
> The repo is meant to look like a compact inference-performance team project, not a toy benchmark wrapper. It has real backend bring-up, workload-shaped evaluation, rollout logic, profiling, and public writeups tied to reproducible artifacts.

For physical-AI / infra-adjacent roles, add:
> I also used it to study placement and operational tradeoffs under constrained hardware, not just model latency in isolation.

## Engineer interview demo flow

In 5 minutes:
1. show the current highlighted finding in the README and its caveat
2. open one artifact directory
3. show one compare output
4. show one profiler-backed report section
5. show one upstream issue or PR

## What not to say

Do not say:
- “I built an inference platform”
- “I recreated what frontier labs do”
- “This is production-ready”
- “It supports many backends” as the headline
- “I do kernel engineering” unless the profiler-backed optimization artifact is genuinely low-level and defensible
- “I improved latency / throughput” unless the README can point to the exact baseline and artifact
- “I built routing logic” unless the routing study exists and includes explicit reason codes and a counterexample case
- “I shipped profiler-backed optimization” unless the trace, candidate, and before/after comparison are all checked in

Say:
- “I used this repo to study serving tradeoffs and package the results as reproducible artifacts.”

## Not yet safe to claim

Do not upgrade the public wording past the current artifact state.

Not yet safe at Bronze:
- measured performance wins
- real serving-stack credibility
- routing effectiveness
- regression protection
- profiler-backed depth

Only safe after the corresponding artifact exists:
- real vLLM benchmark claims after the first artifact pack plus cross-check
- PD claims after the PD study
- rollout-safety claims after the compare engine blocks a known-bad candidate
- optimization claims after the profiler-backed note
- routing claims after the routing study

## Final checklist before applications

You should be able to answer yes to all:
- Can I show one real benchmark artifact pack?
- Can I show one honest PD study?
- Can I show one regression gate blocking a bad candidate?
- Can I show one profiler-backed bottleneck analysis?
- Can I show one routing or placement decision with explicit tradeoffs?
- Can I reproduce the highlighted results?
- Can I point to one upstream contribution?
- Is the README above-the-fold focused on measured findings, not architecture?

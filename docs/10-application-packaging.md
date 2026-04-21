# Application Packaging

This document turns the project into something usable in applications.

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
- one SGLang PD study
- one regression gate example
- one README section with measured numbers

This is enough to include the project, but it should not be the top line of your candidacy yet.

### Gold — strong portfolio centerpiece
You have:
- all Silver requirements
- one profiler-backed optimization artifact
- one routing policy study
- one public writeup
- one upstream issue / PR
- clean reproduction commands

At Gold, the repo can absolutely be a lead project in applications.

### Platinum — exceptional independent signal
You have:
- all Gold requirements
- one topology / communication study
- consistently strong docs
- clear negative results and caveats
- optional extra backend only if it adds clarity

This is the strongest version of the project.

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

## Engineer interview demo flow

In 5 minutes:
1. show the 3 highlighted findings in the README
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

Say:
- “I used this repo to study serving tradeoffs and package the results as reproducible artifacts.”

## Final checklist before applications

You should be able to answer yes to all:
- Can I show one real benchmark artifact pack?
- Can I show one honest PD study?
- Can I show one regression gate blocking a bad candidate?
- Can I show one profiler-backed bottleneck analysis?
- Can I reproduce the highlighted results?
- Can I point to one upstream contribution?
- Is the README above-the-fold focused on measured findings, not architecture?

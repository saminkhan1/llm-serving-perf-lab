# llm-serving-perf-lab — hiring-signal repo-start pack

This pack is optimized for one goal:

> turn the project into **high-signal proof of work** for mid-level LLM inference, workload, performance, and ML systems roles.

It is not a generic project brief. It is a **repo-start pack** that forces the work toward:
- measurable wins
- reproducibility
- profiler evidence
- realistic workload evaluation
- safe rollout logic
- public artifacts that engineers can trust

## What changed versus the earlier pack

This version intentionally:
- **narrows the story** to LLM inference systems / performance engineering
- makes **vLLM + SGLang** the required backends
- makes **TensorRT-LLM optional** until later
- moves **observability, regression, and profiling earlier**
- requires **workload-shaped benchmarks**, not just synthetic traces
- defines **exact proof artifacts** you must have before using the repo as a portfolio centerpiece
- adds **application packaging** and **public writeup** guidance

## Who this is for

Use this pack if you want the eventual repo to read well to:
- frontier-lab hiring managers
- inference / systems engineers
- recruiter screens
- technically serious startups working on LLM serving or performance

## How to use this pack

1. Read `docs/00-start-here.md`
2. Read `docs/01-hiring-signal-charter.md`
3. Follow `docs/03-milestones.md` in order
4. Give coding agents only the current milestone from `docs/07-agent-work-orders.md`
5. Do not market the project publicly until at least **Portfolio Checkpoint A** is complete
6. Do not apply using this repo as a lead artifact until the **Gold bar** in `docs/10-application-packaging.md` is met

## Non-goals

This project must **not** become:
- a training / post-training project
- a paper crawler
- a research agent
- a generic dashboard SaaS
- a new inference engine
- a broad "frontier AI" portfolio repo with weak depth

## Folder overview

- `docs/` — the source-of-truth project contract
- `examples/configs/` — minimal starter configs
- `kickoff/` — first message to send to your coding agent
- `AGENTS.md` — root instructions for the repo

## Core principle

The repo should look like:

> a small but real inference-performance lab with benchmark discipline, routing and rollout logic, profiler-backed optimization work, and clean reproducibility.

Not like:

> an overbuilt abstraction layer with little measured evidence.

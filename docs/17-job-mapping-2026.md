# Job Mapping 2026

Checked: 2026-04-21

This appendix translates current public role language into repo evidence priorities.

It is intentionally dated.
Refresh it when the linked role pages or serving docs materially change.

## Current read

The repo is directionally aligned with mid-level inference / performance hiring, but it is not yet market-clearing.

Until the repo has:
- one real vLLM artifact pack
- one official-tool or GuideLLM cross-check
- one regression gate example
- one profiler-backed note

it still reads more like strong M2 scaffolding plus disciplined docs than completed inference-performance proof.

## Public anchor roles

Use these current public role families as the main market map:
- OpenAI Model Inference
- OpenAI Workload Enablement
- Anthropic Inference
- Anthropic Cloud Inference
- Anthropic Inference Deployment
- Anthropic Inference Routing and Performance
- Google Software Engineer III, AI/ML, GPU Inference, Optimization

Links live in `docs/12-reference-links.md`.

## Requirement matrix

| Role family | Public language visibly rewards | Repo artifact that answers it | Current repo read |
| --- | --- | --- | --- |
| OpenAI Model Inference | High-volume, low-latency, high-availability serving; bottleneck visibility; latency / throughput / efficiency work; GPU-stack familiarity | Real vLLM artifact pack with official metrics and one bottleneck deep dive | Partial until M2 produces a real run |
| OpenAI Workload Enablement | Repeatable benchmarks, stress tests, regression detection, actionable outputs, whole-system characterization | Workload-shaped benchmark harness plus compare engine and fault injection | Strong design fit, but public proof is still missing |
| Anthropic Inference | Intelligent request routing, fleet orchestration, heterogeneous accelerators, compute efficiency | Routing study with reason codes and a bounded claim | Planned, not yet public |
| Anthropic Cloud Inference | Cross-cloud serving, routing, observability, cost/performance judgment | Real backend artifact plus routing / placement writeup with explicit caveats | Partial |
| Anthropic Inference Deployment | Deployment automation, capacity-aware rollout logic, validation pipelines, observability | Regression gate that blocks a known-bad candidate and records why | Planned, not yet public |
| Anthropic Inference Routing and Performance | Cache-aware routing, throughput extraction, latency SLO protection, routing decisions under load | Offline routing study plus explicit counterexample cases | Planned, not yet public |
| Google GPU Inference Optimization | Large-scale inference latency / throughput optimization, accelerators, ML infrastructure, debugging and documentation | Quantization / tensor-parallel / memory-tuning artifact plus profiler-backed note | Stretch-aligned once M6 and later artifacts exist |

## Priority order implied by the market

Do these before more backend breadth:
1. Real vLLM baseline artifact pack
2. Official-tool or GuideLLM cross-check
3. SGLang PD study
4. Regression gate with visible bad-candidate failure
5. Profiler-backed optimization note

Only after those should the repo spend meaningful time on:
- live routing / control plane work
- topology studies
- optional TensorRT-LLM breadth

## Public-claim rule

Map every public sentence to one artifact.

Examples:
- "real serving-stack bring-up" maps to the first vLLM artifact pack
- "validated benchmark result" maps to the saved cross-check output
- "rollout-safe performance tooling" maps to the compare engine artifact
- "profiler-backed optimization" maps to the trace-backed note
- "routing judgment" maps to the routing study

If no artifact exists yet, downgrade the wording.

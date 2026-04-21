# Technical Writeup Template

Use this template for public posts or internal-style notes.

## Title

Use a concrete title such as:
- Studying Prefill/Decode Disaggregation on Small-Scale LLM Serving
- Building a Regression Gate for LLM Serving Config Changes
- Finding a Hot Path in vLLM/SGLang with Profiling

Avoid vague titles like:
- My frontier AI lab project
- Building an inference platform
- Thoughts on LLM performance

## 1. Problem

State the narrow question.

Example:
> Can PD reduce tail latency on a mixed short/long workload on my tested setup, and what tradeoffs appear in throughput and operational complexity?

## 2. Setup

Include:
- backend and version
- model
- hardware
- driver / CUDA relevant versions
- workload
- seed
- configs compared

## 3. Method

Explain:
- baseline
- candidate
- metrics collected
- number of runs
- how results were compared
- whether profiling was used

## 4. Results

Show:
- one summary table
- one or two plots
- key deltas
- interpretation

## 5. What changed the most

Call out the main insight, not every number.

## 6. Caveats

Must include:
- hardware limits
- model limits
- workload limits
- instability or noise if relevant
- what you did not test

## 7. Reproduction

Provide:
- repo commit or tag
- config paths
- exact command
- artifact ids

## 8. Takeaway

One paragraph:
- what you learned
- what holds on this setup
- what you would test next

## Good tone

Use:
- measured
- precise
- caveated
- engineering-first

Avoid:
- hype
- sweeping claims
- “10x” language without hard proof
- “production-ready” unless that is actually true

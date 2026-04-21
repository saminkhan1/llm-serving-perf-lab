# Proof Artifacts

These are the artifacts that actually create hiring signal.

## The rule

Before applying anywhere with this repo as a lead project, you should have at least:

- 2 **hero artifacts**
- 2 **supporting artifacts**
- 1 **public artifact**
- 1 **upstream artifact**

## Hero artifact 1 — baseline serving artifact pack

### Must include
- backend and version
- model
- hardware
- workload
- metrics table
- command used
- report
- caveats

### Why it matters
This is the first proof that the repo is not just scaffolding.

### Common failure mode
A result screenshot without a full reproduction path.

---

## Hero artifact 2 — PD tradeoff study

### Must include
- non-PD baseline
- PD setup
- workload description
- TTFT and ITL / TPOT
- throughput context
- explicit statement of where PD helped and where it did not

### Good claim
“On this workload and setup, PD improved tail decode latency while not improving throughput.”

### Bad claim
“PD is faster.”

---

## Supporting artifact 1 — routing policy win

### Must include
- baseline policy
- candidate policy
- allowed signals
- reason-coded decisions
- metric deltas
- one failure or counterexample case

### Good signal
Shows systems judgment and load-balancing intuition.

---

## Supporting artifact 2 — regression gate block

### Must include
- baseline artifact id
- candidate artifact id
- threshold config
- PASS / WARN / FAIL result
- explanation of failing metrics
- synthetic fault example

### Good signal
Looks like deployment and launch engineering maturity.

---

## Supporting artifact 3 — profiler-backed optimization

### Must include
- baseline profile
- candidate profile
- bottleneck hypothesis
- implemented change
- before/after metrics
- caveat about limits of generalization

### Good signal
Shows depth, not just orchestration.

---

## Supporting artifact 4 — communication/topology study

### Must include
- hardware topology assumptions
- worker-count or concurrency axis
- communication-related explanation
- limits of the tested setup

### Good signal
Shows whole-system thinking.

---

## Public artifact — technical writeup

### Must include
- problem statement
- environment
- methodology
- results
- caveats
- reproduction path

### Preferred topic order
1. PD tradeoff study
2. profiler-backed hot-path study
3. routing policy win

---

## Upstream artifact

Acceptable forms:
- merged PR
- serious issue with minimal repro
- design note that maintainers can act on
- documentation improvement backed by tested behavior

Weak forms:
- typo fix only
- “great project!” issue
- vague bug report with no repro

---

## README above-the-fold checklist

The repo README must show, near the top:
- one-sentence repo description
- three measured wins or findings
- supported backends
- quickstart
- reproduction commands
- link to writeup(s)
- link to upstream contribution

## Evidence discipline

Every artifact used in interviews must answer:
1. what exactly was measured?
2. on what hardware and model?
3. against what baseline?
4. how do I reproduce it?
5. what are the limitations?

If it cannot answer those five, do not lead with it.

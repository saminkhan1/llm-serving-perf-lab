# Risk Register

## Risk 1 — overbuilding the platform

### Symptom
You keep adding abstractions, configs, and adapters without producing portfolio-grade artifacts.

### Correction
Stop. Finish the next proof artifact before any new infrastructure.

---

## Risk 2 — too much TensorRT-LLM too early

### Symptom
You spend weeks on setup breadth before the repo has a single strong vLLM or SGLang result.

### Correction
Return TensorRT-LLM to stretch-only status until Gold readiness.

---

## Risk 3 — synthetic-only evaluation

### Symptom
All workloads are toy distributions with no workload-shaped benchmark.

### Correction
Add at least one ShareGPT-like or equivalent serving-shaped profile before making claims.

---

## Risk 4 — no profiler depth

### Symptom
You have many benchmark results but no convincing root-cause analysis.

### Correction
Move profiling earlier. Treat one profiler-backed note as mandatory.

---

## Risk 5 — README reads like a framework

### Symptom
The repo homepage lists modules and features before results.

### Correction
Rewrite above-the-fold to show findings, artifacts, and repro commands first.

---

## Risk 6 — weak claim discipline

### Symptom
You start making broad statements like “PD is better” or “routing improves performance” with no setup boundaries.

### Correction
Always bind claims to hardware, model, workload, and config.

---

## Risk 7 — no upstream signal

### Symptom
The work stays entirely private to your repo.

### Correction
Open an issue, docs fix, or PR as soon as you find something real and reproducible.

---

## Risk 8 — the repo becomes “agent-branded”

### Symptom
The public narrative focuses on automation, agents, or experiment loops instead of inference systems evidence.

### Correction
Keep the bounded sweep runner as a supporting feature, not the main story.

---

## Risk 9 — no early checkpoint

### Symptom
You keep postponing the first polished artifact.

### Correction
Treat Portfolio Checkpoint A as a hard gate.

---

## Risk 10 — hidden negative results

### Symptom
You omit caveats or failure cases to make the writeup cleaner.

### Correction
Negative results increase credibility. Keep them.

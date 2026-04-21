# Signal Scorecard

Score the repo honestly before using it heavily in applications.

Use 0 to 5 for each category.

## 1. Reproducibility

0 — no runnable artifact path  
1 — partial commands only  
2 — one runnable result with missing metadata  
3 — multiple results reproducible with some manual steps  
4 — highlighted results reproducible from clean docs and commands  
5 — clean reproduction path, artifact index, and stable compare workflow

## 2. Serving-stack credibility

0 — no real backend  
1 — fake / dry-run only  
2 — one backend partially working  
3 — one backend real and stable  
4 — vLLM and SGLang both working with real runs  
5 — strong backend coverage plus clear versioning and caveats

## 3. Workload realism

0 — toy prompts only  
1 — synthetic distributions only  
2 — some workload shaping but weak explanation  
3 — synthetic plus one realistic workload-shaped profile  
4 — multiple workload classes with interference / burstiness / prefix reuse  
5 — workload methodology is clearly explained and limitations are explicit

## 4. Observability and regression discipline

0 — no clear metrics  
1 — basic latency only  
2 — metrics exist but are inconsistent  
3 — stable metrics plus compare engine  
4 — pass/warn/fail gate and visible synthetic faults  
5 — results read like launch / release engineering artifacts

## 5. Performance depth

0 — no profiler evidence  
1 — benchmark numbers only  
2 — profiler exists but weakly interpreted  
3 — one profiler-backed bottleneck analysis  
4 — one profiler-backed optimization artifact  
5 — optimization artifact plus communication/topology study

## 6. Routing and systems judgment

0 — no routing logic  
1 — naive routing only  
2 — routing ideas with weak evaluation  
3 — offline simulator with reason codes  
4 — live routing hook with policy versioning and fallbacks  
5 — clear routing win plus limitations and failure cases

## 7. Public legibility

0 — planning docs only  
1 — weak README  
2 — readable repo but findings buried  
3 — measured results visible above the fold  
4 — strong README plus one writeup  
5 — README, writeup, artifact index, and upstream link all work together

## 8. OSS / external signal

0 — none  
1 — informal discussion only  
2 — vague issue or low-value change  
3 — serious issue with minimal repro  
4 — useful docs or code contribution  
5 — merged PR or clearly impactful public issue / design note

## Interpretation

### 0–15
Not ready to lead with.

### 16–24
Useful supporting project, but not strong enough as a centerpiece.

### 25–32
Strong application project.

### 33–40
Very strong independent signal for the target role family.

## Gold target

Aim for at least:
- total score >= 28
- no category below 3
- Performance depth >= 4
- Public legibility >= 4
- OSS / external signal >= 3

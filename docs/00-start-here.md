# Start Here

This is the **hiring-signal-first** version of the plan.

The previous pack had strong taste, but it still gave too much equal weight to all features. That is risky. Frontier-lab engineers and hiring managers care much more about a few things than about feature count.

## The project must optimize for these signals first

### 1. Reproducible serving evidence
One real backend, one real workload, one stable artifact pack beats five partially wired integrations.

### 2. Observability and regression discipline
If the repo cannot explain why a run is better or worse, it will not read like real systems work.

### 3. Profiler-backed depth
At least one artifact must show you can move from symptoms to root cause to measured improvement.

### 4. Production-style judgment
Canary logic, fault injection, reason-coded routing, and explicit caveats all matter.

### 5. Public legibility
A repo only helps if a stranger can understand the win in under two minutes.

## What changed from the earlier plan

- Required backends changed from **vLLM + SGLang + TensorRT-LLM** to **vLLM + SGLang**, with TensorRT-LLM as a stretch goal after the first strong proof artifacts exist.
- Observability, regression, and profiling now happen **before** most control-plane breadth.
- Workload evaluation must include at least one **workload-shaped** benchmark, not only synthetic distributions.
- The repo is now explicitly optimized for **mid-level inference / performance roles**, not a generic “frontier lab” label.
- Public packaging is part of the plan from the beginning, not an afterthought.

## The first rule

Do not ask “what else can this platform do?”

Ask:

> what is the smallest set of artifacts that would make a skeptical inference engineer say this person knows how to do real systems work?

## Before writing any code

Read these in order:
1. `docs/01-hiring-signal-charter.md`
2. `docs/02-role-alignment.md`
3. `docs/03-milestones.md`
4. `docs/04-proof-artifacts.md`

## The four most important constraints

1. **No breadth before proof**
2. **No custom metrics when official metrics exist**
3. **No public claims without reproducible artifacts**
4. **No “agent” positioning as the main story**

## Minimum bar before public posting

Do not publicize the repo as a portfolio centerpiece until all of the following exist:
- one clean vLLM benchmark artifact pack
- one clean SGLang PD comparison
- one regression gate example
- one profiler-backed note
- one README section with measured results and reproduction commands

Anything less is too easy to dismiss as planning or scaffolding.

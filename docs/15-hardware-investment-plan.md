# Hardware Investment Plan

Checked: 2026-04-21

This document exists to keep hardware spending tightly aligned with the hiring-signal goals of the repo.

## First principle

Do not spend against abstract “future scale.”

Spend only when the next milestone needs real hardware to produce a proof artifact that hiring managers actually care about.

## Pricing references to keep in view

Checked: 2026-04-21

Modal's public pricing currently advertises a Starter plan with `$30 / month` in free credit and roughly:
- L4 at about `$0.80 / hour`
- A10 at about `$1.10 / hour`
- A100 40 GB at about `$2.10 / hour`
- A100 80 GB at about `$2.50 / hour`
- H100 at about `$3.95 / hour`

Google Cloud pricing needs more careful reading:
- some pages show GPU-only prices that do **not** include the rest of the VM bill
- accelerator-optimized machine families often bundle GPU cost into the machine-type price instead of a simple add-on row
- disk, network, and storage still matter for the real bill

Do not compare a Modal per-second rate directly to a Google Cloud GPU-only line item and call that a cost comparison. Use the current source pages in `docs/12-reference-links.md` and estimate the full run cost for the exact machine shape you will use.

## Target proof bar

The practical target for this repo is:
- Gold in `docs/10-application-packaging.md`

For this role family, the minimum convincing artifact set is:
- one real vLLM artifact pack
- one official-tool or GuideLLM cross-check
- one honest SGLang PD study
- one regression gate artifact
- one profiler-backed optimization artifact
- one upstream issue / PR
- one public writeup with reproduction commands

Routing or placement work is still valuable, but it should follow the first proof set instead of blocking it.

## Recommended local setup

Use the Apple Silicon laptop as the daily development machine for:
- code changes
- tests
- docs
- local dry-runs
- artifact inspection

Do not plan around the Intel laptop for anything beyond light editing or verification.

## Recommended cloud strategy

Treat cloud spend as an evidence budget, not a platform bet.

## Provider order

Use providers in this order:
1. local laptop for all non-GPU milestone work
2. Modal free monthly credits for the smallest real GPU-backed runs that can produce a proof artifact
3. Google Cloud trial / promotional credits for larger or more infrastructure-shaped GPU work
4. cheapest marketplace NVIDIA GPUs only after the free-credit paths stop being efficient

This ordering is about expected value, not ideology.

Use the free-credit platforms first when they can answer the next milestone question without distorting the repo story.

### Cheapest repeatable paid path

Use marketplace NVIDIA GPUs and switch shapes by milestone instead of renting a larger machine all the time.

Preferred pattern:
1. one 24 GB class GPU for single-backend and profiling milestones
2. one 2-GPU host for PD, live-routing, and topology milestones

### Preferred GPU class

For budget-sensitive execution, prefer:
- NVIDIA RTX 3090 class GPUs on marketplace providers

Reasons:
- widely available
- low hourly cost
- CUDA + profiler support
- enough for the repo’s current small-model serving story

If promotional cloud credits are available, L4-based instances are also valid and cleaner operationally, but they should be treated as a credit opportunity rather than the baseline plan.

## Provider-specific guidance

### Modal

Use Modal when:
- you can finish the next run within the available monthly free credits
- the milestone only needs one clean real run or a narrow repeat run
- the platform’s managed serving model does not undermine the artifact story

Best uses in this repo:
- first M2 real vLLM baseline attempt
- narrow single-GPU reruns for M2 or M5
- experimentation that benefits from quick bring-up and official vLLM / SGLang examples
- cases where the public pricing and free-credit model let you get one proof artifact faster than managing a VM

Avoid using Modal as the primary platform when:
- you need extended iterative benchmarking over many hours
- you need to control the machine more directly
- you need profiler workflows that are better matched to raw VM access
- the free-credit monthly cadence would slow the repo down

### Google Cloud credits

Use Google Cloud credits when:
- you need more control than Modal provides
- you need 2-GPU work on one host for PD or topology studies
- you want the artifact to look more like direct systems bring-up on rented infrastructure
- you still have enough credits left that the run is effectively free out of pocket

Best uses in this repo:
- M2 if Modal is awkward or its credits are exhausted
- M4 PD study
- M8 live routing / control plane
- M11 topology / communication study

Treat GCP as the preferred free-credit path for:
- multi-step milestone execution
- 2-GPU milestones
- artifacts where lower-level infrastructure control improves credibility
- you need the full machine bill to look like direct systems work, not just managed endpoint bring-up

### Cheapest paid marketplace GPUs

Use marketplace providers when:
- both Modal and GCP credits are exhausted or would introduce more friction than savings
- you need the lowest cash cost for repeat runs
- you are ready to rent exactly the GPU shape the next milestone needs

Best uses in this repo:
- repeat M2 / M6 / M10 iterations on 1x 24 GB GPUs
- short M4 / M8 / M11 runs on 2x GPU hosts

This remains the default cash-paid fallback because it is usually the lowest total cost.

## Milestone-to-hardware map

### M0–M1

Hardware:
- local laptop only

Spend:
- $0

### M2 — vLLM baseline + official metrics

Hardware:
- 1x NVIDIA 24 GB class GPU

Good fits:
- L40S
- RTX 3090
- L4
- A10G

Do not spend on multi-GPU hardware here.

Provider order:
1. Modal free credits
2. Google Cloud credits
3. marketplace paid GPU

Why:
- this is the best milestone for cheap or free single-GPU bring-up
- you only need one strong real artifact, not a long-lived cluster

Current default first attempt:
- provider: Modal free credits
- GPU: `1x L40S`
- model: `Qwen/Qwen2.5-1.5B-Instruct`

Why this default:
- it avoids Hugging Face gating friction from gated alternatives
- it keeps the first proof focused on serving discipline, not model-access troubleshooting
- it preserves headroom to switch hardware or provider later if M2 needs a narrower rerun

### M3 — Portfolio Checkpoint A

Hardware:
- reuse the M2 run outputs

Spend:
- $0 additional if the M2 artifact is already strong

### M4 — SGLang + PD baseline

Hardware:
- 2 GPUs on one host

Good fits:
- 2x RTX 3090
- 2x L4
- 2x A10G

This is the first point where a 2-GPU bill is justified.

Provider order:
1. Google Cloud credits
2. Modal only if remaining monthly credits and GPU availability make the run cheap enough
3. marketplace paid 2-GPU host

Why:
- this milestone needs a cleaner multi-GPU story and enough runtime for comparison work
- GCP is the better free-credit fit for this than Modal

### M5 — regression gate + fault injection

Hardware:
- reuse existing M2/M4 artifact paths
- occasional rerun on 1 GPU if needed

Keep spend low.

Provider order:
1. local machine once prior artifacts exist
2. Modal for a narrow rerun if needed
3. Google Cloud credits only if the rerun must match a prior environment exactly

### M6 — profiling integration

Hardware:
- 1x NVIDIA GPU with Nsight support

Good fit:
- same 24 GB class GPU used in M2

No need to upgrade hardware unless the optimization study demands it.

Provider order:
1. Google Cloud credits if you need direct infrastructure control for profiler work
2. marketplace paid GPU
3. Modal only for lighter-weight profiling where its supported tooling is sufficient

Why:
- this milestone is where low-level control begins to matter more than free monthly convenience

### M7 — routing simulator

Hardware:
- local machine is enough once traces exist

Spend:
- $0 additional unless you need fresh traces

### M8 — live routing / control plane

Hardware:
- 2 GPUs on one host

Provider order:
1. Google Cloud credits
2. marketplace paid 2-GPU host
3. Modal only if the serving setup remains simple and credit burn is acceptable

### M9 — bounded sweep runner

Hardware:
- reuse the cheapest valid shape from M2 or M4 depending on scope

Do not turn M9 into an excuse for broad compute spend.

Provider order:
1. local or prior artifacts first
2. cheapest matching provider for a bounded rerun

### M10 — kernel/runtime optimization artifact

Hardware:
- 1x NVIDIA GPU with profiler support

Upgrade only if the optimization target clearly needs more memory or a different architecture.

Provider order:
1. Google Cloud credits if available
2. marketplace paid GPU
3. avoid Modal unless the profiler workflow stays within its supported model

### M11 — communication/topology artifact

Hardware:
- 2 GPUs on one host

This milestone is the main justification for limited extra spend if the goal is stronger alignment to workload / infra / physical-AI-adjacent roles.

Provider order:
1. Google Cloud credits
2. marketplace paid 2-GPU host
3. skip until later if neither is affordable

## Suggested credit consumption plan

### Phase 1 — no-cost local work

Use:
- local laptop only

Milestones:
- M0
- M1
- code-complete prep for M2

### Phase 2 — Modal first-use path

Use:
- Modal free monthly credits

Milestones:
- first M2 real baseline attempt
- one narrow rerun if the first result is close but not portfolio-grade

Repo path:
- deploy the official Modal vLLM example first with the chosen first-pass model and GPU
- fill in `configs/backends/vllm_modal_example.yaml`
- run `make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml`
- run `make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml`
- point `base_url` at the deployed Modal endpoint root
- run `make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml`
- run the GuideLLM cross-check into `artifacts/<run_id>/guidellm`

Stop using Modal for the main path when:
- the monthly free credit would force artificial delays
- repeated reruns are needed
- the artifact requires more direct systems control

### Phase 3 — Google credit-heavy path

Use:
- Google Cloud credits

Milestones:
- remaining M2 work if needed
- M4
- M6 if profiler workflow benefits from direct host control
- M8
- M11 if pursuing Platinum-strength signal

Use GCP before paid marketplace time whenever the credits are still available and the milestone benefits from a cleaner infrastructure story.

### Phase 4 — cheapest paid fallback

Use:
- marketplace NVIDIA GPU rentals

Milestones:
- any remaining M2 / M4 / M6 / M8 / M10 / M11 runs after credit exhaustion

The goal here is not to move platforms randomly.
The goal is to preserve cash while keeping the artifact story coherent.

## Budget bands

These are planning bands, not promises.

Interpret them as:
- GPU-hour guidance, not guaranteed invoice totals
- enough spend to produce the next proof artifact, not a general experimentation budget
- numbers that should be rechecked against the live pricing pages before purchase

### Minimum viable budget

Goal:
- reach Gold as cheaply as possible

Plan:
- marketplace provider
- 1x GPU for M2 / M6 / M10
- short 2x GPU rentals for M4 / M8

Budget:
- about $150

This requires discipline, few reruns, and no broad sweeps.

### Safer budget

Goal:
- reach Gold with room for reruns, cleaner hosts, and one extra artifact pass

Budget:
- about $250

This is the recommended planning number.

### Stretch budget

Goal:
- Gold plus a stronger M11 topology study and extra repro runs

Budget:
- about $400

Only spend beyond this if the next artifact clearly improves the hiring signal.

## What not to buy

Do not buy for this repo:
- a desktop GPU machine unless you already planned to own one for other reasons
- long-lived multi-GPU reservations before M4 is ready in code
- exotic accelerators before the core vLLM + SGLang artifacts exist
- large cloud commitments tied to one provider

## Spend gate

Before each paid run, answer yes to all:
- Is the next milestone code-complete enough to make the run likely to produce a real artifact?
- Is this spend tied to one of the required proof artifacts?
- Do I know exactly what question the run is answering?
- Will the result change the README / writeup / application story?

If any answer is no, stop and fix the repo first.

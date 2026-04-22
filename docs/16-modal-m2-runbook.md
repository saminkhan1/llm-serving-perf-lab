# Modal M2 Runbook

Use this runbook to produce the first real M2 artifact pack against a Modal-hosted vLLM server.

## Scope

This is still M2 work:
- one real vLLM benchmark artifact pack
- one official-tool cross-check
- bounded claims tied to one tested model, workload, and hardware setup

Do not treat this as M3, M4, or a production deployment guide.

## Prerequisites

You need:
- a Modal account
- a deployed vLLM endpoint based on Modal's official vLLM example
- GuideLLM installed in the environment where you will run the cross-check

Official references:
- Modal vLLM example: https://modal.com/docs/examples/vllm_inference
- Modal web endpoints: https://frontend.modal.com/docs/guide/webhooks
- Modal autoscaling: https://frontend.modal.com/docs/guide/scale
- Modal GPU guide: https://modal.com/docs/guide/gpu
- vLLM production metrics: https://docs.vllm.ai/en/latest/usage/metrics/
- vLLM metrics design / deprecations: https://docs.vllm.ai/en/stable/design/metrics/
- GuideLLM README: https://github.com/vllm-project/guidellm

## Current default bring-up choice

Use this default unless a concrete blocker appears:
- start from Modal's official vLLM example
- use `1x L40S`
- use `Qwen/Qwen2.5-1.5B-Instruct` for the first real M2 proof

Why this default:
- it is a narrow single-GPU path that is good enough for one trustworthy baseline
- it keeps the repo default aligned with the first real M2 proof target instead of relying on a separate override
- it keeps the first proof focused on endpoint health, metrics exposure, and artifact quality
- it keeps the hardware claim honest by pinning the Modal app to a single replica during the benchmark

Do not optimize beyond this default before the first real artifact exists.

## 1. Fill in the backend config

Start from `configs/backends/vllm_modal_example.yaml`.

Replace:
- `base_url` with the deployed Modal endpoint root such as `https://your-workspace--example-vllm-inference-serve.modal.run`
- `metrics.scrape_endpoint` with the same endpoint plus `/metrics`
- `model_id` with the model actually served by the deployed Modal app
- `hardware` with the actual tested GPU shape and count for the deployment you are measuring

Notes:
- `base_url` must be the endpoint root, not `/v1`
- the repo derives `/health`, `/version`, and `/v1/completions` from `base_url`
- the simplest M2 path is an endpoint without extra proxy auth headers
- for the default first run, set `model_id` to `Qwen/Qwen2.5-1.5B-Instruct` and `hardware.accelerator` to `L40S`

## 2. Validate the repo-side wiring

Run:

```bash
uv run lsp validate-config configs/backends/vllm_modal_example.yaml
uv run lsp render-vllm-launch --backend-config configs/backends/vllm_modal_example.yaml
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml
make verify-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
```

`verify-m2` here validates repo logic and plan rendering. It does not itself prove the remote server is healthy.

## 3. Check local/operator readiness

Before touching the remote endpoint, make sure the config no longer contains example placeholders and that required local tools are available:

```bash
make check-m2-readiness BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
```

That check is expected to block until:
- `base_url` and `metrics.scrape_endpoint` are no longer example values
- `hardware.accelerator` is no longer a placeholder
- `guidellm` is installed in `PATH`
- Modal CLI is installed and has a current profile when `hardware.provider` is `modal`

## 4. Run the zero-GPU GuideLLM preflight

Before spending money on Modal again, run the local smoke test for the cross-check path:

```bash
make smoke-guidellm
```

What this proves:
- the repo renders a GuideLLM command that the installed CLI accepts
- the repo executes that command with explicit output filenames
- the repo forces a safer local GuideLLM multiprocessing profile
- the repo can complete and clean up the external cross-check path against a fake local backend
- the repo rejects a zero-exit GuideLLM run if the saved artifact is incomplete

If this step fails, stop there and fix the local orchestration problem first.

## 5. Probe the deployed target

Before the expensive run, check that the deployed server is reachable and exposing official metrics:

```bash
make probe-m2 BACKEND_CONFIG=configs/backends/vllm_modal_example.yaml
```

That probe checks `/health`, `/version`, and `/metrics`.
It does not submit workload traffic or claim a benchmark result.

## 6. Produce the real M2 run

Choose a run id and execute:

```bash
make reproduce \
  RUN=m2-real \
  REPRO_BACKEND=configs/backends/vllm_modal_example.yaml \
  REPRO_WORKLOAD=configs/workloads/chat_short.yaml \
  REPRO_RUN_ID=<run_id>
```

That command should write an artifact directory under `artifacts/<run_id>`.

## 7. Produce the official-tool cross-check

Run GuideLLM against the same deployed endpoint:

```bash
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/<run_id>/guidellm \
  --execute
```

Preserve the GuideLLM outputs next to the main run artifact.
The repo also writes `repo_cross_check_plan.json`, `repo_cross_check_execution.json`, and stdout/stderr logs into the GuideLLM output directory for auditability.

Notes:
- the repo now runs GuideLLM with an explicit `--backend openai_http` and `--model`
- the repo writes `benchmark.json` and `benchmark.csv` explicitly because GuideLLM 0.6.0 does not reliably resolve bare `json` or `csv` aliases with `--output-dir`
- the repo exports `GUIDELLM__MP_CONTEXT_TYPE=spawn` and `GUIDELLM__MAX_WORKER_PROCESSES=1` during execution to avoid a local shutdown hang seen with the default process model on macOS
- the repo now validates the saved GuideLLM artifact and fails the step if request counts do not close cleanly, even when the GuideLLM process exits `0`
- the repo's required metric contract is intentionally narrow and follows current documented core vLLM production metrics rather than deprecated throughput gauges or non-documented timeout / GPU-memory counters
- if the cross-check still fails, stop the Modal app immediately after collecting the failure logs instead of leaving it running

## 8. What must exist before moving to M3

Do not advance until all of the following are true:
- the run completed end to end against the real Modal-hosted server
- the artifact includes metadata, metrics, report, repro command, and caveats
- the GuideLLM cross-check completed and its outputs are saved
- the README wording stays bounded to the tested hardware, model, and workload

## Known caveats

- Modal web endpoints can cold-start; for cleaner results, use Modal settings that keep one container warm when needed
- the repo-owned Modal benchmark script now pins `max_containers=1` and guards against duplicate local `vllm serve` launches so the single-GPU benchmark does not silently scale out mid-run
- this repo does not claim that Modal is the production target, only that it is a valid way to produce the first M2 proof artifact
- if you enable endpoint auth that requires custom HTTP headers, the current repo path will need additional adapter support
- the zero-GPU preflight still requires local sockets and a downloadable tokenizer for the chosen model if that tokenizer is not already cached

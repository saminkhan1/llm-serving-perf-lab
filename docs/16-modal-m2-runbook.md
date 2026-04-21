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
- Modal web endpoints: https://modal.com/docs/guide/webhooks
- Modal GPU guide: https://modal.com/docs/guide/gpu
- vLLM metrics: https://docs.vllm.ai/en/stable/usage/metrics/
- GuideLLM README: https://github.com/vllm-project/guidellm

## 1. Fill in the backend config

Start from `configs/backends/vllm_modal_example.yaml`.

Replace:
- `base_url` with the deployed Modal endpoint root such as `https://your-workspace--example-vllm-inference-serve.modal.run`
- `metrics.scrape_endpoint` with the same endpoint plus `/metrics`
- `model_id` with the model actually served by the deployed Modal app

Notes:
- `base_url` must be the endpoint root, not `/v1`
- the repo derives `/health`, `/version`, and `/v1/completions` from `base_url`
- the simplest M2 path is an endpoint without extra proxy auth headers

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

## 3. Produce the real M2 run

Choose a run id and execute:

```bash
make reproduce \
  RUN=m2-real \
  REPRO_BACKEND=configs/backends/vllm_modal_example.yaml \
  REPRO_WORKLOAD=configs/workloads/chat_short.yaml \
  REPRO_RUN_ID=<run_id>
```

That command should write an artifact directory under `artifacts/<run_id>`.

## 4. Produce the official-tool cross-check

Run GuideLLM against the same deployed endpoint:

```bash
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/<run_id>/guidellm \
  --execute
```

Preserve the GuideLLM outputs next to the main run artifact.

## 5. What must exist before moving to M3

Do not advance until all of the following are true:
- the run completed end to end against the real Modal-hosted server
- the artifact includes metadata, metrics, report, repro command, and caveats
- the GuideLLM cross-check completed and its outputs are saved
- the README wording stays bounded to the tested hardware, model, and workload

## Known caveats

- Modal web endpoints can cold-start; for cleaner results, use Modal settings that keep one container warm when needed
- this repo does not claim that Modal is the production target, only that it is a valid way to produce the first M2 proof artifact
- if you enable endpoint auth that requires custom HTTP headers, the current repo path will need additional adapter support

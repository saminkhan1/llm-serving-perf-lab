# Artifact Index

Use this file to point reviewers at the smallest number of artifacts needed to audit the repo's current proof state.

## Current hero artifacts

No checked-in hero artifacts are present in this checkout right now.

That means:
- there is no current in-repo M2 report path that a reviewer can open directly
- there is no current in-repo GuideLLM cross-check output to audit directly
- README and application-facing wording must stay below Silver until a fresh real run is stored again

## Next artifact expected here

The next entry should be created immediately after a fresh bounded M2 run writes both:
- `artifacts/<run_id>/...`
- `artifacts/<run_id>/guidellm/...`

Use `docs/18-artifact-index-template.md` once those files exist.

Target question for the next hero artifact:
- Can the repo produce one real, reproducible, cross-checked M2 baseline on a single-GPU Modal deployment?

Target reproduction commands:
```bash
make reproduce RUN=m2-real REPRO_BACKEND=configs/backends/vllm_modal_example.yaml REPRO_WORKLOAD=configs/workloads/chat_short.yaml REPRO_RUN_ID=<run_id>
uv run lsp cross-check-guidellm \
  --backend-config configs/backends/vllm_modal_example.yaml \
  --workload-config configs/workloads/chat_short.yaml \
  --output-dir artifacts/<run_id>/guidellm \
  --execute
```

Do not restore Silver wording until the resulting artifact directory and cross-check outputs are present and auditable from repo state.

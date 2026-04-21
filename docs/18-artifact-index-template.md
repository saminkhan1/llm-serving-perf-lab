# Artifact Index Template

Use this template once the repo has real proof artifacts worth linking above the fold.

The point is speed of audit:
- a reviewer should see the question
- the measured result
- the exact repro command
- the caveats

without digging through the whole repo.

## Required columns

Every index entry should include:
- artifact id
- milestone
- status: hero / supporting / public / upstream
- question answered
- hardware
- model
- workload
- baseline and candidate identifiers when applicable
- exact repro command
- primary report link
- raw data links
- main caveat

## Table template

| Artifact ID | Milestone | Status | Question Answered | Hardware | Model | Workload | Repro Command | Primary Report | Raw Data | Caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `m2-<run_id>` | M2 | hero | Replace with the exact benchmark question | Replace | Replace | Replace | `make reproduce RUN=m2-real ...` | `artifacts/<run_id>/report.md` | `artifacts/<run_id>/metrics.parquet` | Bound to tested hardware / model / workload |

## Per-artifact summary block

Use one block like this below the table for each hero artifact:

### `<artifact-id>`

Question:
- What exact uncertainty did this run resolve?

Finding:
- One sentence only, with the hardware, model, workload, and metric named explicitly.

Reproduction:
```bash
make reproduce RUN=<run-or-config> ...
```

Files:
- `artifacts/<run_id>/run.json`
- `artifacts/<run_id>/report.md`
- `artifacts/<run_id>/scorecard.json`
- `artifacts/<run_id>/metrics.parquet`

Caveats:
- Hardware-specific limitation
- Workload-specific limitation
- Anything that prevents broader generalization

## Update rule

Update the index immediately after:
- M2 real baseline
- M4 PD study
- M5 regression gate example
- M6 profiler-backed note
- M13 public release packaging

If an artifact changes what is safe to claim publicly, update `README.md` and `docs/19-proof-readiness-checklist.md` in the same patch.

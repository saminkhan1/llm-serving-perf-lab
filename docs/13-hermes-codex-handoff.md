# Hermes + Codex Handoff

## Goal

Use Hermes as the orchestrator and messaging layer.
Use Codex as the coding worker.
Keep the repo docs on disk as the durable source of truth.

## Repo setup

```bash
mkdir -p ~/repos/llm-serving-perf-lab/docs
cd ~/repos/llm-serving-perf-lab
git init
```

Copy:
- this pack's `docs/` directory into repo `docs/`
- this pack's `AGENTS.md` into repo root

## Operating pattern

- Hermes receives the request from Telegram or CLI
- Hermes delegates coding work to Codex
- Codex works only inside the repo workspace
- milestone boundaries remain strict
- Hermes should interrupt the user only when blocked by missing access, destructive ambiguity, or hard contract conflict

## Required behavior

The coding agent must:
- read local docs first
- execute only one work order at a time
- report changed files, commands, tests, artifact paths, caveats, and next work order
- avoid jumping to future milestones
- prefer smaller, measurable implementations

## Recommended first invocation

Execute Work order A only.

## Recommended second invocation

After reviewing Work order A, execute Work order B.

## Approval policy

The agent may ask for user help only if blocked by:
1. missing credentials or access
2. destructive action with irreversible risk
3. ambiguity that would change the repo contract

Everything else should be handled autonomously.

## Required completion payload

Each completed work order must report:
1. changed files
2. summary of behavior
3. commands run
4. test results
5. artifact paths produced
6. remaining risks
7. exact next recommended work order

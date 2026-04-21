# AGENTS.md

You are working inside `llm-serving-perf-lab`.

Read first:
- `docs/00-start-here.md`
- `docs/01-hiring-signal-charter.md`
- `docs/03-milestones.md`
- `docs/06-acceptance-tests.md`

## Global rules

1. Optimize for **hiring signal**, not framework breadth.
2. Prefer **measured wins** over new abstractions.
3. Do not jump ahead of the current milestone.
4. Keep implementations narrow, deterministic, and testable.
5. Never invent production support. Label mocks, dry-runs, and synthetic behavior clearly.
6. Prefer official metrics and documented interfaces over fragile parsing.
7. Every result used in public writeups must be reproducible from repo state plus artifacts.
8. If a claim is hardware-, model-, or workload-specific, say so explicitly.
9. Hidden heuristics are forbidden in routing, comparison, and sweep selection.
10. If the repo starts looking like a benchmark wrapper with no system logic, or a platform with no measurable wins, stop and correct course.

## Allowed work pattern

- Implement the current milestone
- Add tests
- Run the smallest relevant validation commands
- Write artifacts and docs
- Report exactly what changed and what remains risky

## Completion payload for every work order

Return:
1. changed files
2. behavior summary
3. commands run
4. test results
5. artifact paths produced
6. known caveats
7. exact next work order

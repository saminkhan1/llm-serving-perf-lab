from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lsp.artifacts.models import validate_artifact_dir
from lsp.backends import BackendLifecycleError
from lsp.benchmark_runner import BenchmarkRunFailed, run_benchmark
from lsp.config.loader import load_config, validate_example_configs
from lsp.config.models import BackendConfig, ValidationError, WorkloadConfig
from lsp.fake_run import run_fake_benchmark
from lsp.m2_scaffolding import (
    build_guidellm_cross_check_plan,
    build_vllm_launch_plan,
    check_m2_readiness,
    execute_guidellm_cross_check,
    format_plan_json,
    probe_vllm_target,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lsp", description="LLM serving perf lab CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate-config",
        help="Validate a single YAML config.",
    )
    validate_parser.add_argument("path", type=Path)

    subparsers.add_parser("validate-examples", help="Validate repo example configs.")

    fake_run_parser = subparsers.add_parser(
        "fake-run",
        help="Run the synthetic M0 fake backend path and write an artifact bundle.",
    )
    fake_run_parser.add_argument("--backend-config", type=Path, required=True)
    fake_run_parser.add_argument("--workload-config", type=Path, required=True)
    fake_run_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    fake_run_parser.add_argument("--run-id", type=str, default=None)

    run_parser = subparsers.add_parser(
        "run",
        help="Run the benchmark harness in dry-run mode or through the M2 vLLM adapter path.",
    )
    run_parser.add_argument("--backend-config", type=Path, required=True)
    run_parser.add_argument("--workload-config", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    run_parser.add_argument("--run-id", type=str, default=None)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Use the synthetic M1 harness path. "
            "Without this flag the M2 real backend adapter path is used."
        ),
    )

    validate_artifact_parser = subparsers.add_parser(
        "validate-artifact", help="Validate an emitted artifact directory."
    )
    validate_artifact_parser.add_argument("run_dir", type=Path)

    launch_plan_parser = subparsers.add_parser(
        "render-vllm-launch",
        help="Render the repo-owned vLLM launch or attach plan from a backend config.",
    )
    launch_plan_parser.add_argument("--backend-config", type=Path, required=True)

    cross_check_parser = subparsers.add_parser(
        "cross-check-guidellm",
        help="Render or execute the external GuideLLM cross-check plan for an M2 workload.",
    )
    cross_check_parser.add_argument("--backend-config", type=Path, required=True)
    cross_check_parser.add_argument("--workload-config", type=Path, required=True)
    cross_check_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    cross_check_parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the rendered GuideLLM command. Fails if GuideLLM is not installed.",
    )

    probe_parser = subparsers.add_parser(
        "probe-vllm-target",
        help="Probe a reachable vLLM target for health, runtime metadata, and official metrics.",
    )
    probe_parser.add_argument("--backend-config", type=Path, required=True)

    readiness_parser = subparsers.add_parser(
        "check-m2-readiness",
        help="Check whether repo config and local tools are ready for the final external M2 run.",
    )
    readiness_parser.add_argument("--backend-config", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-config":
        config = load_config(args.path)
        print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "validate-examples":
        results = validate_example_configs()
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0

    if args.command == "fake-run":
        bundle = run_fake_benchmark(
            backend_config_path=args.backend_config,
            workload_config_path=args.workload_config,
            output_dir=args.output_dir,
            run_id=args.run_id,
            argv=argv or sys.argv[1:],
        )
        print(str(bundle.run_dir))
        return 0

    if args.command == "run":
        try:
            bundle = run_benchmark(
                backend_config_path=args.backend_config,
                workload_config_path=args.workload_config,
                output_dir=args.output_dir,
                run_id=args.run_id,
                argv=argv or sys.argv[1:],
                dry_run=args.dry_run,
            )
        except BenchmarkRunFailed as exc:
            print(str(exc.bundle.run_dir), file=sys.stderr)
            print(str(exc), file=sys.stderr)
            return 1
        except ValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(str(bundle.run_dir))
        return 0

    if args.command == "validate-artifact":
        bundle = validate_artifact_dir(args.run_dir)
        print(json.dumps(bundle.metadata.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "render-vllm-launch":
        config = load_config(args.backend_config)
        if not isinstance(config, BackendConfig):
            raise ValidationError("render-vllm-launch requires a backend config")
        print(format_plan_json(build_vllm_launch_plan(config)))
        return 0

    if args.command == "cross-check-guidellm":
        backend = load_config(args.backend_config)
        workload = load_config(args.workload_config)
        if not isinstance(backend, BackendConfig):
            raise ValidationError("cross-check-guidellm requires a backend config")
        if not isinstance(workload, WorkloadConfig):
            raise ValidationError("cross-check-guidellm requires a workload config")
        plan = build_guidellm_cross_check_plan(
            backend=backend,
            workload=workload,
            output_dir=args.output_dir,
        )
        if args.execute:
            return execute_guidellm_cross_check(plan, cwd=Path.cwd())
        print(format_plan_json(plan))
        return 0

    if args.command == "probe-vllm-target":
        backend = load_config(args.backend_config)
        if not isinstance(backend, BackendConfig):
            raise ValidationError("probe-vllm-target requires a backend config")
        try:
            print(format_plan_json(probe_vllm_target(backend)))
            return 0
        except BackendLifecycleError as exc:
            print(
                format_plan_json(
                    {
                        "status": "failed",
                        "backend": backend.backend,
                        "model_id": backend.model_id,
                        "failure_reason": str(exc),
                    }
                ),
                file=sys.stderr,
            )
            return 1

    if args.command == "check-m2-readiness":
        backend = load_config(args.backend_config)
        if not isinstance(backend, BackendConfig):
            raise ValidationError("check-m2-readiness requires a backend config")
        report = check_m2_readiness(backend)
        print(format_plan_json(report))
        return 0 if report["status"] == "ready" else 1

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

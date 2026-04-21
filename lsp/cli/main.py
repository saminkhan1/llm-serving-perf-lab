from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lsp.artifacts.models import validate_artifact_dir
from lsp.config.loader import load_config, validate_example_configs
from lsp.fake_run import run_fake_benchmark


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

    validate_artifact_parser = subparsers.add_parser(
        "validate-artifact", help="Validate an emitted artifact directory."
    )
    validate_artifact_parser.add_argument("run_dir", type=Path)

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

    if args.command == "validate-artifact":
        bundle = validate_artifact_dir(args.run_dir)
        print(json.dumps(bundle.metadata.to_dict(), indent=2, sort_keys=True))
        return 0

    parser.error("unhandled command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

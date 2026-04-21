from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lsp.config.models import (
    BackendConfig,
    ConfigDocument,
    ExperimentConfig,
    PolicyConfig,
    ThresholdConfig,
    ValidationError,
    WorkloadConfig,
)


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValidationError(f"{path} must decode to a mapping")
    return raw


def load_config(path: Path) -> ConfigDocument:
    payload = _read_yaml(path)
    if "backend" in payload:
        return BackendConfig.from_dict(payload)
    if "workload_id" in payload:
        return WorkloadConfig.from_dict(payload)
    if "policy_id" in payload:
        return PolicyConfig.from_dict(payload)
    if "threshold_set_id" in payload:
        return ThresholdConfig.from_dict(payload)
    if "experiment_id" in payload:
        return ExperimentConfig.from_dict(payload)
    raise ValidationError(f"unable to infer config schema for {path}")


def validate_example_configs(root: Path | None = None) -> dict[str, str]:
    repo_root = root or Path.cwd()
    config_paths = sorted((repo_root / "configs").rglob("*.yaml"))
    results: dict[str, str] = {}
    for path in config_paths:
        config = load_config(path)
        results[str(path.relative_to(repo_root))] = config.kind
    return results

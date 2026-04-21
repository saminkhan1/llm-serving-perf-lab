PYTHON ?= python3
UV ?= uv
UV_CACHE_DIR ?= .uv-cache
UV_RUN = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run
UV_SYNC = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) sync --dev

.PHONY: install smoke validate-examples fake-run test lint format-check typecheck verify-m0

install:
	$(UV_SYNC)

smoke:
	$(UV_RUN) pytest tests/smoke/test_fake_run.py

validate-examples:
	$(UV_RUN) lsp validate-examples

fake-run:
	$(UV_RUN) lsp fake-run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/chat_short.yaml

test:
	$(UV_RUN) pytest -m "not gpu and not network"

lint:
	$(UV_RUN) ruff check .

format-check:
	$(UV_RUN) black --check .

typecheck:
	$(UV_RUN) mypy lsp

verify-m0: lint format-check typecheck test validate-examples

PYTHON ?= python3
UV ?= uv

.PHONY: validate-examples fake-run test lint format-check typecheck

validate-examples:
	$(UV) run lsp validate-examples

fake-run:
	$(UV) run lsp fake-run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/chat_short.yaml

test:
	$(UV) run pytest -m "not gpu and not network"

lint:
	$(UV) run ruff check .

format-check:
	$(UV) run black --check .

typecheck:
	$(UV) run mypy lsp

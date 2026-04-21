PYTHON ?= python3
UV ?= uv
UV_CACHE_DIR ?= .uv-cache
UV_RUN = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run
UV_SYNC = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) sync --dev

.PHONY: install smoke validate-examples fake-run run reproduce test lint format-check typecheck verify-m0 verify-m1

install:
	$(UV_SYNC)

smoke:
	$(UV_RUN) pytest tests/smoke/test_fake_run.py

validate-examples:
	$(UV_RUN) lsp validate-examples

fake-run:
	$(UV_RUN) lsp fake-run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/chat_short.yaml

run:
	$(UV_RUN) lsp run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/mixed_short_long.yaml --dry-run

reproduce:
	@test -n "$(RUN)" || (echo "usage: make reproduce RUN=m0|m1|configs/workloads/<profile>.yaml [REPRO_OUTPUT_DIR=artifacts] [REPRO_RUN_ID=<run_id>]" && exit 2)
	@case "$(RUN)" in \
		m0|fake) \
			cmd="$(UV_RUN) lsp fake-run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/chat_short.yaml --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts)" ;; \
		m1|dry-run) \
			cmd="$(UV_RUN) lsp run --backend-config configs/backends/vllm_dev.yaml --workload-config configs/workloads/mixed_short_long.yaml --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts) --dry-run" ;; \
		configs/workloads/*.yaml) \
			cmd="$(UV_RUN) lsp run --backend-config configs/backends/vllm_dev.yaml --workload-config $(RUN) --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts) --dry-run" ;; \
		*) \
			echo "unsupported RUN=$(RUN): use m0, m1, or configs/workloads/<profile>.yaml"; \
			exit 2 ;; \
	esac; \
	if [ -n "$(REPRO_RUN_ID)" ]; then \
		cmd="$$cmd --run-id $(REPRO_RUN_ID)"; \
	fi; \
	echo "$$cmd"; \
	eval "$$cmd"

test:
	$(UV_RUN) pytest -m "not gpu and not network"

lint:
	$(UV_RUN) ruff check .

format-check:
	$(UV_RUN) black --check .

typecheck:
	$(UV_RUN) mypy lsp

verify-m0: lint format-check typecheck test validate-examples

verify-m1: lint format-check typecheck test validate-examples

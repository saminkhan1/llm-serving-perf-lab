PYTHON ?= python3
UV ?= uv
UV_CACHE_DIR ?= .uv-cache
BACKEND_CONFIG ?= configs/backends/vllm_dev.yaml
UV_RUN = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run
UV_SYNC = UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) sync --extra dev
CLI = $(UV_RUN) python3 -m lsp.cli.main

.PHONY: install smoke smoke-guidellm validate-examples fake-run run reproduce test lint format-check typecheck verify-m0 verify-m1 verify-m2 check-m2-readiness probe-m2

install:
	$(UV_SYNC)

smoke:
	$(UV_RUN) pytest tests/smoke/test_fake_run.py

smoke-guidellm:
	$(UV_RUN) pytest tests/smoke/test_guidellm_cross_check.py

validate-examples:
	$(CLI) validate-examples

fake-run:
	$(CLI) fake-run --backend-config $(BACKEND_CONFIG) --workload-config configs/workloads/chat_short.yaml

run:
	$(CLI) run --backend-config $(BACKEND_CONFIG) --workload-config configs/workloads/mixed_short_long.yaml --dry-run

reproduce:
	@test -n "$(RUN)" || (echo "usage: make reproduce RUN=m0|m1|m2-real|configs/workloads/<profile>.yaml [REPRO_BACKEND=configs/backends/<backend>.yaml] [REPRO_OUTPUT_DIR=artifacts] [REPRO_RUN_ID=<run_id>] [REPRO_WORKLOAD=configs/workloads/<profile>.yaml]" && exit 2)
	@case "$(RUN)" in \
		m0|fake) \
			cmd="$(CLI) fake-run --backend-config $(or $(REPRO_BACKEND),$(BACKEND_CONFIG)) --workload-config configs/workloads/chat_short.yaml --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts)" ;; \
		m1|dry-run) \
			cmd="$(CLI) run --backend-config $(or $(REPRO_BACKEND),$(BACKEND_CONFIG)) --workload-config configs/workloads/mixed_short_long.yaml --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts) --dry-run" ;; \
		m2-real) \
			backend="$(or $(REPRO_BACKEND),$(BACKEND_CONFIG))"; \
			workload="$(or $(REPRO_WORKLOAD),configs/workloads/chat_short.yaml)"; \
			echo "M2 real-mode reproduction requires a reachable vLLM server or a local environment where the launch template can be turned into a real command."; \
			echo "Inspect the repo-owned launch plan with: $(CLI) render-vllm-launch --backend-config $$backend"; \
			echo "Inspect the external GuideLLM cross-check plan with: $(CLI) cross-check-guidellm --backend-config $$backend --workload-config $$workload"; \
			cmd="$(CLI) run --backend-config $$backend --workload-config $$workload --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts)" ;; \
		configs/workloads/*.yaml) \
			cmd="$(CLI) run --backend-config $(or $(REPRO_BACKEND),$(BACKEND_CONFIG)) --workload-config $(RUN) --output-dir $(or $(REPRO_OUTPUT_DIR),artifacts) --dry-run" ;; \
		*) \
			echo "unsupported RUN=$(RUN): use m0, m1, m2-real, or configs/workloads/<profile>.yaml"; \
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

verify-m2: lint format-check typecheck test validate-examples
	$(CLI) render-vllm-launch --backend-config $(BACKEND_CONFIG)
	$(CLI) cross-check-guidellm --backend-config $(BACKEND_CONFIG) --workload-config configs/workloads/chat_short.yaml

check-m2-readiness:
	$(CLI) check-m2-readiness --backend-config $(BACKEND_CONFIG)

probe-m2:
	$(CLI) probe-vllm-target --backend-config $(BACKEND_CONFIG)

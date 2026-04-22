from __future__ import annotations

import os
import socket
from pathlib import Path

import modal

APP_NAME = "lsp-m2-qwen-vllm"
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
GPU_TYPE = "L40S:1"
VLLM_PORT = 8000
MINUTES = 60
VLLM_PID_PATH = Path("/tmp/lsp_m2_vllm.pid")
VLLM_START_SENTINEL_PATH = Path("/tmp/lsp_m2_vllm.starting")


vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.19.0")
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

hf_cache_vol = modal.Volume.from_name("lsp-m2-huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("lsp-m2-vllm-cache", create_if_missing=True)

app = modal.App(APP_NAME)


@app.function(
    image=vllm_image,
    gpu=GPU_TYPE,
    max_containers=1,
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=VLLM_PORT, startup_timeout=10 * MINUTES)
def serve() -> None:
    import subprocess

    def port_is_listening() -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(1.0)
            return probe.connect_ex(("127.0.0.1", VLLM_PORT)) == 0

    def pid_is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    if port_is_listening():
        print(f"vLLM already listening on port {VLLM_PORT}; skipping relaunch.")
        return

    if VLLM_PID_PATH.exists():
        try:
            pid = int(VLLM_PID_PATH.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            VLLM_PID_PATH.unlink(missing_ok=True)
            VLLM_START_SENTINEL_PATH.unlink(missing_ok=True)
        else:
            if pid_is_alive(pid):
                print(f"vLLM process {pid} is already booting; skipping duplicate launch.")
                return
            VLLM_PID_PATH.unlink(missing_ok=True)
            VLLM_START_SENTINEL_PATH.unlink(missing_ok=True)

    try:
        VLLM_START_SENTINEL_PATH.touch(exist_ok=False)
    except FileExistsError:
        print("vLLM launch sentinel already exists; skipping duplicate startup hook.")
        return

    cmd = [
        "vllm",
        "serve",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--served-model-name",
        MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--uvicorn-log-level",
        "info",
        "--tensor-parallel-size",
        "1",
        "--gpu-memory-utilization",
        "0.9",
        "--max-num-seqs",
        "32",
        "--max-num-batched-tokens",
        "2048",
        "--enable-prefix-caching",
        "--no-enforce-eager",
    ]

    print("Launching vLLM:", " ".join(cmd))
    process = subprocess.Popen(cmd)
    VLLM_PID_PATH.write_text(str(process.pid), encoding="utf-8")


@app.local_entrypoint()
def main() -> None:
    print("Deploy with: modal deploy scripts/modal_vllm_m2.py")

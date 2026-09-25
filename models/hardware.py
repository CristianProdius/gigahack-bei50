"""Detect CUDA / print the GPU the train script will use."""

from __future__ import annotations

import os
import shutil
import subprocess


PROFILES = {
    "h100": {
        "segment": "yolo11m-seg.pt",
        "detect": "yolo11m.pt",
        "imgsz": 1280,
        "batch": 16,
    },
    "gpu16": {
        "segment": "yolo11s-seg.pt",
        "detect": "yolo11s.pt",
        "imgsz": 1024,
        "batch": 4,
    },
    "cpu": {
        "segment": "yolo11n-seg.pt",
        "detect": "yolo11n.pt",
        "imgsz": 640,
        "batch": 2,
    },
}


def nvidia_smi_name() -> str | None:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.check_output(
            [exe, "--query-gpu=name,memory.total", "--format=csv,noheader"],
            text=True,
            timeout=15,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return out.splitlines()[0].strip() if out else None


def torch_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return f"cuda:{torch.cuda.current_device()} ({torch.cuda.get_device_name(0)})"
    except Exception:
        pass
    return "cpu"


def resolve_profile(cli_profile: str | None = None) -> str:
    if cli_profile:
        return cli_profile
    env = os.environ.get("HARDWARE_PROFILE", "").strip().lower()
    if env in PROFILES:
        return env
    name = (nvidia_smi_name() or "").lower()
    if "h100" in name:
        return "h100"
    if "cuda" in torch_device():
        return "gpu16"
    return "cpu"


def report() -> dict:
    name = nvidia_smi_name()
    return {
        "nvidia_smi": name or "not found",
        "torch_device": torch_device(),
        "profile": resolve_profile(),
        "cuda_visible": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "gpu_host": os.environ.get("GPU_HOST") or os.environ.get("H100") or "",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(report(), indent=2))

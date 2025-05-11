import os
import sys
import platform
import json
from typing import Tuple

from livekit import rtc


def dylib_path(name: str) -> str:
    base_dir = os.path.dirname(__file__)
    resources_dir = os.path.join(base_dir, "resources")

    arch = platform.machine().lower()

    if sys.platform == "linux":
        ext = ".so"
    elif sys.platform == "darwin":
        ext = ".dylib"
    elif sys.platform == "win32":
        ext = ".dll"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    return os.path.join(resources_dir, f"{name}{ext}")

def resource_path(name: str) -> str:
    base_dir = os.path.dirname(__file__)
    resources_dir = os.path.join(base_dir, "resources")
    return os.path.join(resources_dir, name)

def plugin_path() -> str:
    return dylib_path("liblivekit_nc_plugin")

def dependencies_path() -> list[str]:
    return []

def model_path(model: str) -> str:
    if model == "nc":
        return resource_path("c8.f.s.026300-1.0.0_3.1.kef")
    elif model == "bvc":
        return resource_path("hs.c6.f.m.75df8f.kef")
    elif model == "bvct":
        return resource_path("inb.bvc.hs.c6.w.s.23cdb3.kef")
    else:
        raise RuntimeError(f"Unsupported model: {model}")

def NC() -> rtc.NoiseCancellationOptions:
    return rtc.NoiseCancellationOptions(str(id(sys.modules.get("livekit.plugins.noise_cancellation"))), {
        "modelPath": model_path("nc"),
    })

def BVC() -> rtc.NoiseCancellationOptions:
    return rtc.NoiseCancellationOptions(str(id(sys.modules.get("livekit.plugins.noise_cancellation"))), {
        "modelPath": model_path("bvc"),
    })

def BVCTelephony() -> rtc.NoiseCancellationOptions:
    return rtc.NoiseCancellationOptions(str(id(sys.modules.get("livekit.plugins.noise_cancellation"))), {
        "modelPath": model_path("bvct"),
    })

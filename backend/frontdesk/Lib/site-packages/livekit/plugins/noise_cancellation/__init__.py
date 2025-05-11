import sys
import os

from .plugin import plugin_path, dependencies_path, NC, BVC, BVCTelephony


__all__ = [
    "NC",
    "BVC",
    "BVCTelephony",
]

_loaded = False

def load():
    global _loaded
    if not _loaded:
        _loaded = True

        if "LK_OVERRIDE_OPENBLAS_NUM_THREADS" not in os.environ:
            os.environ["OPENBLAS_NUM_THREADS"] = "1"

        from livekit import rtc

        module = sys.modules[__name__]
        module_id = str(id(module))

        plugin = rtc.AudioFilter(module_id, plugin_path(), dependencies_path())

load()

from __future__ import annotations

from functools import lru_cache

from src.agent.runtime import Runtime, build_runtime


@lru_cache(maxsize=1)
def get_runtime() -> Runtime:
    # Single runtime for the process; okay for in-memory store demo.
    return build_runtime()


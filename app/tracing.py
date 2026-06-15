from __future__ import annotations

import os


try:
    from langfuse import observe

    LANGFUSE_AVAILABLE = True

except Exception:
    LANGFUSE_AVAILABLE = False

    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


class _LangfuseContext:
    def update_current_trace(self, *args, **kwargs):
        return None

    def update_current_observation(self, *args, **kwargs):
        return None


langfuse_context = _LangfuseContext()


def tracing_enabled() -> bool:
    return (
        LANGFUSE_AVAILABLE
        and bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
        and bool(os.getenv("LANGFUSE_SECRET_KEY"))
    )
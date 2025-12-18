from importlib import import_module


def __getattr__(name: str):
    """
    Lazy loader for Doctor submodules to avoid eager Qt imports during test collection.
    """
    if name in {"dashboard", "visit"}:
        mod = import_module(f"{__name__}.{name}")
        globals()[name] = mod  # cache for subsequent lookups
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

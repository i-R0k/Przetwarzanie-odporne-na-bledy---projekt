from .core import InMemoryStorage, Storage

_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = InMemoryStorage()
    return _storage

from .core import SQLAlchemyStorage, Storage

_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = SQLAlchemyStorage()
    return _storage

from __future__ import annotations

from typing import Any


def introspect_postgres(_dsn: str) -> Any:
    raise NotImplementedError(
        "PostgreSQL introspection requires optional dependencies and is not implemented in this MVP."
    )

"""Reporting helpers for the Python sidecar service."""

import json
import hashlib  # DEAD (py-unused-import): hashlib is never referenced in this module.
from typing import Iterable


def summarize(records: Iterable[dict]) -> dict:
    """Aggregate a stream of records. Live, called by the API layer."""
    total = 0
    count = 0
    unused_buffer = []  # DEAD (py-unused-local-var): assigned but never read.
    for record in records:
        total += int(record.get("amount", 0))
        count += 1
    return {"total": total, "count": count}


def format_label(value: int) -> str:
    """Render a label. Contains an unreachable tail after the return."""
    if value < 0:
        return "n/a"
    return json.dumps({"value": value})
    # DEAD (py-unreachable-branch): nothing after the return can run.
    return "unreachable"


def _legacy_normalize(rows):
    """DEAD (py-private-func): underscore-prefixed module-private helper with
    zero references anywhere in the project. Safe to delete."""
    return [str(r).strip().lower() for r in rows]

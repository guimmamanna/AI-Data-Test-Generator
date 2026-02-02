from __future__ import annotations

import re
from typing import Iterable

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s]{6,}$")


def is_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch(value.strip()))


def is_phone(value: str) -> bool:
    return bool(PHONE_RE.fullmatch(value.strip()))


def detect_pii(values: Iterable[str]) -> bool:
    for value in values:
        if is_email(value) or is_phone(value):
            return True
    return False

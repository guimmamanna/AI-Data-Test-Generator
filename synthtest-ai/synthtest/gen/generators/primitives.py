from __future__ import annotations

import datetime as dt
import math
import string
import uuid
from typing import List, Optional

from synthtest.util.rng import Rng


DEFAULT_DATE_START = dt.date(2020, 1, 1)
DEFAULT_DATE_END = dt.date(2025, 12, 31)
DEFAULT_DATETIME_START = dt.datetime(2020, 1, 1, 0, 0, 0)
DEFAULT_DATETIME_END = dt.datetime(2025, 12, 31, 23, 59, 59)


def generate_uuid(rng: Rng) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128)))


def generate_int(rng: Rng, min_val: int | None, max_val: int | None, distribution: str | None) -> int:
    min_val = 0 if min_val is None else int(min_val)
    max_val = 1000 if max_val is None else int(max_val)
    if distribution == "normal":
        mean = (min_val + max_val) / 2
        sigma = (max_val - min_val) / 6 or 1
        value = int(round(rng.gauss(mean, sigma)))
    elif distribution == "lognormal":
        value = int(round(_scaled_lognormal(rng, min_val, max_val)))
    else:
        value = rng.randint(min_val, max_val)
    return max(min_val, min(max_val, value))


def generate_decimal(rng: Rng, min_val: float | None, max_val: float | None, distribution: str | None) -> float:
    min_val = 0.0 if min_val is None else float(min_val)
    max_val = 1000.0 if max_val is None else float(max_val)
    if distribution == "normal":
        mean = (min_val + max_val) / 2
        sigma = (max_val - min_val) / 6 or 1.0
        value = rng.gauss(mean, sigma)
    elif distribution == "lognormal":
        value = _scaled_lognormal(rng, min_val, max_val)
    else:
        value = rng.uniform(min_val, max_val)
    return max(min_val, min(max_val, float(value)))


def generate_bool(rng: Rng) -> bool:
    return rng.random() < 0.5


def generate_date(rng: Rng, start: dt.date | None, end: dt.date | None) -> dt.date:
    start = start or DEFAULT_DATE_START
    end = end or DEFAULT_DATE_END
    delta_days = (end - start).days
    offset = rng.randint(0, max(delta_days, 0))
    return start + dt.timedelta(days=offset)


def generate_datetime(rng: Rng, start: dt.datetime | None, end: dt.datetime | None) -> dt.datetime:
    start = start or DEFAULT_DATETIME_START
    end = end or DEFAULT_DATETIME_END
    delta_seconds = int((end - start).total_seconds())
    offset = rng.randint(0, max(delta_seconds, 0))
    return start + dt.timedelta(seconds=offset)


def generate_text(rng: Rng, min_len: int | None, max_len: int | None) -> str:
    min_len = 5 if min_len is None else min_len
    max_len = 20 if max_len is None else max_len
    length = rng.randint(min_len, max_len)
    alphabet = string.ascii_letters + string.digits + " "
    return "".join(rng.choice(alphabet) for _ in range(length)).strip() or "text"


def generate_text_from_regex(rng: Rng, pattern: str) -> str:
    cleaned = pattern.strip()
    if cleaned.startswith("^"):
        cleaned = cleaned[1:]
    if cleaned.endswith("$"):
        cleaned = cleaned[:-1]

    tokens: List[str] = []
    i = 0
    while i < len(cleaned):
        char = cleaned[i]
        charset = None
        literal = None
        if char == "\\" and i + 1 < len(cleaned):
            esc = cleaned[i + 1]
            if esc == "d":
                charset = string.digits
            elif esc == "w":
                charset = string.ascii_letters + string.digits + "_"
            else:
                literal = esc
            i += 2
        elif char == "[":
            end = cleaned.find("]", i)
            if end == -1:
                literal = char
                i += 1
            else:
                charset = _expand_class(cleaned[i + 1 : end])
                i = end + 1
        else:
            literal = char
            i += 1

        repeat = 1
        if i < len(cleaned) and cleaned[i] == "{":
            end = cleaned.find("}", i)
            if end != -1:
                quant = cleaned[i + 1 : end]
                if "," in quant:
                    parts = [p.strip() for p in quant.split(",", 1)]
                    low = int(parts[0] or 0)
                    high = int(parts[1] or low)
                    repeat = rng.randint(low, max(low, high))
                else:
                    repeat = int(quant)
                i = end + 1

        for _ in range(repeat):
            if charset:
                tokens.append(rng.choice(charset))
            elif literal is not None:
                tokens.append(literal)

    return "".join(tokens)


def _expand_class(content: str) -> str:
    chars: List[str] = []
    i = 0
    while i < len(content):
        if i + 2 < len(content) and content[i + 1] == "-":
            start = ord(content[i])
            end = ord(content[i + 2])
            chars.extend(chr(c) for c in range(start, end + 1))
            i += 3
        else:
            chars.append(content[i])
            i += 1
    return "".join(chars)


def generate_enum(rng: Rng, values: List[str], weights: Optional[List[float]] = None) -> str:
    if not values:
        return ""
    if weights and len(weights) == len(values):
        return rng.choices(values, weights=weights, k=1)[0]
    return rng.choice(values)


def parse_date_range(raw: List[str | int | float] | None) -> tuple[dt.date | None, dt.date | None]:
    if not raw or len(raw) < 2:
        return None, None
    start = _to_date(raw[0])
    end = _to_date(raw[1])
    return start, end


def parse_datetime_range(raw: List[str | int | float] | None) -> tuple[dt.datetime | None, dt.datetime | None]:
    if not raw or len(raw) < 2:
        return None, None
    start = _to_datetime(raw[0])
    end = _to_datetime(raw[1])
    return start, end


def _to_date(value: str | int | float) -> dt.date:
    if isinstance(value, (int, float)):
        return dt.date.fromtimestamp(float(value))
    return dt.date.fromisoformat(str(value))


def _to_datetime(value: str | int | float) -> dt.datetime:
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(float(value))
    text = str(value)
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def _scaled_lognormal(rng: Rng, min_val: float, max_val: float) -> float:
    if min_val <= 0:
        min_val = 0.01
    if max_val <= min_val:
        max_val = min_val + 1.0
    value = rng.lognormvariate(0, 1)
    value = math.log1p(value)
    return min_val + (max_val - min_val) * (value / (1 + value))

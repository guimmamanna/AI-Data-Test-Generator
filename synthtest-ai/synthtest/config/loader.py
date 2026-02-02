from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from synthtest.schema.dsl import parse_schema
from synthtest.util.hashing import hash_config


class ConfigLoadError(ValueError):
    pass


def load_config(path: str | Path) -> tuple[Dict[str, Any], str]:
    path = Path(path)
    if not path.exists():
        raise ConfigLoadError(f"Config file not found: {path}")
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        raw = yaml.safe_load(raw_text)
    elif path.suffix.lower() == ".json":
        raw = json.loads(raw_text)
    else:
        raise ConfigLoadError("Config must be YAML or JSON")
    if not isinstance(raw, dict):
        raise ConfigLoadError("Config must be a mapping")
    return raw, hash_config(raw)


def load_schema_from_path(path: str | Path):
    raw, config_hash = load_config(path)
    schema = parse_schema(raw)
    return schema, config_hash

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class RunMetadata(BaseModel):
    dataset_id: str
    dataset_name: str
    seed: int
    mode: str
    timestamp: str
    config_hash: str
    format: str
    row_counts: Dict[str, int]
    tables: List[str]
    max_attempts: int

from __future__ import annotations

import json
import logging
from typing import Any, Dict


_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format="%(message)s")
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, message: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {"message": message, **fields}
    logger.info(json.dumps(payload, sort_keys=True))

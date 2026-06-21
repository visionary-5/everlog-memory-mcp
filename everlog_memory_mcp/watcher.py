from __future__ import annotations

import time
from collections.abc import Callable

from .config import Config
from .indexer import ScanResult, scan


def watch(
    config: Config,
    interval_seconds: int = 30,
    on_scan: Callable[[ScanResult], None] | None = None,
) -> int:
    interval_seconds = max(5, interval_seconds)
    try:
        while True:
            result = scan(config)
            if on_scan is not None:
                on_scan(result)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return 130

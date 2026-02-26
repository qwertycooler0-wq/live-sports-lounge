"""Bridge to the centralized scanner DB for SportRadar data."""

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

_SCANNER_ROOT = Path(os.environ.get(
    "SCANNER_ROOT", "C:/Claude-Coding/centralized-scanner"
))

if not _SCANNER_ROOT.is_dir():
    log.error(
        "Scanner root not found at %s — set SCANNER_ROOT env var to override",
        _SCANNER_ROOT,
    )

if str(_SCANNER_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCANNER_ROOT))

from client.db_reader import DBReader  # noqa: E402

DB_PATH = str(_SCANNER_ROOT / "scanner.db")

if not Path(DB_PATH).exists():
    log.warning("Scanner DB not found at %s — website will show no data until scanner runs", DB_PATH)

# Longer cache TTL for website (data freshness less critical than trading)
reader = DBReader(DB_PATH, cache_ttl_ms=500, stale_threshold_ms=60_000)

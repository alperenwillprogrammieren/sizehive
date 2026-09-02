"""Daily pipeline: fetch feeds, import, extract attributes, send notifications.

Meant to run unattended from a scheduler (Windows Task Scheduler / cron).
Chains the four steps that CLAUDE.md documents as the post-import sequence,
and writes a timestamped log to data/logs/daily_update.log so a failed
overnight run leaves a trail.

Why this exists at all: price history only accrues through repeated imports.
"Real discount" and "all-time low" (app/pricing/history.py) compare against
prices we observed being charged, so a catalogue imported once has nothing
to compare against — every article looks like it has always cost what it
costs today. One run per day is what turns that into a usable signal.

A failed fetch aborts the run rather than falling through to the import:
re-importing yesterday's file would append a second snapshot with identical
prices, which is noise in exactly the history this job exists to build.

Usage: python scripts/daily_update.py
"""
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.extract.run import run_extraction  # noqa: E402
from app.importers.fetch import fetch_awin_feed  # noqa: E402
from app.importers.run import run_import  # noqa: E402
from app.notify.run import run as run_notify  # noqa: E402

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs"
LOG_FILE = LOG_DIR / "daily_update.log"

logger = logging.getLogger("daily_update")


def _configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _step(name: str, fn) -> None:
    started = time.monotonic()
    logger.info("step start: %s", name)
    fn()
    logger.info("step done: %s (%.1fs)", name, time.monotonic() - started)


def main() -> int:
    _configure_logging()
    logger.info("=== daily update starting (%s) ===", datetime.now(timezone.utc).isoformat())

    try:
        _step("fetch awin feed", fetch_awin_feed)
    except Exception:
        logger.exception("fetch failed — aborting before import to keep price history clean")
        return 1

    try:
        _step("import feeds", run_import)
        _step("extract attributes", run_extraction)
        _step("notifications", run_notify)
    except Exception:
        logger.exception("daily update failed")
        return 1

    logger.info("=== daily update finished ok ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

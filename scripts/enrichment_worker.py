"""Long-lived enrichment worker: drain the queue, then poll for more.

Run it as a separate process alongside the API (local-first, no external broker):

    python scripts/enrichment_worker.py            # poll forever
    python scripts/enrichment_worker.py --once     # drain once and exit

It shares the same database as the API (BISE_DATABASE_URL), so jobs enqueued via
the API are picked up here.
"""

# ruff: noqa: E402  (sys.path bootstrap must run before the project imports)
from __future__ import annotations

import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from config.containers import Container
from config.logging import configure_logging, get_logger

from bise.presentation.workers.enrichment_queue import process_enrichment_jobs

logger = get_logger("enrichment_worker")


def main() -> None:
    parser = argparse.ArgumentParser(description="BISE enrichment queue worker")
    parser.add_argument("--once", action="store_true", help="drain the queue once and exit")
    parser.add_argument("--interval", type=float, default=5.0, help="poll interval in seconds")
    args = parser.parse_args()

    configure_logging(level="INFO", json_output=False)
    container = Container()

    if args.once:
        process_enrichment_jobs(container)
        return

    logger.info("enrichment_worker.started", interval=args.interval)
    while True:
        processed = process_enrichment_jobs(container)
        if processed == 0:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()

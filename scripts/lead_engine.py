"""Always-on lead engine: run due campaigns, then poll for more.

This is what makes BISE keep bringing you leads. Run it as a separate process
alongside the API (local-first, no external scheduler, no paid APIs):

    python scripts/lead_engine.py             # run due campaigns forever
    python scripts/lead_engine.py --once      # run everything due once, then exit

It shares the same database as the API (BISE_DATABASE_URL), so campaigns created
via the UI/API are picked up here. Each campaign runs at most once per tick, and
only when it is due (never-run, or past its interval).
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

from bise.presentation.workers.lead_engine import run_due_campaigns

logger = get_logger("lead_engine")


def main() -> None:
    parser = argparse.ArgumentParser(description="BISE always-on lead engine")
    parser.add_argument("--once", action="store_true", help="run due campaigns once and exit")
    parser.add_argument(
        "--interval", type=float, default=60.0, help="seconds to sleep between ticks"
    )
    args = parser.parse_args()

    configure_logging(level="INFO", json_output=False)
    container = Container()

    if args.once:
        run_due_campaigns(container)
        return

    logger.info("lead_engine.started", interval=args.interval)
    while True:
        run_due_campaigns(container)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

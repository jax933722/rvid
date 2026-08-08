"""Background worker: run every campaign that is due.

This is the always-on heartbeat behind continuous lead generation. On each tick
it asks the repository which campaigns are due (never-run, or past their
interval), runs one rotation step for each, and reports how many net-new leads
were surfaced. One failing campaign never stops the others.

It can run inside an API "run due" call or as a long-lived process (see
``scripts/lead_engine.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from config.containers import Container
from config.logging import get_logger

logger = get_logger(__name__)


def run_due_campaigns(container: Container, now: datetime | None = None) -> int:
    """Run one rotation step for each due campaign; return total new leads.

    New companies discovered by a run also change the search index, so the
    search cache is cleared when any leads were surfaced.
    """
    moment = now or datetime.now(UTC)
    with container.unit_of_work() as uow:
        due = list(uow.lead_campaigns.list_due(moment))
    campaign_ids = [c.id for c in due if c.id is not None]

    total_new = 0
    run = container.run_lead_campaign()
    for campaign_id in campaign_ids:
        try:
            result = run.execute(campaign_id)
            total_new += result.new_leads
        except Exception as exc:  # noqa: BLE001 - isolate one campaign's failure
            logger.warning("lead_engine.campaign_failed", campaign_id=campaign_id, error=str(exc))

    if total_new:
        container.search_cache().clear()  # newly discovered companies changed the index

    logger.info(
        "lead_engine.tick_completed",
        due=len(campaign_ids),
        new_leads=total_new,
    )
    return total_new

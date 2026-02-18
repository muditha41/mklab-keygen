"""APScheduler: run validation on the 26th of each month at 00:00 local time."""

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


def make_validation_trigger() -> CronTrigger:
    """Trigger at 00:00 local time on the 26th of every month."""
    return CronTrigger(day_of_month=26, hour=0, minute=0, second=0)


_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Return the global background scheduler (started when protect() runs)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
    return _scheduler


def schedule_monthly_validation(job_func: Callable[[], None]) -> None:
    """
    Schedule job_func to run on the 26th of each month at 00:00 local time.
    job_func will be called with no arguments.
    """
    sched = get_scheduler()
    sched.add_job(
        job_func,
        make_validation_trigger(),
        id="swaps_monthly_validation",
        replace_existing=True,
    )


def shutdown_scheduler() -> None:
    """Stop the global scheduler (e.g. at app exit)."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None

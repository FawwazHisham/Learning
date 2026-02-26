"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 5 — LESSON 3: SCHEDULING & ORCHESTRATION             ║
╚══════════════════════════════════════════════════════════════════╝

ORCHESTRATION = Running multiple bots in the right order at the right time.

OPTIONS:
  schedule    → Simple Python scheduling (single process)
  APScheduler → Advanced scheduling with persistence
  Celery      → Distributed task queue
  Airflow     → DAG-based workflow orchestration (enterprise)
  cron        → OS-level scheduling (simple, reliable)
"""

import os
import time
import datetime
import schedule     # pip install schedule
import logging
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler   # pip install apscheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore     # persistence

logger = logging.getLogger(__name__)


# ─── 1. SCHEDULE LIBRARY (Simple) ────────────────────────────────────────────

def schedule_examples():
    print("── 1. SCHEDULE LIBRARY ──────────────────────────────────────")
    code = '''
    import schedule
    import time

    # ── Define bot jobs
    def run_daily_report():
        print(f"[{datetime.datetime.now()}] Running daily report...")
        # invoke your bot here

    def run_hourly_sync():
        print("Running hourly sync...")

    def run_cleanup():
        print("Cleaning up temp files...")

    # ── Schedule jobs
    schedule.every().day.at("07:00").do(run_daily_report)           # 7am daily
    schedule.every(1).hours.do(run_hourly_sync)                     # Every hour
    schedule.every().monday.at("09:00").do(run_weekly_report)       # Monday 9am
    schedule.every(30).minutes.do(run_quick_check)                  # Every 30 min
    schedule.every().day.at("23:59").do(run_cleanup)                # End of day

    # ── Run scheduler loop
    print("Scheduler started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds

    # ── Run job immediately AND on schedule
    schedule.every().hour.do(run_hourly_sync)
    run_hourly_sync()  # Also run now
    '''
    print(code)


# ─── 2. APSCHEDULER (Advanced) ───────────────────────────────────────────────

def apscheduler_example():
    print("\n── 2. APSCHEDULER (Production Scheduler) ────────────────────")
    code = '''
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

    # ── Setup with SQLite persistence (jobs survive restarts)
    jobstores = {
        "default": SQLAlchemyJobStore(url="sqlite:///scheduler.db")
    }
    scheduler = BackgroundScheduler(jobstores=jobstores)

    # ── Add jobs
    # Cron schedule (every weekday at 8:30am)
    scheduler.add_job(
        func=run_morning_report,
        trigger=CronTrigger(day_of_week="mon-fri", hour=8, minute=30),
        id="morning_report",
        name="Morning Report Bot",
        replace_existing=True,          # Replace if job already exists
        misfire_grace_time=300,         # Run up to 5 min late if system was down
    )

    # Interval schedule
    scheduler.add_job(
        func=sync_crm_data,
        trigger=IntervalTrigger(minutes=15),
        id="crm_sync",
        name="CRM Data Sync",
        max_instances=1,                # Only one instance at a time
    )

    # One-time future job
    scheduler.add_job(
        func=send_reminder,
        trigger="date",
        run_date=datetime.datetime(2024, 12, 31, 23, 59),
        args=["Happy New Year!"],
    )

    # ── Start
    scheduler.start()
    print("APScheduler started")

    # ── Manage jobs
    jobs = scheduler.get_jobs()
    for job in jobs:
        print(f"  {job.id}: {job.name} — next run: {job.next_run_time}")

    scheduler.pause_job("morning_report")    # Pause a job
    scheduler.resume_job("morning_report")   # Resume it
    scheduler.remove_job("crm_sync")         # Remove permanently
    '''
    print(code)


# ─── 3. BOT PIPELINE (Sequential Orchestration) ──────────────────────────────

class BotPipeline:
    """
    Runs multiple bots in sequence.
    If one fails, pipeline can stop or continue based on config.
    """

    def __init__(self, name: str, stop_on_failure: bool = False):
        self.name = name
        self.stop_on_failure = stop_on_failure
        self.stages: list[dict] = []

    def add_stage(
        self,
        name: str,
        func: Callable,
        required: bool = True,
        *args, **kwargs
    ) -> "BotPipeline":
        """Add a stage to the pipeline."""
        self.stages.append({
            "name": name,
            "func": func,
            "required": required,
            "args": args,
            "kwargs": kwargs,
        })
        return self  # Allow chaining

    def run(self) -> dict:
        """Execute all pipeline stages."""
        results = {"pipeline": self.name, "stages": [], "success": True}
        start = time.time()

        print(f"\n{'═'*50}")
        print(f"  PIPELINE: {self.name}")
        print(f"  Stages: {len(self.stages)}")
        print(f"{'═'*50}")

        for i, stage in enumerate(self.stages, 1):
            stage_start = time.time()
            print(f"\n  [{i}/{len(self.stages)}] {stage['name']}...")

            try:
                output = stage["func"](*stage["args"], **stage["kwargs"])
                duration = time.time() - stage_start
                print(f"  ✓ {stage['name']} completed ({duration:.1f}s)")
                results["stages"].append({
                    "name": stage["name"],
                    "success": True,
                    "duration": round(duration, 2),
                    "output": str(output)[:100] if output else None,
                })
            except Exception as e:
                duration = time.time() - stage_start
                print(f"  ✗ {stage['name']} FAILED: {e}")
                results["stages"].append({
                    "name": stage["name"],
                    "success": False,
                    "duration": round(duration, 2),
                    "error": str(e),
                })

                if stage["required"] and self.stop_on_failure:
                    results["success"] = False
                    results["stopped_at"] = stage["name"]
                    break

        results["total_duration"] = round(time.time() - start, 2)
        results["success"] = all(s["success"] for s in results["stages"])

        print(f"\n{'─'*50}")
        print(f"  Pipeline {'PASSED' if results['success'] else 'FAILED'}")
        print(f"  Duration: {results['total_duration']}s")
        print(f"{'─'*50}")

        return results


# ─── 4. CRON REFERENCE ───────────────────────────────────────────────────────

CRON_REFERENCE = """
CRON SYNTAX:
  ┌─────────── minute (0-59)
  │ ┌───────── hour (0-23)
  │ │ ┌─────── day of month (1-31)
  │ │ │ ┌───── month (1-12)
  │ │ │ │ ┌─── day of week (0=Sun, 1=Mon, ..., 6=Sat)
  │ │ │ │ │
  * * * * *

EXAMPLES:
  0 7 * * 1-5     → 7:00am weekdays (Mon-Fri)
  30 8 * * *      → 8:30am daily
  0 */4 * * *     → Every 4 hours
  0 0 * * 0       → Midnight every Sunday
  0 9 1 * *       → 9am on 1st of every month
  */15 * * * *    → Every 15 minutes
  0 18 * * 5      → 6pm every Friday

CRON DEPLOYMENT:
  crontab -e       → Edit user's cron jobs

  # Entry format:
  30 7 * * 1-5  /usr/bin/python3 /home/user/bots/daily_report.py >> /logs/daily.log 2>&1

  # Use full paths for everything (cron has minimal PATH)
  # Redirect output to log files (>> appends, > overwrites)
"""
print(CRON_REFERENCE)


# ─── 5. DEPENDENCY-AWARE PIPELINE ────────────────────────────────────────────

def dependency_pipeline():
    print("\n── 5. DEPENDENCY-AWARE PIPELINE ─────────────────────────────")
    code = '''
    """
    DAG (Directed Acyclic Graph) pipeline.
    Some tasks only run after others complete.

    Stage A ─┬─► Stage B ─► Stage D
             └─► Stage C ─► Stage D
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    PIPELINE = {
        "extract_data":    {"deps": []},              # No dependencies
        "validate_data":   {"deps": ["extract_data"]}, # After extract
        "transform_data":  {"deps": ["validate_data"]},
        "load_to_db":      {"deps": ["transform_data"]},
        "generate_report": {"deps": ["load_to_db"]},
        "send_email":      {"deps": ["generate_report"]},
    }

    def run_dag_pipeline(pipeline: dict, max_parallel: int = 3):
        completed = set()
        results = {}

        while len(completed) < len(pipeline):
            # Find stages ready to run (all deps completed)
            ready = [
                name for name, config in pipeline.items()
                if name not in completed
                and all(dep in completed for dep in config["deps"])
            ]

            if not ready:
                break  # Deadlock or all done

            # Run ready stages in parallel
            with ThreadPoolExecutor(max_workers=min(len(ready), max_parallel)) as ex:
                futures = {ex.submit(run_stage, name): name for name in ready}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                        completed.add(name)
                        print(f"  ✓ Completed: {name}")
                    except Exception as e:
                        print(f"  ✗ Failed: {name}: {e}")
                        results[name] = {"success": False, "error": str(e)}
                        completed.add(name)  # Mark as done (even if failed)

        return results
    '''
    print(code)


# ─── 6. DEMO ──────────────────────────────────────────────────────────────────

def extract_step():
    print("    → Extracting data from API...")
    time.sleep(0.1)
    return {"records": 100}

def transform_step():
    print("    → Transforming records...")
    time.sleep(0.1)
    return {"records": 98}

def validate_step():
    print("    → Validating data quality...")
    time.sleep(0.05)
    return {"passed": True}

def load_step():
    print("    → Loading to database...")
    time.sleep(0.1)
    return {"inserted": 98}

def report_step():
    print("    → Generating report...")
    time.sleep(0.05)
    return "/tmp/report.pdf"


def run_demo():
    pipeline = (BotPipeline("Daily ETL Pipeline", stop_on_failure=True)
                .add_stage("Extract", extract_step)
                .add_stage("Transform", transform_step)
                .add_stage("Validate", validate_step)
                .add_stage("Load", load_step)
                .add_stage("Report", report_step, required=False))

    result = pipeline.run()
    print(f"\n  Result: {'SUCCESS' if result['success'] else 'FAILED'}")


if __name__ == "__main__":
    run_demo()
    schedule_examples()
    apscheduler_example()
    dependency_pipeline()
    print("\n  NEXT: python module_5_advanced/04_combining_tools.py")

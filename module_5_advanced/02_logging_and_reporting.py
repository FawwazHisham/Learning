"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 5 — LESSON 2: LOGGING & REPORTING                    ║
╚══════════════════════════════════════════════════════════════════╝

LOGGING IS THE EYES OF A BOT:
  ► Without logs, you can't debug issues
  ► Without reports, stakeholders don't know what ran
  ► Use structured logging for searchable/parseable logs

LEVELS:
  DEBUG    → Detailed internal info (for development)
  INFO     → Normal operations (what bot is doing)
  WARNING  → Something unexpected but bot continued
  ERROR    → Action failed (bot may continue)
  CRITICAL → Bot cannot continue (needs human)
"""

import os
import csv
import json
import logging
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# ─── 1. PROFESSIONAL LOGGER SETUP ────────────────────────────────────────────

def setup_bot_logger(
    name: str,
    log_dir: str = "/tmp/bot_logs",
    level: str = "INFO",
    console: bool = True,
    file: bool = True,
    json_format: bool = False,
) -> logging.Logger:
    """
    Professional logger for RPA bots.
    Writes to both console and file.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()  # Avoid duplicate handlers on re-run

    # ── Formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # ── Console Handler
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # ── File Handler (daily rotation)
    if file:
        today = datetime.date.today().strftime("%Y-%m-%d")
        log_file = log_path / f"{name}_{today}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.info(f"Logger initialized: {name} → {log_dir}")
    return logger


class JSONFormatter(logging.Formatter):
    """Log in JSON format for structured logging (Splunk, ELK, CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "line":      record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)


# ─── 2. LOGURU — Beautiful Logging ───────────────────────────────────────────

def loguru_guide():
    print("── 2. LOGURU (Alternative to stdlib logging) ────────────────")
    code = '''
    from loguru import logger  # pip install loguru

    # ── Simple setup (much easier than stdlib logging)
    logger.remove()  # Remove default handler

    # Console with colors
    logger.add(
        sink=sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    # File with rotation (automatic log file management)
    logger.add(
        sink="logs/bot_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",       # Rotate at midnight
        retention="7 days",     # Keep 7 days of logs
        compression="zip",      # Compress old logs
        format="{time} | {level} | {name}:{line} | {message}",
    )

    # Usage is identical to stdlib logging
    logger.debug("Debug message")
    logger.info("Bot started processing")
    logger.warning("Slow response: 8.3s")
    logger.error("Element not found: #submit-btn")
    logger.critical("Authentication failed — bot stopping")

    # Context binding (add fields to all subsequent logs)
    task_logger = logger.bind(task_id="TASK-001", user="alice@example.com")
    task_logger.info("Processing record")  # Includes task_id and user

    # Catch and log exceptions automatically
    with logger.catch():
        result = risky_operation()
    '''
    print(code)


# ─── 3. BOT RUN REPORT ───────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """Result of a single task/action."""
    task_name: str
    success: bool
    started_at: datetime.datetime
    ended_at: datetime.datetime
    duration_sec: float = 0.0
    records_processed: int = 0
    records_failed: int = 0
    error: Optional[str] = None
    output_file: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["started_at"] = self.started_at.isoformat()
        d["ended_at"] = self.ended_at.isoformat()
        return d

    @property
    def status(self) -> str:
        return "SUCCESS" if self.success else "FAILED"


@dataclass
class BotRunReport:
    """Complete report for a bot run."""
    bot_name: str
    run_id: str
    started_at: datetime.datetime
    tasks: list[TaskResult] = field(default_factory=list)
    ended_at: Optional[datetime.datetime] = None
    environment: str = "production"

    @property
    def duration_sec(self) -> float:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0.0

    @property
    def total_records(self) -> int:
        return sum(t.records_processed for t in self.tasks)

    @property
    def total_failed(self) -> int:
        return sum(t.records_failed for t in self.tasks)

    @property
    def success_rate(self) -> float:
        total = self.total_records + self.total_failed
        return self.total_records / total * 100 if total > 0 else 0

    @property
    def failed_tasks(self) -> list[TaskResult]:
        return [t for t in self.tasks if not t.success]

    def finish(self):
        self.ended_at = datetime.datetime.now()

    def save_json(self, output_dir: str = "/tmp") -> Path:
        path = Path(output_dir) / f"{self.bot_name}_{self.run_id}.json"
        report_dict = {
            "bot_name": self.bot_name,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_sec": self.duration_sec,
            "total_records": self.total_records,
            "total_failed": self.total_failed,
            "success_rate": f"{self.success_rate:.1f}%",
            "tasks": [t.to_dict() for t in self.tasks],
        }
        path.write_text(json.dumps(report_dict, indent=2))
        return path

    def save_csv(self, output_dir: str = "/tmp") -> Path:
        path = Path(output_dir) / f"{self.bot_name}_{self.run_id}_tasks.csv"
        with open(path, "w", newline="") as f:
            if self.tasks:
                writer = csv.DictWriter(f, fieldnames=self.tasks[0].to_dict().keys())
                writer.writeheader()
                writer.writerows(t.to_dict() for t in self.tasks)
        return path

    def print_summary(self):
        """Print colorized summary to console."""
        lines = [
            f"\n{'═'*55}",
            f"  BOT RUN REPORT: {self.bot_name}",
            f"  Run ID   : {self.run_id}",
            f"  Started  : {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Duration : {self.duration_sec:.1f}s",
            f"  Tasks    : {len(self.tasks)} ({len(self.failed_tasks)} failed)",
            f"  Records  : {self.total_records:,} processed, {self.total_failed:,} failed",
            f"  Success  : {self.success_rate:.1f}%",
            f"{'═'*55}",
        ]

        if self.failed_tasks:
            lines.append(f"\n  FAILED TASKS:")
            for task in self.failed_tasks:
                lines.append(f"  ✗ {task.task_name}: {task.error}")

        print("\n".join(lines))


# ─── 4. SEND NOTIFICATIONS ───────────────────────────────────────────────────

def notification_guide():
    print("\n── 4. NOTIFICATIONS ─────────────────────────────────────────")
    code = '''
    import requests, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # ── Slack Webhook notification
    def notify_slack(webhook_url: str, message: str, color: str = "good"):
        """Send notification to Slack channel."""
        payload = {
            "attachments": [{
                "color": color,        # "good"=green, "warning"=yellow, "danger"=red
                "text": message,
                "footer": "RPA Bot",
                "ts": int(time.time()),
            }]
        }
        requests.post(webhook_url, json=payload, timeout=5)

    # ── Email notification
    def send_email(to: str, subject: str, body: str, attachment: str = None):
        """Send email notification via SMTP."""
        msg = MIMEMultipart()
        msg["From"]    = os.getenv("EMAIL_FROM")
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if attachment:
            from email.mime.base import MIMEBase
            from email import encoders
            with open(attachment, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(attachment).name}")
            msg.attach(part)

        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.send_message(msg)

    # ── Teams webhook
    def notify_teams(webhook_url: str, title: str, message: str):
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "sections": [{"text": message}]
        })

    # ── Usage in bot
    def on_bot_success(report: BotRunReport):
        notify_slack(
            webhook_url=os.getenv("SLACK_WEBHOOK"),
            message=f"✓ {report.bot_name} completed: {report.total_records} records in {report.duration_sec:.0f}s",
            color="good"
        )

    def on_bot_failure(report: BotRunReport):
        notify_slack(
            webhook_url=os.getenv("SLACK_WEBHOOK"),
            message=f"✗ {report.bot_name} FAILED: {report.failed_tasks[0].error}",
            color="danger"
        )
        send_email(
            to="ops-team@company.com",
            subject=f"[ALERT] {report.bot_name} Failed",
            body=f"<h2>Bot Failure</h2><pre>{json.dumps(report.save_json(), indent=2)}</pre>"
        )
    '''
    print(code)


# ─── DEMO ─────────────────────────────────────────────────────────────────────

def run_demo():
    import uuid

    logger = setup_bot_logger("DemoBot", level="INFO")
    logger.info("Bot starting up")

    # Create report
    report = BotRunReport(
        bot_name="InvoiceProcessor",
        run_id=str(uuid.uuid4())[:8],
        started_at=datetime.datetime.now(),
    )

    # Simulate tasks
    import time, random
    tasks_config = [
        ("login", 20, 0),
        ("fetch_invoices", 150, 3),
        ("process_invoices", 145, 8),
        ("export_report", 1, 0),
    ]

    for task_name, records, failures in tasks_config:
        start = datetime.datetime.now()
        time.sleep(0.05)
        end = datetime.datetime.now()

        report.tasks.append(TaskResult(
            task_name=task_name,
            success=(failures == 0 or records > failures),
            started_at=start,
            ended_at=end,
            duration_sec=(end - start).total_seconds(),
            records_processed=records,
            records_failed=failures,
            error=f"3 invoices had invalid data" if failures > 0 else None,
        ))
        logger.info(f"  {task_name}: {records} records, {failures} failed")

    report.finish()
    report.print_summary()

    # Save reports
    json_path = report.save_json("/tmp")
    csv_path = report.save_csv("/tmp")
    print(f"\n  Reports saved:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")


if __name__ == "__main__":
    run_demo()
    loguru_guide()
    notification_guide()
    print("\n  NEXT: python module_5_advanced/03_scheduling_and_orchestration.py")

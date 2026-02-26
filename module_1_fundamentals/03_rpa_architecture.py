"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 1 — LESSON 3: RPA ARCHITECTURE & BOT DESIGN          ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO STRUCTURE A PROFESSIONAL RPA BOT:

    ┌─────────────────────────────────────────────────────────┐
    │                    BOT ARCHITECTURE                      │
    │                                                          │
    │  Config ──► Bot Class ──► Actions ──► Reporter           │
    │     │           │             │           │              │
    │  .env file   __init__    login()      log results        │
    │  JSON cfg    run()       navigate()   save CSV           │
    │              cleanup()   extract()    send email         │
    └─────────────────────────────────────────────────────────┘

DESIGN PRINCIPLES:
  1. Separation of concerns — config, logic, reporting separate
  2. Fail gracefully — every action has error handling
  3. Idempotent — running twice gives same result
  4. Auditable — every action is logged
  5. Configurable — no hardcoded values
"""

import os
import csv
import json
import logging
import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ─── 1. CONFIGURATION DATACLASS ───────────────────────────────────────────────

@dataclass
class BotConfig:
    """
    Central configuration for a bot.
    All bot settings live here — no magic numbers in the code.
    """
    bot_name: str
    target_url: str
    username: str
    password: str
    headless: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    output_dir: Path = Path("./output")
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, bot_name: str, target_url: str) -> "BotConfig":
        """Load config from environment variables."""
        return cls(
            bot_name=bot_name,
            target_url=target_url,
            username=os.getenv("BOT_USERNAME", ""),
            password=os.getenv("BOT_PASSWORD", ""),
            headless=os.getenv("BOT_HEADLESS", "true").lower() == "true",
            timeout=int(os.getenv("BOT_TIMEOUT", "30")),
            max_retries=int(os.getenv("BOT_MAX_RETRIES", "3")),
        )

    @classmethod
    def from_json(cls, path: str) -> "BotConfig":
        """Load config from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


# ─── 2. BOT RESULT / STATUS TRACKING ──────────────────────────────────────────

@dataclass
class BotResult:
    """Tracks the outcome of a bot run or single action."""
    action: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    duration_sec: float = 0.0

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "duration_sec": round(self.duration_sec, 3),
        }

    def __str__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"[{status}] {self.action} ({self.duration_sec:.2f}s)"


# ─── 3. LOGGER SETUP ──────────────────────────────────────────────────────────

def setup_logger(bot_name: str, log_dir: Path = Path("/tmp/logs")) -> logging.Logger:
    """
    Creates a logger that writes to both console and file.
    Every bot should have its own logger.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{bot_name}_{datetime.date.today()}.log"

    logger = logging.getLogger(bot_name)
    logger.setLevel(logging.DEBUG)

    # Console handler (colored output)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    ))

    # File handler (detailed logs)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


# ─── 4. BASE BOT CLASS — Template for All Bots ────────────────────────────────

class BaseBot:
    """
    Base class every bot inherits from.
    Provides: logging, retry logic, result tracking, reporting.

    Usage:
        class MyBot(BaseBot):
            def run(self):
                self.login()
                data = self.scrape_data()
                self.save_results(data)
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = setup_logger(config.bot_name)
        self.results: list[BotResult] = []
        self.start_time: Optional[datetime.datetime] = None
        config.output_dir.mkdir(parents=True, exist_ok=True)

    def record(self, action: str, success: bool,
               data: dict = None, error: str = None,
               duration: float = 0.0) -> BotResult:
        """Record the result of any bot action."""
        result = BotResult(
            action=action,
            success=success,
            data=data,
            error=error,
            duration_sec=duration,
        )
        self.results.append(result)

        if success:
            self.logger.info(f"  {result}")
        else:
            self.logger.error(f"  {result} — {error}")

        return result

    def with_retry(self, func, action_name: str, *args, **kwargs):
        """
        Execute any function with automatic retry on failure.

        Example:
            data = self.with_retry(self.scrape_page, "scrape_page", url=url)
        """
        import time as _time
        last_error = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                start = _time.time()
                result = func(*args, **kwargs)
                duration = _time.time() - start
                self.record(action_name, True, duration=duration)
                return result

            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    f"  [{action_name}] Attempt {attempt}/{self.config.max_retries} failed: {e}"
                )
                if attempt < self.config.max_retries:
                    wait = self.config.retry_delay * attempt  # exponential backoff
                    self.logger.info(f"  Retrying in {wait:.1f}s...")
                    _time.sleep(wait)

        self.record(action_name, False, error=last_error)
        raise RuntimeError(f"{action_name} failed after {self.config.max_retries} retries: {last_error}")

    def save_report(self) -> Path:
        """Save run results to a CSV report file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.config.output_dir / f"{self.config.bot_name}_{timestamp}_report.csv"

        with open(report_path, "w", newline="") as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].to_dict().keys())
                writer.writeheader()
                writer.writerows(r.to_dict() for r in self.results)

        self.logger.info(f"  Report saved: {report_path}")
        return report_path

    def print_summary(self):
        """Print execution summary."""
        total = len(self.results)
        ok    = sum(1 for r in self.results if r.success)
        fail  = total - ok
        elapsed = (datetime.datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        print(f"\n{'─'*50}")
        print(f"  BOT SUMMARY: {self.config.bot_name}")
        print(f"  Total actions : {total}")
        print(f"  Succeeded     : {ok}")
        print(f"  Failed        : {fail}")
        print(f"  Duration      : {elapsed:.1f}s")
        print(f"{'─'*50}")

    def run(self):
        """Override this in subclasses to implement bot logic."""
        raise NotImplementedError("Subclasses must implement run()")

    def start(self):
        """Entry point — wraps run() with setup/cleanup."""
        self.start_time = datetime.datetime.now()
        self.logger.info(f"  {self.config.bot_name} STARTED")
        try:
            self.run()
        except Exception as e:
            self.logger.critical(f"  BOT CRASHED: {e}")
        finally:
            self.save_report()
            self.print_summary()
            self.logger.info(f"  {self.config.bot_name} FINISHED")


# ─── 5. CONCRETE BOT EXAMPLE ──────────────────────────────────────────────────

class SampleBot(BaseBot):
    """
    A concrete bot that demonstrates the architecture.
    In real bots this would use Selenium / PyAutoGUI / requests.
    """

    def login(self) -> bool:
        """Simulate login action."""
        self.logger.info(f"  Logging in to {self.config.target_url}")
        # Real: driver.get(url); fill fields; click submit
        return True

    def navigate_to_page(self, page: str) -> bool:
        """Simulate page navigation."""
        self.logger.info(f"  Navigating to {page}")
        # Real: driver.get(page) or click navigation link
        return True

    def extract_data(self, page_num: int) -> dict:
        """Simulate data extraction."""
        # Real: driver.find_elements(By.CSS_SELECTOR, ".row")
        return {
            "page": page_num,
            "records": [
                {"id": page_num * 10 + i, "value": f"item_{i}"}
                for i in range(3)
            ]
        }

    def run(self):
        """Main bot workflow."""
        # Step 1: Login
        if not self.login():
            raise RuntimeError("Login failed")
        self.record("login", True)

        # Step 2: Process pages
        all_data = []
        for page in range(1, 4):
            try:
                data = self.with_retry(
                    self.extract_data,
                    f"extract_page_{page}",
                    page_num=page
                )
                all_data.extend(data["records"])
                self.logger.info(f"  Page {page}: extracted {len(data['records'])} records")
            except RuntimeError as e:
                self.logger.error(f"  Skipping page {page}: {e}")

        # Step 3: Save data
        output_file = self.config.output_dir / "extracted_data.csv"
        if all_data:
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                writer.writeheader()
                writer.writerows(all_data)
            self.record("save_data", True, data={"file": str(output_file), "rows": len(all_data)})


# ─── Run the demo ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 55)
    print("  RPA FUNDAMENTALS — LESSON 3: BOT ARCHITECTURE")
    print("█" * 55)

    config = BotConfig(
        bot_name="SampleBot",
        target_url="https://example.com",
        username="demo_user",
        password="demo_pass",
        output_dir=Path("/tmp/rpa_output"),
    )

    bot = SampleBot(config)
    bot.start()

    print("\n  KEY ARCHITECTURE CONCEPTS:")
    print("  ─────────────────────────────────────────")
    print("  BotConfig     → All settings in one place")
    print("  BotResult     → Track every action's outcome")
    print("  BaseBot       → Reuse logging, retry, report")
    print("  with_retry()  → Automatic retry on failure")
    print("  start()       → Safe entry point with cleanup")
    print("  ─────────────────────────────────────────")
    print("\n  NEXT: python module_2_selenium/01_selenium_setup.py")

"""
╔══════════════════════════════════════════════════════════════════╗
║     PROJECT 3: API DATA SYNC BOT                                 ║
╚══════════════════════════════════════════════════════════════════╝

SCENARIO:
  Sync users from JSONPlaceholder (source) to a local SQLite
  database (target), generating a reconciliation report.

FEATURES:
  ✓ Fetch from real REST API (jsonplaceholder.typicode.com)
  ✓ Data transformation & validation
  ✓ SQLite database as target
  ✓ Upsert logic (insert new, update changed)
  ✓ Reconciliation report
  ✓ Rate limiting
  ✓ Full error handling
  ✓ Statistics & summary

RUN:
  python projects/project_3_api_data_sync_bot.py
"""

import json
import time
import sqlite3
import logging
import datetime
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ─── DATA MODELS ─────────────────────────────────────────────────────────────

@dataclass
class User:
    id: int
    name: str
    username: str
    email: str
    city: str
    company: str
    phone: str
    website: str
    checksum: str = ""  # Used to detect changes

    @classmethod
    def from_api(cls, data: dict) -> "User":
        """Create User from API response dict."""
        user = cls(
            id       = data["id"],
            name     = data["name"].strip(),
            username = data["username"].lower(),
            email    = data["email"].lower().strip(),
            city     = data["address"]["city"],
            company  = data["company"]["name"],
            phone    = data["phone"],
            website  = data.get("website", ""),
        )
        user.checksum = user._compute_checksum()
        return user

    def _compute_checksum(self) -> str:
        """SHA256 of all fields — used to detect changes."""
        content = "|".join([
            self.name, self.username, self.email,
            self.city, self.company, self.phone
        ])
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "username": self.username,
            "email": self.email, "city": self.city, "company": self.company,
            "phone": self.phone, "website": self.website, "checksum": self.checksum,
        }


@dataclass
class SyncStats:
    started_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    ended_at: Optional[datetime.datetime] = None
    api_calls: int = 0
    records_fetched: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_unchanged: int = 0
    records_failed: int = 0
    api_errors: int = 0

    @property
    def duration_sec(self) -> float:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0.0

    def finish(self):
        self.ended_at = datetime.datetime.now()

    def print(self):
        print(f"\n{'═'*55}")
        print(f"  SYNC STATISTICS")
        print(f"{'═'*55}")
        print(f"  Started       : {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration      : {self.duration_sec:.2f}s")
        print(f"  API calls     : {self.api_calls}")
        print(f"  Records fetched: {self.records_fetched}")
        print(f"  ─────────────────────────────────────────────────")
        print(f"  Inserted      : {self.records_inserted} (new records)")
        print(f"  Updated       : {self.records_updated} (changed records)")
        print(f"  Unchanged     : {self.records_unchanged}")
        print(f"  Failed        : {self.records_failed}")
        print(f"  API Errors    : {self.api_errors}")
        print(f"{'═'*55}")


# ─── DATABASE LAYER ───────────────────────────────────────────────────────────

class UserDatabase:
    """SQLite database manager for user records."""

    def __init__(self, db_path: str = "/tmp/users_sync.db"):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY,
                    name        TEXT NOT NULL,
                    username    TEXT UNIQUE NOT NULL,
                    email       TEXT,
                    city        TEXT,
                    company     TEXT,
                    phone       TEXT,
                    website     TEXT,
                    checksum    TEXT,
                    created_at  TEXT DEFAULT (datetime('now')),
                    updated_at  TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER,
                    action      TEXT,        -- INSERT, UPDATE, ERROR
                    message     TEXT,
                    synced_at   TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def get_all(self) -> dict[int, dict]:
        """Get all users indexed by ID."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
            return {row["id"]: dict(row) for row in rows}

    def upsert(self, user: User) -> str:
        """Insert or update a user. Returns 'inserted', 'updated', or 'unchanged'."""
        existing = self.get_all().get(user.id)

        with self._conn() as conn:
            if not existing:
                conn.execute("""
                    INSERT INTO users (id, name, username, email, city, company, phone, website, checksum)
                    VALUES (:id, :name, :username, :email, :city, :company, :phone, :website, :checksum)
                """, user.to_dict())
                conn.execute(
                    "INSERT INTO sync_log (user_id, action, message) VALUES (?, ?, ?)",
                    (user.id, "INSERT", f"New user: {user.name}")
                )
                conn.commit()
                return "inserted"

            elif existing["checksum"] != user.checksum:
                conn.execute("""
                    UPDATE users SET
                        name=:name, username=:username, email=:email,
                        city=:city, company=:company, phone=:phone,
                        website=:website, checksum=:checksum,
                        updated_at=datetime('now')
                    WHERE id=:id
                """, user.to_dict())
                conn.execute(
                    "INSERT INTO sync_log (user_id, action, message) VALUES (?, ?, ?)",
                    (user.id, "UPDATE", f"Updated: {user.name}")
                )
                conn.commit()
                return "updated"

            else:
                return "unchanged"

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def get_recent_sync_log(self, limit=10) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sync_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


# ─── API CLIENT ───────────────────────────────────────────────────────────────

class JSONPlaceholderAPI:
    """Client for JSONPlaceholder test API."""

    BASE_URL = "https://jsonplaceholder.typicode.com"

    def __init__(self):
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist={500, 502, 503})
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({"Accept": "application/json"})

    def get_users(self) -> list[dict]:
        """Fetch all users from API."""
        response = self.session.get(f"{self.BASE_URL}/users", timeout=15)
        response.raise_for_status()
        return response.json()

    def get_user(self, user_id: int) -> dict:
        response = self.session.get(f"{self.BASE_URL}/users/{user_id}", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_user_posts_count(self, user_id: int) -> int:
        """Get number of posts for a user."""
        response = self.session.get(
            f"{self.BASE_URL}/posts", params={"userId": user_id}, timeout=10
        )
        response.raise_for_status()
        return len(response.json())


# ─── SYNC BOT ────────────────────────────────────────────────────────────────

class DataSyncBot:
    """Syncs users from API to local database."""

    def __init__(self, db_path: str = "/tmp/users_sync.db"):
        self.api = JSONPlaceholderAPI()
        self.db  = UserDatabase(db_path)
        self.stats = SyncStats()
        self.logger = logging.getLogger("DataSyncBot")

    def validate_user(self, data: dict) -> tuple[bool, str]:
        """Validate API data before syncing."""
        required = ["id", "name", "username", "email"]
        for field in required:
            if not data.get(field):
                return False, f"Missing required field: {field}"

        if "@" not in data["email"]:
            return False, f"Invalid email: {data['email']}"

        return True, ""

    def enrich_user(self, user: User) -> User:
        """Optionally enrich user with additional data (posts count, etc.)."""
        # In real scenario, you might fetch additional related data
        return user

    def run_sync(self) -> SyncStats:
        """Main sync operation."""
        self.logger.info("Starting sync...")
        self.logger.info(f"  Target DB: {self.db.db_path}")
        self.logger.info(f"  Source: {self.api.BASE_URL}")

        # ── Fetch from API
        try:
            self.logger.info("  Fetching users from API...")
            raw_users = self.api.get_users()
            self.stats.api_calls += 1
            self.stats.records_fetched = len(raw_users)
            self.logger.info(f"  Fetched {len(raw_users)} users")
        except Exception as e:
            self.logger.error(f"  API fetch failed: {e}")
            self.stats.api_errors += 1
            return self.stats

        # ── Process each user
        for raw in raw_users:
            try:
                # Validate
                valid, error = self.validate_user(raw)
                if not valid:
                    self.logger.warning(f"  Validation failed for user {raw.get('id')}: {error}")
                    self.stats.records_failed += 1
                    continue

                # Transform
                user = User.from_api(raw)
                user = self.enrich_user(user)

                # Upsert to DB
                action = self.db.upsert(user)

                if action == "inserted":
                    self.stats.records_inserted += 1
                    self.logger.info(f"  + INSERT: {user.name} ({user.email})")
                elif action == "updated":
                    self.stats.records_updated += 1
                    self.logger.info(f"  ~ UPDATE: {user.name}")
                else:  # unchanged
                    self.stats.records_unchanged += 1

                time.sleep(0.05)  # Rate limiting

            except Exception as e:
                self.logger.error(f"  Error processing user {raw.get('id')}: {e}")
                self.stats.records_failed += 1

        self.stats.finish()
        return self.stats

    def generate_report(self) -> dict:
        """Generate reconciliation report."""
        total_in_db = self.db.count()
        recent_logs = self.db.get_recent_sync_log(20)

        report = {
            "generated_at": datetime.datetime.now().isoformat(),
            "database": {
                "path": self.db.db_path,
                "total_records": total_in_db,
            },
            "sync_stats": {
                "duration_sec": self.stats.duration_sec,
                "records_fetched": self.stats.records_fetched,
                "records_inserted": self.stats.records_inserted,
                "records_updated": self.stats.records_updated,
                "records_unchanged": self.stats.records_unchanged,
                "records_failed": self.stats.records_failed,
            },
            "recent_activity": recent_logs,
        }

        report_path = Path("/tmp/sync_report.json")
        report_path.write_text(json.dumps(report, indent=2))
        self.logger.info(f"  Report: {report_path}")

        return report


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    print("\n" + "█" * 55)
    print("  PROJECT 3: API DATA SYNC BOT")
    print("█" * 55)

    bot = DataSyncBot(db_path="/tmp/users_sync.db")

    # Run 1: Initial sync (all inserts)
    print("\n► Run 1: Initial Sync")
    stats1 = bot.run_sync()
    stats1.print()

    # Run 2: No changes (all unchanged)
    print("\n► Run 2: Re-sync (should be all unchanged)")
    bot2 = DataSyncBot(db_path="/tmp/users_sync.db")
    stats2 = bot2.run_sync()
    stats2.print()

    # Generate report
    report = bot.generate_report()
    print(f"\n► Total records in database: {report['database']['total_records']}")
    print(f"► Recent activity (last 5):")
    for entry in report["recent_activity"][:5]:
        print(f"  [{entry['action']:6}] User {entry['user_id']}: {entry['message']}")


if __name__ == "__main__":
    main()

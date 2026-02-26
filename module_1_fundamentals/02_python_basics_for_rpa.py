"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 1 — LESSON 2: PYTHON ESSENTIALS FOR RPA              ║
╚══════════════════════════════════════════════════════════════════╝

Key Python concepts you MUST know before writing RPA bots:
  1. Variables, strings, lists, dictionaries
  2. Loops and conditions
  3. Functions
  4. File I/O (reading/writing files)
  5. Exception handling (critical for bots!)
  6. Working with time and dates
  7. Environment variables (for secrets)
  8. Context managers (with statements)
"""

import os
import csv
import json
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv  # pip install python-dotenv


# ─── 1. VARIABLES & DATA TYPES ────────────────────────────────────────────────

print("\n── 1. VARIABLES & DATA TYPES ──────────────────────────────────")

bot_name = "WebScraperBot"            # string
version = 1.0                          # float
max_retries = 3                        # int
is_headless = True                     # bool

# f-strings — used everywhere in RPA for dynamic messages
print(f"Bot: {bot_name} v{version} | Headless: {is_headless}")

# Lists — store multiple URLs, elements, data rows
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

# Dictionaries — store structured data (like a form or record)
user_credentials = {
    "username": "bot_user",
    "password": "secret123",  # In real bots, use env vars (see section 7)
    "url": "https://app.example.com",
}

print(f"Urls to process: {len(urls)}")
print(f"Login URL: {user_credentials['url']}")


# ─── 2. LOOPS — The Heart of Automation ───────────────────────────────────────

print("\n── 2. LOOPS ────────────────────────────────────────────────────")

# Process multiple URLs (very common in scraping bots)
for i, url in enumerate(urls, 1):
    print(f"  [{i}/{len(urls)}] Processing: {url}")
    # In real bot: driver.get(url) then extract data

# While loop with counter (for retry logic)
attempt = 0
while attempt < max_retries:
    attempt += 1
    print(f"  Attempt {attempt}/{max_retries}")
    success = True  # Simulate success
    if success:
        print("  Success! Breaking retry loop.")
        break
    time.sleep(1)  # Wait before retry


# ─── 3. FUNCTIONS — Reusable Bot Actions ──────────────────────────────────────

print("\n── 3. FUNCTIONS ────────────────────────────────────────────────")


def login(url: str, username: str, password: str) -> bool:
    """
    Template for a login action.
    Returns True if login succeeded, False otherwise.
    """
    print(f"  Navigating to: {url}")
    print(f"  Logging in as: {username}")
    # Real code: driver.get(url), find fields, send_keys, click
    return True  # Simulate success


def extract_data(selector: str, element_type: str = "text") -> str:
    """
    Template for data extraction.
    selector: CSS selector or XPath
    element_type: 'text', 'href', 'value'
    """
    # Real code: driver.find_element(By.CSS_SELECTOR, selector).text
    return f"[extracted {element_type} from {selector}]"


success = login(user_credentials["url"], user_credentials["username"], user_credentials["password"])
print(f"  Login result: {'OK' if success else 'FAILED'}")

data = extract_data("#product-price", "text")
print(f"  Extracted: {data}")


# ─── 4. FILE I/O — Reading/Writing Automation Data ────────────────────────────

print("\n── 4. FILE I/O ─────────────────────────────────────────────────")

# ── CSV Files (common for input/output data)
sample_csv = "/tmp/rpa_sample.csv"

# Write CSV
rows = [
    {"name": "Alice", "email": "alice@example.com", "status": "pending"},
    {"name": "Bob",   "email": "bob@example.com",   "status": "pending"},
    {"name": "Carol", "email": "carol@example.com", "status": "pending"},
]

with open(sample_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "email", "status"])
    writer.writeheader()
    writer.writerows(rows)
print(f"  Written {len(rows)} rows to {sample_csv}")

# Read CSV (bot reads input data)
with open(sample_csv, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"  Processing: {row['name']} <{row['email']}>")

# ── JSON Files (for config and API data)
config = {
    "bot_name": "FormFillerBot",
    "target_url": "https://forms.example.com",
    "headless": True,
    "timeout": 30,
    "retry_count": 3,
}

config_path = "/tmp/bot_config.json"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

with open(config_path, "r") as f:
    loaded_config = json.load(f)
print(f"  Loaded config for: {loaded_config['bot_name']}")

# ── Path handling (use pathlib, not string concatenation!)
output_dir = Path("/tmp/rpa_output")
output_dir.mkdir(exist_ok=True)
report_file = output_dir / f"report_{datetime.date.today()}.txt"
report_file.write_text("Bot run completed successfully.\n")
print(f"  Report saved: {report_file}")


# ─── 5. EXCEPTION HANDLING — Critical for Reliable Bots ───────────────────────

print("\n── 5. EXCEPTION HANDLING ───────────────────────────────────────")


def safe_click(element_id: str) -> bool:
    """
    Always wrap bot actions in try/except.
    Bots WILL encounter errors — handle them gracefully.
    """
    try:
        # Real: driver.find_element(By.ID, element_id).click()
        if element_id == "missing-button":
            raise Exception("ElementNotFound: #missing-button")
        print(f"  Clicked: #{element_id}")
        return True

    except Exception as e:
        print(f"  ERROR clicking #{element_id}: {e}")
        # Options: retry, skip, log, raise, notify
        return False


safe_click("submit-btn")        # succeeds
safe_click("missing-button")    # handles error gracefully

# Specific exception types (Selenium exceptions shown as comments)
def navigate_safely(url: str) -> bool:
    try:
        # driver.get(url)
        # WebDriverWait(driver, 10).until(EC.title_contains("Dashboard"))
        print(f"  Navigated to: {url}")
        return True
    # except TimeoutException:
    #     print("  Page took too long to load")
    # except WebDriverException as e:
    #     print(f"  Browser error: {e}")
    except Exception as e:
        print(f"  Navigation failed: {e}")
        return False
    finally:
        print("  Navigation attempt complete (finally always runs)")


navigate_safely("https://example.com")


# ─── 6. TIME & DATES ──────────────────────────────────────────────────────────

print("\n── 6. TIME & DATES ─────────────────────────────────────────────")

now = datetime.datetime.now()
today = datetime.date.today()

print(f"  Current time : {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Today        : {today}")
print(f"  Timestamp    : {now.timestamp():.0f}")

# Timestamped filenames (very common in RPA)
filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.csv"
print(f"  Output file  : {filename}")

# Measuring execution time
start = time.time()
time.sleep(0.1)  # Simulate work
elapsed = time.time() - start
print(f"  Task time    : {elapsed:.3f}s")

# Waiting (bots often need to wait for pages/processes)
print("  Waiting 0.5s for page to load...")
time.sleep(0.5)
print("  Done waiting.")


# ─── 7. ENVIRONMENT VARIABLES — Never Hardcode Secrets! ───────────────────────

print("\n── 7. ENVIRONMENT VARIABLES ────────────────────────────────────")

# Create a sample .env file
env_file = Path("/tmp/.env")
env_file.write_text(
    "BOT_USERNAME=admin\n"
    "BOT_PASSWORD=super_secret_password\n"
    "API_KEY=abc123xyz\n"
    "TARGET_URL=https://app.example.com\n"
)

# Load env file
load_dotenv(env_file)

# Access safely
username = os.getenv("BOT_USERNAME", "default_user")
password = os.getenv("BOT_PASSWORD")
api_key  = os.getenv("API_KEY")

print(f"  Username : {username}")
print(f"  Password : {'*' * len(password) if password else 'NOT SET'}")
print(f"  API Key  : {api_key[:3]}***{api_key[-3:] if api_key else ''}")

# NEVER do this:
# password = "mypassword123"   ← hardcoded secret, dangerous!

# ALWAYS do this:
# password = os.getenv("BOT_PASSWORD")  ← safe!


# ─── 8. CONTEXT MANAGERS ──────────────────────────────────────────────────────

print("\n── 8. CONTEXT MANAGERS ─────────────────────────────────────────")

# Files automatically close
with open("/tmp/output.txt", "w") as f:
    f.write("Bot output\n")
    print("  File open inside 'with' block")
# File is automatically closed here

# Custom context manager for bot sessions
from contextlib import contextmanager


@contextmanager
def bot_session(bot_name: str):
    """Ensures browser always closes, even if bot crashes."""
    print(f"  [{bot_name}] Starting session...")
    # Real: driver = webdriver.Chrome()
    try:
        yield bot_name  # provides driver in real code
    except Exception as e:
        print(f"  [{bot_name}] Error during session: {e}")
        raise
    finally:
        # Real: driver.quit()
        print(f"  [{bot_name}] Session ended. Browser closed.")


with bot_session("ScraperBot") as bot:
    print(f"  [{bot}] Running automation...")
    # All bot actions go here


# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "─" * 55)
print("  PYTHON FOR RPA — SUMMARY")
print("─" * 55)
concepts = [
    ("Variables/Types",   "Store URLs, credentials, data"),
    ("Loops",             "Process multiple records/pages"),
    ("Functions",         "Reuse login(), click(), extract()"),
    ("File I/O",          "Read CSV input, write results"),
    ("Try/Except",        "Handle errors without crashing"),
    ("Time/Dates",        "Waits, timestamps, scheduling"),
    ("Env Variables",     "Keep secrets out of code"),
    ("Context Managers",  "Auto-cleanup (browser/files)"),
]
for concept, use in concepts:
    print(f"  {concept:<20} → {use}")
print("─" * 55)
print("  NEXT: python module_1_fundamentals/03_rpa_architecture.py")

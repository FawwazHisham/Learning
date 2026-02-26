"""
╔══════════════════════════════════════════════════════════════════╗
║         MODULE 1 — LESSON 1: WHAT IS RPA?                       ║
╚══════════════════════════════════════════════════════════════════╝

ROBOTIC PROCESS AUTOMATION (RPA):
  ► Software robots (bots) that mimic human actions on computers
  ► No changes to existing systems needed
  ► Works at the UI layer (what a human would see/click)

WHY PYTHON FOR RPA?
  ► Free and open-source
  ► Massive ecosystem (Selenium, PyAutoGUI, requests, etc.)
  ► Easy to learn and read
  ► Integrates with databases, cloud, APIs, Excel, etc.

REAL WORLD USE CASES:
  ─────────────────────────────────────────────────────
  FINANCE      │ Invoice processing, bank reconciliation
  HR           │ Employee onboarding, payroll data entry
  IT           │ Server monitoring, ticket creation
  HEALTHCARE   │ Patient data migration, report generation
  E-COMMERCE   │ Price monitoring, order processing
  ─────────────────────────────────────────────────────
"""

# ─── Simple demonstration of RPA concept ──────────────────────────────────────

import time
import datetime


def simulate_human_task(task_name: str, steps: list[str]) -> dict:
    """
    Simulates how a human would perform repetitive tasks step by step.
    In real RPA, each step would be automated by a bot.
    """
    print(f"\n{'='*55}")
    print(f"  TASK: {task_name}")
    print(f"  Started: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*55}")

    results = {"task": task_name, "steps": [], "status": "success"}

    for i, step in enumerate(steps, 1):
        print(f"  Step {i}: {step}")
        time.sleep(0.3)  # Simulating work being done
        results["steps"].append({"step": i, "action": step, "done": True})

    print(f"\n  ✓ Task completed at {datetime.datetime.now().strftime('%H:%M:%S')}")
    return results


# ─── Example: Human task vs Bot task ──────────────────────────────────────────

HUMAN_TASK = "Log into website and download report (MANUAL)"
HUMAN_STEPS = [
    "Open browser",
    "Navigate to website URL",
    "Click on username field",
    "Type username",
    "Click on password field",
    "Type password",
    "Click Login button",
    "Wait for dashboard to load",
    "Click on Reports menu",
    "Select 'Monthly Summary'",
    "Click Download button",
    "Save file to folder",
    "Close browser",
]

BOT_TASK = "Log into website and download report (AUTOMATED BOT)"
BOT_STEPS = [
    "driver.get('https://example.com/login')",
    "driver.find_element(By.ID, 'username').send_keys(USERNAME)",
    "driver.find_element(By.ID, 'password').send_keys(PASSWORD)",
    "driver.find_element(By.ID, 'login-btn').click()",
    "WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))",
    "driver.find_element(By.LINK_TEXT, 'Reports').click()",
    "driver.find_element(By.LINK_TEXT, 'Monthly Summary').click()",
    "driver.find_element(By.ID, 'download-btn').click()",
]


# ─── RPA Tool Comparison ───────────────────────────────────────────────────────

def print_rpa_tools_comparison():
    tools = {
        "Selenium": {
            "type": "Web Automation",
            "use_for": "Browsers (Chrome, Firefox, Edge)",
            "strength": "Powerful web interaction, widely used",
            "limitation": "Web only, needs browser driver",
            "example": "Login to web app, fill forms, scrape data",
        },
        "PyAutoGUI": {
            "type": "Desktop Automation",
            "use_for": "Any GUI application (desktop/native apps)",
            "strength": "Controls mouse & keyboard system-wide",
            "limitation": "Pixel-based, fragile to screen changes",
            "example": "Automate Excel, Notepad, any desktop app",
        },
        "Requests/API": {
            "type": "API Automation",
            "use_for": "Backend services, REST APIs",
            "strength": "Fast, reliable, no UI dependency",
            "limitation": "Needs API access (credentials/keys)",
            "example": "Fetch data, create records, trigger services",
        },
    }

    print("\n" + "─" * 65)
    print("  RPA TOOL COMPARISON")
    print("─" * 65)
    for tool, info in tools.items():
        print(f"\n  [{tool}]")
        for key, val in info.items():
            print(f"    {key:<12}: {val}")
    print("─" * 65)


# ─── RPA Process Flow ──────────────────────────────────────────────────────────

def explain_rpa_flow():
    """
    Standard RPA bot flow:

    INPUT ──► PROCESS ──► OUTPUT
      │           │           │
    File       Automate     File
    Email      Navigate     Email
    Schedule   Click/Type   DB Record
    API call   Extract      API call
    """
    flow = [
        ("TRIGGER",   "What starts the bot",    "Schedule, file arrival, API call, email"),
        ("INPUT",     "Data the bot reads",      "Excel file, web page, database, API response"),
        ("PROCESS",   "Actions the bot takes",   "Navigate, click, type, extract, calculate"),
        ("VALIDATE",  "Check for errors",        "Data validation, exception handling, retries"),
        ("OUTPUT",    "What the bot produces",   "Filled form, downloaded file, database update"),
        ("LOG",       "Track what happened",     "Audit trail, error reports, notifications"),
    ]

    print("\n" + "─" * 60)
    print("  STANDARD RPA BOT FLOW")
    print("─" * 60)
    for stage, what, example in flow:
        print(f"\n  [{stage}]")
        print(f"    What    : {what}")
        print(f"    Example : {example}")
    print("─" * 60)


# ─── Run demonstrations ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 55)
    print("  RPA FUNDAMENTALS — LESSON 1: WHAT IS RPA?")
    print("█" * 55)

    # Show the comparison between human and bot
    human_result = simulate_human_task(HUMAN_TASK, HUMAN_STEPS[:5])  # First 5 steps
    bot_result = simulate_human_task(BOT_TASK, BOT_STEPS[:4])

    print(f"\n  Human steps needed : {len(HUMAN_STEPS)}")
    print(f"  Bot lines of code  : {len(BOT_STEPS)}")
    print(f"  Automation gain    : Same result, 100% consistent, runs 24/7")

    print_rpa_tools_comparison()
    explain_rpa_flow()

    print("\n" + "─" * 55)
    print("  NEXT LESSON: Python Basics for RPA")
    print("  Run: python module_1_fundamentals/02_python_basics_for_rpa.py")
    print("─" * 55)

"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 1: SELENIUM SETUP & FIRST BOT             ║
╚══════════════════════════════════════════════════════════════════╝

SELENIUM = Browser Automation Library
  ► Controls Chrome, Firefox, Edge, Safari
  ► Clicks buttons, fills forms, reads page content
  ► Works exactly like a human using a browser

ARCHITECTURE:
  Your Python Code
       │
       ▼ (sends commands via WebDriver Protocol)
  ChromeDriver / GeckoDriver
       │
       ▼ (controls the browser)
  Chrome / Firefox
       │
       ▼ (loads pages)
  Web Application

INSTALL:
  pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ─── 1. BROWSER SETUP OPTIONS ─────────────────────────────────────────────────

def create_driver(headless: bool = True, download_dir: str = "/tmp") -> webdriver.Chrome:
    """
    Create and configure a Chrome WebDriver instance.

    headless=True  → Runs without visible browser window (for servers/production)
    headless=False → Shows browser (good for development/debugging)
    """
    options = Options()

    # ── Display settings
    if headless:
        options.add_argument("--headless=new")    # New headless mode (Chrome 112+)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    # ── Performance & Stability
    options.add_argument("--no-sandbox")             # Required in Docker/CI
    options.add_argument("--disable-dev-shm-usage")  # Prevents memory crashes
    options.add_argument("--disable-gpu")            # Required in headless mode
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")

    # ── Anti-bot detection (makes Selenium look more like a real browser)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # ── Download settings
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.notifications": 2,  # Block popups
    }
    options.add_experimental_option("prefs", prefs)

    # ── Auto-install ChromeDriver (matches your Chrome version)
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)  # Default wait for elements (use explicit waits instead)

    return driver


# ─── 2. BASIC NAVIGATION ───────────────────────────────────────────────────────

def demo_basic_navigation(driver: webdriver.Chrome):
    """Demonstrates basic browser navigation commands."""
    print("\n── BASIC NAVIGATION ───────────────────────────────────────")

    # Navigate to URL
    driver.get("https://example.com")
    print(f"  Title  : {driver.title}")
    print(f"  URL    : {driver.current_url}")

    # Navigate back/forward
    driver.get("https://example.org")
    print(f"  Went to: {driver.current_url}")
    driver.back()
    print(f"  Back to: {driver.current_url}")
    driver.forward()
    print(f"  Forward: {driver.current_url}")

    # Refresh
    driver.refresh()
    print(f"  Refreshed: {driver.title}")

    # Window management
    print(f"  Window size: {driver.get_window_size()}")
    driver.set_window_size(1280, 720)
    driver.maximize_window()

    # JavaScript execution
    title = driver.execute_script("return document.title;")
    print(f"  JS title: {title}")

    # Scroll
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("  Scrolled to bottom")
    driver.execute_script("window.scrollTo(0, 0);")
    print("  Scrolled to top")


# ─── 3. SCREENSHOTS ────────────────────────────────────────────────────────────

def take_screenshot(driver: webdriver.Chrome, filename: str = "/tmp/screenshot.png"):
    """Take a screenshot — essential for debugging and reporting."""
    driver.save_screenshot(filename)
    print(f"  Screenshot saved: {filename}")

    # Element-level screenshot
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.screenshot("/tmp/element_screenshot.png")
        print("  Element screenshot saved")
    except Exception as e:
        print(f"  Element screenshot failed: {e}")


# ─── 4. MULTIPLE WINDOWS & TABS ───────────────────────────────────────────────

def demo_windows_and_tabs(driver: webdriver.Chrome):
    """Working with multiple browser windows and tabs."""
    print("\n── WINDOWS & TABS ─────────────────────────────────────────")

    # Store original window handle
    original_window = driver.current_window_handle
    print(f"  Original window: {original_window}")

    # Open new tab via JavaScript
    driver.execute_script("window.open('https://example.com', '_blank');")

    # Get all windows
    all_windows = driver.window_handles
    print(f"  Total windows: {len(all_windows)}")

    # Switch to new tab
    driver.switch_to.window(all_windows[-1])
    print(f"  New tab title: {driver.title}")

    # Switch back to original
    driver.switch_to.window(original_window)
    print(f"  Back to: {driver.title}")

    # Close new tab
    driver.switch_to.window(all_windows[-1])
    driver.close()
    driver.switch_to.window(original_window)
    print("  Closed new tab, back to original")


# ─── 5. YOUR FIRST COMPLETE BOT ───────────────────────────────────────────────

def run_first_bot():
    """
    A complete, working mini-bot.
    Opens a page, reads content, takes screenshot.
    """
    print("\n" + "═" * 55)
    print("  FIRST BOT: Wikipedia Title Extractor")
    print("═" * 55)

    driver = None
    try:
        driver = create_driver(headless=True)

        # Navigate
        driver.get("https://en.wikipedia.org/wiki/Robotic_process_automation")
        print(f"  Page: {driver.title}")

        # Extract heading
        wait = WebDriverWait(driver, 10)
        heading = wait.until(EC.presence_of_element_located((By.ID, "firstHeading")))
        print(f"  Heading: {heading.text}")

        # Extract first paragraph
        first_para = driver.find_element(By.CSS_SELECTOR, "#mw-content-text p")
        print(f"  First para (100 chars): {first_para.text[:100]}...")

        # Count links on page
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"  Total links on page: {len(links)}")

        # Screenshot
        take_screenshot(driver, "/tmp/first_bot_screenshot.png")

        print("\n  Bot completed successfully!")

    except Exception as e:
        print(f"  Bot error: {e}")
    finally:
        if driver:
            driver.quit()
            print("  Browser closed.")


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 55)
    print("  SELENIUM — LESSON 1: SETUP & FIRST BOT")
    print("█" * 55)

    print("""
  SELENIUM QUICK REFERENCE:
  ─────────────────────────────────────────────────────
  driver.get(url)              → Navigate to URL
  driver.title                 → Get page title
  driver.current_url           → Get current URL
  driver.back() / .forward()   → Navigation history
  driver.refresh()             → Reload page
  driver.quit()                → Close browser
  driver.save_screenshot(path) → Take screenshot
  driver.execute_script(js)    → Run JavaScript
  driver.window_handles        → List open windows
  ─────────────────────────────────────────────────────
    """)

    # Uncomment to run (requires Chrome installed):
    # run_first_bot()

    print("  NOTE: Uncomment 'run_first_bot()' to execute.")
    print("  Requires: pip install selenium webdriver-manager")
    print("  Requires: Google Chrome installed")
    print("\n  NEXT: python module_2_selenium/02_locators.py")

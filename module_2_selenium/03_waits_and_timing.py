"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 3: WAITS & TIMING                         ║
╚══════════════════════════════════════════════════════════════════╝

WHY WAITS MATTER:
  Modern web apps load content dynamically (JavaScript, AJAX).
  If your bot clicks before an element loads — it crashes.
  Proper waits = reliable bots.

3 TYPES OF WAITS:
  ┌────────────────────────────────────────────────────────┐
  │  1. Implicit Wait  ← Global default (avoid overuse)    │
  │  2. Explicit Wait  ← BEST: wait for specific condition │
  │  3. time.sleep()   ← Avoid (wastes time, not smart)    │
  └────────────────────────────────────────────────────────┘

RULE: ALWAYS use Explicit Waits (WebDriverWait + EC)
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException,
)


# ─── 1. IMPLICIT WAIT (Set Once, Applies Globally) ────────────────────────────

def demo_implicit_wait():
    """
    Implicit wait: Selenium waits up to N seconds for ANY element.
    Set once when creating driver. Don't mix with explicit waits.

    WHEN TO USE: Only as a safe default fallback.
    """
    print("IMPLICIT WAIT:")
    print("""
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)  # Wait up to 5 seconds for elements

    # Now every find_element() automatically waits up to 5 seconds
    element = driver.find_element(By.ID, "slow-loading-element")
    """)


# ─── 2. EXPLICIT WAIT — The Right Way ─────────────────────────────────────────

def demo_explicit_waits():
    """
    Explicit wait: Wait for a SPECIFIC condition to be true.
    Much smarter than sleep() or implicit wait.
    """
    print("\n── EXPLICIT WAITS (WebDriverWait + Expected Conditions) ────")

    # All Expected Conditions from selenium.webdriver.support.expected_conditions
    ec_reference = {
        # ── Presence / Visibility
        "presence_of_element_located":        "Element exists in DOM (may be hidden)",
        "visibility_of_element_located":      "Element is visible on screen",
        "visibility_of":                      "Element (already found) becomes visible",
        "invisibility_of_element_located":    "Element becomes invisible/disappears",

        # ── Clickability
        "element_to_be_clickable":            "Element is visible AND enabled",
        "element_to_be_selected":             "Checkbox/radio is selected",

        # ── Text
        "text_to_be_present_in_element":      "Element contains specific text",
        "text_to_be_present_in_element_value": "Input's value attribute contains text",
        "title_is":                           "Page title equals string",
        "title_contains":                     "Page title contains string",

        # ── URL
        "url_contains":                       "Current URL contains string",
        "url_matches":                        "Current URL matches regex",
        "url_to_be":                          "Current URL equals string",

        # ── Multiple Elements
        "presence_of_all_elements_located":   "At least one element in list exists",
        "visibility_of_all_elements_located": "All elements in list are visible",

        # ── Frames & Windows
        "frame_to_be_available_and_switch_to_it": "Frame is ready, switches to it",
        "new_window_is_opened":               "A new window/tab was opened",
        "number_of_windows_to_be":            "Exact number of windows open",

        # ── Alerts
        "alert_is_present":                   "A JavaScript alert is present",

        # ── Staleness
        "staleness_of":                       "Element is no longer in DOM",
    }

    print("\n  ALL EXPECTED CONDITIONS:")
    for ec_name, description in ec_reference.items():
        print(f"  EC.{ec_name:<45} → {description}")


# ─── 3. PRACTICAL WAIT PATTERNS ───────────────────────────────────────────────

def wait_patterns_guide():
    """Common wait patterns used in real bots."""
    driver = None  # Would be real driver in production

    print("\n── PRACTICAL WAIT PATTERNS ─────────────────────────────────")

    # ── Pattern 1: Wait for element to be clickable (most common)
    pattern_1 = """
    wait = WebDriverWait(driver, 10)

    # Wait up to 10s for login button to be clickable
    login_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "login-btn"))
    )
    login_btn.click()
    """

    # ── Pattern 2: Wait for page to load (URL change)
    pattern_2 = """
    # After form submit, wait for redirect to dashboard
    wait.until(EC.url_contains("/dashboard"))
    print("Now on dashboard:", driver.current_url)
    """

    # ── Pattern 3: Wait for content to load
    pattern_3 = """
    # Wait for table rows to appear after search
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    """

    # ── Pattern 4: Wait for success message
    pattern_4 = """
    # Wait for "Form submitted successfully" to appear
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CLASS_NAME, "alert-success"),
            "successfully"
        )
    )
    """

    # ── Pattern 5: Wait for loading spinner to disappear
    pattern_5 = """
    # Wait for loading overlay to disappear
    wait.until(
        EC.invisibility_of_element_located((By.ID, "loading-spinner"))
    )
    # Page is ready!
    """

    # ── Pattern 6: Wait for alert
    pattern_6 = """
    # Submit might trigger a JavaScript confirm dialog
    wait.until(EC.alert_is_present())
    alert = driver.switch_to.alert
    print("Alert text:", alert.text)
    alert.accept()  # Click OK
    # alert.dismiss()  # Click Cancel
    """

    # ── Pattern 7: Custom wait condition
    pattern_7 = """
    # Wait for element count to be > 5
    from selenium.webdriver.support.ui import WebDriverWait

    def has_more_than_5_rows(driver):
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        return len(rows) > 5

    wait = WebDriverWait(driver, 15)
    wait.until(has_more_than_5_rows)
    """

    # ── Pattern 8: FluentWait (poll every N seconds)
    pattern_8 = """
    from selenium.webdriver.support.wait import WebDriverWait

    # Poll every 500ms, ignore specific exceptions, timeout 30s
    wait = WebDriverWait(
        driver,
        timeout=30,
        poll_frequency=0.5,
        ignored_exceptions=[StaleElementReferenceException]
    )

    element = wait.until(
        EC.visibility_of_element_located((By.ID, "dynamic-content"))
    )
    """

    patterns = [
        ("Wait for clickable",     pattern_1),
        ("Wait for URL change",    pattern_2),
        ("Wait for content load",  pattern_3),
        ("Wait for success msg",   pattern_4),
        ("Wait for spinner gone",  pattern_5),
        ("Wait for JS alert",      pattern_6),
        ("Custom wait condition",  pattern_7),
        ("FluentWait (polling)",   pattern_8),
    ]

    for name, code in patterns:
        print(f"\n  ► {name}:")
        print(code)


# ─── 4. HANDLING STALE ELEMENTS ───────────────────────────────────────────────

def handle_stale_element_pattern():
    """
    StaleElementReferenceException happens when:
    - Page refreshed after finding an element
    - AJAX reloaded part of the page
    - Angular/React re-rendered the component

    Solution: Re-find the element.
    """
    print("\n── STALE ELEMENT HANDLING ──────────────────────────────────")
    code = """
    from selenium.common.exceptions import StaleElementReferenceException

    def click_with_retry(driver, by, value, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                element = driver.find_element(by, value)
                element.click()
                return True
            except StaleElementReferenceException:
                print(f"Stale element, retry {attempt+1}/{max_attempts}")
                time.sleep(0.5)
        return False

    # Usage:
    click_with_retry(driver, By.ID, "submit-btn")
    """
    print(code)


# ─── 5. WAIT ANTI-PATTERNS (What NOT to do) ───────────────────────────────────

def wait_anti_patterns():
    print("\n── WAIT ANTI-PATTERNS (Avoid These!) ──────────────────────")

    print("""
  ❌ BAD: time.sleep(5)
     ─ Wastes time if page loads faster
     ─ Fails if page is slow
     ─ Not self-documenting

  ✓ GOOD: wait.until(EC.element_to_be_clickable((By.ID, "btn")))
     ─ Returns immediately when ready
     ─ Timeouts with clear error
     ─ Self-documenting

  ─────────────────────────────────────────────────────────────

  ❌ BAD: Mixing implicit and explicit waits
     driver.implicitly_wait(10)
     WebDriverWait(driver, 5).until(...)  # Unpredictable!

  ✓ GOOD: Use ONLY explicit waits, set implicit to 0
     driver.implicitly_wait(0)
     WebDriverWait(driver, 10).until(...)

  ─────────────────────────────────────────────────────────────

  ❌ BAD: wait.until(EC.presence_of_element_located(...))
         element.click()  # Element might not be clickable yet!

  ✓ GOOD: wait.until(EC.element_to_be_clickable(...))
         element.click()  # Element is visible AND enabled
    """)


# ─── 6. TIMING UTILITIES ──────────────────────────────────────────────────────

def timing_utilities():
    """Helper functions for timing in bots."""

    # Measure how long a page takes to load
    measure_load_code = """
    import time

    start = time.time()
    driver.get("https://example.com")
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    load_time = time.time() - start
    print(f"Page loaded in {load_time:.2f}s")
    """

    # Smart sleep with progress
    smart_sleep_code = """
    import time

    def smart_wait(seconds: float, reason: str = ""):
        '''
        Use time.sleep() ONLY when you MUST wait for
        non-element reasons (rate limiting, file download, etc.)
        '''
        print(f"  Waiting {seconds}s{f' ({reason})' if reason else ''}...")
        time.sleep(seconds)
    """

    print("\n── TIMING UTILITIES ─────────────────────────────────────────")
    print("  Measure page load time:")
    print(measure_load_code)
    print("  Smart sleep:")
    print(smart_sleep_code)


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  SELENIUM — LESSON 3: WAITS & TIMING")
    print("█" * 60)

    demo_implicit_wait()
    demo_explicit_waits()
    wait_patterns_guide()
    handle_stale_element_pattern()
    wait_anti_patterns()
    timing_utilities()

    print("\n" + "─" * 55)
    print("  WAIT GOLDEN RULES:")
    print("  1. ALWAYS use explicit waits (WebDriverWait + EC)")
    print("  2. Wait for the SPECIFIC condition you need")
    print("  3. Set a reasonable timeout (10-30s typical)")
    print("  4. Never use time.sleep() for element waits")
    print("  5. Handle TimeoutException gracefully")
    print("─" * 55)
    print("  NEXT: python module_2_selenium/04_forms_and_inputs.py")

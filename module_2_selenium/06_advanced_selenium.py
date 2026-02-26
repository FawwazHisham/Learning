"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 6: ADVANCED SELENIUM TECHNIQUES           ║
╚══════════════════════════════════════════════════════════════════╝

ADVANCED TOPICS:
  1. JavaScript execution (bypassing UI)
  2. Network interception (CDP)
  3. Cookies & session management
  4. Proxy configuration
  5. Browser profiles & extensions
  6. Parallel browser sessions
  7. Visual testing & screenshots
  8. Page Object Model (POM) design pattern
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import base64
from pathlib import Path


# ─── 1. JAVASCRIPT EXECUTION ──────────────────────────────────────────────────

def javascript_execution_guide():
    print("── 1. JAVASCRIPT EXECUTION ──────────────────────────────────")
    code = """
    # execute_script runs JS synchronously
    # execute_async_script runs JS asynchronously

    # ── Read page data
    title = driver.execute_script("return document.title;")
    url   = driver.execute_script("return window.location.href;")
    ready = driver.execute_script("return document.readyState;")

    # ── Scroll
    driver.execute_script("window.scrollTo(0, 0);")           # Top
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Bottom
    driver.execute_script("window.scrollBy(0, 300);")         # Down 300px

    # ── Scroll element into view
    element = driver.find_element(By.ID, "hidden-below")
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

    # ── Click hidden elements (not recommended but sometimes necessary)
    hidden_btn = driver.find_element(By.ID, "hidden-submit")
    driver.execute_script("arguments[0].click();", hidden_btn)

    # ── Highlight element (for debugging/screenshots)
    def highlight(driver, element, color="red", border=3):
        driver.execute_script(
            "arguments[0].style.border = arguments[1];",
            element, f"{border}px solid {color}"
        )

    # ── Set input value directly (bypasses React/Angular restrictions)
    input_el = driver.find_element(By.ID, "amount")
    driver.execute_script("arguments[0].value = '1000';", input_el)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}))",
        input_el
    )

    # ── Remove element (e.g., cookie banner)
    driver.execute_script(
        "var el = document.querySelector('.cookie-banner'); if(el) el.remove();"
    )

    # ── Get page performance metrics
    perf = driver.execute_script("return window.performance.timing;")
    load_time = perf['loadEventEnd'] - perf['navigationStart']
    print(f"Page load time: {load_time}ms")

    # ── Async script (for AJAX checks)
    result = driver.execute_async_script('''
        var callback = arguments[arguments.length - 1];
        fetch('/api/status')
            .then(r => r.json())
            .then(data => callback(data));
    ''')
    print("API status:", result)
    """
    print(code)


# ─── 2. COOKIES & SESSION MANAGEMENT ─────────────────────────────────────────

def cookies_and_sessions():
    print("\n── 2. COOKIES & SESSION MANAGEMENT ─────────────────────────")
    code = """
    import json, pickle

    # ── Get all cookies
    cookies = driver.get_cookies()
    print(f"Cookies: {len(cookies)}")

    # ── Get specific cookie
    session_cookie = driver.get_cookie("session_id")
    print(f"Session: {session_cookie['value']}")

    # ── Add a cookie (must be on the right domain first)
    driver.get("https://example.com")  # Navigate to domain first
    driver.add_cookie({
        "name": "session_token",
        "value": "abc123xyz",
        "domain": "example.com",
        "path": "/",
        "secure": True,
    })

    # ── Delete cookies
    driver.delete_cookie("old_cookie")
    driver.delete_all_cookies()

    # ── SAVE LOGIN SESSION (avoid re-logging in every run)
    def save_session(driver, filepath="session.pkl"):
        '''Save cookies after login for reuse.'''
        with open(filepath, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        print(f"Session saved to {filepath}")

    def load_session(driver, url, filepath="session.pkl"):
        '''Load saved cookies to restore login session.'''
        driver.get(url)  # Must navigate to domain first
        with open(filepath, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()  # Reload to apply cookies
        print("Session loaded and applied")

    # Usage:
    # First run: login normally, then save_session(driver)
    # Later runs: load_session(driver, "https://app.example.com")
    # Check if still logged in and skip login if so
    """
    print(code)


# ─── 3. CHROME DEVTOOLS PROTOCOL (CDP) ───────────────────────────────────────

def cdp_advanced():
    print("\n── 3. CHROME DEVTOOLS PROTOCOL (CDP) ───────────────────────")
    code = """
    # CDP gives direct access to Chrome internals

    # ── Intercept network requests
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setRequestInterception", {
        "patterns": [{"urlPattern": "*.jpg", "interceptionStage": "HeadersReceived"}]
    })

    # ── Block certain requests (e.g., ads, tracking)
    driver.execute_cdp_cmd("Network.setBlockedURLs", {
        "urls": ["*google-analytics*", "*doubleclick*", "*facebook.com/tr*"]
    })

    # ── Emulate mobile device
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "mobile": True,
        "width": 375,
        "height": 667,
        "deviceScaleFactor": 2,
    })

    # ── Set geolocation
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "accuracy": 100
    })

    # ── Capture full-page screenshot
    screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "format": "png",
        "captureBeyondViewport": True,  # Full page!
    })
    import base64
    with open("/tmp/full_page.png", "wb") as f:
        f.write(base64.b64decode(screenshot["data"]))

    # ── Print to PDF
    pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "format": "A4",
    })
    with open("/tmp/page.pdf", "wb") as f:
        f.write(base64.b64decode(pdf_data["data"]))
    """
    print(code)


# ─── 4. PARALLEL BROWSER SESSIONS ────────────────────────────────────────────

def parallel_sessions():
    print("\n── 4. PARALLEL BROWSER SESSIONS ─────────────────────────────")
    code = """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service

    def scrape_url(url: str) -> dict:
        '''Each thread gets its own driver instance.'''
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        try:
            driver.get(url)
            title = driver.title
            return {"url": url, "title": title, "success": True}
        except Exception as e:
            return {"url": url, "error": str(e), "success": False}
        finally:
            driver.quit()  # ALWAYS close driver in finally!

    # Process 5 URLs in parallel (5 browser instances)
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_url, url): url for url in urls}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"  Done: {result['url']} → {result.get('title', 'ERROR')}")

    print(f"Processed {len(results)} URLs")
    """
    print(code)


# ─── 5. PAGE OBJECT MODEL (POM) ───────────────────────────────────────────────

def page_object_model():
    """
    POM = Design pattern that separates:
    - Page structure (locators) from
    - Test/bot logic (what to do)

    Makes bots maintainable. If a locator changes,
    you only update it in ONE place.
    """
    print("\n── 5. PAGE OBJECT MODEL (POM) ───────────────────────────────")
    code = '''
    # ── Base Page (all pages inherit this)
    class BasePage:
        def __init__(self, driver):
            self.driver = driver
            self.wait = WebDriverWait(driver, 10)

        def find(self, by, value):
            return self.wait.until(EC.presence_of_element_located((by, value)))

        def click(self, by, value):
            self.wait.until(EC.element_to_be_clickable((by, value))).click()

        def type(self, by, value, text):
            el = self.find(by, value)
            el.clear()
            el.send_keys(text)

        def get_text(self, by, value) -> str:
            return self.find(by, value).text

        def wait_for_url(self, partial_url):
            self.wait.until(EC.url_contains(partial_url))

        def screenshot(self, name):
            self.driver.save_screenshot(f"/tmp/{name}.png")


    # ── Login Page
    class LoginPage(BasePage):
        URL = "https://app.example.com/login"

        # Locators (only defined here, not scattered in bot code)
        USERNAME_FIELD = (By.ID, "username")
        PASSWORD_FIELD = (By.ID, "password")
        LOGIN_BUTTON   = (By.CSS_SELECTOR, "button[type='submit']")
        ERROR_MSG      = (By.CLASS_NAME, "login-error")

        def open(self):
            self.driver.get(self.URL)
            return self

        def login(self, username: str, password: str) -> "DashboardPage":
            self.type(*self.USERNAME_FIELD, username)
            self.type(*self.PASSWORD_FIELD, password)
            self.click(*self.LOGIN_BUTTON)
            return DashboardPage(self.driver)

        def get_error(self) -> str:
            try:
                return self.get_text(*self.ERROR_MSG)
            except:
                return ""


    # ── Dashboard Page
    class DashboardPage(BasePage):
        WELCOME_MSG = (By.CLASS_NAME, "welcome-banner")
        REPORTS_BTN = (By.LINK_TEXT, "Reports")

        def is_loaded(self) -> bool:
            try:
                self.wait_for_url("/dashboard")
                return True
            except:
                return False

        def go_to_reports(self) -> "ReportsPage":
            self.click(*self.REPORTS_BTN)
            return ReportsPage(self.driver)


    # ── Using POM in a bot
    def run_bot(driver):
        login_page = LoginPage(driver).open()
        dashboard = login_page.login("admin", "password123")

        if dashboard.is_loaded():
            print("Login successful!")
            reports = dashboard.go_to_reports()
        else:
            error = login_page.get_error()
            print(f"Login failed: {error}")
    '''
    print(code)


# ─── 6. COMMON SELENIUM EXCEPTIONS ───────────────────────────────────────────

def exception_guide():
    print("\n── 6. SELENIUM EXCEPTION GUIDE ──────────────────────────────")
    exceptions = [
        ("NoSuchElementException",
         "Element not in DOM",
         "Check locator; wait for element; use try/except"),
        ("TimeoutException",
         "Element not found within wait time",
         "Increase timeout; check if page loaded; verify locator"),
        ("StaleElementReferenceException",
         "Element was in DOM but page changed",
         "Re-find element; use retry wrapper"),
        ("ElementClickInterceptedException",
         "Another element is blocking the click",
         "Scroll into view; close overlay; use JS click"),
        ("ElementNotInteractableException",
         "Element exists but can't be interacted with",
         "Wait for visibility; check if disabled; use JS"),
        ("WebDriverException",
         "Browser-level error",
         "Check ChromeDriver version; check Chrome version"),
        ("SessionNotCreatedException",
         "Can't create browser session",
         "Update ChromeDriver; check Chrome installation"),
        ("InvalidSelectorException",
         "Malformed CSS/XPath selector",
         "Validate selector in browser DevTools console"),
        ("MoveTargetOutOfBoundsException",
         "ActionChains target outside viewport",
         "Scroll element into view first"),
        ("UnexpectedAlertPresentException",
         "Alert appeared unexpectedly",
         "Handle/dismiss alert before other actions"),
    ]

    print(f"\n  {'Exception':<40} {'Cause':<30} Solution")
    print(f"  {'─'*40} {'─'*30} {'─'*30}")
    for exc, cause, solution in exceptions:
        print(f"  {exc:<40} {cause:<30}")
        print(f"  {'':40} {'':30} ↳ {solution}")
        print()


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  SELENIUM — LESSON 6: ADVANCED TECHNIQUES")
    print("█" * 60)

    javascript_execution_guide()
    cookies_and_sessions()
    cdp_advanced()
    parallel_sessions()
    page_object_model()
    exception_guide()

    print("\n" + "─" * 55)
    print("  ADVANCED SELENIUM SUMMARY:")
    print("  ► execute_script() for bypassing UI restrictions")
    print("  ► Save/load cookies to skip re-login")
    print("  ► CDP for network control & full-page screenshots")
    print("  ► ThreadPoolExecutor for parallel scraping")
    print("  ► Page Object Model for maintainable bots")
    print("─" * 55)
    print("  NEXT: python module_3_pyautogui/01_mouse_control.py")

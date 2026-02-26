# RPA Python Automation — CHEAT SHEET

## Selenium Quick Reference

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Setup
driver = webdriver.Chrome()
wait   = WebDriverWait(driver, 10)

# Navigation
driver.get("https://url.com")
driver.back() / driver.forward() / driver.refresh()
driver.quit()   # Always close!

# Locators (best → worst)
By.ID                    # "login-btn"
By.CSS_SELECTOR          # ".class", "#id", "tag[attr='val']"
By.XPATH                 # "//button[text()='Submit']"
By.NAME                  # "username"
By.LINK_TEXT             # "Click Here"

# Find elements
el = driver.find_element(By.ID, "submit")
els = driver.find_elements(By.CSS_SELECTOR, ".row")

# Interactions
el.click()
el.clear(); el.send_keys("text")
el.send_keys(Keys.ENTER)
el.text                             # Get text
el.get_attribute("href")            # Get attribute

# Waits (ALWAYS use explicit waits)
wait.until(EC.element_to_be_clickable((By.ID, "btn"))).click()
wait.until(EC.visibility_of_element_located((By.ID, "msg")))
wait.until(EC.url_contains("/dashboard"))
wait.until(EC.text_to_be_present_in_element((By.ID, "x"), "OK"))

# Dropdowns
from selenium.webdriver.support.ui import Select
Select(el).select_by_visible_text("Option A")
Select(el).select_by_value("opt_a")

# ActionChains
ActionChains(driver).move_to_element(el).perform()  # Hover
ActionChains(driver).context_click(el).perform()    # Right click
ActionChains(driver).drag_and_drop(src, tgt).perform()

# JavaScript
driver.execute_script("return document.title")
driver.execute_script("arguments[0].click()", el)
driver.execute_script("window.scrollTo(0, 0)")

# Frames
driver.switch_to.frame("frame-id")
driver.switch_to.default_content()
```

---

## PyAutoGUI Quick Reference

```python
import pyautogui, time
pyautogui.FAILSAFE = True   # NEVER disable!
pyautogui.PAUSE = 0.05

# Screen info
w, h = pyautogui.size()
x, y = pyautogui.position()

# Mouse
pyautogui.moveTo(x, y, duration=0.5)
pyautogui.moveRel(dx, dy)
pyautogui.click(x, y)
pyautogui.click(x, y, button='right')
pyautogui.doubleClick(x, y)
pyautogui.scroll(-3)              # Scroll down
pyautogui.dragTo(x, y, duration=0.5)

# Keyboard
pyautogui.typewrite("text", interval=0.05)
pyautogui.press("enter")
pyautogui.hotkey("ctrl", "c")
pyautogui.keyDown("shift"); pyautogui.keyUp("shift")

# Screenshots
img = pyautogui.screenshot()
img = pyautogui.screenshot(region=(x, y, w, h))
img.save("/tmp/screen.png")

# Image recognition
pos = pyautogui.locateCenterOnScreen("btn.png", confidence=0.85)
if pos: pyautogui.click(pos)

# OCR
import pytesseract
text = pytesseract.image_to_string(img, config="--psm 6")
```

---

## Requests (API) Quick Reference

```python
import requests

# Basic requests
r = requests.get(url, params={"key": "val"}, timeout=10)
r = requests.post(url, json={"field": "val"})
r = requests.put(url, json=data)
r = requests.patch(url, json=partial_data)
r = requests.delete(url)

# Response
r.status_code        # 200, 404, etc.
r.ok                 # True if 200-299
r.json()             # Parse JSON body
r.text               # Raw text
r.content            # Raw bytes
r.headers            # Response headers
r.raise_for_status() # Raises on 4xx/5xx

# Session (reuse headers/cookies)
with requests.Session() as s:
    s.headers["Authorization"] = "Bearer token"
    s.get(url1)
    s.post(url2, json=data)

# Auth types
requests.get(url, auth=("user", "pass"))           # Basic Auth
requests.get(url, headers={"X-API-Key": key})      # API Key
requests.get(url, headers={"Authorization": f"Bearer {token}"})

# Download file
with requests.get(url, stream=True) as r:
    with open("file.pdf", "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
```

---

## Error Handling Patterns

```python
# Selenium exceptions
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

# API exceptions
try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
except requests.Timeout:
    print("Timed out")
except requests.HTTPError as e:
    print(f"HTTP {e.response.status_code}")
except requests.ConnectionError:
    print("No connection")

# Retry with tenacity
from tenacity import retry, stop_after_attempt, wait_exponential
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=60))
def unreliable_function():
    ...
```

---

## Bot Architecture Pattern

```python
# 1. Config
@dataclass
class BotConfig:
    target_url: str
    username: str = os.getenv("BOT_USER", "")
    password: str = os.getenv("BOT_PASS", "")
    headless: bool = True
    timeout: int = 30

# 2. Base Bot
class BaseBot:
    def __init__(self, config): ...
    def with_retry(self, func, *args): ...   # Auto-retry
    def record(self, action, success): ...   # Log results
    def save_report(self): ...               # CSV report
    def run(self): raise NotImplementedError # Override

# 3. Concrete Bot
class MyBot(BaseBot):
    def login(self): ...
    def process(self): ...
    def run(self):
        self.login()
        self.process()

# 4. Run safely
bot = MyBot(BotConfig(target_url="https://..."))
bot.start()  # Handles setup, cleanup, reporting
```

---

## Common Patterns

```python
# ── Wait for element, click safely
def safe_click(driver, by, value, timeout=10):
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    ).click()

# ── Extract table data
rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
data = [[cell.text for cell in row.find_elements(By.TAG_NAME, "td")] for row in rows]

# ── Scroll to element
driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element)

# ── Type unicode text (clipboard trick)
import pyperclip
pyperclip.copy("Unicode text: 中文 🚀")
pyautogui.hotkey("ctrl", "v")

# ── Wait for window (PyAutoGUI)
import pygetwindow as gw
def wait_for_window(title, timeout=10):
    for _ in range(timeout * 2):
        wins = gw.getWindowsWithTitle(title)
        if wins: return wins[0]
        time.sleep(0.5)
    raise TimeoutError(f"Window not found: {title}")

# ── Paginated API fetch
def get_all_pages(api, endpoint, per_page=100):
    all_items, page = [], 1
    while True:
        items = api.get(endpoint, params={"page": page, "per_page": per_page})
        if not items: break
        all_items.extend(items)
        if len(items) < per_page: break
        page += 1
    return all_items
```

---

## Decision Guide: Which Tool to Use?

```
Need to automate a WEB APP?
  ├─ Has API?  ──────────► Use requests (FASTEST, most reliable)
  └─ No API
      ├─ Login required? ─► Selenium (with session cookies)
      └─ Public data?  ───► requests + BeautifulSoup (static)
                         └─► Selenium (if JS-rendered)

Need to automate a DESKTOP APP?
  ├─ Excel/Word? ─────────► openpyxl / python-pptx (no UI needed)
  ├─ Has keyboard shortcuts? ► PyAutoGUI hotkeys (most reliable)
  ├─ Has UI you can see? ─► PyAutoGUI + image recognition
  └─ Legacy app with no API? ► PyAutoGUI + OCR

Need to MOVE DATA between systems?
  ├─ Both have APIs? ─────► requests (pure API pipeline)
  ├─ Source is web, target is API? ► Selenium + requests
  └─ Neither has API? ────► PyAutoGUI (last resort)
```

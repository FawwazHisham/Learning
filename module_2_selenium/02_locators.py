"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 2: ELEMENT LOCATORS                       ║
╚══════════════════════════════════════════════════════════════════╝

LOCATORS = How Selenium finds elements on a web page
  Finding the right element is 80% of web automation.

THE 8 LOCATOR STRATEGIES (ranked best to worst):
  ┌─────────────────────────────────────────────────────────┐
  │  1. ID             ← BEST: unique, fast, stable          │
  │  2. CSS Selector   ← Powerful, flexible, fast            │
  │  3. XPath          ← Most powerful but verbose           │
  │  4. Name           ← Good for form fields                │
  │  5. Link Text      ← For anchor tags                     │
  │  6. Partial Link   ← Partial text match for anchors      │
  │  7. Tag Name       ← Too broad, use sparingly            │
  │  8. Class Name     ← Often not unique, use CSS instead   │
  └─────────────────────────────────────────────────────────┘

INSPECT ELEMENTS IN BROWSER:
  → Right-click element → "Inspect"
  → Or press F12 to open DevTools
  → In Elements tab: right-click → Copy → Copy selector
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


# ─── LOCATOR REFERENCE GUIDE ──────────────────────────────────────────────────

LOCATOR_EXAMPLES = {

    # ── ID (ALWAYS use if available)
    # HTML: <input id="search-box" />
    "id": (By.ID, "search-box"),

    # ── CSS Selector (most versatile)
    "css_class":     (By.CSS_SELECTOR, ".submit-btn"),          # by class
    "css_id":        (By.CSS_SELECTOR, "#login-form"),          # by id
    "css_tag":       (By.CSS_SELECTOR, "button[type='submit']"),# by attribute
    "css_child":     (By.CSS_SELECTOR, "form > input"),         # direct child
    "css_contains":  (By.CSS_SELECTOR, "a[href*='dashboard']"), # href contains
    "css_starts":    (By.CSS_SELECTOR, "a[href^='/admin']"),    # href starts with
    "css_nth":       (By.CSS_SELECTOR, "tr:nth-child(2) td"),   # nth row, all cells
    "css_first":     (By.CSS_SELECTOR, ".result-item:first-child"),

    # ── XPath (when CSS isn't enough)
    "xpath_id":      (By.XPATH, "//*[@id='submit']"),
    "xpath_text":    (By.XPATH, "//button[text()='Login']"),     # exact text
    "xpath_contains":(By.XPATH, "//a[contains(text(),'Home')]"), # contains text
    "xpath_parent":  (By.XPATH, "//input[@name='email']/.."),    # parent element
    "xpath_sibling": (By.XPATH, "//label[text()='Name']/following-sibling::input"),
    "xpath_index":   (By.XPATH, "(//tr)[3]/td[2]"),              # 3rd row, 2nd cell
    "xpath_attr":    (By.XPATH, "//input[@placeholder='Search']"),

    # ── Name (HTML forms)
    # HTML: <input name="username" />
    "name": (By.NAME, "username"),

    # ── Link Text (exact match)
    # HTML: <a href="/home">Home</a>
    "link_text": (By.LINK_TEXT, "Home"),

    # ── Partial Link Text
    # HTML: <a href="/dashboard">Go to Dashboard</a>
    "partial_link": (By.PARTIAL_LINK_TEXT, "Dashboard"),

    # ── Tag Name (gets all matching elements)
    "tag_name": (By.TAG_NAME, "button"),   # finds ALL buttons

    # ── Class Name
    "class_name": (By.CLASS_NAME, "error-message"),
}


# ─── CSS SELECTOR CHEAT SHEET ─────────────────────────────────────────────────

CSS_CHEATSHEET = """
CSS SELECTOR CHEAT SHEET
─────────────────────────────────────────────────────────────────────
SELECTOR              │ MATCHES
─────────────────────────────────────────────────────────────────────
#myId                 │ <div id="myId">
.myClass              │ <div class="myClass">
div                   │ All <div> elements
div.myClass           │ <div class="myClass"> (tag + class)
div#myId              │ <div id="myId"> (tag + id)
a[href]               │ <a> with any href attribute
a[href="url"]         │ <a href="url"> (exact match)
a[href*="keyword"]    │ href containing "keyword"
a[href^="https"]      │ href starting with "https"
a[href$=".pdf"]       │ href ending with ".pdf"
div > p               │ <p> direct child of <div>
div p                 │ <p> anywhere inside <div>
div + p               │ <p> immediately after <div>
div ~ p               │ All <p> after <div> (siblings)
li:first-child        │ First <li> in its parent
li:last-child         │ Last <li> in its parent
li:nth-child(2)       │ Second <li>
li:nth-child(odd)     │ Odd-numbered <li> elements
input:not([disabled]) │ <input> that is not disabled
─────────────────────────────────────────────────────────────────────
"""

XPATH_CHEATSHEET = """
XPATH CHEAT SHEET
─────────────────────────────────────────────────────────────────────
XPATH                          │ MEANING
─────────────────────────────────────────────────────────────────────
//div                          │ Any <div> anywhere
//div[@id='box']               │ <div id="box">
//div[@class='info']           │ <div class="info"> (exact)
//div[contains(@class,'info')] │ class contains "info"
//button[text()='Submit']      │ <button> with exact text
//button[.='Submit']           │ Same (shorthand)
//a[contains(text(),'Click')]  │ Text contains "Click"
//input[@type='text']          │ Text input fields
//div[@id='parent']/child::*   │ All direct children
//div[@id='box']/..            │ Parent of #box
//tr[3]/td[2]                  │ Row 3, cell 2
(//div[@class='row'])[2]       │ Second element in set
//div[not(@class)]             │ <div> without class
//input[@name and @id]         │ Has both name and id attrs
─────────────────────────────────────────────────────────────────────
"""


# ─── PRACTICAL LOCATOR FUNCTIONS ──────────────────────────────────────────────

def find_element_safe(driver, by, value, timeout=10):
    """
    Safe element finder with explicit wait.
    Always use this instead of driver.find_element() directly.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except TimeoutException:
        print(f"  TIMEOUT: Element not found — ({by}, '{value}')")
        return None
    except Exception as e:
        print(f"  ERROR finding element: {e}")
        return None


def find_elements_safe(driver, by, value, timeout=10):
    """
    Safe finder for multiple elements.
    Returns empty list if none found (never raises).
    """
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((by, value)))
        return driver.find_elements(by, value)
    except TimeoutException:
        return []  # Return empty list, not an error
    except Exception:
        return []


def get_element_info(element) -> dict:
    """Extract all useful info from an element."""
    try:
        return {
            "tag":       element.tag_name,
            "text":      element.text,
            "id":        element.get_attribute("id"),
            "class":     element.get_attribute("class"),
            "href":      element.get_attribute("href"),
            "value":     element.get_attribute("value"),
            "visible":   element.is_displayed(),
            "enabled":   element.is_enabled(),
            "selected":  element.is_selected(),
            "location":  element.location,
            "size":      element.size,
        }
    except Exception as e:
        return {"error": str(e)}


# ─── REAL-WORLD LOCATOR PATTERNS ──────────────────────────────────────────────

def demo_real_patterns():
    """
    Common locator patterns you'll use in real bots.
    (These are code templates — not executed here)
    """
    driver = None  # Would be: create_driver()

    print("PATTERN 1: Find table rows and extract data")
    code_pattern_1 = """
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            data.append({
                "name":   cells[0].text,
                "email":  cells[1].text,
                "status": cells[2].text,
            })
    """
    print(code_pattern_1)

    print("PATTERN 2: Find element by partial text")
    code_pattern_2 = """
    # Find a button containing the word "Submit"
    btn = driver.find_element(
        By.XPATH, "//button[contains(text(), 'Submit')]"
    )
    btn.click()
    """
    print(code_pattern_2)

    print("PATTERN 3: Find a form field by its label")
    code_pattern_3 = """
    # If label says "Email Address:", find the next input sibling
    email_field = driver.find_element(
        By.XPATH, "//label[contains(text(),'Email')]/following-sibling::input"
    )
    email_field.send_keys("user@example.com")
    """
    print(code_pattern_3)

    print("PATTERN 4: Find all links in navigation menu")
    code_pattern_4 = """
    nav_links = driver.find_elements(By.CSS_SELECTOR, "nav a")
    for link in nav_links:
        print(f"  {link.text} → {link.get_attribute('href')}")
    """
    print(code_pattern_4)

    print("PATTERN 5: Wait for specific text to appear")
    code_pattern_5 = """
    wait = WebDriverWait(driver, 15)
    # Wait until element with text "Success" is visible
    success_msg = wait.until(
        EC.text_to_be_present_in_element(
            (By.CLASS_NAME, "status-message"), "Success"
        )
    )
    """
    print(code_pattern_5)


# ─── LOCATOR DEBUGGER (run in browser console) ─────────────────────────────────

JS_LOCATOR_TESTER = """
// Paste this in browser DevTools console to test selectors:

// Test CSS selector:
document.querySelectorAll('.your-selector').length  // count matches
document.querySelector('.your-selector')           // first match

// Test XPath:
document.evaluate('//your/xpath', document, null,
  XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotLength
"""


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  SELENIUM — LESSON 2: ELEMENT LOCATORS")
    print("█" * 60)

    print(CSS_CHEATSHEET)
    print(XPATH_CHEATSHEET)

    print("\n── LOCATOR STRATEGIES (ordered by preference) ──────────────")
    strategies = [
        ("1. By.ID",              "By.ID, 'submit-btn'",          "BEST — always unique"),
        ("2. By.CSS_SELECTOR",    "By.CSS_SELECTOR, '#id .cls'",  "Very powerful, fast"),
        ("3. By.XPATH",           "By.XPATH, '//button[...]'",    "Most powerful"),
        ("4. By.NAME",            "By.NAME, 'username'",          "Good for form fields"),
        ("5. By.LINK_TEXT",       "By.LINK_TEXT, 'Click Here'",   "Exact anchor text"),
        ("6. By.PARTIAL_LINK_TEXT","By.PARTIAL_LINK_TEXT, 'Click'","Partial anchor text"),
        ("7. By.TAG_NAME",        "By.TAG_NAME, 'button'",        "Use with find_elements"),
        ("8. By.CLASS_NAME",      "By.CLASS_NAME, 'btn-primary'", "Often not unique"),
    ]
    for strat, example, note in strategies:
        print(f"  {strat:<25} │ {example:<35} │ {note}")

    demo_real_patterns()

    print("\n  NEXT: python module_2_selenium/03_waits_and_timing.py")

"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 4: FORMS, INPUTS & USER INTERACTIONS      ║
╚══════════════════════════════════════════════════════════════════╝

FORM INTERACTIONS:
  ► Text input         : send_keys()
  ► Click              : click()
  ► Dropdowns          : Select class
  ► Checkboxes/Radio   : click() if not selected
  ► File upload        : send_keys(filepath)
  ► Date pickers       : JS injection or keyboard
  ► Drag & drop        : ActionChains
  ► Right-click        : ActionChains
  ► Hover              : ActionChains
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# ─── 1. TEXT INPUT ────────────────────────────────────────────────────────────

def text_input_patterns():
    """All ways to interact with text input fields."""
    driver = None  # Real driver in production

    print("── TEXT INPUT ───────────────────────────────────────────────")
    code = """
    wait = WebDriverWait(driver, 10)

    # ── Basic send_keys
    field = wait.until(EC.element_to_be_clickable((By.ID, "username")))
    field.clear()               # Clear existing text first!
    field.send_keys("my_user")  # Type text

    # ── Clear and type in one line
    driver.find_element(By.ID, "search").clear()
    driver.find_element(By.ID, "search").send_keys("python RPA")

    # ── Using Keys for special keys
    from selenium.webdriver.common.keys import Keys

    field.send_keys(Keys.CONTROL + "a")  # Select all
    field.send_keys(Keys.BACKSPACE)      # Delete
    field.send_keys(Keys.ENTER)          # Press Enter (submit forms)
    field.send_keys(Keys.TAB)            # Move to next field
    field.send_keys(Keys.ESCAPE)         # Close modal/dropdown

    # ── Simulate typing (human-like, slower but more realistic)
    import time
    text = "Hello World"
    for char in text:
        field.send_keys(char)
        time.sleep(0.05)  # 50ms between keystrokes

    # ── Get current value
    current_value = field.get_attribute("value")
    print(f"Field value: {current_value}")

    # ── Using JavaScript to set value (when send_keys doesn't work)
    driver.execute_script(
        "arguments[0].value = arguments[1];",
        field, "new value"
    )
    # Trigger the change event so the app detects the change
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
        field
    )
    """
    print(code)


# ─── 2. DROPDOWN MENUS ────────────────────────────────────────────────────────

def dropdown_patterns():
    """Select elements (HTML <select> dropdowns)."""
    driver = None

    print("\n── DROPDOWN MENUS ───────────────────────────────────────────")
    code = """
    from selenium.webdriver.support.ui import Select

    # Find the select element
    dropdown_element = driver.find_element(By.ID, "country-select")
    dropdown = Select(dropdown_element)

    # ── Select by visible text
    dropdown.select_by_visible_text("United States")

    # ── Select by value attribute
    # <option value="us">United States</option>
    dropdown.select_by_value("us")

    # ── Select by index (0-based)
    dropdown.select_by_index(0)  # First option

    # ── Get selected option
    selected = dropdown.first_selected_option
    print(f"Selected: {selected.text}")

    # ── Get all options
    for option in dropdown.options:
        print(f"  {option.get_attribute('value')}: {option.text}")

    # ── Multi-select dropdowns
    multi_dropdown = Select(driver.find_element(By.ID, "tags"))
    if multi_dropdown.is_multiple:
        multi_dropdown.select_by_visible_text("Python")
        multi_dropdown.select_by_visible_text("Automation")
        # Deselect
        multi_dropdown.deselect_by_visible_text("Python")
        multi_dropdown.deselect_all()

    # ── CUSTOM DROPDOWNS (not <select> elements - use click)
    # These are div-based dropdowns (Bootstrap, Material UI, etc.)
    dropdown_trigger = driver.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
    dropdown_trigger.click()
    # Wait for options to appear
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".dropdown-menu"))
    )
    option = driver.find_element(By.XPATH, "//li[text()='Option 1']")
    option.click()
    """
    print(code)


# ─── 3. CHECKBOXES & RADIO BUTTONS ───────────────────────────────────────────

def checkbox_radio_patterns():
    print("\n── CHECKBOXES & RADIO BUTTONS ──────────────────────────────")
    code = """
    # ── Checkbox
    checkbox = driver.find_element(By.ID, "terms-checkbox")

    # Check only if not already checked
    if not checkbox.is_selected():
        checkbox.click()

    # Uncheck only if checked
    if checkbox.is_selected():
        checkbox.click()

    # ── Radio buttons
    # Select "Male" radio button
    male_radio = driver.find_element(
        By.XPATH, "//input[@type='radio'][@value='male']"
    )
    if not male_radio.is_selected():
        male_radio.click()

    # Get all radio options in a group
    radios = driver.find_elements(
        By.XPATH, "//input[@name='gender'][@type='radio']"
    )
    for radio in radios:
        print(f"  {radio.get_attribute('value')}: {'✓' if radio.is_selected() else '○'}")
    """
    print(code)


# ─── 4. FILE UPLOAD ───────────────────────────────────────────────────────────

def file_upload_patterns():
    print("\n── FILE UPLOAD ──────────────────────────────────────────────")
    code = """
    import os

    # ── Standard file input (<input type="file">)
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    # Send the full absolute path to the file
    file_path = os.path.abspath("/path/to/document.pdf")
    file_input.send_keys(file_path)

    # ── Multiple file upload
    file_input.send_keys(
        os.path.abspath("file1.pdf") + "\\n" +
        os.path.abspath("file2.pdf")
    )

    # ── Drag and drop file (using JavaScript)
    # For drag-and-drop zones (not standard file inputs)
    js = '''
        var input = document.createElement('input');
        input.type = 'file';
        input.onchange = function() {
            var files = this.files;
            var event = new Event('drop');
            event.dataTransfer = { files: files };
            document.querySelector('.drop-zone').dispatchEvent(event);
        };
        input.click();
    '''
    # Note: This technique varies by app. Inspect the specific drop zone.
    """
    print(code)


# ─── 5. ACTION CHAINS — Advanced Interactions ────────────────────────────────

def action_chains_patterns():
    """ActionChains for complex mouse/keyboard interactions."""
    print("\n── ACTION CHAINS ────────────────────────────────────────────")
    code = """
    from selenium.webdriver.common.action_chains import ActionChains

    actions = ActionChains(driver)

    # ── Hover over element (reveals dropdown menu)
    menu = driver.find_element(By.ID, "nav-products")
    actions.move_to_element(menu).perform()
    # Now submenu should be visible
    submenu_item = driver.find_element(By.LINK_TEXT, "Electronics")
    submenu_item.click()

    # ── Right-click (context menu)
    element = driver.find_element(By.ID, "file-item")
    actions.context_click(element).perform()
    # Click option in context menu
    driver.find_element(By.LINK_TEXT, "Delete").click()

    # ── Double-click
    cell = driver.find_element(By.CSS_SELECTOR, "td.editable")
    actions.double_click(cell).perform()

    # ── Drag and drop
    source = driver.find_element(By.ID, "drag-item")
    target = driver.find_element(By.ID, "drop-zone")
    actions.drag_and_drop(source, target).perform()

    # ── Drag and drop by offset (pixels)
    actions.drag_and_drop_by_offset(source, 200, 0).perform()

    # ── Click and hold, then move (slider)
    slider = driver.find_element(By.ID, "range-slider")
    actions.click_and_hold(slider).move_by_offset(50, 0).release().perform()

    # ── Key combinations
    actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()  # Ctrl+A
    actions.key_down(Keys.CONTROL).send_keys("c").key_up(Keys.CONTROL).perform()  # Ctrl+C

    # ── Chained actions (build sequence, then perform once)
    actions = ActionChains(driver)
    actions.move_to_element(menu)
    actions.pause(0.5)             # Wait 500ms
    actions.click(menu)
    actions.send_keys("search term")
    actions.send_keys(Keys.ENTER)
    actions.perform()              # Execute all at once
    """
    print(code)


# ─── 6. FRAMES & IFRAMES ──────────────────────────────────────────────────────

def iframe_patterns():
    """Switching to and from iframes."""
    print("\n── IFRAMES ──────────────────────────────────────────────────")
    code = """
    # Elements inside an <iframe> are not accessible from the main page.
    # You must switch into the iframe first.

    # ── Switch by index
    driver.switch_to.frame(0)

    # ── Switch by name/id attribute
    driver.switch_to.frame("my-iframe")

    # ── Switch by WebElement
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe.editor-frame")
    driver.switch_to.frame(iframe)

    # ── Interact with content inside iframe
    editor = driver.find_element(By.CSS_SELECTOR, ".editor-content")
    editor.send_keys("Hello from inside iframe!")

    # ── Switch back to main page
    driver.switch_to.default_content()

    # ── Nested iframes
    driver.switch_to.frame("outer-frame")
    driver.switch_to.frame("inner-frame")
    # ... interact
    driver.switch_to.parent_frame()   # Go up one level
    driver.switch_to.default_content()  # Back to main
    """
    print(code)


# ─── 7. ALERTS & DIALOGS ──────────────────────────────────────────────────────

def alert_patterns():
    """JavaScript alerts, confirms, and prompts."""
    print("\n── ALERTS & DIALOGS ─────────────────────────────────────────")
    code = """
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(driver, 10)

    # ── Alert (just OK button)
    wait.until(EC.alert_is_present())
    alert = driver.switch_to.alert
    print(f"Alert says: {alert.text}")
    alert.accept()   # Click OK

    # ── Confirm dialog (OK / Cancel)
    wait.until(EC.alert_is_present())
    confirm = driver.switch_to.alert
    print(f"Confirm: {confirm.text}")
    confirm.accept()   # Click OK
    # confirm.dismiss()  # Click Cancel

    # ── Prompt (text input + OK/Cancel)
    wait.until(EC.alert_is_present())
    prompt = driver.switch_to.alert
    prompt.send_keys("My input text")   # Type in the prompt
    prompt.accept()
    """
    print(code)


# ─── 8. FORM SUBMISSION STRATEGIES ───────────────────────────────────────────

def form_submission_strategies():
    print("\n── FORM SUBMISSION STRATEGIES ───────────────────────────────")
    code = """
    # Strategy 1: Click submit button
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    # Strategy 2: Press Enter on last field
    last_field = driver.find_element(By.ID, "password")
    last_field.send_keys(Keys.ENTER)

    # Strategy 3: Submit the form element directly
    form = driver.find_element(By.TAG_NAME, "form")
    form.submit()

    # Strategy 4: JavaScript submit (when button is hidden/disabled)
    driver.execute_script("document.getElementById('myForm').submit();")

    # After submit: wait for result
    wait = WebDriverWait(driver, 15)
    # Wait for success message
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "success")))
    # OR wait for URL to change
    wait.until(EC.url_contains("/confirmation"))
    # OR wait for redirect
    wait.until(EC.title_contains("Thank You"))
    """
    print(code)


# ─── 9. COMPLETE FORM FILLER EXAMPLE ─────────────────────────────────────────

def complete_form_filler_demo():
    """Template for a complete form automation bot."""
    print("\n── COMPLETE FORM FILLER TEMPLATE ────────────────────────────")
    code = '''
    def fill_registration_form(driver, data: dict):
        """
        Fill and submit a registration form.
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "country": "United States",
            "agree_terms": True,
        }
        """
        wait = WebDriverWait(driver, 10)

        # Navigate to form
        driver.get("https://example.com/register")

        # Fill text fields
        wait.until(EC.visibility_of_element_located((By.ID, "first_name")))

        driver.find_element(By.ID, "first_name").clear()
        driver.find_element(By.ID, "first_name").send_keys(data["first_name"])

        driver.find_element(By.ID, "last_name").clear()
        driver.find_element(By.ID, "last_name").send_keys(data["last_name"])

        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys(data["email"])

        # Select dropdown
        country_select = Select(driver.find_element(By.ID, "country"))
        country_select.select_by_visible_text(data["country"])

        # Check terms checkbox
        terms = driver.find_element(By.ID, "terms")
        if data["agree_terms"] and not terms.is_selected():
            terms.click()

        # Submit
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Wait for confirmation
        try:
            wait.until(EC.url_contains("/success"))
            return {"success": True, "url": driver.current_url}
        except TimeoutException:
            error = driver.find_element(By.CLASS_NAME, "error-msg")
            return {"success": False, "error": error.text}
    '''
    print(code)


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  SELENIUM — LESSON 4: FORMS & USER INTERACTIONS")
    print("█" * 60)

    text_input_patterns()
    dropdown_patterns()
    checkbox_radio_patterns()
    file_upload_patterns()
    action_chains_patterns()
    iframe_patterns()
    alert_patterns()
    form_submission_strategies()
    complete_form_filler_demo()

    print("\n" + "─" * 55)
    print("  KEY TAKEAWAYS:")
    print("  ► Always .clear() before .send_keys()")
    print("  ► Use Select class for <select> dropdowns")
    print("  ► Use ActionChains for hover, drag, right-click")
    print("  ► Switch frames before interacting with iframe content")
    print("  ► Wait for alerts before switching to them")
    print("─" * 55)
    print("  NEXT: python module_2_selenium/05_web_scraping.py")

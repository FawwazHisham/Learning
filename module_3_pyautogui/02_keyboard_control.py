"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 3 — LESSON 2: KEYBOARD CONTROL                       ║
╚══════════════════════════════════════════════════════════════════╝

KEYBOARD AUTOMATION:
  ► typewrite()  → Type a string (with human-like speed)
  ► press()      → Press a single key
  ► hotkey()     → Press key combinations (Ctrl+C, Alt+Tab)
  ► keyDown()/keyUp() → Hold/release keys
"""

import time
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


# ─── 1. TYPING TEXT ───────────────────────────────────────────────────────────

print("── 1. TYPING TEXT ───────────────────────────────────────────")

typing_reference = """
TYPING FUNCTIONS:
────────────────────────────────────────────────────────────────────────
pyautogui.typewrite('Hello')            → Types 'Hello' fast
pyautogui.typewrite('Hello', interval=0.1) → Types with 0.1s between keys

⚠ typewrite() only works with ASCII characters!
  For special chars (accents, unicode), use:
  pyautogui.write('Hello')  (newer API, same as typewrite)

  Or use clipboard trick for unicode:
  import pyperclip
  pyperclip.copy('Héllo Wörld')
  pyautogui.hotkey('ctrl', 'v')
────────────────────────────────────────────────────────────────────────
"""
print(typing_reference)


# ─── 2. KEY PRESS ────────────────────────────────────────────────────────────

print("── 2. SINGLE KEY PRESS ──────────────────────────────────────")

key_reference = """
ALL SPECIAL KEYS:
────────────────────────────────────────────────────────────────────────
NAVIGATION:   'up', 'down', 'left', 'right'
              'home', 'end', 'pageup', 'pagedown'
              'tab', 'escape', 'enter', 'return', 'backspace'
              'delete', 'insert'

FUNCTION KEYS: 'f1' through 'f12'

MODIFIERS:    'shift', 'ctrl', 'alt', 'win' (Windows key), 'command' (Mac)

MEDIA KEYS:   'volumeup', 'volumedown', 'volumemute'
              'playpause', 'nexttrack', 'prevtrack'

SPECIAL:      'space', 'printscreen', 'capslock', 'numlock', 'scrolllock'
              'pause', 'apps' (context menu key)

NUMBER PAD:   'num0'–'num9', 'numlock', 'add', 'subtract', 'multiply',
              'divide', 'decimal', 'separator'
────────────────────────────────────────────────────────────────────────

USAGE:
  pyautogui.press('enter')         → Press Enter
  pyautogui.press('f5')            → Press F5 (refresh)
  pyautogui.press('escape')        → Press Escape
  pyautogui.press(['left','left']) → Press left arrow twice
"""
print(key_reference)


# ─── 3. HOTKEYS (KEY COMBINATIONS) ───────────────────────────────────────────

print("── 3. HOTKEYS ───────────────────────────────────────────────")

hotkey_reference = """
COMMON HOTKEYS:
────────────────────────────────────────────────────────────────────────
pyautogui.hotkey('ctrl', 'c')          → Copy
pyautogui.hotkey('ctrl', 'v')          → Paste
pyautogui.hotkey('ctrl', 'x')          → Cut
pyautogui.hotkey('ctrl', 'z')          → Undo
pyautogui.hotkey('ctrl', 'y')          → Redo
pyautogui.hotkey('ctrl', 's')          → Save
pyautogui.hotkey('ctrl', 'a')          → Select All
pyautogui.hotkey('ctrl', 'f')          → Find
pyautogui.hotkey('ctrl', 'n')          → New
pyautogui.hotkey('ctrl', 'o')          → Open
pyautogui.hotkey('ctrl', 'p')          → Print
pyautogui.hotkey('ctrl', 'w')          → Close tab/window
pyautogui.hotkey('ctrl', 't')          → New tab (browser)
pyautogui.hotkey('ctrl', 'shift', 'i') → DevTools (browser)
pyautogui.hotkey('alt', 'tab')         → Switch windows
pyautogui.hotkey('alt', 'f4')          → Close window
pyautogui.hotkey('win', 'd')           → Show desktop (Windows)
pyautogui.hotkey('ctrl', 'alt', 't')   → Terminal (Linux)
────────────────────────────────────────────────────────────────────────
"""
print(hotkey_reference)


# ─── 4. KEY DOWN / KEY UP ────────────────────────────────────────────────────

print("── 4. KEY DOWN / KEY UP ─────────────────────────────────────")

keydown_reference = """
HOLD KEYS (for shift+click, ctrl+click, etc.):
────────────────────────────────────────────────────────────────────────
# Hold Shift while clicking (select multiple items)
pyautogui.keyDown('shift')
pyautogui.click(100, 200)  # First item
pyautogui.click(100, 400)  # Last item (selects range)
pyautogui.keyUp('shift')

# Hold Ctrl while clicking (select individual items)
pyautogui.keyDown('ctrl')
pyautogui.click(100, 200)  # Item 1
pyautogui.click(100, 300)  # Item 2
pyautogui.click(100, 400)  # Item 3
pyautogui.keyUp('ctrl')

# IMPORTANT: Always pair keyDown with keyUp!
# If bot crashes between them, key stays held down!
# Use try/finally:
try:
    pyautogui.keyDown('ctrl')
    pyautogui.click(200, 300)
finally:
    pyautogui.keyUp('ctrl')
────────────────────────────────────────────────────────────────────────
"""
print(keydown_reference)


# ─── 5. TYPING UNICODE / SPECIAL CHARACTERS ──────────────────────────────────

print("── 5. UNICODE & SPECIAL CHARACTERS ─────────────────────────")

unicode_code = '''
# typewrite() only handles ASCII. For unicode, use clipboard:

import pyperclip  # pip install pyperclip

def type_unicode(text: str):
    """Type any text including unicode, emojis, etc."""
    original_clipboard = pyperclip.paste()  # Save clipboard
    pyperclip.copy(text)                    # Copy text to clipboard
    pyautogui.hotkey("ctrl", "v")           # Paste
    time.sleep(0.1)
    pyperclip.copy(original_clipboard)      # Restore clipboard

# Usage
type_unicode("Héllo Wörld! 🚀")
type_unicode("中文测试")
type_unicode("アイウエオ")
'''
print(unicode_code)


# ─── 6. READING CURRENT CLIPBOARD ────────────────────────────────────────────

print("── 6. CLIPBOARD OPERATIONS ──────────────────────────────────")

clipboard_code = '''
import pyperclip  # pip install pyperclip

# Read what's on clipboard
text = pyperclip.paste()
print(f"Clipboard: {text}")

# Write to clipboard
pyperclip.copy("New clipboard content")

# PATTERN: Select all, copy, read
# (read content from any input field)
pyautogui.click(x=500, y=300)          # Click on field
pyautogui.hotkey('ctrl', 'a')          # Select all
pyautogui.hotkey('ctrl', 'c')          # Copy
time.sleep(0.1)
field_value = pyperclip.paste()        # Read
print(f"Field contains: {field_value}")
'''
print(clipboard_code)


# ─── 7. TYPING IN FORMS — Complete Example ───────────────────────────────────

print("── 7. FORM AUTOMATION EXAMPLE ───────────────────────────────")

form_example = '''
"""
Automate filling a desktop application form.
Uses Tab to navigate between fields (like a human would).
"""
import pyautogui
import time
import pyperclip

pyautogui.FAILSAFE = True

def fill_desktop_form(data: dict):
    """
    Fill a simple desktop app form using keyboard navigation.
    Assumes form is already open and first field is focused.
    """
    time.sleep(0.5)  # Ensure app is ready

    # Clear and type in first field (Name)
    pyautogui.hotkey('ctrl', 'a')           # Select all
    pyautogui.typewrite(data['name'], interval=0.05)

    pyautogui.press('tab')                  # Move to next field

    # Email field
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(data['email'], interval=0.05)

    pyautogui.press('tab')                  # Phone field

    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(data['phone'], interval=0.05)

    pyautogui.press('tab')                  # Move to Submit button
    pyautogui.press('enter')                # Click Submit

    time.sleep(0.5)

    # Read confirmation message from screen (using screenshot + OCR)
    screenshot = pyautogui.screenshot()
    # In real code: use pytesseract to read text from screenshot
    print("Form submitted!")


def process_batch(records: list[dict]):
    """Process multiple records."""
    for i, record in enumerate(records, 1):
        print(f"Processing record {i}/{len(records)}: {record['name']}")
        fill_desktop_form(record)
        time.sleep(1)  # Wait between records


if __name__ == "__main__":
    records = [
        {"name": "Alice Smith", "email": "alice@example.com", "phone": "555-0101"},
        {"name": "Bob Jones",   "email": "bob@example.com",   "phone": "555-0102"},
    ]

    print("Starting in 5 seconds — switch to target app!")
    time.sleep(5)

    process_batch(records)
    print("All records processed!")
'''
print(form_example)


# ─── Summary ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "─" * 55)
    print("  KEYBOARD CONTROL — SUMMARY:")
    print("  ► typewrite()  → Type ASCII text")
    print("  ► press()      → Single key press")
    print("  ► hotkey()     → Key combinations")
    print("  ► keyDown/Up() → Hold modifier keys")
    print("  ► pyperclip    → Unicode text via clipboard")
    print("  ► Tab          → Navigate between form fields")
    print("─" * 55)
    print("  NEXT: python module_3_pyautogui/03_screenshots_and_ocr.py")

"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 3 — LESSON 3: SCREENSHOTS, IMAGE RECOGNITION & OCR   ║
╚══════════════════════════════════════════════════════════════════╝

VISUAL AUTOMATION:
  ► Screenshots         → Capture screen for analysis/documentation
  ► Image Recognition   → Find buttons/elements by their appearance
  ► OCR                 → Read text from screen images

TOOLS:
  pyautogui   → Screenshots, image search
  Pillow      → Image processing
  pytesseract → OCR (requires Tesseract installation)

INSTALL:
  pip install pyautogui pillow pytesseract
  # Also install Tesseract OCR engine:
  # Ubuntu:  sudo apt install tesseract-ocr
  # macOS:   brew install tesseract
  # Windows: https://github.com/tesseract-ocr/tesseract
"""

import time
import pyautogui
from PIL import Image, ImageGrab, ImageFilter, ImageEnhance
from pathlib import Path
import pytesseract  # pip install pytesseract


# ─── 1. TAKING SCREENSHOTS ───────────────────────────────────────────────────

print("── 1. SCREENSHOTS ───────────────────────────────────────────")

screenshot_reference = """
SCREENSHOT FUNCTIONS:
────────────────────────────────────────────────────────────────────────
# Full screen screenshot
screenshot = pyautogui.screenshot()
screenshot.save("/tmp/full_screen.png")

# Screenshot of specific region (left, top, width, height)
region_shot = pyautogui.screenshot(region=(100, 100, 800, 600))
region_shot.save("/tmp/region.png")

# Screenshot as PIL Image (for processing)
img = pyautogui.screenshot()
pixels = img.load()
color_at_center = pixels[960, 540]  # RGB tuple
print(f"Pixel at center: {color_at_center}")

# Get pixel color at specific position
color = pyautogui.pixel(500, 300)
print(f"Color at (500,300): {color}")  # (R, G, B)

# Check if pixel matches expected color
if pyautogui.pixelMatchesColor(500, 300, (255, 0, 0), tolerance=10):
    print("Red pixel found!")
────────────────────────────────────────────────────────────────────────
"""
print(screenshot_reference)

# Demo: Take a screenshot
screenshot = pyautogui.screenshot()
screenshot.save("/tmp/demo_screenshot.png")
print(f"  Screenshot saved: {screenshot.size[0]}x{screenshot.size[1]} pixels")


# ─── 2. IMAGE RECOGNITION — Find Elements by Appearance ──────────────────────

print("\n── 2. IMAGE RECOGNITION ─────────────────────────────────────")

image_recognition_code = '''
"""
Image recognition finds UI elements by their visual appearance.
REQUIRES: You save reference images (templates) of buttons/icons.

BEST FOR:
  - Applications without IDs or selectors
  - Consistent UI that doesn't change resolution
  - Verifying visual elements appear on screen
"""

# ── Find element on screen (returns center coordinates or None)
location = pyautogui.locateOnScreen(
    "assets/ok_button.png",   # Reference image you took
    confidence=0.9            # 0-1, how similar (needs opencv)
)

if location:
    print(f"Button found at: {location}")
    # locateOnScreen returns (left, top, width, height)
    center = pyautogui.center(location)  # Get center (x, y)
    pyautogui.click(center)
else:
    print("Button not found on screen!")

# ── Find ALL occurrences
locations = list(pyautogui.locateAllOnScreen("assets/checkbox.png", confidence=0.8))
print(f"Found {len(locations)} checkboxes")

# ── locateCenterOnScreen (combines locate + center)
center = pyautogui.locateCenterOnScreen("assets/ok_button.png", confidence=0.85)
if center:
    pyautogui.click(center)

# ── Wait for image to appear (retry loop)
def wait_for_image(image_path, timeout=10, confidence=0.9):
    """Wait until an image appears on screen."""
    start = time.time()
    while time.time() - start < timeout:
        pos = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if pos:
            return pos
        time.sleep(0.5)
    raise TimeoutError(f"Image not found: {image_path}")

# Usage:
try:
    pos = wait_for_image("assets/loading_done.png", timeout=15)
    print(f"Loading complete! Continue at {pos}")
except TimeoutError:
    print("Timeout: Loading didn\'t complete")

# ── SCREENSHOT REGION FOR TEMPLATES
# How to create reference images:
def capture_template(region, save_path):
    """Capture a region for use as template."""
    shot = pyautogui.screenshot(region=region)
    shot.save(save_path)
    print(f"Template saved: {save_path} ({shot.size})")

# Capture the Submit button at known location
capture_template(region=(500, 400, 120, 40), save_path="assets/submit_btn.png")
'''
print(image_recognition_code)


# ─── 3. OCR — Reading Text from Screen ───────────────────────────────────────

print("\n── 3. OCR WITH PYTESSERACT ──────────────────────────────────")

ocr_reference = """
OCR CONFIGURATION:
────────────────────────────────────────────────────────────────────────
PSM (Page Segmentation Mode):
  psm 3  = Automatic page segmentation (default)
  psm 6  = Assume uniform block of text
  psm 7  = Single text line
  psm 8  = Single word
  psm 10 = Single character
  psm 11 = Sparse text (scattered text)
  psm 13 = Raw line (most permissive)

OEM (OCR Engine Mode):
  oem 0 = Legacy Tesseract
  oem 1 = LSTM neural network (best for most cases)
  oem 3 = Both (default)
────────────────────────────────────────────────────────────────────────
"""
print(ocr_reference)

ocr_code = '''
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import pyautogui

# On Windows, set path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# ── Basic OCR on full screenshot
screenshot = pyautogui.screenshot()
text = pytesseract.image_to_string(screenshot)
print("Screen text:", text[:200])

# ── OCR on specific screen region
region = (100, 200, 600, 400)  # (left, top, width, height)
region_shot = pyautogui.screenshot(region=region)
text = pytesseract.image_to_string(region_shot, config="--psm 6")
print(f"Region text: {text.strip()}")

# ── OCR with preprocessing (MUCH better accuracy)
def screenshot_to_text(region=None, psm=6):
    """
    Take screenshot and extract text with image preprocessing.
    Preprocessing dramatically improves OCR accuracy.
    """
    # Take screenshot
    if region:
        img = pyautogui.screenshot(region=region)
    else:
        img = pyautogui.screenshot()

    # Convert to grayscale (required for best OCR)
    img = img.convert("L")

    # Scale up (Tesseract works better on larger images)
    width, height = img.size
    img = img.resize((width * 2, height * 2), Image.LANCZOS)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Optional: threshold to pure black/white
    img = img.point(lambda p: 255 if p > 128 else 0)

    # OCR
    config = f"--psm {psm} --oem 1"
    text = pytesseract.image_to_string(img, config=config)
    return text.strip()

# ── Extract structured data from screen
def get_table_from_screen(region):
    """Extract table data from a screen region."""
    img = pyautogui.screenshot(region=region)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    # Reconstruct text with positions
    words = []
    for i, word in enumerate(data["text"]):
        if word.strip():
            words.append({
                "text": word,
                "confidence": data["conf"][i],
                "x": data["left"][i],
                "y": data["top"][i],
            })
    return words

# ── Read numbers from screen
def read_number_from_screen(region):
    """Extract only numbers from a screen region."""
    img = pyautogui.screenshot(region=region)
    img = img.convert("L")
    # Config: only recognize digits
    text = pytesseract.image_to_string(img, config="--psm 8 -c tessedit_char_whitelist=0123456789.")
    try:
        return float(text.strip())
    except ValueError:
        return None

# Example usage:
balance_region = (800, 100, 200, 40)  # Region showing account balance
balance = read_number_from_screen(balance_region)
print(f"Balance: ${balance:.2f}")

# ── Verify UI state with OCR
def verify_text_on_screen(expected_text, region=None, timeout=5):
    """Wait for specific text to appear on screen."""
    start = time.time()
    while time.time() - start < timeout:
        actual = screenshot_to_text(region)
        if expected_text.lower() in actual.lower():
            return True
        time.sleep(0.5)
    return False

if verify_text_on_screen("Success", timeout=10):
    print("Operation succeeded!")
else:
    print("Operation may have failed — expected text not found")
'''
print(ocr_code)


# ─── 4. VISUAL VERIFICATION BOT ──────────────────────────────────────────────

VISUAL_BOT_EXAMPLE = '''
"""
VISUAL AUTOMATION BOT EXAMPLE
Reads text from screen, reacts to what it sees.
"""
import pyautogui
import pytesseract
import time
from PIL import ImageEnhance

def read_status_bar():
    """Read the status bar text at the bottom of screen."""
    screen_w, screen_h = pyautogui.size()
    status_region = (0, screen_h - 40, screen_w, 40)  # Bottom bar
    img = pyautogui.screenshot(region=status_region)
    img = img.convert("L")
    return pytesseract.image_to_string(img, config="--psm 7").strip()

def wait_for_operation(expected_completion_text, timeout=30):
    """Monitor status bar until operation completes."""
    start = time.time()
    while time.time() - start < timeout:
        status = read_status_bar()
        print(f"\\r  Status: {status[:50]:<50}", end="")

        if expected_completion_text.lower() in status.lower():
            print("\\n  Operation complete!")
            return True
        if "error" in status.lower() or "failed" in status.lower():
            print(f"\\n  ERROR detected: {status}")
            return False
        time.sleep(1)

    print("\\n  Timeout!")
    return False

def run_data_processing_bot():
    """Full bot that processes data in a desktop app."""
    # Open application
    pyautogui.hotkey("win", "r")       # Open Run dialog
    time.sleep(0.3)
    pyautogui.typewrite("notepad.exe", interval=0.05)
    pyautogui.press("enter")
    time.sleep(1)

    # Type data
    pyautogui.typewrite("Processing complete", interval=0.05)
    pyautogui.hotkey("ctrl", "s")
    time.sleep(0.5)

    # Save with timestamp
    pyautogui.typewrite(f"output_{time.strftime("%Y%m%d")}.txt", interval=0.05)
    pyautogui.press("enter")

    print("Bot finished!")

if __name__ == "__main__":
    print("Starting in 3 seconds...")
    time.sleep(3)
    run_data_processing_bot()
'''
print("\n── COMPLETE VISUAL BOT EXAMPLE ──────────────────────────────")
print(VISUAL_BOT_EXAMPLE)


if __name__ == "__main__":
    print("\n" + "─" * 55)
    print("  SCREENSHOTS & OCR — SUMMARY:")
    print("  ► pyautogui.screenshot()     → Capture screen")
    print("  ► locateOnScreen()           → Find by image")
    print("  ► pytesseract.image_to_string() → Read text")
    print("  ► Preprocess images for better OCR accuracy")
    print("  ► Use regions to focus OCR on specific areas")
    print("─" * 55)
    print("  NEXT: python module_3_pyautogui/04_desktop_automation.py")

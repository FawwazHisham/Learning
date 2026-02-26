"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 3 — LESSON 1: PYAUTOGUI MOUSE CONTROL               ║
╚══════════════════════════════════════════════════════════════════╝

PYAUTOGUI = Desktop Automation Library
  ► Controls mouse and keyboard at OS level
  ► Works with ANY application (not just browsers)
  ► Great for: desktop apps, legacy software, file managers

COORDINATE SYSTEM:
  (0,0) ──────────────────────► X axis
    │    Screen
    │    ┌──────────────────┐
    │    │                  │
    ▼    │   (960, 540)     │  ← Center of 1920x1080 screen
  Y axis │                  │
         └──────────────────┘

INSTALL:
  pip install pyautogui pillow pygetwindow

SAFETY FEATURE:
  Move mouse to top-left corner (0,0) to trigger FAILSAFE
  This stops the bot immediately — always keep this enabled!
"""

import time
import pyautogui

# ─── SAFETY SETTINGS ──────────────────────────────────────────────────────────

# NEVER disable FAILSAFE in production!
pyautogui.FAILSAFE = True    # Move mouse to (0,0) to stop bot

# Pause between every PyAutoGUI action (prevents too-fast execution)
pyautogui.PAUSE = 0.1        # 0.1 second pause after each call


# ─── 1. SCREEN INFORMATION ────────────────────────────────────────────────────

print("── 1. SCREEN INFORMATION ───────────────────────────────────")

screen_width, screen_height = pyautogui.size()
print(f"  Screen size  : {screen_width} x {screen_height}")

current_x, current_y = pyautogui.position()
print(f"  Mouse position: ({current_x}, {current_y})")


# ─── 2. MOUSE MOVEMENT ────────────────────────────────────────────────────────

print("\n── 2. MOUSE MOVEMENT ────────────────────────────────────────")

movement_reference = """
MOUSE MOVEMENT FUNCTIONS:
────────────────────────────────────────────────────────────────────────
pyautogui.moveTo(x, y)              → Move to absolute coordinates
pyautogui.moveTo(x, y, duration=0.5)→ Move smoothly over 0.5 seconds
pyautogui.moveRel(dx, dy)           → Move relative to current position
pyautogui.moveRel(dx, dy, duration) → Smooth relative move

MOVEMENT TWEENS (animation curves for duration):
  pyautogui.easeInQuad    → Starts slow, ends fast
  pyautogui.easeOutQuad   → Starts fast, ends slow
  pyautogui.easeInOutQuad → Slow at both ends (most human-like)
  pyautogui.linear        → Constant speed

EXAMPLE:
  pyautogui.moveTo(500, 300, duration=0.5, tween=pyautogui.easeInOutQuad)
────────────────────────────────────────────────────────────────────────
"""
print(movement_reference)

# Demo: Move mouse to center of screen
center_x = screen_width // 2
center_y = screen_height // 2
print(f"  Moving to center ({center_x}, {center_y})...")
pyautogui.moveTo(center_x, center_y, duration=0.5)

# Move relative
pyautogui.moveRel(100, 0, duration=0.3)   # Right 100px
pyautogui.moveRel(-100, 100, duration=0.3) # Left 100px, Down 100px
print(f"  New position: {pyautogui.position()}")


# ─── 3. MOUSE CLICKS ──────────────────────────────────────────────────────────

print("\n── 3. MOUSE CLICKS ──────────────────────────────────────────")

click_reference = """
CLICK FUNCTIONS:
────────────────────────────────────────────────────────────────────────
pyautogui.click()                     → Left click at current position
pyautogui.click(x, y)                 → Move to (x,y) and left click
pyautogui.click(x, y, button='right') → Right click
pyautogui.click(x, y, button='middle')→ Middle click
pyautogui.doubleClick(x, y)           → Double left click
pyautogui.tripleClick(x, y)           → Triple click (select all text)
pyautogui.rightClick(x, y)            → Right click (shorthand)
pyautogui.middleClick(x, y)           → Middle click (shorthand)

CLICK WITH MULTIPLE CLICKS:
pyautogui.click(x, y, clicks=2, interval=0.25) → Double click with delay
pyautogui.click(x, y, clicks=3, interval=0.1)  → Triple click

CLICK AND DRAG:
pyautogui.dragTo(x, y, duration=0.5)  → Drag from current pos to (x,y)
pyautogui.dragRel(dx, dy, duration)   → Drag relative distance

MOUSE DOWN/UP (for complex interactions):
pyautogui.mouseDown()                 → Hold left button
pyautogui.mouseUp()                   → Release left button
pyautogui.mouseDown(button='right')   → Hold right button
────────────────────────────────────────────────────────────────────────
"""
print(click_reference)


# ─── 4. SCROLLING ────────────────────────────────────────────────────────────

print("── 4. SCROLLING ─────────────────────────────────────────────")

scroll_reference = """
SCROLL FUNCTIONS:
────────────────────────────────────────────────────────────────────────
pyautogui.scroll(clicks)          → Scroll at current position
                                    Positive = up, Negative = down
pyautogui.scroll(3)               → Scroll up 3 clicks
pyautogui.scroll(-5)              → Scroll down 5 clicks
pyautogui.scroll(-3, x=500, y=400)→ Scroll at specific coordinates

SCROLL TO LOAD MORE CONTENT:
  for _ in range(5):
      pyautogui.scroll(-10)       → Scroll down 10 clicks
      time.sleep(0.5)             → Wait for content to load
────────────────────────────────────────────────────────────────────────
"""
print(scroll_reference)

# Demo scroll
print("  Scrolling down 3 clicks...")
pyautogui.scroll(-3)
time.sleep(0.3)
print("  Scrolling up 3 clicks...")
pyautogui.scroll(3)


# ─── 5. DRAG AND DROP ────────────────────────────────────────────────────────

print("\n── 5. DRAG AND DROP ─────────────────────────────────────────")

drag_code = """
# ── Simple drag from one location to another
pyautogui.dragTo(x=400, y=300, duration=0.5, button='left')

# ── Drag relative to current position
pyautogui.dragRel(xOffset=200, yOffset=0, duration=0.5)

# ── Drag using mouseDown/moveTo/mouseUp (more control)
pyautogui.mouseDown(x=100, y=200)          # Grab item
time.sleep(0.1)
pyautogui.moveTo(x=300, y=200, duration=0.5)  # Move it
pyautogui.mouseUp()                        # Release

# ── Drag slider to specific value
def set_slider(slider_x, slider_y, min_val, max_val, target_val, slider_width):
    '''Move a slider to a target value.'''
    proportion = (target_val - min_val) / (max_val - min_val)
    target_x = slider_x + int(proportion * slider_width)
    pyautogui.dragTo(target_x, slider_y, duration=0.5)

# Example: Volume slider from 0-100, currently at 0, set to 75
# Slider starts at x=200, ends at x=400 (width=200)
set_slider(200, 400, 0, 100, 75, 200)
"""
print(drag_code)


# ─── 6. GET MOUSE POSITION (Find coordinates) ────────────────────────────────

print("── 6. FIND COORDINATES TOOL ─────────────────────────────────")
coordinate_finder_code = '''
"""
Run this script to find coordinates on your screen.
Hover over any element and watch the coordinates update.
Press Ctrl+C to stop.
"""
import pyautogui
import time

print("Hover over elements to find their coordinates.")
print("Press Ctrl+C to stop.")

try:
    while True:
        x, y = pyautogui.position()
        pixel_color = pyautogui.screenshot().getpixel((x, y))
        print(f"\\r  Position: ({x:4d}, {y:4d}) | Color: {pixel_color}", end="")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\\nStopped.")
'''
print(coordinate_finder_code)


# ─── 7. COMPLETE MOUSE AUTOMATION EXAMPLE ────────────────────────────────────

MOUSE_EXAMPLE = '''
"""
EXAMPLE: Automate drawing a square in MS Paint / any drawing app.
Demonstrates mouse movement and clicking patterns.
"""
import pyautogui
import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def draw_square(start_x, start_y, size=200, duration=0.5):
    """Draw a square using click and drag."""
    # Move to start position
    pyautogui.moveTo(start_x, start_y, duration=0.3)

    # Draw 4 sides
    pyautogui.mouseDown()                                    # Hold button
    pyautogui.moveTo(start_x + size, start_y, duration)     # Right
    pyautogui.moveTo(start_x + size, start_y + size, duration)  # Down
    pyautogui.moveTo(start_x, start_y + size, duration)     # Left
    pyautogui.moveTo(start_x, start_y, duration)             # Up (close)
    pyautogui.mouseUp()                                      # Release

def automate_desktop_app():
    """Example workflow for a desktop app."""
    # 1. Click on app in taskbar to bring to front
    pyautogui.click(100, 1050)  # Taskbar icon position
    time.sleep(0.5)

    # 2. Use keyboard shortcut
    pyautogui.hotkey("ctrl", "n")  # New file
    time.sleep(0.3)

    # 3. Draw
    draw_square(300, 200, size=200)

    # 4. Save
    pyautogui.hotkey("ctrl", "s")
    time.sleep(0.5)

    # 5. Type filename in save dialog
    pyautogui.typewrite("my_drawing.png", interval=0.05)
    pyautogui.press("enter")

if __name__ == "__main__":
    print("Starting in 3 seconds...")
    time.sleep(3)  # Give user time to switch to target app
    automate_desktop_app()
'''
print("\n── COMPLETE EXAMPLE ─────────────────────────────────────────")
print(MOUSE_EXAMPLE)


# ─── Summary ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "─" * 55)
    print("  PYAUTOGUI MOUSE — SUMMARY:")
    print("  ► pyautogui.size()      → Screen dimensions")
    print("  ► pyautogui.position()  → Current mouse position")
    print("  ► pyautogui.moveTo()    → Move to coordinates")
    print("  ► pyautogui.click()     → Click at position")
    print("  ► pyautogui.scroll()    → Scroll up/down")
    print("  ► pyautogui.dragTo()    → Drag to position")
    print("  ► Always keep FAILSAFE = True!")
    print("─" * 55)
    print("  NEXT: python module_3_pyautogui/02_keyboard_control.py")

"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 3 — LESSON 5: ADVANCED PYAUTOGUI                     ║
╚══════════════════════════════════════════════════════════════════╝

ADVANCED PATTERNS:
  1. Context-aware automation (check before clicking)
  2. Error recovery patterns
  3. Screen state machine
  4. Recording & playback
  5. Combining PyAutoGUI + Selenium
  6. Performance optimization
"""

import time
import json
import pyautogui
import pygetwindow as gw
from dataclasses import dataclass, field
from typing import Callable, Optional
from PIL import Image
import logging


pyautogui.FAILSAFE = True
logger = logging.getLogger(__name__)


# ─── 1. CONTEXT-AWARE AUTOMATION ────────────────────────────────────────────

def context_aware_patterns():
    print("── 1. CONTEXT-AWARE AUTOMATION ─────────────────────────────")
    code = '''
    # BAD: Blindly clicking at coordinates
    pyautogui.click(500, 300)  # What if the button isn't there?

    # GOOD: Verify before acting
    def smart_click(image_path: str, confidence=0.85) -> bool:
        """Only click if image is found."""
        pos = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if pos:
            pyautogui.click(pos)
            return True
        return False

    # GOOD: Check screen state before action
    def is_dialog_open() -> bool:
        """Check if a confirmation dialog is currently showing."""
        return pyautogui.locateOnScreen("assets/dialog_bg.png", confidence=0.8) is not None

    def is_loading() -> bool:
        """Check if a loading spinner is visible."""
        return pyautogui.locateOnScreen("assets/spinner.png", confidence=0.8) is not None

    def wait_for_loading_done(timeout=30):
        """Wait until loading spinner disappears."""
        start = time.time()
        while time.time() - start < timeout:
            if not is_loading():
                return True
            time.sleep(0.5)
        return False

    # FULL WORKFLOW with state checking:
    def submit_form():
        smart_click("assets/submit_btn.png")  # Click only if found

        if not wait_for_loading_done(timeout=15):
            raise RuntimeError("Operation timed out")

        if is_dialog_open():             # Handle unexpected dialog
            smart_click("assets/ok_btn.png")

        # Verify success
        if pyautogui.locateOnScreen("assets/success_icon.png"):
            return True
        elif pyautogui.locateOnScreen("assets/error_icon.png"):
            return False
    '''
    print(code)


# ─── 2. SCREEN STATE MACHINE ──────────────────────────────────────────────────

def screen_state_machine():
    print("\n── 2. SCREEN STATE MACHINE ──────────────────────────────────")
    code = '''
    """
    State Machine Pattern:
    Bot detects current screen state and acts accordingly.
    Very robust for apps with many possible screens.

    States:
      LOGIN_PAGE → DASHBOARD → REPORTS_PAGE → DONE
                 ↑
               ERROR
    """
    from enum import Enum

    class ScreenState(Enum):
        UNKNOWN      = "unknown"
        LOGIN_PAGE   = "login_page"
        DASHBOARD    = "dashboard"
        REPORTS_PAGE = "reports"
        ERROR_DIALOG = "error"
        LOADING      = "loading"
        DONE         = "done"

    def detect_state() -> ScreenState:
        """Determine current screen state by visual inspection."""
        checks = [
            (ScreenState.ERROR_DIALOG, "assets/error_dialog.png"),
            (ScreenState.LOADING,      "assets/loading_spinner.png"),
            (ScreenState.REPORTS_PAGE, "assets/reports_header.png"),
            (ScreenState.DASHBOARD,    "assets/dashboard_logo.png"),
            (ScreenState.LOGIN_PAGE,   "assets/login_form.png"),
        ]

        for state, image in checks:
            if pyautogui.locateOnScreen(image, confidence=0.85):
                return state

        return ScreenState.UNKNOWN

    def handle_state(state: ScreenState) -> ScreenState:
        """Execute action for current state, return next state."""
        if state == ScreenState.LOGIN_PAGE:
            pyautogui.click(*pyautogui.locateCenterOnScreen("assets/username_field.png"))
            pyautogui.typewrite("admin", interval=0.05)
            pyautogui.press("tab")
            pyautogui.typewrite("password123", interval=0.05)
            pyautogui.press("enter")
            return ScreenState.LOADING

        elif state == ScreenState.LOADING:
            time.sleep(1)
            return detect_state()

        elif state == ScreenState.DASHBOARD:
            pyautogui.click(*pyautogui.locateCenterOnScreen("assets/reports_btn.png"))
            return ScreenState.LOADING

        elif state == ScreenState.REPORTS_PAGE:
            # Download report
            pyautogui.click(*pyautogui.locateCenterOnScreen("assets/download_btn.png"))
            time.sleep(2)
            return ScreenState.DONE

        elif state == ScreenState.ERROR_DIALOG:
            pyautogui.click(*pyautogui.locateCenterOnScreen("assets/dismiss_btn.png"))
            return detect_state()

        return ScreenState.UNKNOWN

    def run_state_machine(max_steps=20):
        """Run bot as a state machine."""
        state = detect_state()
        steps = 0

        while state != ScreenState.DONE and steps < max_steps:
            print(f"State: {state.value}")
            state = handle_state(state)
            steps += 1

        if state == ScreenState.DONE:
            print("Bot completed successfully!")
        else:
            print(f"Bot stopped in state: {state.value}")
    '''
    print(code)


# ─── 3. RECORDING & PLAYBACK ──────────────────────────────────────────────────

def recording_playback():
    print("\n── 3. MOUSE RECORDER & PLAYBACK ─────────────────────────────")
    code = '''
    """
    Record human mouse actions and replay them.
    Useful for creating templates from manual demonstrations.
    """
    import json
    import time
    import pyautogui
    from pynput import mouse  # pip install pynput

    class MouseRecorder:
        def __init__(self):
            self.events = []
            self.start_time = None
            self.recording = False

        def on_move(self, x, y):
            if self.recording:
                self.events.append({
                    "type": "move",
                    "x": x, "y": y,
                    "t": time.time() - self.start_time
                })

        def on_click(self, x, y, button, pressed):
            if self.recording:
                self.events.append({
                    "type": "click",
                    "x": x, "y": y,
                    "button": button.name,
                    "pressed": pressed,
                    "t": time.time() - self.start_time
                })

        def on_scroll(self, x, y, dx, dy):
            if self.recording:
                self.events.append({
                    "type": "scroll",
                    "x": x, "y": y,
                    "dy": dy,
                    "t": time.time() - self.start_time
                })

        def start(self):
            self.recording = True
            self.start_time = time.time()
            self.events = []
            self.listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll
            )
            self.listener.start()
            print("Recording started... Press Ctrl+C to stop")

        def stop(self):
            self.recording = False
            self.listener.stop()
            print(f"Recorded {len(self.events)} events")

        def save(self, path="recording.json"):
            with open(path, "w") as f:
                json.dump(self.events, f, indent=2)

        def load(self, path="recording.json"):
            with open(path) as f:
                self.events = json.load(f)

        def playback(self, speed=1.0):
            """Replay recorded events."""
            print(f"Playing back {len(self.events)} events...")
            prev_time = 0
            for event in self.events:
                # Wait for the right time
                wait = (event["t"] - prev_time) / speed
                if wait > 0:
                    time.sleep(min(wait, 0.1))  # Cap wait at 0.1s
                prev_time = event["t"]

                if event["type"] == "move":
                    pyautogui.moveTo(event["x"], event["y"])
                elif event["type"] == "click" and event["pressed"]:
                    pyautogui.click(event["x"], event["y"],
                                   button=event["button"])
                elif event["type"] == "scroll":
                    pyautogui.scroll(event["dy"], x=event["x"], y=event["y"])

            print("Playback complete!")

    # Usage:
    recorder = MouseRecorder()
    recorder.start()
    try:
        time.sleep(30)  # Record for 30 seconds
    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop()
        recorder.save("my_recording.json")

    # Later, replay:
    recorder.load("my_recording.json")
    recorder.playback(speed=2.0)  # 2x speed
    '''
    print(code)


# ─── 4. COMBINING PYAUTOGUI + SELENIUM ───────────────────────────────────────

def selenium_pyautogui_combination():
    print("\n── 4. COMBINING SELENIUM + PYAUTOGUI ────────────────────────")
    code = '''
    """
    Use Selenium for browser control + PyAutoGUI for file upload dialogs
    and OS-level interactions that Selenium can't handle.
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import pyautogui
    import time

    def upload_file_with_dialog(driver, upload_btn_selector: str, file_path: str):
        """
        Handle file upload when clicking opens an OS file dialog.
        Selenium can usually handle <input type="file"> directly,
        but some apps open custom dialogs that need PyAutoGUI.
        """
        # Click the upload button in browser
        driver.find_element(By.CSS_SELECTOR, upload_btn_selector).click()
        time.sleep(1)  # Wait for file dialog to open

        # Now use PyAutoGUI to interact with the OS file dialog
        pyautogui.typewrite(file_path, interval=0.03)  # Type file path
        pyautogui.press("enter")                        # Confirm
        time.sleep(1)

    def handle_browser_download_dialog(download_confirm_text="Save"):
        """
        Handle browser download notification bar (if it appears).
        More reliable than Selenium for OS-level dialogs.
        """
        # Wait for download bar to appear
        time.sleep(1)
        # Check if "Save" button appears in browser UI
        save_btn = pyautogui.locateCenterOnScreen(
            "assets/browser_save_btn.png", confidence=0.8
        )
        if save_btn:
            pyautogui.click(save_btn)
            print("Clicked Save in download dialog")

    def take_full_page_screenshot(driver, output_path: str):
        """
        Take full page screenshot using PyAutoGUI for the part
        that Selenium's screenshot might miss.
        """
        # Scroll to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.3)

        # Get total page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        screenshots = []
        scroll_pos = 0

        while scroll_pos < total_height:
            driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            time.sleep(0.3)
            screenshots.append(pyautogui.screenshot())
            scroll_pos += viewport_height

        # Stitch screenshots together
        from PIL import Image
        total_width = screenshots[0].width
        combined = Image.new("RGB", (total_width, total_height))
        for i, img in enumerate(screenshots):
            combined.paste(img, (0, i * viewport_height))

        combined.save(output_path)
        print(f"Full page screenshot saved: {output_path}")
    '''
    print(code)


# ─── 5. PYAUTOGUI GOTCHAS & TIPS ─────────────────────────────────────────────

def gotchas_and_tips():
    print("\n── 5. GOTCHAS & TIPS ────────────────────────────────────────")
    tips = [
        ("Screen resolution",
         "Coordinates are absolute pixels. If resolution changes, bot breaks.\n"
         "    ► Use image recognition instead of hardcoded coordinates.\n"
         "    ► Use pyautogui.size() to calculate relative positions."),
        ("Multi-monitor",
         "Screen coordinates extend across all monitors.\n"
         "    ► (0,0) is top-left of primary monitor.\n"
         "    ► Secondary monitor may be at (-1920, 0) or (1920, 0)."),
        ("DPI scaling",
         "HiDPI screens may double coordinates.\n"
         "    ► Test on target machine.\n"
         "    ► pyautogui.screenshot() automatically handles DPI."),
        ("App must be focused",
         "typewrite() sends to whatever app has focus.\n"
         "    ► Always call window.activate() before typing.\n"
         "    ► Add time.sleep(0.2) after activate()."),
        ("Lag and timing",
         "Apps may lag when responding to automation.\n"
         "    ► Increase pyautogui.PAUSE for slow apps.\n"
         "    ► Use image/OCR verification instead of fixed sleeps."),
        ("FAILSAFE",
         "Never set FAILSAFE = False in production.\n"
         "    ► Always keep it True.\n"
         "    ► Mouse to (0,0) stops the bot in emergencies."),
        ("Screen lock",
         "Bot stops working if screen locks.\n"
         "    ► Disable screen lock during bot runs.\n"
         "    ► Or run in a virtual machine/screen session."),
        ("pyautogui on Linux",
         "Requires display server (Xorg/Wayland).\n"
         "    ► For headless Linux: use Xvfb virtual display.\n"
         "    ► pip install pyvirtualdisplay; apt install xvfb"),
    ]

    for title, detail in tips:
        print(f"\n  ► {title}:")
        print(f"    {detail}")


# ─── 6. LINUX HEADLESS DISPLAY ───────────────────────────────────────────────

def linux_headless_setup():
    print("\n── 6. LINUX HEADLESS SETUP (for servers) ────────────────────")
    code = '''
    """
    PyAutoGUI requires a display. On Linux servers (no GUI),
    use Xvfb (virtual framebuffer).
    """

    # ── Option 1: pyvirtualdisplay Python wrapper
    from pyvirtualdisplay import Display  # pip install pyvirtualdisplay

    display = Display(visible=False, size=(1920, 1080))
    display.start()

    # Now PyAutoGUI works!
    import pyautogui
    pyautogui.screenshot().save("/tmp/headless.png")

    display.stop()

    # ── Option 2: Start Xvfb manually
    # Terminal: Xvfb :99 -screen 0 1920x1080x24 &
    # Then: export DISPLAY=:99
    # Then run Python script

    # ── Context manager pattern (safe cleanup)
    from contextlib import contextmanager

    @contextmanager
    def virtual_display(width=1920, height=1080):
        from pyvirtualdisplay import Display
        display = Display(visible=False, size=(width, height))
        display.start()
        try:
            yield display
        finally:
            display.stop()

    with virtual_display():
        import pyautogui
        # All PyAutoGUI code here
        pyautogui.screenshot().save("/tmp/test.png")
    '''
    print(code)


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  PYAUTOGUI — LESSON 5: ADVANCED TECHNIQUES")
    print("█" * 60)

    context_aware_patterns()
    screen_state_machine()
    recording_playback()
    selenium_pyautogui_combination()
    gotchas_and_tips()
    linux_headless_setup()

    print("\n" + "─" * 55)
    print("  ADVANCED PYAUTOGUI SUMMARY:")
    print("  ► Check state before acting (context-aware)")
    print("  ► State machines handle complex multi-screen apps")
    print("  ► Record & playback for rapid prototyping")
    print("  ► Combine with Selenium for file dialogs")
    print("  ► Use Xvfb for Linux server deployments")
    print("─" * 55)
    print("  NEXT: python module_4_apis/01_http_basics.py")

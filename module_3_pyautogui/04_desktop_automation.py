"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 3 — LESSON 4: DESKTOP APPLICATION AUTOMATION         ║
╚══════════════════════════════════════════════════════════════════╝

REAL-WORLD DESKTOP AUTOMATION SCENARIOS:
  1. File management (Windows Explorer, Finder)
  2. Microsoft Office (Excel, Word, Outlook)
  3. Legacy applications (SAP, mainframe terminals)
  4. Desktop GUI apps (custom ERP, CRM tools)

KEY CHALLENGE: No CSS selectors. Must use:
  ► Coordinates (fragile)
  ► Image recognition (better)
  ► Keyboard shortcuts (most robust)
  ► pygetwindow for window management
"""

import time
import pyautogui
import pygetwindow as gw  # pip install pygetwindow
from pathlib import Path
from PIL import Image
import subprocess
import sys


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


# ─── 1. WINDOW MANAGEMENT ────────────────────────────────────────────────────

def window_management_guide():
    print("── 1. WINDOW MANAGEMENT ─────────────────────────────────────")
    code = """
    import pygetwindow as gw

    # ── List all open windows
    all_windows = gw.getAllWindows()
    for win in all_windows:
        print(f"  '{win.title}' at ({win.left}, {win.top}), size {win.width}x{win.height}")

    # ── Find window by title (partial match)
    notepad_wins = gw.getWindowsWithTitle("Notepad")
    if notepad_wins:
        win = notepad_wins[0]
        print(f"Found: {win.title}")
    else:
        print("Notepad not found")

    # ── Activate (bring to front)
    win.activate()
    time.sleep(0.2)          # Give it time to come to front

    # ── Maximize / Minimize / Restore
    win.maximize()
    win.minimize()
    win.restore()             # Restore from minimized/maximized

    # ── Move and resize
    win.moveTo(0, 0)          # Move to top-left
    win.resizeTo(1280, 720)   # Resize to 1280x720
    win.moveRel(100, 0)       # Move 100px right

    # ── Close window
    win.close()               # Sends close signal
    # win.kill()              # Force kill process

    # ── Get window bounds for screenshot
    region = (win.left, win.top, win.width, win.height)
    screenshot = pyautogui.screenshot(region=region)

    # ── Focus app and interact
    def focus_and_interact(window_title: str):
        wins = gw.getWindowsWithTitle(window_title)
        if not wins:
            raise RuntimeError(f"Window not found: {window_title}")
        win = wins[0]
        win.activate()
        time.sleep(0.3)  # Wait for focus
        return win
    """
    print(code)


# ─── 2. MICROSOFT EXCEL AUTOMATION ───────────────────────────────────────────

def excel_automation():
    print("\n── 2. EXCEL AUTOMATION ──────────────────────────────────────")

    # APPROACH 1: openpyxl (no UI needed, best approach)
    openpyxl_code = '''
    # ── APPROACH 1: openpyxl (no UI, FASTEST, RECOMMENDED)
    import openpyxl
    from openpyxl import Workbook

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Data"

    # Write headers
    headers = ["Date", "Product", "Quantity", "Price", "Total"]
    ws.append(headers)

    # Write data
    data = [
        ["2024-01-01", "Widget A", 100, 9.99, 999.0],
        ["2024-01-02", "Widget B", 50,  19.99, 999.5],
    ]
    for row in data:
        ws.append(row)

    # Format cells
    from openpyxl.styles import Font, PatternFill, Alignment
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="366092")

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Auto-fit columns
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    # Save
    wb.save("sales_report.xlsx")
    print("Excel file saved!")

    # Read existing Excel
    wb = openpyxl.load_workbook("data.xlsx")
    ws = wb["Sheet1"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        print(row)
    '''
    print(openpyxl_code)

    # APPROACH 2: PyAutoGUI (when you MUST use the UI)
    pyautogui_excel_code = '''
    # ── APPROACH 2: PyAutoGUI (when macro/formula interaction needed)

    def automate_excel_ui(data_file: str):
        """Open Excel, paste data, run macro."""
        # Open file with default application
        import subprocess
        subprocess.Popen(["start", "excel.exe", data_file], shell=True)
        time.sleep(3)  # Wait for Excel to open

        # Bring Excel to front
        excel_win = focus_and_interact("Microsoft Excel")

        # Navigate to a cell
        pyautogui.hotkey("ctrl", "g")   # Go To dialog
        time.sleep(0.3)
        pyautogui.typewrite("B2", interval=0.05)
        pyautogui.press("enter")

        # Type in cell
        pyautogui.typewrite("=SUM(A1:A10)", interval=0.05)
        pyautogui.press("enter")

        # Run a macro (Alt+F8)
        pyautogui.hotkey("alt", "f8")
        time.sleep(0.5)
        pyautogui.typewrite("RefreshData", interval=0.05)
        pyautogui.press("enter")  # Run macro
        time.sleep(2)

        # Save and close
        pyautogui.hotkey("ctrl", "s")
        time.sleep(1)
        pyautogui.hotkey("alt", "f4")
    '''
    print(pyautogui_excel_code)


# ─── 3. FILE MANAGER AUTOMATION ──────────────────────────────────────────────

def file_manager_automation():
    print("\n── 3. FILE MANAGER AUTOMATION ───────────────────────────────")
    code = '''
    # ── Move files using Python's built-in shutil (BEST approach)
    import shutil
    from pathlib import Path

    # Copy file
    shutil.copy("source.txt", "destination.txt")

    # Move file
    shutil.move("old_location/file.pdf", "new_location/file.pdf")

    # Copy entire directory
    shutil.copytree("src_folder", "dst_folder")

    # ── When you MUST use File Explorer (e.g., for complex UI operations)
    def open_folder_in_explorer(folder_path: str):
        """Open a folder in Windows Explorer."""
        import subprocess
        subprocess.Popen(f"explorer.exe {folder_path}")
        time.sleep(1)

    def select_and_copy_files_ui(source_folder: str, target_folder: str):
        """Use Windows Explorer to copy files (via right-click)."""
        open_folder_in_explorer(source_folder)
        time.sleep(1)

        # Select all files
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)

        # Copy
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.2)

        # Open target folder
        open_folder_in_explorer(target_folder)
        time.sleep(1)

        # Paste
        pyautogui.hotkey("ctrl", "v")
        time.sleep(2)

        print("Files copied!")
    '''
    print(code)


# ─── 4. NOTEPAD / TEXT EDITOR AUTOMATION ─────────────────────────────────────

def notepad_automation_demo():
    """
    Full working demo: Open Notepad, type, save, close.
    Works on Linux with gedit/nano, on Windows with notepad.
    """
    print("\n── 4. TEXT EDITOR AUTOMATION DEMO ───────────────────────────")
    code = '''
    def automate_notepad(content: str, save_path: str):
        """Open Notepad, type content, save to path."""

        # ── Detect OS and open appropriate editor
        import sys, subprocess, time

        if sys.platform == "win32":
            subprocess.Popen("notepad.exe")
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "TextEdit"])
        else:  # Linux
            subprocess.Popen(["gedit"])

        time.sleep(1.5)  # Wait for app to open

        # ── Type content
        pyautogui.typewrite(content, interval=0.02)

        # ── Save file (Ctrl+S or Ctrl+Shift+S for new file)
        pyautogui.hotkey("ctrl", "s")
        time.sleep(0.5)

        # ── In save dialog: type path and confirm
        # (On Windows, the filename field should be focused)
        pyautogui.hotkey("ctrl", "a")         # Clear existing text
        pyautogui.typewrite(save_path, interval=0.03)
        pyautogui.press("enter")
        time.sleep(0.5)

        # ── Close the application
        pyautogui.hotkey("alt", "f4")

        print(f"Saved to: {save_path}")

    # Usage
    automate_notepad(
        content="RPA with Python\\nAutomation is fun!",
        save_path="C:\\\\Users\\\\User\\\\Desktop\\\\rpa_output.txt"
    )
    '''
    print(code)


# ─── 5. WAIT PATTERNS FOR DESKTOP APPS ───────────────────────────────────────

def desktop_wait_patterns():
    print("\n── 5. WAIT PATTERNS FOR DESKTOP APPS ────────────────────────")
    code = '''
    # Desktop apps don't have WebDriverWait.
    # Use these patterns instead:

    # ── Wait for window to appear
    def wait_for_window(title: str, timeout: int = 10):
        import pygetwindow as gw
        start = time.time()
        while time.time() - start < timeout:
            wins = gw.getWindowsWithTitle(title)
            if wins:
                return wins[0]
            time.sleep(0.5)
        raise TimeoutError(f"Window not found: {title}")

    # ── Wait for image to appear on screen
    def wait_for_image(image_path: str, timeout: int = 10, confidence: float = 0.8):
        start = time.time()
        while time.time() - start < timeout:
            pos = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if pos:
                return pos
            time.sleep(0.5)
        raise TimeoutError(f"Image not found: {image_path}")

    # ── Wait for text to appear (via OCR)
    def wait_for_text(expected: str, region=None, timeout: int = 10):
        import pytesseract
        start = time.time()
        while time.time() - start < timeout:
            img = pyautogui.screenshot(region=region)
            text = pytesseract.image_to_string(img)
            if expected.lower() in text.lower():
                return True
            time.sleep(0.5)
        return False

    # ── Wait for color to change (for status indicators)
    def wait_for_color(x: int, y: int, expected_color, tolerance=15, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            if pyautogui.pixelMatchesColor(x, y, expected_color, tolerance=tolerance):
                return True
            time.sleep(0.3)
        return False

    # Example: Wait for loading indicator (red) to become green
    # Loading = (255, 0, 0), Done = (0, 128, 0)
    if wait_for_color(status_x, status_y, (0, 128, 0), timeout=30):
        print("Process complete!")
    '''
    print(code)


# ─── 6. ROBUST DESKTOP BOT CLASS ─────────────────────────────────────────────

ROBUST_DESKTOP_BOT = '''
"""
PRODUCTION-READY DESKTOP AUTOMATION BOT
Handles: window management, retries, error recovery, logging
"""
import pyautogui
import pygetwindow as gw
import pytesseract
import time
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

class DesktopBot:
    def __init__(self, app_name: str, app_exe: str = None):
        self.app_name = app_name
        self.app_exe = app_exe
        self.window = None
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def launch(self):
        """Launch the application if not running."""
        wins = gw.getWindowsWithTitle(self.app_name)
        if wins:
            self.window = wins[0]
            logger.info(f"Found existing window: {self.app_name}")
        else:
            if self.app_exe:
                import subprocess
                subprocess.Popen(self.app_exe)
                self.window = self._wait_for_window(timeout=10)
            else:
                raise RuntimeError(f"App not found: {self.app_name}")
        return self

    def focus(self):
        """Bring window to front."""
        if self.window:
            self.window.activate()
            time.sleep(0.2)
        return self

    def _wait_for_window(self, timeout=10):
        for _ in range(timeout * 2):
            wins = gw.getWindowsWithTitle(self.app_name)
            if wins:
                return wins[0]
            time.sleep(0.5)
        raise TimeoutError(f"Window not found: {self.app_name}")

    def click_image(self, image_path: str, confidence=0.85, timeout=10):
        """Find and click an element by its image."""
        start = time.time()
        while time.time() - start < timeout:
            pos = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if pos:
                pyautogui.click(pos)
                return pos
            time.sleep(0.3)
        raise TimeoutError(f"Image not found: {image_path}")

    def read_region(self, region: tuple, psm: int = 6) -> str:
        """Read text from a screen region using OCR."""
        img = pyautogui.screenshot(region=region)
        img = img.convert("L")
        width, height = img.size
        img = img.resize((width * 2, height * 2))
        return pytesseract.image_to_string(img, config=f"--psm {psm}").strip()

    def safe_type(self, text: str):
        """Type text safely."""
        self.focus()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.typewrite(str(text), interval=0.03)

    def screenshot(self, name="screenshot"):
        """Take screenshot of the app window."""
        if self.window:
            region = (self.window.left, self.window.top,
                      self.window.width, self.window.height)
            img = pyautogui.screenshot(region=region)
            path = f"/tmp/{name}.png"
            img.save(path)
            return path
'''
print("\n── ROBUST DESKTOP BOT ────────────────────────────────────────")
print(ROBUST_DESKTOP_BOT)


if __name__ == "__main__":
    print("\n" + "─" * 55)
    print("  DESKTOP AUTOMATION — SUMMARY:")
    print("  ► pygetwindow  → Find/manage windows")
    print("  ► openpyxl     → Excel (no UI, preferred)")
    print("  ► locateOnScreen → Find elements by image")
    print("  ► OCR regions  → Read text from screen")
    print("  ► Keyboard shortcuts → Most reliable approach")
    print("─" * 55)
    print("  NEXT: python module_3_pyautogui/05_advanced_pyautogui.py")

    window_management_guide()
    excel_automation()
    file_manager_automation()
    notepad_automation_demo()
    desktop_wait_patterns()

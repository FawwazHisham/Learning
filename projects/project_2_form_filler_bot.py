"""
╔══════════════════════════════════════════════════════════════════╗
║     PROJECT 2: FORM FILLER BOT (Selenium + CSV Input)           ║
╚══════════════════════════════════════════════════════════════════╝

SCENARIO:
  HR department needs to register 50 employees in a web portal.
  Manual entry = 2 hours. Bot = 5 minutes.

FEATURES:
  ✓ Reads employee data from CSV
  ✓ Fills web form for each employee
  ✓ Handles dropdowns, checkboxes, text fields
  ✓ Takes screenshot on success/failure
  ✓ Updates CSV with processing status
  ✓ Skips already-processed rows (idempotent)
  ✓ Handles validation errors gracefully

TARGET: https://demoqa.com/automation-practice-form (free demo site)
"""

import csv
import time
import logging
import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


# ─── DATA MODEL ───────────────────────────────────────────────────────────────

@dataclass
class Employee:
    first_name: str
    last_name: str
    email: str
    gender: str            # Male, Female, Other
    mobile: str
    dob: str               # MM/DD/YYYY
    subjects: str          # Comma-separated: "Maths, English"
    hobbies: str           # Comma-separated: "Sports, Reading"
    address: str
    state: str
    city: str
    status: str = "pending"    # pending, success, failed
    error_msg: str = ""
    screenshot: str = ""


def load_employees_from_csv(csv_path: str) -> list[Employee]:
    """Load employee data from CSV file."""
    employees = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(Employee(**row))
    return employees


def save_employees_to_csv(employees: list[Employee], csv_path: str):
    """Save employees with updated status back to CSV."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        from dataclasses import asdict
        writer = csv.DictWriter(f, fieldnames=asdict(employees[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(e) for e in employees)


def create_sample_csv(output_path: str):
    """Create a sample input CSV for testing."""
    sample_data = [
        {
            "first_name": "John", "last_name": "Doe",
            "email": "john.doe@example.com", "gender": "Male",
            "mobile": "1234567890", "dob": "01/15/1990",
            "subjects": "Maths", "hobbies": "Sports,Reading",
            "address": "123 Main St", "state": "NCR", "city": "Delhi",
            "status": "pending", "error_msg": "", "screenshot": "",
        },
        {
            "first_name": "Jane", "last_name": "Smith",
            "email": "jane.smith@example.com", "gender": "Female",
            "mobile": "9876543210", "dob": "03/22/1992",
            "subjects": "English", "hobbies": "Music,Travelling",
            "address": "456 Oak Ave", "state": "Uttar Pradesh", "city": "Agra",
            "status": "pending", "error_msg": "", "screenshot": "",
        },
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_data)

    print(f"Sample CSV created: {output_path}")


# ─── FORM FILLER BOT ─────────────────────────────────────────────────────────

class FormFillerBot:

    FORM_URL = "https://demoqa.com/automation-practice-form"
    SCREENSHOT_DIR = Path("/tmp/form_filler_screenshots")

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("FormFillerBot")

    def _init_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        # Disable GPU and scroll bars to avoid element intercept issues
        options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 15)

    def _screenshot(self, filename: str) -> str:
        path = str(self.SCREENSHOT_DIR / filename)
        self.driver.save_screenshot(path)
        return path

    def _scroll_to(self, element):
        """Scroll element into view."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)

    def _fill_text(self, by, value, text: str):
        """Clear and fill a text field."""
        element = self.wait.until(EC.presence_of_element_located((by, value)))
        self._scroll_to(element)
        element.clear()
        element.send_keys(text)

    def _click(self, by, value):
        """Wait for element and click."""
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        self._scroll_to(element)
        element.click()

    def _fill_employee_form(self, emp: Employee):
        """Fill all form fields for one employee."""

        # Navigate to form
        self.driver.get(self.FORM_URL)
        time.sleep(0.5)

        # ── Close ads/banners
        try:
            self.driver.execute_script(
                "var ads = document.querySelectorAll('.google-auto-placed,.adsbygoogle'); "
                "ads.forEach(el => el.remove());"
            )
        except Exception:
            pass

        # ── Name
        self._fill_text(By.ID, "firstName", emp.first_name)
        self._fill_text(By.ID, "lastName", emp.last_name)

        # ── Email
        self._fill_text(By.ID, "userEmail", emp.email)

        # ── Gender (radio button)
        gender_map = {"Male": "gender-radio-1", "Female": "gender-radio-2", "Other": "gender-radio-3"}
        if emp.gender in gender_map:
            # Use JavaScript click (label may intercept)
            radio = self.driver.find_element(By.ID, gender_map[emp.gender])
            self.driver.execute_script("arguments[0].click();", radio)

        # ── Mobile
        self._fill_text(By.ID, "userNumber", emp.mobile)

        # ── Date of Birth (click datepicker, type date)
        dob_field = self.wait.until(EC.element_to_be_clickable((By.ID, "dateOfBirthInput")))
        self._scroll_to(dob_field)
        dob_field.click()
        time.sleep(0.3)
        dob_field.send_keys(Keys.CONTROL + "a")
        dob_field.send_keys(emp.dob)
        dob_field.send_keys(Keys.ESCAPE)

        # ── Subjects (type and press Enter)
        if emp.subjects:
            for subject in emp.subjects.split(","):
                subject = subject.strip()
                subjects_field = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "subjectsInput"))
                )
                subjects_field.send_keys(subject)
                time.sleep(0.5)
                # Select first suggestion
                try:
                    suggestion = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".subjects-auto-complete__option"))
                    )
                    suggestion.click()
                except TimeoutException:
                    subjects_field.send_keys(Keys.ESCAPE)

        # ── Hobbies (checkboxes)
        hobby_map = {"Sports": "hobbies-checkbox-1", "Reading": "hobbies-checkbox-2",
                     "Music": "hobbies-checkbox-3"}
        if emp.hobbies:
            for hobby in emp.hobbies.split(","):
                hobby = hobby.strip()
                if hobby in hobby_map:
                    checkbox = self.driver.find_element(By.ID, hobby_map[hobby])
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)

        # ── Address
        self._fill_text(By.ID, "currentAddress", emp.address)

        # ── State (custom dropdown)
        state_dropdown = self.wait.until(
            EC.element_to_be_clickable((By.ID, "react-select-3-input"))
        )
        self._scroll_to(state_dropdown)
        state_dropdown.send_keys(emp.state)
        time.sleep(0.3)
        state_dropdown.send_keys(Keys.ENTER)

        # ── City (depends on state selection)
        time.sleep(0.3)
        city_dropdown = self.wait.until(
            EC.element_to_be_clickable((By.ID, "react-select-4-input"))
        )
        city_dropdown.send_keys(emp.city)
        time.sleep(0.3)
        city_dropdown.send_keys(Keys.ENTER)

    def _submit_and_verify(self, emp: Employee) -> bool:
        """Submit form and verify success."""
        # Find and click submit
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "submit")))
        self._scroll_to(submit_btn)
        self.driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(0.5)

        # Check for success modal
        try:
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "example-modal-sizes-title-lg"))
            )
            return True
        except TimeoutException:
            return False

    def process_employee(self, emp: Employee) -> Employee:
        """Process a single employee registration."""
        if emp.status == "success":
            self.logger.info(f"  Skipping {emp.first_name} {emp.last_name} (already processed)")
            return emp

        self.logger.info(f"  Processing: {emp.first_name} {emp.last_name}")

        try:
            self._fill_employee_form(emp)
            success = self._submit_and_verify(emp)

            if success:
                emp.status = "success"
                emp.screenshot = self._screenshot(
                    f"success_{emp.first_name}_{emp.last_name}.png"
                )
                self.logger.info(f"  ✓ Registered: {emp.first_name} {emp.last_name}")
            else:
                emp.status = "failed"
                emp.error_msg = "Form submission failed — no success modal"
                emp.screenshot = self._screenshot(
                    f"failed_{emp.first_name}_{emp.last_name}.png"
                )
                self.logger.error(f"  ✗ Failed: {emp.first_name} {emp.last_name}")

        except Exception as e:
            emp.status = "failed"
            emp.error_msg = str(e)
            emp.screenshot = self._screenshot(
                f"error_{emp.first_name}_{emp.last_name}.png"
            )
            self.logger.error(f"  ✗ Error for {emp.first_name}: {e}")

        return emp

    def run(self, input_csv: str, output_csv: str = None):
        """Process all employees from CSV file."""
        if not output_csv:
            output_csv = input_csv.replace(".csv", "_processed.csv")

        employees = load_employees_from_csv(input_csv)
        pending = [e for e in employees if e.status == "pending"]

        self.logger.info(f"  Loaded {len(employees)} employees ({len(pending)} pending)")

        self._init_driver()
        try:
            for i, emp in enumerate(employees, 1):
                self.logger.info(f"  [{i}/{len(employees)}] {emp.first_name} {emp.last_name}")
                self.process_employee(emp)
                save_employees_to_csv(employees, output_csv)  # Save after each
                time.sleep(random.uniform(0.5, 1.0))
        finally:
            self.driver.quit()

        # Print summary
        success = [e for e in employees if e.status == "success"]
        failed  = [e for e in employees if e.status == "failed"]

        print(f"\n{'─'*50}")
        print(f"  RESULTS: {len(success)} success, {len(failed)} failed")
        if failed:
            print("  FAILED:")
            for e in failed:
                print(f"    ✗ {e.first_name} {e.last_name}: {e.error_msg}")
        print(f"  Output: {output_csv}")
        print(f"{'─'*50}")

        return employees


import random

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Create sample input CSV
    input_csv  = "/tmp/employees_input.csv"
    output_csv = "/tmp/employees_processed.csv"

    create_sample_csv(input_csv)
    print(f"Sample CSV: {input_csv}")
    print("Starting form filler bot...")

    bot = FormFillerBot(headless=True)
    bot.run(input_csv, output_csv)

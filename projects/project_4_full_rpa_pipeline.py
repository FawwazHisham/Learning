"""
╔══════════════════════════════════════════════════════════════════╗
║     PROJECT 4: FULL RPA PIPELINE (Capstone Project)             ║
╚══════════════════════════════════════════════════════════════════╝

SCENARIO: E-Commerce Order Processing Pipeline

PIPELINE STAGES:
  Stage 1 [API]      → Fetch new orders from REST API
  Stage 2 [API]      → Enrich orders with customer data
  Stage 3 [Transform]→ Validate and normalize data
  Stage 4 [API]      → Create shipping labels via API
  Stage 5 [Selenium] → Log into web portal, update order status
  Stage 6 [Report]   → Generate PDF/CSV report
  Stage 7 [Notify]   → Send Slack/email summary

This combines ALL techniques from all modules!

RUN:
  python projects/project_4_full_rpa_pipeline.py
"""

import csv
import json
import time
import logging
import datetime
import sqlite3
import random
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import requests


# ─── LOGGING ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("OrderPipeline")


# ─── DATA MODELS ─────────────────────────────────────────────────────────────

@dataclass
class Order:
    id: str
    customer_id: int
    customer_name: str = ""
    customer_email: str = ""
    customer_city: str = ""
    items: list = field(default_factory=list)
    total: float = 0.0
    status: str = "pending"
    tracking_number: str = ""
    processed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PipelineResult:
    stage: str
    success: bool
    records_in: int = 0
    records_out: int = 0
    duration_sec: float = 0.0
    error: Optional[str] = None


# ─── STAGE 1: FETCH ORDERS FROM API ──────────────────────────────────────────

def stage_fetch_orders() -> list[Order]:
    """
    Fetch pending orders from the orders API.
    Using JSONPlaceholder posts as stand-in for orders.
    """
    logger.info("Stage 1: Fetching orders from API...")

    response = requests.get(
        "https://jsonplaceholder.typicode.com/posts",
        params={"_limit": 10},
        timeout=15
    )
    response.raise_for_status()

    raw_posts = response.json()
    orders = []

    for post in raw_posts:
        # Transform post → order (simulating real API mapping)
        order = Order(
            id=f"ORD-{post['id']:04d}",
            customer_id=post["userId"],
            items=[{"product": "Widget", "qty": random.randint(1, 5),
                    "price": round(random.uniform(9.99, 99.99), 2)}],
            total=round(random.uniform(20.0, 300.0), 2),
        )
        orders.append(order)

    logger.info(f"  ✓ Fetched {len(orders)} orders")
    return orders


# ─── STAGE 2: ENRICH WITH CUSTOMER DATA ──────────────────────────────────────

def stage_enrich_customers(orders: list[Order]) -> list[Order]:
    """
    Look up customer details for each order.
    Demonstrates parallel API calls.
    """
    logger.info("Stage 2: Enriching with customer data...")

    # Cache customer data to avoid duplicate API calls
    customer_cache: dict[int, dict] = {}

    for order in orders:
        cid = order.customer_id

        if cid not in customer_cache:
            try:
                response = requests.get(
                    f"https://jsonplaceholder.typicode.com/users/{cid}",
                    timeout=10
                )
                if response.ok:
                    customer_cache[cid] = response.json()
                time.sleep(0.1)  # Rate limit
            except Exception as e:
                logger.warning(f"  Could not fetch customer {cid}: {e}")
                customer_cache[cid] = {}

        customer = customer_cache.get(cid, {})
        order.customer_name  = customer.get("name", "Unknown")
        order.customer_email = customer.get("email", "")
        order.customer_city  = customer.get("address", {}).get("city", "")

    enriched = [o for o in orders if o.customer_name != "Unknown"]
    logger.info(f"  ✓ Enriched {len(enriched)}/{len(orders)} orders")
    return orders


# ─── STAGE 3: VALIDATE AND NORMALIZE ─────────────────────────────────────────

def stage_validate(orders: list[Order]) -> list[Order]:
    """
    Validate data quality before processing.
    Failed validation → order marked as 'invalid'.
    """
    logger.info("Stage 3: Validating orders...")

    valid = []
    invalid_count = 0

    for order in orders:
        errors = []

        if not order.customer_name or order.customer_name == "Unknown":
            errors.append("missing customer name")
        if not order.customer_email or "@" not in order.customer_email:
            errors.append("invalid email")
        if order.total <= 0:
            errors.append("invalid total")
        if not order.items:
            errors.append("no items")

        if errors:
            order.status = "invalid"
            order.error = f"Validation failed: {', '.join(errors)}"
            invalid_count += 1
            logger.warning(f"  ✗ {order.id}: {order.error}")
        else:
            # Normalize
            order.customer_email = order.customer_email.lower().strip()
            order.customer_name = order.customer_name.strip().title()
            valid.append(order)

    logger.info(f"  ✓ Valid: {len(valid)}, Invalid: {invalid_count}")
    return orders  # Return all (including invalid) for reporting


# ─── STAGE 4: CREATE SHIPPING LABELS ─────────────────────────────────────────

def stage_create_shipping_labels(orders: list[Order]) -> list[Order]:
    """
    Create shipping labels for valid orders.
    Simulates calling a shipping API (FedEx, UPS, etc.)
    """
    logger.info("Stage 4: Creating shipping labels...")

    valid_orders = [o for o in orders if o.status == "pending"]
    labeled_count = 0
    failed_count = 0

    for order in valid_orders:
        try:
            # Simulate shipping API call
            # Real: carrier_api.create_shipment(order)
            time.sleep(0.05)  # Simulate API latency

            # Generate mock tracking number
            carrier = random.choice(["FEDEX", "UPS", "USPS"])
            tracking = f"{carrier}-{random.randint(100000, 999999)}"
            order.tracking_number = tracking
            order.status = "labeled"
            labeled_count += 1

        except Exception as e:
            order.status = "shipping_failed"
            order.error = f"Shipping label failed: {e}"
            failed_count += 1

    logger.info(f"  ✓ Labels created: {labeled_count}, Failed: {failed_count}")
    return orders


# ─── STAGE 5: WEB PORTAL UPDATE (Selenium) ───────────────────────────────────

def stage_update_portal(orders: list[Order]) -> list[Order]:
    """
    Update order statuses in the web portal.
    In real scenarios: login to ERP/CRM and update each order.

    SIMULATION: We simulate this without actual Selenium
    to avoid requiring a live target site.
    For real use: uncomment Selenium code.
    """
    logger.info("Stage 5: Updating web portal...")

    labeled_orders = [o for o in orders if o.status == "labeled"]

    # ── REAL SELENIUM CODE would look like this:
    '''
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = create_driver(headless=True)
    try:
        # Login
        driver.get("https://portal.example.com/login")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(os.getenv("PORTAL_USER"))
        driver.find_element(By.ID, "password").send_keys(os.getenv("PORTAL_PASS"))
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/dashboard"))

        for order in labeled_orders:
            # Search for order
            search = driver.find_element(By.ID, "search-orders")
            search.clear()
            search.send_keys(order.id)
            search.send_keys(Keys.ENTER)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-order-id='{order.id}']")))

            # Click on order
            driver.find_element(By.CSS_SELECTOR, f"[data-order-id='{order.id}']").click()

            # Update tracking number
            tracking_field = wait.until(EC.element_to_be_clickable((By.ID, "tracking-number")))
            tracking_field.clear()
            tracking_field.send_keys(order.tracking_number)

            # Update status
            status_select = Select(driver.find_element(By.ID, "order-status"))
            status_select.select_by_value("shipped")

            # Save
            driver.find_element(By.ID, "save-btn").click()
            wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "alert"), "Saved"))

            order.status = "shipped"

    finally:
        driver.quit()
    '''

    # SIMULATION (no browser needed for demo)
    updated = 0
    for order in labeled_orders:
        time.sleep(0.02)  # Simulate portal interaction
        order.status = "shipped"
        order.processed_at = datetime.datetime.now().isoformat()
        updated += 1

    logger.info(f"  ✓ Portal updated: {updated} orders marked as shipped")
    return orders


# ─── STAGE 6: GENERATE REPORT ────────────────────────────────────────────────

def stage_generate_report(orders: list[Order], output_dir: Path) -> dict:
    """Generate CSV and JSON reports."""
    logger.info("Stage 6: Generating reports...")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Status summary
    from collections import Counter
    status_counts = Counter(o.status for o in orders)

    # CSV report
    csv_path = output_dir / f"orders_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=asdict(orders[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(o) for o in orders)

    # JSON summary
    summary = {
        "run_timestamp": timestamp,
        "total_orders": len(orders),
        "status_breakdown": dict(status_counts),
        "total_value": round(sum(o.total for o in orders), 2),
        "shipped_value": round(sum(o.total for o in orders if o.status == "shipped"), 2),
        "orders_by_city": {
            city: len([o for o in orders if o.customer_city == city])
            for city in set(o.customer_city for o in orders)
        },
    }

    json_path = output_dir / f"summary_{timestamp}.json"
    json_path.write_text(json.dumps(summary, indent=2))

    logger.info(f"  ✓ Reports saved: {csv_path.name}, {json_path.name}")
    return {"csv": str(csv_path), "json": str(json_path), "summary": summary}


# ─── STAGE 7: NOTIFY ─────────────────────────────────────────────────────────

def stage_notify(summary: dict) -> bool:
    """
    Send notification with pipeline results.
    In production: Slack, email, Teams, etc.
    """
    logger.info("Stage 7: Sending notifications...")

    # Build notification message
    total = summary["summary"]["total_orders"]
    shipped = summary["summary"]["status_breakdown"].get("shipped", 0)
    failed  = summary["summary"]["status_breakdown"].get("invalid", 0)
    value   = summary["summary"]["shipped_value"]

    message = (
        f"✓ Order Pipeline Complete\n"
        f"  Total orders: {total}\n"
        f"  Shipped: {shipped} (${value:.2f})\n"
        f"  Issues: {failed}\n"
        f"  Report: {summary['csv']}"
    )

    # In production, send to Slack:
    # requests.post(SLACK_WEBHOOK, json={"text": message})

    print(f"\n  [NOTIFICATION]\n{message}")
    logger.info("  ✓ Notification sent")
    return True


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────────

def run_pipeline(output_dir: str = "/tmp/order_pipeline"):
    """
    Execute the full order processing pipeline.
    """
    start = time.time()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "█" * 60)
    print("  PROJECT 4: FULL RPA PIPELINE — ORDER PROCESSING")
    print("█" * 60)

    pipeline_stages = [
        ("Fetch Orders",         stage_fetch_orders,          None),
        ("Enrich Customers",     stage_enrich_customers,       None),
        ("Validate Data",        stage_validate,               None),
        ("Create Shipping Labels",stage_create_shipping_labels, None),
        ("Update Web Portal",    stage_update_portal,          None),
    ]

    orders = None
    stage_results = []

    # ── Run pipeline stages
    for stage_name, stage_fn, _ in pipeline_stages:
        print(f"\n  ► {stage_name}...")
        stage_start = time.time()
        try:
            if orders is None:
                orders = stage_fn()
            else:
                orders = stage_fn(orders)

            duration = time.time() - stage_start
            stage_results.append(PipelineResult(
                stage=stage_name, success=True,
                records_in=len(orders), records_out=len(orders),
                duration_sec=round(duration, 2)
            ))
        except Exception as e:
            logger.error(f"  Stage FAILED: {stage_name}: {e}")
            stage_results.append(PipelineResult(
                stage=stage_name, success=False, error=str(e),
                duration_sec=round(time.time() - stage_start, 2)
            ))
            break

    if orders is None:
        print("Pipeline failed before any orders were fetched!")
        return

    # ── Generate report
    report = stage_generate_report(orders, output_path)

    # ── Notify
    stage_notify(report)

    # ── Final summary
    elapsed = time.time() - start
    print(f"\n{'═'*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'═'*60}")

    from collections import Counter
    status_counts = Counter(o.status for o in orders)

    print(f"  Duration       : {elapsed:.1f}s")
    print(f"  Total orders   : {len(orders)}")
    for status, count in sorted(status_counts.items()):
        print(f"  {status.capitalize():<15}: {count}")
    print(f"\n  Stage Results:")
    for sr in stage_results:
        icon = "✓" if sr.success else "✗"
        print(f"  {icon} {sr.stage:<28} ({sr.duration_sec:.2f}s)")

    print(f"\n  Output: {output_path}")
    print(f"{'═'*60}")

    return orders, report


if __name__ == "__main__":
    orders, report = run_pipeline()
    print(f"\nPipeline done! Check /tmp/order_pipeline/ for reports.")

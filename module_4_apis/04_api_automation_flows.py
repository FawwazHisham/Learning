"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 4 — LESSON 4: API AUTOMATION FLOWS                   ║
╚══════════════════════════════════════════════════════════════════╝

REAL-WORLD API AUTOMATION PATTERNS:
  1. Data sync between two systems
  2. Bulk operations (create/update hundreds of records)
  3. Data transformation pipeline
  4. Multi-API orchestration
  5. Webhook handling
  6. Async API calls for speed
"""

import csv
import json
import time
import asyncio
import aiohttp       # pip install aiohttp
import requests
from pathlib import Path
from typing import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE_URL = "https://jsonplaceholder.typicode.com"


# ─── 1. DATA SYNC PATTERN ────────────────────────────────────────────────────

def data_sync_pattern():
    print("── 1. DATA SYNC: Two-System Sync ────────────────────────────")
    code = '''
    """
    Sync data from Source System → Target System.
    Handles: creates, updates, skips unchanged records.

    Example: Sync customers from CRM to ERP.
    """
    import requests

    def get_source_records(source_api) -> list[dict]:
        """Fetch all records from source system."""
        return source_api.get_all("/customers", per_page=500)

    def get_target_records(target_api) -> dict[str, dict]:
        """Get target system records indexed by external_id."""
        records = target_api.get_all("/customers")
        return {r["external_id"]: r for r in records}

    def sync_customers(source_api, target_api) -> dict:
        results = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        source_records = get_source_records(source_api)
        target_index = get_target_records(target_api)

        for record in source_records:
            external_id = str(record["id"])
            try:
                if external_id not in target_index:
                    # CREATE new record
                    target_api.post("/customers", data={
                        "external_id": external_id,
                        "name": record["name"],
                        "email": record["email"],
                    })
                    results["created"] += 1

                else:
                    existing = target_index[external_id]
                    # Check if update needed
                    if (existing["name"] != record["name"] or
                        existing["email"] != record["email"]):
                        target_api.patch(
                            f"/customers/{existing['id']}",
                            data={"name": record["name"], "email": record["email"]}
                        )
                        results["updated"] += 1
                    else:
                        results["skipped"] += 1

            except Exception as e:
                print(f"  Error syncing {external_id}: {e}")
                results["errors"] += 1

        return results

    stats = sync_customers(source_api, target_api)
    print(f"Sync complete: {stats}")
    '''
    print(code)


# ─── 2. BULK OPERATIONS WITH RATE LIMITING ───────────────────────────────────

def bulk_operations():
    print("\n── 2. BULK OPERATIONS ───────────────────────────────────────")
    code = '''
    from time import sleep
    from tqdm import tqdm  # pip install tqdm (progress bar)

    def bulk_create(api, items: list[dict], batch_size=50, delay=0.1) -> list:
        """
        Create many records efficiently with rate limiting.
        """
        created = []
        errors = []

        # Process in batches (some APIs have bulk endpoints)
        batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]

        for batch_num, batch in enumerate(tqdm(batches, desc="Processing batches"), 1):
            batch_results = []

            for item in batch:
                try:
                    result = api.post("/records", data=item)
                    batch_results.append(result)
                    created.append(result)
                except Exception as e:
                    errors.append({"item": item, "error": str(e)})

            # Rate limiting delay between batches
            if batch_num < len(batches):
                sleep(delay)

        print(f"\\nCreated: {len(created)}, Errors: {len(errors)}")
        return created, errors

    # ── With real progress tracking
    def process_csv_to_api(csv_path: str, api) -> dict:
        """Read CSV file and create API records from each row."""
        import csv

        with open(csv_path) as f:
            rows = list(csv.DictReader(f))

        print(f"Processing {len(rows)} records...")
        return bulk_create(api, rows)
    '''
    print(code)


# ─── 3. DATA TRANSFORMATION PIPELINE ─────────────────────────────────────────

def transformation_pipeline():
    print("\n── 3. DATA TRANSFORMATION PIPELINE ─────────────────────────")
    code = '''
    """
    Extract → Transform → Load (ETL) pipeline via APIs.
    """
    from datetime import datetime
    from typing import Generator

    # ── EXTRACT
    def extract_orders(api, start_date: str, end_date: str) -> Generator:
        """Yield orders page by page (memory efficient)."""
        page = 1
        while True:
            orders = api.get("/orders", params={
                "created_after": start_date,
                "created_before": end_date,
                "page": page,
                "per_page": 100,
            })
            if not orders:
                break
            yield from orders
            page += 1

    # ── TRANSFORM
    def transform_order(order: dict) -> dict:
        """Normalize order data for target system."""
        return {
            "order_id":     order["id"],
            "customer":     order["customer"]["email"],
            "total_amount": float(order["total"]) / 100,  # Cents to dollars
            "currency":     order["currency"].upper(),
            "status":       order["status"].lower(),
            "created_at":   datetime.fromisoformat(order["created_at"]).strftime("%Y-%m-%d"),
            "items":        len(order.get("line_items", [])),
        }

    def validate_order(order: dict) -> tuple[bool, str]:
        """Validate transformed order before loading."""
        if not order.get("order_id"):
            return False, "Missing order_id"
        if order["total_amount"] < 0:
            return False, "Negative amount"
        if order["status"] not in ("pending", "completed", "cancelled"):
            return False, f"Unknown status: {order['status']}"
        return True, ""

    # ── LOAD
    def load_orders(target_api, orders: list[dict]) -> dict:
        """Load transformed orders to target system."""
        results = {"loaded": 0, "rejected": 0}
        for order in orders:
            valid, error = validate_order(order)
            if valid:
                target_api.post("/orders", data=order)
                results["loaded"] += 1
            else:
                print(f"  Rejected {order.get('order_id')}: {error}")
                results["rejected"] += 1
        return results

    # ── FULL PIPELINE
    def run_etl_pipeline(source_api, target_api, start_date, end_date):
        pipeline_results = {"extracted": 0, "transformed": 0, "loaded": 0, "errors": 0}
        orders_to_load = []

        for raw_order in extract_orders(source_api, start_date, end_date):
            pipeline_results["extracted"] += 1
            try:
                transformed = transform_order(raw_order)
                orders_to_load.append(transformed)
                pipeline_results["transformed"] += 1
            except Exception as e:
                print(f"  Transform error: {e}")
                pipeline_results["errors"] += 1

        load_results = load_orders(target_api, orders_to_load)
        pipeline_results.update(load_results)
        return pipeline_results
    '''
    print(code)


# ─── 4. ASYNC API CALLS ───────────────────────────────────────────────────────

ASYNC_EXAMPLE = '''
"""
Async API calls using aiohttp for high-speed parallel requests.
Use when you need to make many API calls quickly.

sync version:  1000 requests × 100ms each = ~100 seconds
async version: 1000 requests (concurrent)  = ~5-10 seconds
"""
import asyncio
import aiohttp
from tqdm.asyncio import tqdm  # pip install tqdm


async def fetch_one(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch a single URL asynchronously."""
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def fetch_all(urls: list[str], concurrency: int = 20) -> list:
    """
    Fetch all URLs concurrently, limited by concurrency semaphore.
    concurrency=20 means max 20 simultaneous requests.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def fetch_with_semaphore(session, url):
        async with semaphore:
            try:
                data = await fetch_one(session, url)
                return {"url": url, "data": data, "success": True}
            except Exception as e:
                return {"url": url, "error": str(e), "success": False}

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_with_semaphore(session, url) for url in urls]
        # tqdm shows progress bar
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            results.append(await coro)

    return results


async def bulk_create_async(api_url: str, records: list[dict],
                            token: str, concurrency: int = 10) -> list:
    """Create many records via API in parallel."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def create_one(session, record):
        async with semaphore:
            try:
                async with session.post(api_url, json=record, headers=headers) as r:
                    r.raise_for_status()
                    return await r.json()
            except Exception as e:
                return {"error": str(e), "record": record}

    async with aiohttp.ClientSession() as session:
        tasks = [create_one(session, r) for r in records]
        results = await asyncio.gather(*tasks)

    return results


# Run async code
if __name__ == "__main__":
    urls = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 11)]

    import time
    start = time.time()
    results = asyncio.run(fetch_all(urls, concurrency=5))
    elapsed = time.time() - start

    success = [r for r in results if r["success"]]
    print(f"Fetched {len(success)}/{len(urls)} in {elapsed:.2f}s")
'''


# ─── 5. MULTI-API ORCHESTRATION ──────────────────────────────────────────────

def multi_api_orchestration():
    print("\n── 5. MULTI-API ORCHESTRATION ───────────────────────────────")
    code = '''
    """
    Bot that combines multiple APIs:
    1. Read new orders from Shopify API
    2. Look up customer in HubSpot CRM
    3. Create shipping label in ShipStation
    4. Send confirmation via SendGrid email API
    """

    def process_new_orders():
        # 1. Get new orders from Shopify
        shopify = ShopifyClient(token=os.getenv("SHOPIFY_TOKEN"))
        new_orders = shopify.get_orders(fulfillment_status="unfulfilled", limit=50)

        for order in new_orders:
            try:
                customer_email = order["email"]

                # 2. Find/create customer in CRM
                hubspot = HubSpotClient(api_key=os.getenv("HUBSPOT_KEY"))
                customer = hubspot.find_or_create_contact(email=customer_email)

                # Update CRM with order info
                hubspot.create_deal(
                    contact_id=customer["id"],
                    amount=float(order["total_price"]),
                    name=f"Order #{order['order_number']}",
                )

                # 3. Create shipping label
                shipstation = ShipStationClient(
                    key=os.getenv("SS_KEY"),
                    secret=os.getenv("SS_SECRET")
                )
                label = shipstation.create_shipment(
                    order_number=order["order_number"],
                    ship_to=order["shipping_address"],
                    weight_oz=calculate_weight(order["line_items"]),
                )

                # 4. Send confirmation email
                sendgrid = SendGridClient(api_key=os.getenv("SENDGRID_KEY"))
                sendgrid.send_email(
                    to=customer_email,
                    template_id="d-xxxxx",
                    data={
                        "order_number": order["order_number"],
                        "tracking_number": label["tracking_number"],
                        "carrier": label["carrier"],
                    }
                )

                # 5. Update Shopify order status
                shopify.fulfill_order(
                    order_id=order["id"],
                    tracking_number=label["tracking_number"],
                    tracking_company=label["carrier"],
                )

                print(f"  Processed order #{order['order_number']}")

            except Exception as e:
                # Log error and continue with next order
                logger.error(f"Failed order #{order['order_number']}: {e}")
                notify_team(f"Order processing failed: #{order['order_number']}")

    # Schedule to run every 15 minutes
    import schedule
    schedule.every(15).minutes.do(process_new_orders)

    while True:
        schedule.run_pending()
        time.sleep(30)
    '''
    print(code)


# ─── 6. WORKING DEMO ──────────────────────────────────────────────────────────

def working_demo():
    print("\n── WORKING DEMO: API Data Pipeline ──────────────────────────")

    print("  Step 1: Extract data from API...")
    response = requests.get(f"{BASE_URL}/users")
    users = response.json()
    print(f"  Extracted {len(users)} users")

    print("\n  Step 2: Transform data...")
    transformed = []
    for user in users:
        transformed.append({
            "id":       user["id"],
            "name":     user["name"].upper(),
            "email":    user["email"].lower(),
            "city":     user["address"]["city"],
            "company":  user["company"]["name"],
            "username": user["username"],
        })
    print(f"  Transformed {len(transformed)} records")

    print("\n  Step 3: Simulate API bulk create...")
    created = 0
    for record in transformed[:3]:  # Only 3 for demo
        response = requests.post(f"{BASE_URL}/users", json=record)
        if response.status_code == 201:
            created += 1
    print(f"  Created {created} records via API")

    print("\n  Step 4: Save output to CSV...")
    output_path = Path("/tmp/api_output.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=transformed[0].keys())
        writer.writeheader()
        writer.writerows(transformed)
    print(f"  Saved to: {output_path}")

    print("\n  Pipeline complete!")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  MODULE 4 — API AUTOMATION FLOWS")
    print("█" * 60)

    data_sync_pattern()
    bulk_operations()
    transformation_pipeline()
    multi_api_orchestration()

    print("\n── ASYNC EXAMPLE ─────────────────────────────────────────────")
    print(ASYNC_EXAMPLE)

    working_demo()

    print("\n" + "─" * 55)
    print("  NEXT: python module_4_apis/05_webhooks_and_events.py")

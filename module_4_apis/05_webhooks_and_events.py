"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 4 — LESSON 5: WEBHOOKS & EVENT-DRIVEN AUTOMATION     ║
╚══════════════════════════════════════════════════════════════════╝

POLLING vs WEBHOOKS:
  ┌─────────────────────────────────────────────────────────┐
  │  POLLING (Pull):                                         │
  │  Your bot → API every 60s → "Any new events?"           │
  │  Inefficient, slow, wastes API calls                     │
  │                                                          │
  │  WEBHOOKS (Push):                                        │
  │  Event happens → API → Your server instantly            │
  │  Efficient, real-time, event-driven                      │
  └─────────────────────────────────────────────────────────┘

COMMON WEBHOOK SENDERS:
  GitHub, Stripe, Shopify, Twilio, Slack, PagerDuty
"""

import json
import hmac
import hashlib
import time
from flask import Flask, request, jsonify  # pip install flask
from threading import Thread
import requests


# ─── 1. RECEIVING WEBHOOKS (Server Side) ─────────────────────────────────────

app = Flask(__name__)

WEBHOOK_SECRET = "your_webhook_secret_here"


@app.route("/webhook/github", methods=["POST"])
def handle_github_webhook():
    """
    GitHub webhook handler.
    Triggered when a push, PR, or issue happens.
    """
    # ── 1. Verify signature (ALWAYS verify webhooks!)
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_github_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # ── 2. Parse event type
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    # ── 3. Handle different events
    if event_type == "push":
        handle_push(payload)
    elif event_type == "pull_request":
        handle_pull_request(payload)
    elif event_type == "issues":
        handle_issue(payload)
    else:
        print(f"Unhandled event: {event_type}")

    # ── Always return 200 quickly (process in background)
    return jsonify({"status": "received"}), 200


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature using HMAC-SHA256."""
    if not signature_header:
        return False

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    expected_header = f"sha256={expected}"
    return hmac.compare_digest(expected_header, signature_header)


def handle_push(payload: dict):
    """React to a git push."""
    repo = payload["repository"]["name"]
    branch = payload["ref"].split("/")[-1]
    pusher = payload["pusher"]["name"]
    commits = payload.get("commits", [])

    print(f"  Push to {repo}/{branch} by {pusher}")
    print(f"  Commits: {len(commits)}")

    # Example reactions:
    if branch == "main":
        # Trigger deployment
        trigger_deployment(repo, branch)
    elif branch.startswith("hotfix/"):
        # Send urgent notification
        notify_team(f"Hotfix pushed: {repo}/{branch}")


def handle_pull_request(payload: dict):
    """React to PR events."""
    action = payload["action"]  # opened, closed, merged, etc.
    pr = payload["pull_request"]

    if action == "opened":
        print(f"  New PR: #{pr['number']} - {pr['title']}")
        # Auto-assign reviewers, add labels, etc.
    elif action == "closed" and pr.get("merged"):
        print(f"  PR #{pr['number']} merged!")
        # Trigger release process
    elif action == "review_requested":
        reviewer = payload["requested_reviewer"]["login"]
        notify_reviewer(reviewer, pr["html_url"])


def handle_issue(payload: dict):
    """React to issue events."""
    action = payload["action"]
    issue = payload["issue"]

    if action == "opened" and "bug" in [l["name"] for l in issue.get("labels", [])]:
        # Create ticket in Jira
        create_jira_ticket(
            title=issue["title"],
            description=issue["body"],
            url=issue["html_url"]
        )


# ─── Stub functions for demo ────────────────────────────────────────────
def trigger_deployment(repo, branch): print(f"  → Triggering deployment: {repo}/{branch}")
def notify_team(msg): print(f"  → Team notification: {msg}")
def notify_reviewer(reviewer, url): print(f"  → Notifying {reviewer}: {url}")
def create_jira_ticket(**kwargs): print(f"  → Creating Jira ticket: {kwargs['title']}")


# ─── 2. STRIPE WEBHOOK HANDLER ───────────────────────────────────────────────

stripe_webhook_code = '''
@app.route("/webhook/stripe", methods=["POST"])
def handle_stripe_webhook():
    """
    Stripe webhook — handles payment events.
    """
    import stripe  # pip install stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        payment_id = data["id"]
        amount = data["amount"] / 100  # Convert cents to dollars
        currency = data["currency"]
        customer = data.get("customer")
        print(f"  Payment succeeded: {payment_id} — ${amount:.2f} {currency}")
        # Update database, send receipt, fulfill order, etc.

    elif event_type == "payment_intent.payment_failed":
        print(f"  Payment failed: {data['id']}")
        # Notify customer, retry logic, etc.

    elif event_type == "customer.subscription.deleted":
        customer_id = data["customer"]
        print(f"  Subscription cancelled: {customer_id}")
        # Revoke access, send cancellation email, etc.

    return jsonify({"status": "ok"}), 200
'''
print("── STRIPE WEBHOOK ───────────────────────────────────────────")
print(stripe_webhook_code)


# ─── 3. PROCESSING WEBHOOKS ASYNCHRONOUSLY ───────────────────────────────────

async_webhook_code = '''
"""
Best practice: Return 200 immediately, process in background.
Webhook providers re-send if they don't get 200 quickly.
"""
from threading import Thread
from queue import Queue
import logging

event_queue = Queue()

def webhook_worker():
    """Background worker that processes webhook events."""
    while True:
        event = event_queue.get()
        try:
            process_event(event)
        except Exception as e:
            logging.error(f"Event processing error: {e}")
        finally:
            event_queue.task_done()

# Start background worker
worker = Thread(target=webhook_worker, daemon=True)
worker.start()


@app.route("/webhook", methods=["POST"])
def webhook():
    """Accept webhook, queue for async processing, return 200 instantly."""
    payload = request.json
    event_queue.put(payload)              # Queue for background processing
    return jsonify({"status": "queued"}), 200   # Return immediately

def process_event(event: dict):
    """Heavy processing here — runs in background."""
    event_type = event.get("type")
    print(f"Processing: {event_type}")
    # ... complex processing ...
    time.sleep(2)   # Simulating work
    print(f"Done: {event_type}")
'''
print("\n── ASYNC WEBHOOK PROCESSING ─────────────────────────────────")
print(async_webhook_code)


# ─── 4. SENDING WEBHOOKS (outbound) ──────────────────────────────────────────

def sending_webhooks_guide():
    print("\n── 4. SENDING WEBHOOKS (Outbound) ───────────────────────────")
    code = '''
    import hmac, hashlib, json, requests

    def send_webhook(url: str, payload: dict, secret: str = "") -> bool:
        """
        Send a webhook with HMAC signature.
        For notifying other services when events occur in your system.
        """
        body = json.dumps(payload, separators=(",", ":")).encode()
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Source": "my-rpa-bot",
            "X-Timestamp": str(int(time.time())),
        }

        # Sign if secret provided
        if secret:
            sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            headers["X-Signature-256"] = f"sha256={sig}"

        try:
            response = requests.post(url, data=body, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Webhook failed: {e}")
            return False

    # Usage: Notify downstream system when bot finishes a task
    send_webhook(
        url="https://downstream.example.com/webhook",
        payload={
            "event": "rpa_task_completed",
            "task_name": "invoice_processor",
            "records_processed": 150,
            "errors": 2,
            "timestamp": time.time(),
        },
        secret=os.getenv("WEBHOOK_SECRET")
    )
    '''
    print(code)


# ─── 5. POLLING FALLBACK ──────────────────────────────────────────────────────

def smart_polling():
    print("\n── 5. SMART POLLING (when webhooks aren't available) ────────")
    code = '''
    """
    When webhooks aren't available, use smart polling:
    - Track last check timestamp
    - Only process new/changed records
    - Exponential backoff on errors
    """
    import json
    from pathlib import Path

    STATE_FILE = Path("bot_state.json")

    def load_state() -> dict:
        """Load bot state from file (persists across runs)."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {"last_check": "2024-01-01T00:00:00Z", "processed_ids": []}

    def save_state(state: dict):
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def poll_for_changes(api, interval_seconds=60):
        """Continuously poll API for new/changed records."""
        state = load_state()
        consecutive_errors = 0

        while True:
            try:
                # Fetch only records changed since last check
                new_records = api.get("/records", params={
                    "updated_after": state["last_check"],
                    "order": "asc"
                })

                if new_records:
                    print(f"Found {len(new_records)} new/changed records")
                    for record in new_records:
                        if record["id"] not in state["processed_ids"]:
                            process_record(record)
                            state["processed_ids"].append(record["id"])
                            # Keep only last 10000 IDs (memory management)
                            state["processed_ids"] = state["processed_ids"][-10000:]

                state["last_check"] = datetime.now(timezone.utc).isoformat()
                save_state(state)
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                backoff = min(interval_seconds * (2 ** consecutive_errors), 3600)
                print(f"Error (retry in {backoff}s): {e}")
                time.sleep(backoff)
                continue

            time.sleep(interval_seconds)
    '''
    print(code)


# ─── WORKING DEMO ─────────────────────────────────────────────────────────────

def demo_webhook_simulation():
    """Simulate receiving and processing a webhook."""
    print("\n── WEBHOOK SIMULATION DEMO ──────────────────────────────────")

    # Simulate incoming webhook payload (like what GitHub would send)
    payload = {
        "event": "new_order",
        "order": {
            "id": "ORD-12345",
            "customer": "alice@example.com",
            "total": 99.99,
            "items": [
                {"product": "Widget", "qty": 2, "price": 49.99}
            ]
        },
        "timestamp": time.time()
    }

    # Simulate processing
    print(f"\n  Received webhook: {payload['event']}")
    order = payload["order"]
    print(f"  Order ID   : {order['id']}")
    print(f"  Customer   : {order['customer']}")
    print(f"  Total      : ${order['total']:.2f}")
    print(f"  Items      : {len(order['items'])}")

    # React to the event
    print("\n  Processing order...")
    time.sleep(0.3)
    print("  → Sending confirmation email")
    time.sleep(0.2)
    print("  → Creating shipping label")
    time.sleep(0.2)
    print("  → Updating inventory")
    print("\n  Order processed successfully!")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  MODULE 4 — LESSON 5: WEBHOOKS & EVENTS")
    print("█" * 60)

    sending_webhooks_guide()
    smart_polling()
    demo_webhook_simulation()

    print("\n" + "─" * 55)
    print("  WEBHOOK SUMMARY:")
    print("  ► ALWAYS verify webhook signatures")
    print("  ► Return 200 immediately, process in background")
    print("  ► Use webhooks over polling when possible")
    print("  ► Smart polling: track state, fetch only deltas")
    print("  ► Handle duplicate events (idempotent processing)")
    print("─" * 55)
    print("  NEXT: python module_5_advanced/01_error_handling_and_retry.py")

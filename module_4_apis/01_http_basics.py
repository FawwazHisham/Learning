"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 4 — LESSON 1: HTTP & API FUNDAMENTALS               ║
╚══════════════════════════════════════════════════════════════════╝

APIs = Application Programming Interfaces
  ► Direct communication with services (no browser/UI needed)
  ► FASTEST and most reliable form of automation
  ► No anti-bot detection, no screen coordinates

HTTP METHODS:
  GET     → Read data
  POST    → Create new data
  PUT     → Replace existing data
  PATCH   → Update part of data
  DELETE  → Remove data

STATUS CODES:
  2xx → Success (200 OK, 201 Created, 204 No Content)
  3xx → Redirect (301 Moved, 302 Found)
  4xx → Client Error (400 Bad Request, 401 Unauthorized, 404 Not Found)
  5xx → Server Error (500 Internal Server Error, 503 Service Unavailable)
"""

import json
import requests  # pip install requests

# Using JSONPlaceholder — free fake REST API for testing
BASE_URL = "https://jsonplaceholder.typicode.com"


# ─── 1. BASIC HTTP REQUESTS ───────────────────────────────────────────────────

print("── 1. BASIC HTTP REQUESTS ───────────────────────────────────")

# ── GET Request
response = requests.get(f"{BASE_URL}/posts/1")
print(f"\nGET /posts/1")
print(f"  Status : {response.status_code}")
print(f"  Type   : {response.headers.get('Content-Type')}")
print(f"  Body   : {json.dumps(response.json(), indent=2)[:200]}...")

# ── POST Request (create resource)
new_post = {
    "title": "RPA Automation Guide",
    "body": "Using Python for RPA is powerful!",
    "userId": 1
}
response = requests.post(f"{BASE_URL}/posts", json=new_post)
print(f"\nPOST /posts")
print(f"  Status   : {response.status_code}")
print(f"  Created  : {response.json()}")

# ── PUT Request (replace resource)
updated_post = {
    "id": 1,
    "title": "Updated Title",
    "body": "Updated content here",
    "userId": 1
}
response = requests.put(f"{BASE_URL}/posts/1", json=updated_post)
print(f"\nPUT /posts/1 → Status: {response.status_code}")

# ── PATCH Request (partial update)
response = requests.patch(f"{BASE_URL}/posts/1", json={"title": "Only Title Changed"})
print(f"PATCH /posts/1 → Status: {response.status_code}")

# ── DELETE Request
response = requests.delete(f"{BASE_URL}/posts/1")
print(f"DELETE /posts/1 → Status: {response.status_code}")


# ─── 2. REQUEST PARAMETERS ───────────────────────────────────────────────────

print("\n── 2. REQUEST PARAMETERS ────────────────────────────────────")

# ── Query Parameters (?key=value&key2=value2)
params = {"userId": 1, "_limit": 3}
response = requests.get(f"{BASE_URL}/posts", params=params)
posts = response.json()
print(f"\nGET /posts?userId=1&_limit=3")
print(f"  Actual URL: {response.url}")
print(f"  Got {len(posts)} posts")

# ── Request Headers
headers = {
    "Authorization": "Bearer your_token_here",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "MyRPABot/1.0",
    "X-Custom-Header": "rpa_bot",
}
response = requests.get(f"{BASE_URL}/posts/1", headers=headers)
print(f"\nGET with headers → Status: {response.status_code}")

# ── Request Body Types
# JSON (most common for REST APIs)
response = requests.post(f"{BASE_URL}/posts", json={"title": "test"})

# Form data (application/x-www-form-urlencoded)
response = requests.post("https://httpbin.org/post", data={"field1": "value1"})

# Multipart form (for file uploads)
with open("/tmp/demo.txt", "w") as f:
    f.write("test content")
with open("/tmp/demo.txt", "rb") as f:
    response = requests.post("https://httpbin.org/post",
                             files={"file": ("demo.txt", f, "text/plain")})
print(f"File upload → Status: {response.status_code}")


# ─── 3. RESPONSE HANDLING ─────────────────────────────────────────────────────

print("\n── 3. RESPONSE HANDLING ─────────────────────────────────────")

response = requests.get(f"{BASE_URL}/users/1")

# ── Access response data
print(f"\nResponse for GET /users/1:")
print(f"  status_code  : {response.status_code}")
print(f"  ok           : {response.ok}")          # True if 200-299
print(f"  headers      : {dict(list(response.headers.items())[:3])}...")

# ── JSON response
user = response.json()
print(f"  user.name    : {user['name']}")
print(f"  user.email   : {user['email']}")

# ── Text response
print(f"  text (100)   : {response.text[:100]}")

# ── Raw bytes (for file downloads)
# response.content  → raw bytes

# ── raise_for_status() — auto-raise on 4xx/5xx
try:
    r = requests.get(f"{BASE_URL}/posts/99999")  # Doesn't exist
    r.raise_for_status()
    print("Success")
except requests.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} {e.response.reason}")


# ─── 4. SESSIONS (Persist Headers/Cookies) ───────────────────────────────────

print("\n── 4. SESSIONS ──────────────────────────────────────────────")

session_code = '''
# Use Session to avoid repeating headers/cookies on every request
with requests.Session() as session:
    # Set headers once for all requests
    session.headers.update({
        "Authorization": "Bearer my_token",
        "Content-Type": "application/json",
    })

    # All requests automatically use these headers
    response1 = session.get("https://api.example.com/users")
    response2 = session.get("https://api.example.com/orders")
    response3 = session.post("https://api.example.com/orders", json={"item": "A"})

    # Session also maintains cookies automatically
    # (important for login-based APIs)
'''
print(session_code)

# Demo session
with requests.Session() as session:
    session.headers.update({"Accept": "application/json"})
    r1 = session.get(f"{BASE_URL}/posts/1")
    r2 = session.get(f"{BASE_URL}/posts/2")
    print(f"Session requests: {r1.status_code}, {r2.status_code}")


# ─── 5. TIMEOUTS & RETRIES ────────────────────────────────────────────────────

print("\n── 5. TIMEOUTS & RETRIES ────────────────────────────────────")

# Always set timeouts! Default is no timeout (hangs forever)
timeout_code = '''
# ── Set timeout (seconds)
response = requests.get(url, timeout=10)         # 10s for both connect & read
response = requests.get(url, timeout=(3, 10))    # 3s connect, 10s read

# ── Retry with urllib3 (built into requests)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry(
    total=3,
    backoff_factor=1.0,
    status_forcelist=(500, 502, 503, 504)
) -> requests.Session:
    """
    Create a requests Session with automatic retry on failures.
    backoff_factor: wait = {backoff_factor} * 2^(retry_number - 1)
      retry 1: 1s, retry 2: 2s, retry 3: 4s
    """
    session = requests.Session()
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods={"GET", "POST", "PUT", "PATCH", "DELETE"},
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Usage:
session = create_session_with_retry(total=3, backoff_factor=1)
response = session.get("https://api.example.com/data", timeout=10)
'''
print(timeout_code)


# ─── 6. DOWNLOADING FILES ────────────────────────────────────────────────────

print("── 6. DOWNLOADING FILES ─────────────────────────────────────")

download_code = '''
import requests
from pathlib import Path

def download_file(url: str, save_path: str, chunk_size=8192) -> Path:
    """
    Download a file from URL, streaming to avoid memory issues.
    Works for large files (PDFs, Excel, ZIP archives).
    """
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()

        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\\r  Downloading: {pct:.1f}%", end="")

    print(f"\\n  Downloaded: {path} ({path.stat().st_size:,} bytes)")
    return path

# Usage:
# download_file("https://example.com/report.pdf", "/tmp/report.pdf")
'''
print(download_code)


# ─── 7. HTTP REFERENCE ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "─" * 60)
    print("  HTTP QUICK REFERENCE")
    print("─" * 60)

    status_codes = [
        (200, "OK",                    "Request succeeded"),
        (201, "Created",               "Resource created (after POST)"),
        (204, "No Content",            "Success, no body (DELETE, PUT)"),
        (400, "Bad Request",           "Invalid request data"),
        (401, "Unauthorized",          "Missing/invalid authentication"),
        (403, "Forbidden",             "Authenticated but no permission"),
        (404, "Not Found",             "Resource doesn't exist"),
        (409, "Conflict",              "State conflict (duplicate data)"),
        (422, "Unprocessable Entity",  "Validation failed"),
        (429, "Too Many Requests",     "Rate limit exceeded"),
        (500, "Internal Server Error", "Server crashed"),
        (503, "Service Unavailable",   "Server overloaded/down"),
    ]

    print(f"  {'Code':<5} {'Name':<25} Description")
    print(f"  {'─'*5} {'─'*25} {'─'*30}")
    for code, name, desc in status_codes:
        print(f"  {code:<5} {name:<25} {desc}")

    print("─" * 60)
    print("  NEXT: python module_4_apis/02_rest_api_client.py")

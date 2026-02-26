"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 4 — LESSON 3: API AUTHENTICATION METHODS             ║
╚══════════════════════════════════════════════════════════════════╝

AUTHENTICATION TYPES:
  1. API Key           → Simple key in header/query param
  2. Bearer Token      → JWT or OAuth token in Authorization header
  3. Basic Auth        → Base64(username:password) in header
  4. OAuth 2.0         → Industry standard (Google, GitHub, etc.)
  5. Session/Cookie    → Login once, use cookie
  6. HMAC Signature    → Sign requests with secret (AWS-style)
"""

import os
import time
import base64
import hashlib
import hmac
import json
import requests
from datetime import datetime, timezone
from urllib.parse import urlencode


# ─── 1. API KEY ───────────────────────────────────────────────────────────────

def api_key_examples():
    print("── 1. API KEY AUTH ──────────────────────────────────────────")
    code = '''
    # API key in header (most common)
    headers = {"X-API-Key": "your_api_key_here"}
    response = requests.get("https://api.example.com/data", headers=headers)

    # API key in query parameter
    response = requests.get(
        "https://api.example.com/data",
        params={"api_key": "your_api_key_here"}
    )

    # API key as session default
    session = requests.Session()
    session.headers.update({"X-API-Key": os.getenv("API_KEY")})

    # OpenWeatherMap API example
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": "London", "appid": API_KEY, "units": "metric"}
    )
    if response.ok:
        data = response.json()
        print(f"London: {data['main']['temp']}°C, {data['weather'][0]['description']}")
    '''
    print(code)


# ─── 2. BEARER TOKEN (JWT) ───────────────────────────────────────────────────

def bearer_token_examples():
    print("\n── 2. BEARER TOKEN ──────────────────────────────────────────")
    code = '''
    # Simple bearer token
    token = os.getenv("API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.example.com/profile", headers=headers)

    # Token with expiry — refresh when needed
    class TokenManager:
        def __init__(self, login_url, credentials):
            self.login_url = login_url
            self.credentials = credentials
            self._token = None
            self._expires_at = 0

        def get_token(self) -> str:
            """Get valid token, refreshing if expired."""
            if time.time() >= self._expires_at - 60:  # Refresh 60s before expiry
                self._refresh()
            return self._token

        def _refresh(self):
            response = requests.post(self.login_url, json=self.credentials)
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._expires_at = time.time() + data.get("expires_in", 3600)
            print("Token refreshed!")

        @property
        def auth_header(self) -> dict:
            return {"Authorization": f"Bearer {self.get_token()}"}


    # Usage
    tm = TokenManager(
        login_url="https://api.example.com/auth/token",
        credentials={"username": os.getenv("USERNAME"), "password": os.getenv("PASSWORD")}
    )

    # Token auto-refreshes when expired
    response = requests.get("https://api.example.com/data", headers=tm.auth_header)
    '''
    print(code)


# ─── 3. BASIC AUTH ───────────────────────────────────────────────────────────

def basic_auth_examples():
    print("\n── 3. BASIC AUTH ────────────────────────────────────────────")
    code = '''
    # Method 1: requests built-in Basic Auth
    response = requests.get(
        "https://api.example.com/data",
        auth=("username", "password")
    )

    # Method 2: Manual header
    credentials = base64.b64encode(b"username:password").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = requests.get("https://api.example.com/data", headers=headers)

    # Method 3: HTTPBasicAuth
    from requests.auth import HTTPBasicAuth
    response = requests.get(
        "https://api.example.com/data",
        auth=HTTPBasicAuth(os.getenv("API_USER"), os.getenv("API_PASS"))
    )

    # Real example: GitHub API with Basic Auth
    username = os.getenv("GITHUB_USERNAME")
    token    = os.getenv("GITHUB_TOKEN")     # GitHub Personal Access Token
    response = requests.get(
        "https://api.github.com/repos/python/cpython",
        auth=(username, token)
    )
    data = response.json()
    print(f"Stars: {data['stargazers_count']:,}")
    '''
    print(code)


# ─── 4. OAUTH 2.0 ────────────────────────────────────────────────────────────

def oauth2_guide():
    print("\n── 4. OAUTH 2.0 ─────────────────────────────────────────────")

    print("""
  OAUTH 2.0 FLOWS:
  ─────────────────────────────────────────────────────────────────
  1. Authorization Code  → For apps where USER grants permission
     Used by: Google Drive, GitHub, Slack
     Flow: User → Auth Page → Code → Exchange for Token

  2. Client Credentials  → Machine-to-machine (NO user involved)
     Used by: Server APIs, internal services
     Flow: Client ID + Secret → Token → API

  3. Resource Owner Password  → Direct username/password
     (Deprecated, avoid if possible)

  ─────────────────────────────────────────────────────────────────
  FOR RPA BOTS: Use Client Credentials (most common for automation)
  ─────────────────────────────────────────────────────────────────
    """)

    code = '''
    # ── Client Credentials Flow (for automation/bots)
    import os
    import requests

    def get_oauth_token(token_url: str, client_id: str, client_secret: str,
                        scope: str = "") -> dict:
        """Get OAuth 2.0 token using client credentials."""
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scope:
            data["scope"] = scope

        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
        # Returns: {"access_token": "...", "token_type": "Bearer", "expires_in": 3600}

    # Salesforce example
    token_data = get_oauth_token(
        token_url="https://login.salesforce.com/services/oauth2/token",
        client_id=os.getenv("SF_CLIENT_ID"),
        client_secret=os.getenv("SF_CLIENT_SECRET"),
    )
    access_token = token_data["access_token"]

    # Use token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://yourinstance.salesforce.com/services/data/v57.0/query",
        headers=headers,
        params={"q": "SELECT Id, Name FROM Account LIMIT 10"}
    )

    # ── Microsoft / Azure AD example
    def get_azure_token(tenant_id, client_id, client_secret, scope):
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        return get_oauth_token(url, client_id, client_secret, scope)

    token = get_azure_token(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        scope="https://graph.microsoft.com/.default"
    )
    '''
    print(code)


# ─── 5. SESSION/COOKIE AUTH ──────────────────────────────────────────────────

def session_auth_examples():
    print("\n── 5. SESSION / COOKIE AUTH ─────────────────────────────────")
    code = '''
    # For APIs that use login/session cookies (like web apps with APIs)
    session = requests.Session()

    # 1. Login (creates session cookie)
    login_response = session.post(
        "https://app.example.com/api/login",
        json={
            "username": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD")
        }
    )
    login_response.raise_for_status()
    print(f"Logged in: {login_response.json().get('message')}")

    # 2. Session automatically includes cookies on all subsequent requests
    data = session.get("https://app.example.com/api/dashboard").json()
    result = session.post("https://app.example.com/api/export",
                          json={"format": "csv"}).json()

    # 3. Save session for reuse
    import pickle
    with open("session.pkl", "wb") as f:
        pickle.dump(session.cookies, f)

    # Load saved session
    new_session = requests.Session()
    with open("session.pkl", "rb") as f:
        new_session.cookies.update(pickle.load(f))

    # Verify session is still valid
    r = new_session.get("https://app.example.com/api/me")
    if r.status_code == 401:
        print("Session expired, need to re-login")
    else:
        print(f"Session valid: {r.json()['username']}")
    '''
    print(code)


# ─── 6. HMAC SIGNATURE AUTH (AWS-style) ──────────────────────────────────────

def hmac_auth_example():
    print("\n── 6. HMAC SIGNATURE AUTH ───────────────────────────────────")

    class HMACAuth(requests.auth.AuthBase):
        """
        Custom requests auth for HMAC-signed requests.
        Example: AWS, Stripe webhook verification.
        """
        def __init__(self, access_key: str, secret_key: str):
            self.access_key = access_key
            self.secret_key = secret_key.encode()

        def __call__(self, r):
            timestamp = str(int(time.time()))
            body = r.body or ""
            if isinstance(body, bytes):
                body = body.decode()

            # Build message to sign: method + url + timestamp + body
            message = f"{r.method}\n{r.url}\n{timestamp}\n{body}"

            # HMAC-SHA256 signature
            signature = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            # Add auth headers
            r.headers.update({
                "X-Access-Key": self.access_key,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
            })
            return r

    # Usage
    code = '''
    auth = HMACAuth(
        access_key=os.getenv("ACCESS_KEY"),
        secret_key=os.getenv("SECRET_KEY")
    )

    response = requests.post(
        "https://api.example.com/data",
        json={"records": [...]},
        auth=auth  # Automatically signs the request
    )
    '''
    print(code)


# ─── 7. STORING CREDENTIALS SECURELY ─────────────────────────────────────────

def secure_credentials():
    print("\n── 7. SECURE CREDENTIAL STORAGE ────────────────────────────")
    code = '''
    # ── Option 1: .env file (Development)
    # .env file:
    # API_KEY=abc123
    # API_SECRET=xyz789

    from dotenv import load_dotenv
    import os
    load_dotenv()
    api_key = os.getenv("API_KEY")

    # ── Option 2: OS Keyring (Personal machines)
    import keyring  # pip install keyring
    keyring.set_password("myapp", "api_key", "secret_value")
    api_key = keyring.get_password("myapp", "api_key")

    # ── Option 3: AWS Secrets Manager (Production)
    import boto3
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret = client.get_secret_value(SecretId="prod/myapp/credentials")
    creds = json.loads(secret["SecretString"])

    # ── Option 4: HashiCorp Vault (Enterprise)
    import hvac  # pip install hvac
    vault = hvac.Client(url="https://vault.company.com", token=os.getenv("VAULT_TOKEN"))
    secret = vault.secrets.kv.read_secret_version(path="myapp/creds")
    api_key = secret["data"]["data"]["api_key"]

    # ── NEVER DO THESE:
    # api_key = "abc123"                     # Hardcoded secret
    # git commit -m "add api key"            # Committed secret
    # print(f"Using key: {api_key}")         # Logged secret
    '''
    print(code)


# ─── DEMO ─────────────────────────────────────────────────────────────────────

def run_demo():
    print("\n" + "═" * 55)
    print("  AUTHENTICATION DEMO (using public test API)")
    print("═" * 55)

    # Demo with Basic Auth using httpbin.org
    print("\n► Basic Auth Demo:")
    response = requests.get(
        "https://httpbin.org/basic-auth/user/pass",
        auth=("user", "pass")
    )
    print(f"  Status: {response.status_code}")
    print(f"  Result: {response.json()}")

    # Demo checking response headers for rate limits
    print("\n► Rate Limit Headers:")
    response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
    rate_headers = {k: v for k, v in response.headers.items()
                    if "rate" in k.lower() or "limit" in k.lower()}
    if rate_headers:
        print(f"  {rate_headers}")
    else:
        print("  (No rate limit headers on this test API)")

    print("\n► HTTP Response Headers:")
    for key in ["Content-Type", "Server", "Cache-Control"]:
        print(f"  {key}: {response.headers.get(key, 'N/A')}")


if __name__ == "__main__":
    run_demo()

    print("\n" + "─" * 55)
    print("  AUTHENTICATION SUMMARY:")
    print("  ► API Key    → X-API-Key or ?api_key=")
    print("  ► Bearer     → Authorization: Bearer <token>")
    print("  ► Basic Auth → Authorization: Basic base64(u:p)")
    print("  ► OAuth 2.0  → Client Credentials for bots")
    print("  ► Session    → Login once, reuse cookies")
    print("  ► NEVER hardcode secrets — use .env or vault")
    print("─" * 55)
    print("  NEXT: python module_4_apis/04_api_automation_flows.py")

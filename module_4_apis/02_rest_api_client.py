"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 4 — LESSON 2: BUILDING A REST API CLIENT             ║
╚══════════════════════════════════════════════════════════════════╝

A REUSABLE API CLIENT that you can use for any REST API:
  ► Handles authentication
  ► Automatic retries with backoff
  ► Response parsing
  ► Error handling
  ► Rate limiting
  ► Logging
"""

import time
import json
import logging
from typing import Any, Optional
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# ─── BASE API CLIENT ──────────────────────────────────────────────────────────

class APIClient:
    """
    Generic REST API client.
    Subclass this for specific APIs (GitHub, Jira, Salesforce, etc.)

    Usage:
        class GitHubClient(APIClient):
            BASE_URL = "https://api.github.com"

            def get_repos(self, username):
                return self.get(f"/users/{username}/repos")
    """

    BASE_URL = ""
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        token: str = "",
        username: str = "",
        password: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
    ):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = self._create_session(max_retries)

        # Set authentication
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            self.session.headers["X-API-Key"] = api_key
        elif username and password:
            self.session.auth = (username, password)

        # Default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create session with automatic retry on transient errors."""
        session = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=1.0,
            status_forcelist={500, 502, 503, 504},
            allowed_methods={"GET", "POST", "PUT", "PATCH", "DELETE"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        data: Any = None,
        headers: dict = None,
        **kwargs
    ) -> requests.Response:
        """Base request method with logging and error handling."""
        url = self._url(endpoint)
        logger.debug(f"  {method} {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )

            logger.debug(f"  → {response.status_code} ({response.elapsed.total_seconds():.2f}s)")

            response.raise_for_status()
            return response

        except requests.Timeout:
            raise APIError(f"Timeout after {self.timeout}s: {method} {url}")
        except requests.ConnectionError as e:
            raise APIError(f"Connection failed: {e}")
        except requests.HTTPError as e:
            status = e.response.status_code
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text
            raise APIHTTPError(status, body, url=url) from e

    # ── Convenience methods
    def get(self, endpoint: str, params: dict = None, **kwargs) -> Any:
        r = self._request("GET", endpoint, params=params, **kwargs)
        return r.json() if r.content else None

    def post(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        r = self._request("POST", endpoint, data=data, **kwargs)
        return r.json() if r.content else None

    def put(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        r = self._request("PUT", endpoint, data=data, **kwargs)
        return r.json() if r.content else None

    def patch(self, endpoint: str, data: Any = None, **kwargs) -> Any:
        r = self._request("PATCH", endpoint, data=data, **kwargs)
        return r.json() if r.content else None

    def delete(self, endpoint: str, **kwargs) -> bool:
        self._request("DELETE", endpoint, **kwargs)
        return True

    def download(self, endpoint: str, save_path: str) -> str:
        """Download a file from an API endpoint."""
        r = self._request("GET", endpoint, stream=True)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return save_path


# ─── CUSTOM EXCEPTIONS ────────────────────────────────────────────────────────

class APIError(Exception):
    """Base API error."""
    pass


class APIHTTPError(APIError):
    """HTTP error with status code and response body."""
    def __init__(self, status_code: int, body: Any, url: str = ""):
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(f"HTTP {status_code}: {body}")

    @property
    def is_not_found(self) -> bool:
        return self.status_code == 404

    @property
    def is_unauthorized(self) -> bool:
        return self.status_code == 401

    @property
    def is_rate_limited(self) -> bool:
        return self.status_code == 429

    @property
    def is_server_error(self) -> bool:
        return self.status_code >= 500


# ─── PAGINATED API CLIENT ────────────────────────────────────────────────────

class PaginatedAPIClient(APIClient):
    """API client with built-in pagination support."""

    def get_all(
        self,
        endpoint: str,
        params: dict = None,
        page_param: str = "page",
        per_page_param: str = "per_page",
        per_page: int = 100,
        max_pages: int = 100,
    ) -> list:
        """
        Fetch all pages of a paginated endpoint.
        Returns combined list of all results.
        """
        params = params or {}
        params[per_page_param] = per_page
        all_items = []

        for page in range(1, max_pages + 1):
            params[page_param] = page
            response = self.get(endpoint, params=params.copy())

            # Handle different response shapes
            if isinstance(response, list):
                items = response
            elif isinstance(response, dict):
                items = (response.get("items") or
                         response.get("data") or
                         response.get("results") or
                         response.get("records") or [])
            else:
                break

            if not items:
                break  # No more pages

            all_items.extend(items)
            logger.info(f"  Page {page}: +{len(items)} items (total: {len(all_items)})")

            if len(items) < per_page:
                break  # Last page (less than full page returned)

        return all_items


# ─── RATE-LIMITED API CLIENT ─────────────────────────────────────────────────

class RateLimitedAPIClient(APIClient):
    """
    API client that respects rate limits automatically.
    Reads Retry-After header and waits accordingly.
    """

    def __init__(self, *args, requests_per_second: float = 2.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_second = requests_per_second
        self._min_interval = 1.0 / requests_per_second
        self._last_request_time = 0.0

    def _request(self, method, endpoint, **kwargs):
        # Throttle requests
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        try:
            response = super()._request(method, endpoint, **kwargs)
            self._last_request_time = time.time()
            return response

        except APIHTTPError as e:
            if e.is_rate_limited:
                # Read Retry-After header
                retry_after = int(
                    self.session.last_response.headers.get("Retry-After", 60)
                )
                logger.warning(f"  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                return super()._request(method, endpoint, **kwargs)  # Retry
            raise


# ─── CONCRETE API IMPLEMENTATIONS ────────────────────────────────────────────

class JSONPlaceholderClient(PaginatedAPIClient):
    """Client for JSONPlaceholder test API."""

    BASE_URL = "https://jsonplaceholder.typicode.com"

    def get_posts(self, user_id: int = None, limit: int = None) -> list:
        params = {}
        if user_id:
            params["userId"] = user_id
        if limit:
            params["_limit"] = limit
        return self.get("/posts", params=params)

    def get_post(self, post_id: int) -> dict:
        return self.get(f"/posts/{post_id}")

    def create_post(self, title: str, body: str, user_id: int) -> dict:
        return self.post("/posts", data={
            "title": title,
            "body": body,
            "userId": user_id,
        })

    def update_post(self, post_id: int, **fields) -> dict:
        return self.patch(f"/posts/{post_id}", data=fields)

    def delete_post(self, post_id: int) -> bool:
        return self.delete(f"/posts/{post_id}")

    def get_user(self, user_id: int) -> dict:
        return self.get(f"/users/{user_id}")

    def get_user_comments(self, user_id: int) -> list:
        """Get all comments by fetching posts then their comments."""
        posts = self.get_posts(user_id=user_id)
        comments = []
        for post in posts:
            post_comments = self.get(f"/posts/{post['id']}/comments")
            comments.extend(post_comments)
        return comments


# ─── DEMO ─────────────────────────────────────────────────────────────────────

def run_demo():
    print("\n" + "═" * 55)
    print("  REST API CLIENT DEMO")
    print("═" * 55)

    client = JSONPlaceholderClient()

    # GET a post
    post = client.get_post(1)
    print(f"\n► Get post #1:")
    print(f"  Title: {post['title']}")
    print(f"  Body : {post['body'][:50]}...")

    # GET posts for a user
    user_posts = client.get_posts(user_id=1, limit=3)
    print(f"\n► User 1 posts ({len(user_posts)} shown):")
    for p in user_posts:
        print(f"  [{p['id']}] {p['title'][:40]}")

    # CREATE a post
    new_post = client.create_post(
        title="RPA Automation Tips",
        body="Python makes RPA easy!",
        user_id=1
    )
    print(f"\n► Created post ID: {new_post['id']}")

    # UPDATE post
    updated = client.update_post(1, title="Updated via API")
    print(f"► Updated title: {updated['title']}")

    # Error handling
    print(f"\n► Error handling:")
    try:
        client.get_post(99999)
    except APIHTTPError as e:
        print(f"  Got {e.status_code} error as expected")
        print(f"  is_not_found: {e.is_not_found}")

    # Get user info
    user = client.get_user(1)
    print(f"\n► User 1: {user['name']} <{user['email']}>")
    print(f"  Company: {user['company']['name']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run_demo()
    print("\n  NEXT: python module_4_apis/03_authentication.py")

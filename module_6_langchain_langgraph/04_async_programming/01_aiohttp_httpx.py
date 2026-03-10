"""
04_async_programming/01_aiohttp_httpx.py
==========================================
Async Programming: aiohttp & httpx

CONCEPTS COVERED:
  - async/await fundamentals
  - aiohttp: async HTTP client/server
  - httpx: modern sync+async HTTP client
  - Concurrent LLM requests with asyncio.gather()
  - Connection pooling and session reuse
  - Timeout and retry patterns (async)
  - Rate limiting with asyncio.Semaphore
  - Streaming async responses

Why async matters for AI agents:
  - LLM calls take 1-30 seconds each
  - With sync code: 10 calls = 10-300 seconds sequentially
  - With async: 10 calls = time of the SLOWEST one (parallel)
"""

import asyncio
import time
import json
from typing import AsyncIterator
import aiohttp
import httpx
from loguru import logger


# ── 1. aiohttp basics ────────────────────────────────────────────────────────
async def aiohttp_basic_get():
    """Single GET request with aiohttp."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://httpbin.org/json") as response:
            print(f"Status: {response.status}")
            data = await response.json()
            print(f"Data: {data}")
    # Session closes automatically when exiting the context manager


# ── 2. aiohttp with custom headers and timeout ───────────────────────────────
async def aiohttp_with_config():
    """Configure session headers, timeout, and connection limits."""

    # Shared headers (e.g., auth token)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-token",
    }

    # Timeout configuration
    timeout = aiohttp.ClientTimeout(
        total=30,        # total request time
        connect=5,       # time to establish connection
        sock_read=25,    # time to read response
    )

    # Connection pool limits
    connector = aiohttp.TCPConnector(
        limit=10,         # max total connections
        limit_per_host=5, # max connections per host
    )

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
        connector=connector,
    ) as session:
        async with session.post(
            "https://httpbin.org/post",
            json={"prompt": "What is LangGraph?"},
        ) as resp:
            print(f"POST status: {resp.status}")


# ── 3. httpx — cleaner API, works sync AND async ─────────────────────────────
def httpx_sync():
    """httpx works synchronously too — great for scripts."""
    with httpx.Client(timeout=30) as client:
        response = client.get("https://httpbin.org/get")
        print(f"httpx sync: {response.status_code}")


async def httpx_async():
    """httpx async client."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://httpbin.org/get")
        print(f"httpx async: {response.status_code}")
        return response.json()


# ── 4. Concurrent requests — the key power of async ───────────────────────────
async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch a single URL and return JSON."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return {"url": url, "status": resp.status, "data": await resp.json()}
    except Exception as e:
        return {"url": url, "error": str(e)}


async def fetch_many_urls_concurrent():
    """
    Fetch multiple URLs IN PARALLEL — not one at a time!
    asyncio.gather() runs all coroutines concurrently.
    """
    urls = [
        "https://httpbin.org/json",
        "https://httpbin.org/get",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
    ]

    start = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        # All requests fire at the same time!
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.perf_counter() - start
    print(f"\n=== Concurrent Fetch: {len(urls)} URLs in {elapsed:.2f}s ===")

    for result in results:
        if isinstance(result, Exception):
            print(f"  ERROR: {result}")
        else:
            print(f"  {result['url']}: {result['status']}")


# ── 5. Rate limiting with asyncio.Semaphore ──────────────────────────────────
async def rate_limited_llm_calls(prompts: list[str], max_concurrent: int = 3):
    """
    Limit concurrent LLM API calls to avoid rate limit errors.
    Semaphore allows at most `max_concurrent` calls at once.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def call_with_limit(session: aiohttp.ClientSession, prompt: str) -> str:
        async with semaphore:  # blocks if max_concurrent already running
            logger.debug(f"Processing: {prompt[:30]}...")
            await asyncio.sleep(0.1)  # simulate API call
            return f"Response to: {prompt}"

    async with aiohttp.ClientSession() as session:
        tasks = [call_with_limit(session, p) for p in prompts]
        return await asyncio.gather(*tasks)


# ── 6. Streaming HTTP responses (for LLM streaming) ──────────────────────────
async def stream_llm_response(url: str, payload: dict) -> AsyncIterator[str]:
    """
    Stream a response line-by-line (Server-Sent Events / streaming APIs).
    This is the pattern for OpenAI/Anthropic streaming endpoints.
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            async for line in response.content:
                decoded = line.decode("utf-8").strip()
                if decoded.startswith("data: "):
                    data = decoded[6:]  # strip "data: " prefix
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass


# ── 7. httpx with retry (combining with tenacity) ────────────────────────────
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AsyncLLMClient:
    """
    Production async HTTP client for LLM APIs.
    - Reuses connections (no per-call session creation)
    - Retries on transient failures
    - Rate limiting via semaphore
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        max_concurrent: int = 5,
        timeout: float = 60.0,
    ):
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=30),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    )
    async def complete(self, messages: list[dict], **kwargs) -> dict:
        """Make a chat completion request with retry."""
        async with self.semaphore:
            response = await self._client.post(
                "/chat/completions",
                json={"messages": messages, **kwargs},
            )
            response.raise_for_status()
            return response.json()

    async def batch_complete(self, batch: list[list[dict]]) -> list[dict]:
        """Process a batch of message lists concurrently."""
        tasks = [self.complete(messages) for messages in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)


# ── 8. Async context managers pattern ────────────────────────────────────────
class AsyncAgent:
    """Agent that manages its own async resources."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        logger.info("Agent session opened")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()
        logger.info("Agent session closed")

    async def process(self, query: str) -> str:
        """Process a query (uses the shared session)."""
        await asyncio.sleep(0.1)  # simulate work
        return f"Processed: {query}"


# ── Demo ─────────────────────────────────────────────────────────────────────
async def main():
    print("=== Async Programming Demo ===\n")

    # httpx sync (for comparison)
    print("1. httpx sync:")
    httpx_sync()

    # Rate-limited batch processing
    print("\n2. Rate-limited concurrent processing:")
    prompts = [f"Explain concept {i}" for i in range(8)]
    start = time.perf_counter()
    results = await rate_limited_llm_calls(prompts, max_concurrent=3)
    elapsed = time.perf_counter() - start
    print(f"   {len(results)} tasks done in {elapsed:.2f}s (max 3 concurrent)")

    # Async context manager
    print("\n3. Async agent context manager:")
    async with AsyncAgent(api_key="demo-key") as agent:
        response = await agent.process("What is LangGraph?")
        print(f"   Result: {response}")

    print("\n✓ Async patterns summary:")
    print("  asyncio.gather()     → run coroutines concurrently")
    print("  asyncio.Semaphore()  → limit concurrent operations")
    print("  async with ...       → manage resources safely")
    print("  async for ...        → iterate over async streams")


if __name__ == "__main__":
    asyncio.run(main())

"""
08_redis_caching/01_redis_basics.py
=====================================
Redis: Caching & Sessions for AI Agents

CONCEPTS COVERED:
  - Connecting to Redis
  - Strings: basic key-value with TTL
  - Hashes: storing structured data
  - Lists: conversation queues
  - Sets: tracking unique items
  - LLM response caching (save money!)
  - Session management
  - Rate limiting
  - Pub/Sub for agent communication
  - Async Redis

WHY REDIS FOR AI AGENTS?
  - Cache expensive LLM responses (avoid re-calling API)
  - Rate limiting (enforce per-user API quotas)
  - Session storage (fast access to conversation state)
  - Real-time pub/sub between agents
  - Job queues for async agent tasks
"""

import asyncio
import hashlib
import json
import time
from datetime import timedelta
from typing import Optional
import redis
import redis.asyncio as aioredis
from loguru import logger


# ── 1. Connecting to Redis ─────────────────────────────────────────────────────
def get_redis_client() -> redis.Redis:
    """Get a sync Redis client."""
    return redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,  # return str instead of bytes
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
    )

# Or from URL:
# r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

def get_async_redis_client() -> aioredis.Redis:
    """Get an async Redis client."""
    return aioredis.Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True,
    )


# ── 2. Check if Redis is available ────────────────────────────────────────────
def is_redis_available() -> bool:
    try:
        r = get_redis_client()
        r.ping()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


REDIS_AVAILABLE = is_redis_available()
print(f"=== Redis Demo ===")
print(f"Redis available: {REDIS_AVAILABLE}")


# ── 3. String operations: basic key-value ─────────────────────────────────────
class SimpleCache:
    """Basic cache with TTL using Redis strings."""

    def __init__(self, client: redis.Redis, prefix: str = "cache"):
        self.r = client
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        """Store a value with expiration."""
        self.r.setex(self._key(key), ttl_seconds, value)

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value (None if not found or expired)."""
        return self.r.get(self._key(key))

    def delete(self, key: str) -> None:
        self.r.delete(self._key(key))

    def exists(self, key: str) -> bool:
        return bool(self.r.exists(self._key(key)))

    def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds (-2 if key doesn't exist)."""
        return self.r.ttl(self._key(key))


if REDIS_AVAILABLE:
    r = get_redis_client()
    cache = SimpleCache(r, prefix="demo")

    cache.set("greeting", "Hello from Redis!", ttl_seconds=60)
    value = cache.get("greeting")
    ttl   = cache.ttl("greeting")
    print(f"Cached value: {value!r} (TTL: {ttl}s)")


# ── 4. LLM Response Cache ─────────────────────────────────────────────────────
class LLMResponseCache:
    """
    Cache LLM responses to avoid redundant API calls.

    Why this matters:
      - GPT-4o: ~$0.005/1k input tokens
      - 1000 identical queries = $5.00 wasted without caching
      - With cache: $0.005 for the first call, $0 for all others
    """

    def __init__(self, client: redis.Redis, default_ttl: int = 86400):
        self.r = client
        self.default_ttl = default_ttl  # 24 hours
        self.prefix = "llm_cache"
        self.hits = 0
        self.misses = 0

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        """Create a deterministic cache key from request parameters."""
        cache_input = json.dumps({
            "prompt":      prompt,
            "model":       model,
            "temperature": temperature,
        }, sort_keys=True)
        hash_val = hashlib.sha256(cache_input.encode()).hexdigest()
        return f"{self.prefix}:{hash_val}"

    def get(self, prompt: str, model: str, temperature: float = 0.0) -> Optional[dict]:
        """Try to get a cached response."""
        key = self._make_key(prompt, model, temperature)
        cached = self.r.get(key)
        if cached:
            self.hits += 1
            logger.debug(f"Cache HIT for prompt: {prompt[:40]}...")
            data = json.loads(cached)
            data["from_cache"] = True
            return data
        self.misses += 1
        logger.debug(f"Cache MISS for prompt: {prompt[:40]}...")
        return None

    def set(
        self,
        prompt: str,
        model: str,
        response: str,
        token_count: int = 0,
        temperature: float = 0.0,
        ttl: int = None,
    ) -> None:
        """Cache a response."""
        # Only cache deterministic responses (temperature=0)
        if temperature > 0:
            logger.debug("Skipping cache: temperature > 0 (non-deterministic)")
            return

        key = self._make_key(prompt, model, temperature)
        data = {
            "response":    response,
            "model":       model,
            "token_count": token_count,
            "cached_at":   time.time(),
            "from_cache":  False,
        }
        self.r.setex(key, ttl or self.default_ttl, json.dumps(data))

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


if REDIS_AVAILABLE:
    print("\n=== LLM Cache Demo ===")
    llm_cache = LLMResponseCache(r)

    prompt = "What is LangGraph?"
    model  = "gpt-4o-mini"

    # First call: cache miss
    result = llm_cache.get(prompt, model)
    print(f"First call (miss): {result}")

    # Store response
    llm_cache.set(prompt, model, "LangGraph builds stateful AI agent graphs.", token_count=42)

    # Second call: cache hit!
    result = llm_cache.get(prompt, model)
    print(f"Second call (hit): {result}")
    print(f"Hit rate: {llm_cache.hit_rate:.0%}")


# ── 5. Redis Hashes: session storage ──────────────────────────────────────────
class SessionStore:
    """Store user sessions as Redis hashes."""

    def __init__(self, client: redis.Redis, ttl: int = 3600):
        self.r = client
        self.ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def create_session(self, session_id: str, user_id: str, data: dict = None) -> None:
        key = self._key(session_id)
        self.r.hset(key, mapping={
            "user_id":    user_id,
            "created_at": str(time.time()),
            "turn_count": "0",
            **(data or {}),
        })
        self.r.expire(key, self.ttl)  # set TTL

    def get_session(self, session_id: str) -> Optional[dict]:
        key = self._key(session_id)
        data = self.r.hgetall(key)
        return data if data else None

    def update_field(self, session_id: str, field: str, value: str) -> None:
        key = self._key(session_id)
        self.r.hset(key, field, value)
        self.r.expire(key, self.ttl)  # refresh TTL on activity

    def increment_turns(self, session_id: str) -> int:
        key = self._key(session_id)
        return self.r.hincrby(key, "turn_count", 1)

    def delete_session(self, session_id: str) -> None:
        self.r.delete(self._key(session_id))


if REDIS_AVAILABLE:
    print("\n=== Session Store Demo ===")
    sessions = SessionStore(r, ttl=3600)

    sessions.create_session("sess_001", user_id="user_42", data={"name": "Alice"})
    sess = sessions.get_session("sess_001")
    print(f"Session: {sess}")

    turn = sessions.increment_turns("sess_001")
    print(f"After increment: turn_count = {turn}")


# ── 6. Rate Limiter ───────────────────────────────────────────────────────────
class RateLimiter:
    """
    Sliding window rate limiter.
    Limits calls per time window (e.g., 10 API calls per minute).
    """

    def __init__(self, client: redis.Redis, limit: int, window_seconds: int):
        self.r = client
        self.limit = limit
        self.window = window_seconds

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if the identifier (user ID, IP, etc.) is within rate limit.
        Returns (allowed: bool, remaining: int).
        """
        key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - self.window

        pipe = self.r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # remove old entries
        pipe.zadd(key, {str(now): now})               # add current request
        pipe.zcard(key)                               # count requests in window
        pipe.expire(key, self.window)                 # set expiry
        results = pipe.execute()

        count = results[2]
        allowed = count <= self.limit
        remaining = max(0, self.limit - count)

        return allowed, remaining


if REDIS_AVAILABLE:
    print("\n=== Rate Limiter Demo ===")
    limiter = RateLimiter(r, limit=5, window_seconds=60)

    user = "user_42"
    for i in range(7):
        allowed, remaining = limiter.is_allowed(user)
        status = "✓" if allowed else "✗ BLOCKED"
        print(f"  Call {i+1}: {status} (remaining: {remaining})")


# ── 7. Async Redis ────────────────────────────────────────────────────────────
async def async_redis_demo():
    """Using Redis in async agent code."""
    print("\n=== Async Redis Demo ===")

    if not REDIS_AVAILABLE:
        print("Redis not available")
        return

    async_client = aioredis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

    try:
        # Async set/get
        await async_client.setex("async_key", 60, "async_value")
        value = await async_client.get("async_key")
        print(f"Async value: {value}")

        # Async hash
        await async_client.hset("async_session", mapping={"user": "Alice", "turn": "1"})
        session = await async_client.hgetall("async_session")
        print(f"Async session: {session}")

        # Pipeline (batch operations)
        async with async_client.pipeline() as pipe:
            pipe.set("batch_1", "value_1")
            pipe.set("batch_2", "value_2")
            pipe.get("batch_1")
            results = await pipe.execute()
        print(f"Pipeline results: {results}")

    finally:
        await async_client.aclose()


asyncio.run(async_redis_demo())


# ── 8. Pub/Sub for agent communication ────────────────────────────────────────
PUBSUB_EXAMPLE = '''
# Agent A publishes results
async def agent_a_publish():
    client = aioredis.Redis.from_url("redis://localhost:6379")
    await client.publish("agent_results", json.dumps({
        "agent": "researcher",
        "result": "LangGraph is...",
        "status": "done",
    }))

# Agent B subscribes and reacts
async def agent_b_subscribe():
    client = aioredis.Redis.from_url("redis://localhost:6379")
    pubsub = client.pubsub()
    await pubsub.subscribe("agent_results")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            print(f"Agent B received from {data['agent']}: {data['result']}")
            break
'''
print("\n=== Pub/Sub Pattern (code structure) ===")
print("Publisher:  await client.publish(channel, message)")
print("Subscriber: pubsub = client.pubsub(); await pubsub.subscribe(channel)")

print("\n✓ Redis key use cases for AI agents:")
print("  LLM caching      → save API costs (temperature=0 responses)")
print("  Session storage  → fast access to conversation state")
print("  Rate limiting    → enforce per-user quotas")
print("  Job queues       → async agent task queues")
print("  Pub/Sub          → real-time agent-to-agent messaging")

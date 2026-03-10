"""
01_foundations/04_tenacity_retry.py
=====================================
Foundation: Resilient Retries with tenacity

CONCEPTS COVERED:
  - Why retries matter for LLM APIs (rate limits, transient errors)
  - @retry decorator: basic usage
  - Exponential backoff with jitter
  - Retry on specific exceptions
  - Before/after hooks for logging
  - Async retry support
  - Stop conditions (max attempts, max time)
  - Custom retry predicates
"""

import random
import time
import asyncio
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random_exponential,   # exponential + jitter (best for LLM APIs)
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    after_log,
    RetryError,
    TryAgain,
)
import logging

# Tenacity works with standard logging — bridge loguru to it
tenacity_logger = logging.getLogger("tenacity")


# ── 1. Basic retry — retry any exception ─────────────────────────────────────
@retry(stop=stop_after_attempt(3))
def flaky_api_call_basic():
    """Fails the first 2 times, succeeds on the 3rd."""
    if random.random() < 0.7:
        raise ConnectionError("Transient network error")
    return "success"


# ── 2. Exponential backoff — the standard for LLM APIs ───────────────────────
# wait_random_exponential adds jitter to prevent thundering herd:
#   attempt 1: wait 1–2s
#   attempt 2: wait 2–4s
#   attempt 3: wait 4–8s
#   ... up to multiplier * max

@retry(
    stop=stop_after_attempt(6),
    wait=wait_random_exponential(min=1, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(tenacity_logger, logging.WARNING),
)
def call_openai_api(prompt: str) -> str:
    """Simulates an OpenAI API call with rate-limit resilience."""
    if random.random() < 0.5:
        raise ConnectionError("Rate limit exceeded (429)")
    return f"GPT response: {prompt}"


# ── 3. Stop after time limit (useful for latency-sensitive agents) ─────────────
@retry(
    stop=stop_after_delay(30),      # give up after 30 seconds total
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type(TimeoutError),
)
def time_sensitive_operation():
    """Won't retry past 30 seconds total."""
    raise TimeoutError("Upstream timeout")


# ── 4. Retry on bad results (not just exceptions) ─────────────────────────────
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=1, max=8),
    retry=retry_if_result(lambda result: result is None),  # retry if None returned
)
def get_llm_structured_output(prompt: str) -> dict | None:
    """Retry if LLM returns None (failed to parse structured output)."""
    # Simulate LLM sometimes failing to return valid JSON
    if random.random() < 0.6:
        return None  # triggers retry
    return {"answer": "42", "confidence": 0.95}


# ── 5. Multiple stop/wait conditions combined ─────────────────────────────────
@retry(
    stop=(stop_after_attempt(10) | stop_after_delay(60)),  # whichever comes first
    wait=wait_random_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry {retry_state.attempt_number} — "
        f"waiting {retry_state.next_action.sleep:.1f}s..."
    ),
)
def production_llm_call(prompt: str) -> str:
    """Production-grade LLM call: up to 10 retries OR 60s total."""
    if random.random() < 0.3:
        raise ConnectionError("Network blip")
    return f"Response: {prompt}"


# ── 6. Async retry — for async LLM clients ───────────────────────────────────
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(min=1, max=20),
    retry=retry_if_exception_type(Exception),
)
async def async_llm_call(prompt: str) -> str:
    """Async retry works identically to sync — just add async/await."""
    await asyncio.sleep(0.1)  # simulate async API call
    if random.random() < 0.5:
        raise ConnectionError("Async rate limit")
    return f"Async response: {prompt}"


# ── 7. Manual TryAgain — retry from inside the function ───────────────────────
@retry(stop=stop_after_attempt(5))
def validate_llm_output(prompt: str) -> dict:
    """Use TryAgain to trigger a retry based on business logic."""
    response = f'{{"result": "{prompt}", "valid": {str(random.random() > 0.5).lower()}}}'
    import json
    data = json.loads(response)

    if not data.get("valid"):
        logger.warning("LLM output failed validation — retrying")
        raise TryAgain  # triggers tenacity retry

    return data


# ── 8. Decorator factory — reusable retry configs ─────────────────────────────
def llm_retry(max_attempts: int = 6, max_wait: int = 60):
    """Factory that returns a pre-configured @retry decorator."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(min=1, max=max_wait),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda rs: logger.warning(
            f"[LLM] Retry {rs.attempt_number}/{max_attempts} "
            f"— sleeping {rs.next_action.sleep:.1f}s"
        ),
    )

@llm_retry(max_attempts=4, max_wait=30)
def call_anthropic_claude(prompt: str) -> str:
    return f"Claude: {prompt}"


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=== Tenacity Retry Demo ===")

    # 1. Basic
    try:
        result = call_openai_api("What is LangGraph?")
        logger.success(f"OpenAI result: {result}")
    except RetryError:
        logger.error("All retries exhausted for OpenAI")

    # 2. Structured output with result-based retry
    try:
        output = get_llm_structured_output("Explain AI agents")
        logger.success(f"Structured output: {output}")
    except RetryError:
        logger.error("Failed to get structured output after retries")

    # 3. Async
    async def main():
        try:
            result = await async_llm_call("Tell me about LangChain")
            logger.success(f"Async result: {result}")
        except RetryError:
            logger.error("Async retries exhausted")

    asyncio.run(main())

    logger.success("Tenacity demo complete!")

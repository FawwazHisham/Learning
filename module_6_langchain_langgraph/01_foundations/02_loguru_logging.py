"""
01_foundations/02_loguru_logging.py
====================================
Foundation: Structured Logging with loguru

CONCEPTS COVERED:
  - Why loguru > Python's built-in logging
  - Levels, formats, sinks (console + file)
  - Structured context with bind()
  - Log rotation and retention
  - Async-safe logging
  - Decorating functions with @logger.catch
"""

import sys
import time
from loguru import logger

# ── 1. Default logger (already has a stderr sink) ─────────────────────────────
# Just import and use — zero config needed for basic usage
logger.info("Hello from loguru!")
logger.debug("This is debug")
logger.warning("Watch out!")
logger.error("Something went wrong")
logger.success("All good!")   # loguru-specific level


# ── 2. Remove default sink, add custom ones ────────────────────────────────────
logger.remove()  # remove the default stderr handler

# Console: colorized, human-readable
logger.add(
    sys.stdout,
    level="DEBUG",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# File sink: JSON for log aggregation (e.g., ELK, Datadog)
logger.add(
    "logs/agent_{time:YYYY-MM-DD}.log",
    level="INFO",
    format="{time} | {level} | {name}:{line} | {message}",
    rotation="10 MB",      # rotate when file hits 10 MB
    retention="7 days",    # delete logs older than 7 days
    compression="zip",     # compress rotated files
    serialize=True,        # write as JSON lines
)


# ── 3. Structured context with bind() ─────────────────────────────────────────
# bind() creates a child logger with extra fields attached to every log call

def process_agent_request(user_id: str, session_id: str, query: str):
    """Every log in this function automatically includes user/session context."""
    request_logger = logger.bind(user_id=user_id, session_id=session_id)

    request_logger.info(f"Processing query: {query!r}")
    # → "Processing query: ..." + user_id=abc123, session_id=sess_xyz

    try:
        # simulate work
        result = f"Answer to: {query}"
        request_logger.success(f"Query resolved in {0.42:.2f}s")
        return result
    except Exception as e:
        request_logger.error(f"Query failed: {e}")
        raise


# ── 4. @logger.catch — auto-catch and log exceptions ─────────────────────────
@logger.catch(reraise=True)
def risky_function(x: int) -> int:
    """Any exception is logged with full traceback automatically."""
    if x == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return 100 // x


# ── 5. Timing decorator pattern ───────────────────────────────────────────────
from functools import wraps
from typing import Callable, Any

def log_timing(func: Callable) -> Callable:
    """Decorator: log how long a function takes."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        logger.debug(f"→ {func.__name__} started")
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"← {func.__name__} done in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"✗ {func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper


@log_timing
def slow_llm_call(prompt: str) -> str:
    """Simulate an LLM call."""
    time.sleep(0.1)  # simulate latency
    return f"Response to: {prompt}"


# ── 6. Log levels reference ───────────────────────────────────────────────────
"""
TRACE    (5)  — most verbose, internal details
DEBUG   (10)  — development diagnostics
INFO    (20)  — normal operation events
SUCCESS (25)  — loguru-specific: positive outcomes
WARNING (30)  — something unexpected but recoverable
ERROR   (40)  — a failure that needs attention
CRITICAL(50)  — system-level failure, may need to stop
"""


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=== Loguru Demo ===")

    # Context binding
    result = process_agent_request("user_42", "sess_abc", "What is LangGraph?")
    logger.info(f"Result: {result}")

    # Timing
    response = slow_llm_call("Tell me about AI agents")
    logger.info(f"LLM response: {response}")

    # Exception catching
    try:
        risky_function(0)
    except ZeroDivisionError:
        logger.warning("Caught expected error — continuing")

    logger.success("Loguru demo complete!")

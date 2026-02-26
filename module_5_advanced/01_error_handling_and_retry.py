"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 5 — LESSON 1: PRODUCTION ERROR HANDLING & RETRY      ║
╚══════════════════════════════════════════════════════════════════╝

WHY ERROR HANDLING IS CRITICAL FOR RPA:
  Bots run unattended. When they crash at 2am, nobody fixes them.
  Good error handling means:
  ► Bot recovers automatically from transient errors
  ► Important failures send alerts to humans
  ► Every failure is logged with enough context to debug
  ► Bot never gets stuck or corrupts data
"""

import time
import logging
import functools
import traceback
from typing import Callable, Any, TypeVar
from tenacity import (  # pip install tenacity
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    RetryError,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


# ─── 1. TENACITY — Production Retry Library ───────────────────────────────────

def tenacity_guide():
    print("── 1. TENACITY RETRY LIBRARY ────────────────────────────────")
    code = '''
    from tenacity import (
        retry, stop_after_attempt, wait_exponential,
        wait_random_exponential, retry_if_exception_type,
        before_sleep_log, RetryError
    )
    import logging
    logger = logging.getLogger(__name__)

    # ── Basic retry (3 attempts)
    @retry(stop=stop_after_attempt(3))
    def fetch_data():
        return requests.get("https://api.example.com/data").json()

    # ── Exponential backoff (1s, 2s, 4s, 8s...)
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        reraise=True  # Re-raise the last exception instead of RetryError
    )
    def call_api(endpoint):
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        return response.json()

    # ── Random jitter (prevents thundering herd)
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(multiplier=1, max=60),  # Adds randomness
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def flaky_api_call():
        ...

    # ── Retry only on specific exceptions
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2),
    )
    def network_call():
        ...  # Only retries on network errors, not ValueError

    # ── Retry based on return value (e.g., retry if job still running)
    @retry(
        retry=retry_if_result(lambda result: result["status"] == "running"),
        stop=stop_after_attempt(20),
        wait=wait_exponential(multiplier=5, max=60),
    )
    def check_job_status(job_id: str) -> dict:
        return api.get(f"/jobs/{job_id}")

    # Wait until job is "completed" or "failed"
    result = check_job_status("job_123")
    if result["status"] == "completed":
        download_results(result["output_url"])
    '''
    print(code)


# ─── 2. CUSTOM RETRY DECORATOR ────────────────────────────────────────────────

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_failure: Callable = None
):
    """
    Custom retry decorator with configurable backoff.

    Usage:
        @retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"  [{func.__name__}] Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff  # Exponential backoff
                    else:
                        logger.error(
                            f"  [{func.__name__}] All {max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )

            if on_failure:
                on_failure(func.__name__, last_exception)

            raise last_exception

        return wrapper
    return decorator


# ─── 3. EXCEPTION HIERARCHY ───────────────────────────────────────────────────

class RPAError(Exception):
    """Base exception for all RPA bot errors."""
    def __init__(self, message: str, retryable: bool = False, context: dict = None):
        super().__init__(message)
        self.retryable = retryable
        self.context = context or {}


class NavigationError(RPAError):
    """Failed to navigate to a page."""
    def __init__(self, url: str, reason: str):
        super().__init__(f"Navigation failed: {url} — {reason}", retryable=True,
                        context={"url": url})


class ElementNotFoundError(RPAError):
    """Element not found on page."""
    def __init__(self, selector: str, page: str = ""):
        super().__init__(f"Element not found: {selector}", retryable=False,
                        context={"selector": selector, "page": page})


class AuthenticationError(RPAError):
    """Login/authentication failed."""
    def __init__(self, reason: str):
        super().__init__(f"Authentication failed: {reason}", retryable=False)


class DataValidationError(RPAError):
    """Input/output data failed validation."""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(f"Validation failed: {field}={value!r} — {reason}",
                        retryable=False,
                        context={"field": field, "value": value})


class RateLimitError(RPAError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(f"Rate limited — retry after {retry_after}s", retryable=True,
                        context={"retry_after": retry_after})


# ─── 4. CIRCUIT BREAKER ───────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Circuit Breaker pattern — stops calling a failing service.

    States:
      CLOSED  → Normal operation (calls pass through)
      OPEN    → Too many failures (calls are blocked)
      HALF    → Testing if service recovered (allow some calls)

    Prevents bot from hammering a broken service.
    """

    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._state = self.CLOSED
        self._last_failure_time = 0

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = self.HALF_OPEN
        return self._state

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        state = self.state

        if state == self.OPEN:
            raise RuntimeError(f"Circuit OPEN — service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self._failures = 0
        self._state = self.CLOSED

    def _on_failure(self):
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = self.OPEN
            logger.warning(f"Circuit OPENED after {self._failures} failures")


# ─── 5. GLOBAL ERROR HANDLER FOR BOTS ────────────────────────────────────────

class BotErrorHandler:
    """
    Centralized error handler for RPA bots.
    Classifies errors, decides retry strategy, sends alerts.
    """

    def __init__(self, bot_name: str, notify_on_critical: bool = True):
        self.bot_name = bot_name
        self.notify_on_critical = notify_on_critical
        self.error_counts: dict[str, int] = {}

    def handle(self, error: Exception, context: dict = None, reraise: bool = False):
        """Handle any exception — log, classify, notify."""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        error_info = {
            "bot":        self.bot_name,
            "error_type": error_type,
            "message":    str(error),
            "traceback":  traceback.format_exc(),
            "context":    context or {},
            "count":      self.error_counts[error_type],
        }

        # Classify severity
        is_retryable = isinstance(error, RPAError) and error.retryable
        is_critical   = self._is_critical(error)

        if is_critical:
            logger.critical(f"  CRITICAL: {error_type}: {error}")
            if self.notify_on_critical:
                self._send_alert(error_info)
        elif is_retryable:
            logger.warning(f"  RETRYABLE: {error_type}: {error}")
        else:
            logger.error(f"  ERROR: {error_type}: {error}")

        if reraise:
            raise error

        return {"error": str(error), "retryable": is_retryable, "critical": is_critical}

    def _is_critical(self, error: Exception) -> bool:
        critical_types = (
            AuthenticationError,
            MemoryError,
            SystemError,
        )
        return isinstance(error, critical_types)

    def _send_alert(self, error_info: dict):
        """Send alert to team (Slack, email, PagerDuty)."""
        message = (
            f"🚨 Bot CRITICAL Error\n"
            f"Bot: {error_info['bot']}\n"
            f"Error: {error_info['error_type']}: {error_info['message']}\n"
            f"Count: {error_info['count']}"
        )
        # In production: send to Slack, send email, trigger PagerDuty
        print(f"  [ALERT]: {message}")


# ─── 6. DEMO ──────────────────────────────────────────────────────────────────

def run_demo():
    logging.basicConfig(level=logging.INFO)

    print("\n── DEMO: Retry decorator ────────────────────────────────────")

    call_count = [0]

    @retry_on_failure(max_attempts=3, delay=0.1, backoff=2.0)
    def unreliable_function():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError("Connection refused")
        return "Success!"

    result = unreliable_function()
    print(f"  Result: {result} (after {call_count[0]} attempts)")

    print("\n── DEMO: Circuit breaker ────────────────────────────────────")
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    fail_count = [0]

    def failing_service():
        fail_count[0] += 1
        raise RuntimeError("Service down")

    for i in range(6):
        try:
            cb.call(failing_service)
        except RuntimeError as e:
            print(f"  Attempt {i+1}: {e}")
        except RuntimeError as e:  # Covers "Circuit OPEN" too
            print(f"  Attempt {i+1}: Circuit blocked call: {e}")

    print(f"\n  Circuit state: {cb.state}")

    print("\n── DEMO: Error handler ──────────────────────────────────────")
    handler = BotErrorHandler("DemoBot")

    errors = [
        NavigationError("https://example.com", "timeout"),
        AuthenticationError("Wrong password"),
        DataValidationError("email", "not-an-email", "invalid format"),
        RateLimitError(retry_after=30),
    ]

    for err in errors:
        result = handler.handle(err, context={"step": "demo"})
        print(f"  {type(err).__name__}: retryable={result['retryable']}, critical={result['critical']}")


if __name__ == "__main__":
    run_demo()
    print("\n  NEXT: python module_5_advanced/02_logging_and_reporting.py")

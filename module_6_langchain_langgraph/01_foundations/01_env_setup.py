"""
01_foundations/01_env_setup.py
==============================
Foundation: Environment Setup with python-dotenv

CONCEPTS COVERED:
  - Loading environment variables safely with python-dotenv
  - Validating required config at startup
  - Never hardcoding secrets in source code
"""

from dotenv import load_dotenv
import os

# ── 1. Load .env file ─────────────────────────────────────────────────────────
# By default looks for .env in cwd and parent directories
load_dotenv()

# You can also load a specific file:
# load_dotenv("/path/to/specific/.env")

# override=True forces .env values to override existing env vars
# load_dotenv(override=True)


# ── 2. Read variables ─────────────────────────────────────────────────────────
openai_key  = os.getenv("OPENAI_API_KEY")       # None if missing
anthropic_key = os.getenv("ANTHROPIC_API_KEY")  # None if missing
db_url      = os.getenv("DATABASE_URL", "sqlite:///./default.sqlite")  # with default
log_level   = os.getenv("LOG_LEVEL", "INFO")


# ── 3. Validate required variables ───────────────────────────────────────────
def require_env(*keys: str) -> dict[str, str]:
    """Raise early if any required env var is missing."""
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Copy .env.example → .env and fill in the values."
        )
    return {k: os.environ[k] for k in keys}


# ── 4. Centralized config object ─────────────────────────────────────────────
class Config:
    """Single source of truth for application configuration."""

    OPENAI_API_KEY:    str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DATABASE_URL:      str = os.getenv("DATABASE_URL", "sqlite:///./agent.sqlite")
    REDIS_URL:         str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    LOG_LEVEL:         str = os.getenv("LOG_LEVEL", "INFO")
    APP_ENV:           str = os.getenv("APP_ENV", "development")

    @classmethod
    def is_production(cls) -> bool:
        return cls.APP_ENV == "production"

    @classmethod
    def has_openai(cls) -> bool:
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def has_anthropic(cls) -> bool:
        return bool(cls.ANTHROPIC_API_KEY)


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cfg = Config()
    print(f"Environment  : {cfg.APP_ENV}")
    print(f"Log level    : {cfg.LOG_LEVEL}")
    print(f"Has OpenAI   : {cfg.has_openai()}")
    print(f"Has Anthropic: {cfg.has_anthropic()}")
    print(f"Database     : {cfg.DATABASE_URL}")
    print(f"Redis        : {cfg.REDIS_URL}")

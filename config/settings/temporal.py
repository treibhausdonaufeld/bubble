from pathlib import Path

import environ

env = environ.Env()
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent


READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# Temporal.io
# ------------------------------------------------------------------------------
# https://docs.temporal.io/docs/server/configuration
TEMPORAL_ADDRESS: str = env("TEMPORAL_ADDRESS", default="localhost:7233")
TEMPORAL_NAMESPACE: str = env("TEMPORAL_NAMESPACE", default="default")
TEMPORAL_TASK_QUEUE: str = env("TEMPORAL_TASK_QUEUE", default="bubble-task-queue")
TEMPORAL_LOG_LEVEL: str = env("TEMPORAL_LOG_LEVEL", default="INFO")
if TEMPORAL_LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    error_msg = (
        f"Invalid TEMPORAL_LOG_LEVEL: {TEMPORAL_LOG_LEVEL}. "
        "Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    raise ValueError(error_msg)

# Temporal worker configuration
TEMPORAL_MAX_CONCURRENT_ACTIVITIES: int = env.int(
    "TEMPORAL_MAX_CONCURRENT_ACTIVITIES",
    default=10,
)
TEMPORAL_MAX_CONCURRENT_WORKFLOWS: int = env.int(
    "TEMPORAL_MAX_CONCURRENT_WORKFLOWS",
    default=5,
)

# AI configuration
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", default="claude-3-5-sonnet-20241022")

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

# Temporal worker configuration
TEMPORAL_MAX_CONCURRENT_ACTIVITIES: int = env.int(
    "TEMPORAL_MAX_CONCURRENT_ACTIVITIES",
    default=10,
)
TEMPORAL_MAX_CONCURRENT_WORKFLOWS: int = env.int(
    "TEMPORAL_MAX_CONCURRENT_WORKFLOWS",
    default=5,
)

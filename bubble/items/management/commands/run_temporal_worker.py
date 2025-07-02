"""Django management command to run the Temporal worker for items."""

import asyncio
import logging
import signal
import sys
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from bubble.items.temporal.temporal_worker import TemporalWorker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to run the Temporal worker."""

    help = "Run the Temporal worker for item processing"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--temporal-address",
            type=str,
            default=getattr(settings, "TEMPORAL_ADDRESS", "localhost:7233"),
            help="Temporal server address (default: localhost:7233)",
        )
        parser.add_argument(
            "--task-queue",
            type=str,
            default=settings.TEMPORAL_TASK_QUEUE,
            help="Task queue name ",
        )
        parser.add_argument(
            "--max-activities",
            type=int,
            default=10,
            help="Maximum concurrent activities (default: 10)",
        )
        parser.add_argument(
            "--max-workflows",
            type=int,
            default=5,
            help="Maximum concurrent workflows (default: 5)",
        )
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Log level (default: INFO)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution."""
        # Configure logging
        log_level = getattr(logging, options["log_level"])
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Create worker instance
        worker = TemporalWorker(
            temporal_address=options["temporal_address"],
            task_queue=options["task_queue"],
            max_concurrent_activities=options["max_activities"],
            max_concurrent_workflows=options["max_workflows"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Temporal worker on {options['temporal_address']} "
                f"for task queue '{options['task_queue']}'",
            ),
        )

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING("Received shutdown signal, stopping worker..."),
            )
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Run the worker
            asyncio.run(self._run_worker(worker))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Worker stopped by user"))
        except Exception as err:
            logger.exception("Worker error")
            error_msg = "Worker failed"
            raise CommandError(error_msg) from err

    async def _run_worker(self, worker: TemporalWorker) -> None:
        """Run the worker with proper error handling."""
        try:
            await worker.start()
        except Exception:
            logger.exception("Worker startup failed")
            raise
        finally:
            await worker.stop()

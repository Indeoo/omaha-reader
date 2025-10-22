from pathlib import Path
from typing import Optional, List

from loguru import logger


class LogAccumulator:
    """
    Captures log messages in memory and writes them to file on demand.

    This allows conditional logging - only write logs to file when needed,
    while still maintaining console output throughout.
    """

    def __init__(self):
        self.logs: List[str] = []
        self.handler_id: Optional[int] = None

    def start_capture(self):
        """
        Start capturing logs to memory.

        Attaches a custom sink to loguru that captures formatted messages
        to an in-memory list. Filters out console-only messages.
        """
        self.logs.clear()

        # Add a custom sink that captures to memory
        self.handler_id = logger.add(
            self._capture_sink,
            format="<white>{time:HH:mm:ss}</white> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{line}</cyan> - <white>{message}</white>",
            filter=lambda record: not record["extra"].get("console_only", False),
            colorize=False  # Don't include ANSI color codes in file output
        )

    def _capture_sink(self, message):
        """Custom sink function that captures formatted log messages to memory."""
        self.logs.append(message)

    def write_to_file(self, file_path: Path):
        """
        Write accumulated logs to file.

        Args:
            file_path: Path to the log file to create/write
        """
        if not self.logs:
            return

        # Ensure parent directory exists
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write all accumulated logs
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(self.logs)

    def clear(self):
        """Clear accumulated logs from memory."""
        self.logs.clear()

    def has_logs(self) -> bool:
        """Check if any logs have been accumulated."""
        return len(self.logs) > 0

    def stop_capture(self):
        """
        Stop capturing logs and cleanup handler.

        Should be called when done with this accumulator to prevent memory leaks.
        """
        if self.handler_id is not None:
            logger.remove(self.handler_id)
            self.handler_id = None

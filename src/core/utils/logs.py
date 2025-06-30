from loguru import logger
import sys
import os
import atexit

# Create a separate logger for console-only messages
console_logger = logger.bind(console_only=True)

# Global variable to track log file path and if any logs were written
_log_file_path = None
_logs_written = False


def _check_and_cleanup_empty_log():
    global _log_file_path, _logs_written
    if _log_file_path and not _logs_written and os.path.exists(_log_file_path):
        try:
            if os.path.getsize(_log_file_path) == 0:
                os.remove(_log_file_path)
        except:
            pass


def _log_interceptor(record):
    global _logs_written
    if not record["extra"].get("console_only", False):
        _logs_written = True
    return True


def load_logger(timestamp_folder):
    global _log_file_path, _logs_written

    logger.remove()
    logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - "
                                  "<white>{message}</white>")

    _log_file_path = timestamp_folder + "/app.log"
    _logs_written = False

    logger.add(_log_file_path,
               format="<white>{time:HH:mm:ss}</white> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{line}</cyan> - <white>{"
                      "message}</white>",
               filter=lambda record: _log_interceptor(record) and not record["extra"].get("console_only", False))

    # Register cleanup function
    atexit.register(_check_and_cleanup_empty_log)
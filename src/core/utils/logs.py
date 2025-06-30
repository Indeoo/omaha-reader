from loguru import logger
import sys
import os

# Create a separate logger for console-only messages
console_logger = logger.bind(console_only=True)

_file_handler_added = False
_log_file_path = None


def load_logger(timestamp_folder):
    global _file_handler_added, _log_file_path

    logger.remove()
    logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - "
                                  "<white>{message}</white>")

    # Store the log file path but don't create the handler yet
    _log_file_path = timestamp_folder + "/app.log"
    _file_handler_added = False

    # Add a custom handler that creates the file handler on first use
    logger.add(_lazy_file_handler,
               format="<white>{time:HH:mm:ss}</white> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{line}</cyan> - <white>{"
                      "message}</white>",
               filter=lambda record: not record["extra"].get("console_only", False))


def _lazy_file_handler(message):
    global _file_handler_added, _log_file_path

    if not _file_handler_added and _log_file_path:
        # Remove the lazy handler and add the real file handler
        logger.remove(_lazy_file_handler)
        logger.add(_log_file_path,
                   format="<white>{time:HH:mm:ss}</white> | "
                          "<level>{level: <8}</level> | "
                          "<cyan>{line}</cyan> - <white>{"
                          "message}</white>",
                   filter=lambda record: not record["extra"].get("console_only", False))
        _file_handler_added = True

        # Log the current message to the newly created file handler
        logger.opt(depth=1).log(message.record["level"].name, message.record["message"])
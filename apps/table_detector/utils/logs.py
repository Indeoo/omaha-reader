import sys

from loguru import logger

# Create a separate logger for console-only messages
console_logger = logger.bind(console_only=True)


def load_logger(timestamp_folder):
    logger.remove()
    logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - "
                                  "<white>{message}</white>")

    # Only add file handler if directory exists and we expect to log something
    # The file will only be created when first message is actually written
    logger.add(timestamp_folder + "/app.log",
               format="<white>{time:HH:mm:ss}</white> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{line}</cyan> - <white>{"
                      "message}</white>",
               filter=lambda record: not record["extra"].get("console_only", False),
               delay=True)
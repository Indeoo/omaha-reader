from sys import stderr

from loguru import logger


def load_logger(timestamp_folder):
    # LOGGING SETTING
    logger.remove()
    logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - "
                              "<white>{message}</white>")
    logger.add(timestamp_folder + "/app.log",
               format="<white>{time:HH:mm:ss}</white> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{line}</cyan> - <white>{"
                      "message}</white>")

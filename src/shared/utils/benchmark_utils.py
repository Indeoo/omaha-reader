import functools
import time

from loguru import logger


def benchmark(func):
    """Simple benchmark decorator that prints execution time to console"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"⏱️  {func.__name__} executed in {execution_time:.4f} seconds")

        return result

    return wrapper
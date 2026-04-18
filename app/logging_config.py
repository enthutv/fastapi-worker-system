import logging
import sys


def setup_logging() -> None:
    """
    Configure application-wide logging once.

    We keep this simple and production-friendly:
    - timestamps
    - level
    - logger name
    - message
    """
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

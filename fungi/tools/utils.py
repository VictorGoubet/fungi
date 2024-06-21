import logging


def get_logger(name: str = "NodeLogger", level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger.

    :param name: Name of the logger.
    :param level: Logging level.
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Check if the logger already has handlers to avoid adding multiple handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

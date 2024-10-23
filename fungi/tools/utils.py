import logging


def get_logger(name: str = "P2PLogger", level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger.

    This function creates and configures a logger with the specified name and logging level.
    If a logger with the given name already exists, it returns that logger instead of creating a new one.

    :param name: Name of the logger. Defaults to "P2PLogger".
    :param level: Logging level. Defaults to logging.INFO.
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

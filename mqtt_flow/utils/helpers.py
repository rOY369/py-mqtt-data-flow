import logging


def get_logger(name, level=logging.INFO):

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

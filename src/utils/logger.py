import logging


def setup_logger(name, log_file, level=logging.INFO):
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')  # Simpler format for console
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
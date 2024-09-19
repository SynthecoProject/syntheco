"""
logger module
This module provides several levels of logging
throughout the runs of Syntheco
"""

import logging
import os


def setup_logger(
    log_file="syntheco_log.txt", data_log_file="synthco_data.txt", log_level="INFO"
):
    """
    setup_logger
    initiallizes the logger

    Arguments:
        log_file      - Filename for the general logging file
        data_log_file - Filename for the data logging file
        log_level     - Default logging level for output
                        can be ["INFO","DEBUG","WARN","ERROR","CRIT"]

    Returns
        Nothing
    """

    logger = logging.getLogger("syntheco_logger")
    logger.setLevel(log_level)

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(name)s : %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    data_logger = logging.getLogger("syntheco_data_logger")
    data_logger.setLevel("INFO")
    data_file_handler = logging.FileHandler(data_log_file)
    data_formatter = logging.Formatter("%(asctime)s: %(message)s")
    data_file_handler.setFormatter(data_formatter)
    data_logger.addHandler(data_file_handler)


def log(level="INFO", msg=None):
    """
    log

    Helper function that handles logging to the general
    syntheco output file

    Arguments:
        level - The logging level you would like to use
                can be ["INFO","DEBUG","WARN","ERROR","CRIT"]
        msg   - The message to be logged.

    Returns:
       Nothing, output is logged to files
    """

    logger = logging.getLogger("syntheco_logger")
    if msg is None:
        logger.error("Logging made without message")
        return
    if level == "INFO":
        logger.info(msg)
    elif level == "DEBUG":
        logger.debug(msg)
    elif level == "WARN":
        logger.warning(msg)
    elif level == "ERROR":
        logger.error(msg)
    elif level == "CRIT":
        logger.critical(msg)
    else:
        logger.error("Trying to log {} with an unknown level".format(msg))
    return


def data_log(msg=None):
    """
    data_log

    Helper function that handles logging to the data
    syntheco output file

    Arguments:
        msg   - The message to be logged.

    Returns:
       Nothing, output is logged to files
    """
    logger = logging.getLogger("syntheco_data_logger")

    if msg is None:
        logger.error("Logging made without message")
        return

    logger.info(msg)

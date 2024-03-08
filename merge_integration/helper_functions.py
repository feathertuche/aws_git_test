import logging
import os
from datetime import datetime


def setup_logging(level=logging.DEBUG):
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file = os.path.join(log_folder, f"apiLog_{current_date}.log")

    logging.basicConfig(
        level=level,
        filename=log_file,
        filemode="a",
        format="%(asctime)s [%(levelname)s] : %(filename)s:%(lineno)d - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        encoding="utf-8",
    )

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Create a formatter for the console handler
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] : %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    console_handler.setFormatter(formatter)

    # Create a separate logger for the console output
    console_logger = logging.getLogger("console")
    console_logger.propagate = False
    console_logger.addHandler(console_handler)


def api_log(level=logging.DEBUG, msg=""):
    # Get the console logger
    console_logger = logging.getLogger("console")

    # Log the message to the console
    console_logger.log(level, msg)

    # Log the message to the file
    logging.log(level, msg)


setup_logging()

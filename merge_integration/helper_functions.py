import logging
from datetime import datetime
import os


def api_log(level=logging.DEBUG, msg=""):
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Create the folder if it doesn't exist
    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Construct the log file path with the current date
    file = os.path.join(log_folder, f"apiLog_{current_date}.log")

    # Configure logging to write to the log file
    logging.basicConfig(level=level, filename=file, filemode='a', format='%(asctime)s [%(levelname)s] : %(filename)s:%(lineno)d - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p', encoding='utf-8')

    # Log the message
    logging.log(level, msg)
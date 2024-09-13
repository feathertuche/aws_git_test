import logging
import os
from datetime import datetime
import boto3
import watchtower

class DailyLogger:
    """
    This class is used to create a logger object that will be used to log
    """

    def __init__(self, log_folder):
        """
        This method is used to initialize the DailyLogger class
        :param log_folder:  The folder where the logs will be stored
        """
        self.log_folder = log_folder
        os.makedirs(self.log_folder, exist_ok=True)

        # Set up CloudWatch logs client
        self.cloudwatch_log_group_name = os.getenv('REQUEST_CLOUDWATCH_LOG_GROUP', 'your-default-log-group')
        self.boto3_logs_client = boto3.client("logs", region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))

    def configure_logger(self, logger_name, log_file=None, enable_console=False, enable_cloudwatch=False):
        """
        This method is used to configure the logger
        :param logger_name: The name of the logger
        :param log_file: The name of the log file (optional)
        :param enable_console: Boolean to enable console logging
        :param enable_cloudwatch: Boolean to enable CloudWatch logging
        :return: Configured logger object
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )

        # File handler (Only if log_file is provided)
        if log_file:
            log_path = os.path.join(self.log_folder, log_file)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # CloudWatch handler
        if enable_cloudwatch:
            try:
                cloudwatch_handler = watchtower.CloudWatchLogHandler(
                    boto3_client=self.boto3_logs_client,
                    log_group_name=self.cloudwatch_log_group_name,
                    stream_name=logger_name,
                    use_queues=False
                )
                cloudwatch_handler.setLevel(logging.DEBUG)
                cloudwatch_handler.setFormatter(formatter)
                logger.addHandler(cloudwatch_handler)
            except Exception as e:
                logger.error(f"Failed to set up CloudWatch logging: {e}")

        return logger

    def log_message(self, logger, level, msg, api_path=None):
        """
        Log a message
        :param logger: The logger to use
        :param level: The log level
        :param msg: The message to log
        :param api_path: The API path, if applicable
        """
        logger.log(level, msg)
        if api_path and '/api/erp/health/' in api_path:
            logger.info(f"Logged message for API path: {api_path}")

# Example Usage
current_date = datetime.now().strftime("%Y-%m-%d")
log_folder_name = os.path.join("logs", current_date)

logger_object = DailyLogger(log_folder_name)

request_logger = logger_object.configure_logger(
    "request_logger", 
    log_file=None,  # Skip file logging
    enable_console=False, 
    enable_cloudwatch=True
)

api_logger = logger_object.configure_logger(
    "api_logger", 
    log_file="None",  # File logging enabled for API logger
    enable_console=True, 
    enable_cloudwatch=True
)

def api_log(level=logging.DEBUG, msg="", api_path=None):
    """
    This function is used to log messages to the API log file
    :param level: The log level
    :param msg: The message to log
    :param api_path: The API path, if applicable
    :return:
    """
    logger_object.log_message(api_logger, level, msg, api_path)

def request_log(level=logging.DEBUG, msg=""):
    """
    This function is used to log messages to the request log file
    :param level: The log level
    :param msg: The message to log
    :return:
    """
    request_logger.log(level, msg)

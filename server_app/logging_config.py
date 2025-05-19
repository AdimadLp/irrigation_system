import logging
import os
from concurrent_log_handler import ConcurrentRotatingFileHandler
import inspect


class CustomLogger(logging.Logger):
    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
    ):
        # Get the frame of the caller
        frame = inspect.currentframe()

        # Go up the stack to find the caller's caller
        for _ in range(2):  # Adjust this number if needed
            if frame is None:
                break
            frame = frame.f_back

        if frame and frame.f_code.co_filename != __file__:
            if extra is None:
                extra = {}
            extra["custom_funcname"] = frame.f_code.co_name
            extra["scriptname"] = os.path.basename(frame.f_code.co_filename)
        else:
            extra = extra or {}
            extra["custom_funcname"] = "unknown"
            extra["scriptname"] = "unknown"

        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)


def setup_logger(name):
    logger = CustomLogger(name)

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(scriptname)s - %(custom_funcname)s - %(levelname)s - %(message)s"
    )

    # Create a file handler for all logs with a maximum file size of 10MB
    file_handler = ConcurrentRotatingFileHandler(
        "app.log", maxBytes=10 * 1024, backupCount=1
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Create a file handler for error logs with a maximum file size of 5MB
    error_file_handler = ConcurrentRotatingFileHandler(
        "error.log", maxBytes=5 * 1024 * 1024, backupCount=1
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # Create a console handler for debug logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Add a filter to only allow debug logs from your code
    def debug_filter(record):
        return (
            record.levelno == logging.DEBUG
            and "irrigation_service.py" in record.scriptname
        )

    console_handler.addFilter(debug_filter)

    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


# Set the custom logger class as the default
logging.setLoggerClass(CustomLogger)

root_logger = setup_logger("root")
logging.root = root_logger
logging.Logger.root = root_logger
logging.Logger.manager.root = root_logger

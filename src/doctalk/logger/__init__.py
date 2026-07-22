import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# one line format for every log message
LOGGING_FORMAT = "[%(asctime)s] %(levelname)s - %(module)s - %(message)s"

LOG_DIR = "logs"
LOG_FILEPATH = os.path.join(LOG_DIR, "running_logs.log")


def setup_logging(level=logging.INFO):
    '''
    set up logging once. call this from main.py at startup
    send every log line to two places:
        - Terminal to see progress live while it runs
        - logs/running_logs.log, to read after it finishes
    '''
    # make log folder if it is not there yet
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(LOGGING_FORMAT)

    # write to the file, rotates when it gets big so it never grows forever
    file_handler = RotatingFileHandler(
        LOG_FILEPATH,
        maxBytes=1_000_000,      # max size ~1 MB then it rolls over
        backupCount=3,           # keep 3 old ones : .log.1, .log.2, .log.3
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # write the same lines to the terminal
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # the root logger is the top level one, to which other loggers respond
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # only attach handlers to the root logger if not attached yet
    # helps prevent duplicate lines if run twice
    if not root_logger.hasHandlers():
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)


# the object that will be imported and called in other files, e.g. logger.info()
logger = logging.getLogger("doctalkLogger")
import logging
import traceback
import sys

def log_exception():
    """Log detailed exception information."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    logging.error("Exception details:\n" + "".join(tb_lines))
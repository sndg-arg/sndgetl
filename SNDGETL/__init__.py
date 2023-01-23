import sys
import logging

log_format = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"

def init_log(log_file_path=None, rootloglevel=logging.DEBUG):
    default_formatter = logging.Formatter(log_format)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(default_formatter)
    root = logging.getLogger()

    if log_file_path:
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(default_formatter)
        root.addHandler(fh)

    root.addHandler(console_handler)
    root.setLevel(rootloglevel)

class ProcessingException(Exception):
    def __init__(self, message, data):
        self.message = message
        self.data = data
        super().__init__(self.message)

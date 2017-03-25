import os
import logging
from logging.config import fileConfig

this_dir, this_filename = os.path.split(__file__)
log_file = os.path.join(this_dir, 'logging.ini')

fileConfig(log_file)
logger = logging.getLogger()

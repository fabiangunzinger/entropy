"""
Project configuration file.

"""

import os
from pathlib import Path

AWS_PROFILE = "3di"
AWS_PIECES = "s3://3di-data-mdb/clean/pieces"
AWS_PROJECT = "s3://3di-project-entropy"

ROOTDIR = Path(__file__).parent.parent
FIGDIR = os.path.join(ROOTDIR, "output", "figures")
TABDIR = os.path.join(ROOTDIR, "output", "tables")

# Data preprocessing parameters
# Income and spend expressed in '000s of Pounds
MAX_ACTIVE_ACCOUNTS = 10
MIN_YEAR_INCOME = 5
MIN_MONTH_SPEND = 0.2
MIN_MONTH_TXNS = 10
WIN_PCT = 1

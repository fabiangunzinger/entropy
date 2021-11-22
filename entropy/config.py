"""
Project configuration file.

"""

import os
from pathlib import Path

AWS_PROFILE = '3di'

ROOTDIR = Path(__file__).parent.parent
FIGDIR = os.path.join(ROOTDIR, 'output', 'figures')
TABDIR = os.path.join(ROOTDIR, 'output', 'tables')



